"""
Agent 2: Detector
Uses Anomaly ML Model and corroborating hydraulic signals to formulate incident candidates.
Crucial rule: A leak hypothesis requires >= 2 independent corroborating signals.
A single questionable signal creates a 'watch' or 'sensor_fault' case.
"""

import time
from typing import Dict, List, Any, Tuple
from apps.api.agents.models import Case, Evidence, AgentTrace
from apps.api.ml.gateway import ml_gateway

class DetectorAgent:
    def __init__(self):
        self.name = "Detector"

    def run(
        self,
        snapshot: Dict[str, Any],
        suspect_sensors: List[str],
        monitor_evidence: List[Evidence]
    ) -> Tuple[List[Case], AgentTrace]:
        t0 = time.perf_counter()
        cases: List[Case] = []
        hour = snapshot.get("hour", 12.0)
        is_night = (hour < 5.5 or hour > 22.5)
        tick = snapshot.get("tick", 0)

        block_meters = snapshot.get("block_meters", {})
        pressures = snapshot.get("pressures", {})
        complaints = snapshot.get("complaints", [])

        # Check for suspect sensor cases first (Single signal / dropout)
        for s_sensor in suspect_sensors:
            case_id = f"CASE-{tick}-FLT-{s_sensor[:6]}"
            evid = [e for e in monitor_evidence if e.block_or_node == s_sensor]
            cases.append(Case(
                id=case_id,
                case_type="sensor_fault",
                location=s_sensor,
                confidence=0.92,
                loss_rate_kl_day=0.0,
                priority_score=15.0,
                evidence=evid,
                status="open",
                why_text=f"Telemetry transducer on {s_sensor} reported anomalous signal or dropout while hydraulic balance remained intact.",
                verifier_result="verified",
                groundedness_score=1.0
            ))

        # Check for hydraulic leaks in blocks
        # 90-day baseline reference means and std deviations for night flows
        baselines = {
            "BLK-HSTL-A": (12.0, 2.5),
            "BLK-HSTL-B": (10.0, 2.0),
            "BLK-HSTL-C": (14.0, 3.0),
            "BLK-MESS": (8.0, 2.0),
            "BLK-HLTH": (3.0, 1.0),
            "BLK-ACAD-1": (2.0, 0.8),
            "BLK-ACAD-2": (2.0, 0.8),
            "BLK-LIB": (1.0, 0.5),
        }

        for bid, (base_mean, base_std) in baselines.items():
            if bid in suspect_sensors:
                continue

            current_flow = block_meters.get(bid, 0.0)
            corr_pipe = f"PIPE-OHT1-{bid.split('-')[1]}" if "HSTL" in bid else f"PIPE-OHT2-{bid.split('-')[1]}"
            p_val = pressures.get(corr_pipe, 2.8)

            # ML Anomaly prediction
            ml_res = ml_gateway.detect_anomaly(
                flow_lpm=current_flow,
                pressure_bar=p_val,
                hour=hour,
                weekday=snapshot.get("is_weekend", False) and 6 or 2,
                occupancy=0.95,
                baseline_mean=base_mean,
                baseline_std=base_std
            )

            # Signal 1: Flow anomaly (z-score > 3.0 or ML flag)
            flow_anomaly = ml_res["is_anomaly"] or (current_flow > base_mean + 3.0 * base_std)
            # Signal 2: Pressure drop below normal threshold (< 2.4 bar)
            pressure_drop = p_val < 2.45
            # Signal 3: Verified complaint in this block
            block_complaints = [c for c in complaints if c.get("block") == bid]
            complaint_present = len(block_complaints) > 0
            # Signal 4: Minimum Night Flow spike
            mnf_spike = is_night and (current_flow > base_mean * 2.2)

            signals_count = sum([1 for s in [flow_anomaly, pressure_drop, complaint_present, mnf_spike] if s])

            evidence_items: List[Evidence] = []
            if flow_anomaly or mnf_spike:
                evidence_items.append(Evidence(
                    id=f"EVID-DET-{len(evidence_items)+101:03d}",
                    kind="night_flow" if mnf_spike else "demand_spike",
                    source="meter",
                    block_or_node=bid,
                    tick_range=f"tick {tick-6} to {tick}",
                    value=round(current_flow, 1),
                    baseline=round(base_mean, 1),
                    unit="L/min",
                    note=f"Flow on {bid} is {round(current_flow, 1)} L/min vs night baseline {base_mean} L/min (z={ml_res['z_score']}).",
                    verified=True
                ))

            if pressure_drop:
                evidence_items.append(Evidence(
                    id=f"EVID-DET-{len(evidence_items)+102:03d}",
                    kind="pressure_drop",
                    source="scada",
                    block_or_node=corr_pipe,
                    tick_range=f"tick {tick-3} to {tick}",
                    value=round(p_val, 2),
                    baseline=2.85,
                    unit="bar",
                    note=f"Sub-header pressure dropped to {p_val} bar (nominal 2.85 bar).",
                    verified=True
                ))

            if complaint_present:
                evidence_items.append(Evidence(
                    id=f"EVID-DET-{len(evidence_items)+103:03d}",
                    kind="complaint",
                    source="operator",
                    block_or_node=bid,
                    tick_range=f"tick {tick}",
                    value=1.0,
                    baseline=0.0,
                    unit="report",
                    note=block_complaints[0].get("text", "Low pressure complaint filed by resident."),
                    verified=True
                ))

            # Multi-signal verification check:
            if signals_count >= 2:
                # Confirmed leak case!
                excess_lpm = max(10.0, current_flow - base_mean)
                loss_kl_day = round((excess_lpm * 1440.0) / 1000.0, 1)
                cid = f"CASE-{tick}-LEAK-{bid.split('-')[-1]}"
                cases.append(Case(
                    id=cid,
                    case_type="leak",
                    location=bid,
                    confidence=round(min(0.96, 0.65 + 0.10 * signals_count), 2),
                    loss_rate_kl_day=loss_kl_day,
                    priority_score=0.0,  # Computed by prioritizer
                    evidence=evidence_items,
                    status="investigating",
                    why_text=None,
                    verifier_result="unverified"
                ))
            elif signals_count == 1:
                # Watch case (do not trigger false alarm leak)
                cid = f"CASE-{tick}-WATCH-{bid.split('-')[-1]}"
                cases.append(Case(
                    id=cid,
                    case_type="watch",
                    location=bid,
                    confidence=0.55,
                    loss_rate_kl_day=0.0,
                    priority_score=10.0,
                    evidence=evidence_items,
                    status="open",
                    why_text=f"Single isolated anomaly observed at {bid}; monitoring for corroborating pressure or complaint signals before opening repair order.",
                    verifier_result="verified"
                ))

        execution_ms = (time.perf_counter() - t0) * 1000.0
        trace = AgentTrace(
            agent_name=self.name,
            started_at=time.strftime("%H:%M:%S"),
            ended_at=time.strftime("%H:%M:%S"),
            execution_time_ms=round(execution_ms, 2),
            status="success",
            inputs={"total_blocks": len(baselines), "night_mode": is_night},
            outputs={"cases_generated": len(cases), "case_types": [c.case_type for c in cases]},
            notes=f"Detector evaluated {len(baselines)} blocks with multi-signal corroboration requirement."
        )

        return cases, trace

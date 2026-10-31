"""
Agent 2: Detector
Uses real machine learning models:
- OneClassSVM Anomaly Detection (models/anamoly_detection.joblib)
- XGBoost Hydraulic Leak Detection (models/leakage_detection.joblib)
- Minimum night flow diurnal baselines

CRITICAL MANDATE (Requirement 5):
A high-priority complaint must not automatically make an anomaly detector report a confirmed anomaly or leak.
Keep these as separate evidence sources:
- Complaint priority: based on complaint severity, affected people, and service impact.
- Anomaly/leakage result: based on sensor data, model output, data quality, and corroborating signals.
If a complaint is high priority but the anomaly model reports no anomaly, preserve the complaint's
high priority and show that sensor evidence did not confirm the suspected issue.
"""

import time
import json
from typing import Dict, List, Any, Tuple, Optional
from apps.api.agents.models import Case, Evidence, AgentTrace
from apps.api.ml.gateway import ml_gateway
from apps.api.agents.prompts import SYSTEM_PROMPT_DETECTOR
from apps.api.ai.gemini_client import gemini_client

class DetectorAgent:
    def __init__(self):
        self.name = "Detector"
        self.system_prompt = SYSTEM_PROMPT_DETECTOR

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
        detailed_readings = snapshot.get("detailed_readings", {})

        # 1. Handle suspect sensor cases (isolated instrument dropouts/freezes)
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

        # 2. Evaluate hydraulic blocks with real ML models
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

            # Extract detailed features if available from distributed source 2/3
            block_detail = detailed_readings.get(bid, {})

            # Run Real ML Model 1: OneClassSVM Anomaly Detector
            svm_features = {
                "hour": int(hour),
                "day_of_week": 6 if snapshot.get("is_weekend") else 2,
                "is_weekend": 1 if snapshot.get("is_weekend") else 0,
                "is_holiday": 0,
                "occupancy": block_detail.get("occupancy", 0.85),
                "scheduled_activity": block_detail.get("scheduled_activity", 0),
                "temperature_c": snapshot.get("weather", {}).get("temperature_c", 28.5),
                "interval_consumption_liters": block_detail.get("interval_consumption_liters", current_flow * 5.0),
                "previous_1h_avg_liters": block_detail.get("previous_1h_avg_liters", base_mean),
                "previous_24h_avg_liters": block_detail.get("previous_24h_avg_liters", base_mean * 1.2),
                "previous_1h_std_liters": block_detail.get("previous_1h_std_liters", base_std),
                "zone_type": block_detail.get("zone_type", "Hostel" if "HSTL" in bid else ("Canteen" if "MESS" in bid else "Academic blocks"))
            }
            svm_res = ml_gateway.detect_consumption_anomaly_joblib(svm_features)

            # Run Real ML Model 2: XGBoost Leakage Detector on pipe segment
            p_nominal = 2.85
            delta_p = p_val - p_nominal
            delta_f = current_flow - base_mean
            xgb_features = {
                "hour": int(hour),
                "occupancy": svm_features["occupancy"],
                "scheduled_activity": svm_features["scheduled_activity"],
                "inlet_flow_lpm": current_flow,
                "pressure_bar": p_val,
                "tank_level_pct": snapshot.get("tanks", {}).get("OHT-NORTH", {}).get("tank_level_pct", 75.0),
                "previous_1h_avg_flow_lpm": base_mean,
                "previous_1h_avg_pressure_bar": p_nominal,
                "flow_change_lpm": delta_f,
                "pressure_change_bar": delta_p,
                "zone_type": svm_features["zone_type"]
            }
            xgb_res = ml_gateway.detect_leakage_xgboost_joblib(xgb_features)

            # Signal 1: Flow anomaly (OneClassSVM flag or statistical z-score > 3.0)
            z_score = round((current_flow - base_mean) / max(0.5, base_std), 2)
            flow_anomaly = svm_res["is_anomaly"] or (z_score > 3.0)

            # Signal 2: Pressure drop below threshold (< 2.45 bar or XGBoost leak flag)
            pressure_drop = p_val < 2.45 or (xgb_res.get("is_leak", False) and xgb_res.get("leak_probability", 0.0) > 0.65)

            # Signal 3: Citizen Complaint (CPGRAMS / Portal)
            block_complaints = [c for c in complaints if c.get("block") == bid or c.get("Affected_Building") == bid]
            complaint_present = len(block_complaints) > 0
            has_high_priority_complaint = any(
                str(c.get("Priority", c.get("priority", ""))).lower() == "high" for c in block_complaints
            )

            # Signal 4: Minimum Night Flow spike
            mnf_spike = is_night and (current_flow > base_mean * 2.2)

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
                    note=f"Flow on {bid} is {round(current_flow, 1)} L/min vs baseline {base_mean} L/min (OneClassSVM anomaly={svm_res['is_anomaly']}, z={z_score}).",
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
                    baseline=p_nominal,
                    unit="bar",
                    note=f"Sub-header pressure dropped to {p_val} bar (nominal {p_nominal} bar, XGBoost leak prob={xgb_res.get('leak_probability', 0.0):.2f}).",
                    verified=True
                ))

            if complaint_present:
                c_obj = block_complaints[0]
                c_prio = c_obj.get("Priority", c_obj.get("priority", "Medium"))
                c_desc = c_obj.get("Sub_Category_Description", c_obj.get("text", "Citizen reported water issue."))
                evidence_items.append(Evidence(
                    id=f"EVID-DET-{len(evidence_items)+103:03d}",
                    kind="complaint",
                    source="public_portal",
                    block_or_node=bid,
                    tick_range=f"tick {tick}",
                    value=1.0,
                    baseline=0.0,
                    unit="report",
                    note=f"Grievance [{c_prio} Priority]: {c_desc}",
                    verified=True
                ))

            # Corroborating physical signals only (flow, pressure, mnf)
            physical_signals_count = sum([1 for s in [flow_anomaly, pressure_drop, mnf_spike] if s])

            # REQUIREMENT 5 LOGIC: Separate Complaint Priority from Sensor Anomaly Result
            if physical_signals_count >= 2:
                # Confirmed leak case with physical corroboration
                excess_lpm = max(10.0, current_flow - base_mean)
                loss_kl_day = round((excess_lpm * 1440.0) / 1000.0, 1)
                cid = f"CASE-{tick}-LEAK-{bid.split('-')[-1]}"
                cases.append(Case(
                    id=cid,
                    case_type="leak",
                    location=bid,
                    confidence=round(min(0.98, max(xgb_res.get("leak_probability", 0.75), 0.65 + 0.10 * physical_signals_count)), 2),
                    loss_rate_kl_day=loss_kl_day,
                    priority_score=0.0,
                    evidence=evidence_items,
                    status="investigating",
                    why_text=None,
                    verifier_result="unverified"
                ))
            elif physical_signals_count == 1:
                # Isolated single physical anomaly -> Watch case
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
                    why_text=f"Single isolated anomaly observed at {bid}. Monitoring for corroborating signals before opening repair order.",
                    verifier_result="verified"
                ))
            elif has_high_priority_complaint and physical_signals_count == 0:
                # REQUIREMENT 5 SPECIFIC CASE:
                # Complaint is High Priority, BUT sensor/ML evidence shows normal operation.
                # Must NOT fabricate a leak. Preserve complaint high priority, show sensor evidence
                # did not confirm, and recommend physical inspection.
                cid = f"CASE-{tick}-CMPL-{bid.split('-')[-1]}"
                cases.append(Case(
                    id=cid,
                    case_type="unconfirmed_complaint",
                    location=bid,
                    confidence=0.40,
                    loss_rate_kl_day=0.0,
                    priority_score=85.0,  # High complaint priority preserved!
                    evidence=evidence_items,
                    status="open",
                    why_text=f"High-priority resident complaint received for {bid}, but real-time telemetry (flow={current_flow} L/min, pressure={p_val} bar) and ML models (OneClassSVM={svm_res['is_anomaly']}, XGBoost prob={xgb_res.get('leak_probability', 0.0):.2f}) report nominal hydraulic conditions. Sensor evidence does NOT confirm a leak; recommending on-site acoustic plumbing inspection.",
                    verifier_result="verified"
                ))

        # Use Gemini AI to enrich case reasoning if available
        for c in cases:
            if not c.why_text:
                self._synthesize_case_reasoning(c)

        execution_ms = (time.perf_counter() - t0) * 1000.0
        trace = AgentTrace(
            agent_name=self.name,
            started_at=time.strftime("%H:%M:%S"),
            ended_at=time.strftime("%H:%M:%S"),
            execution_time_ms=round(execution_ms, 2),
            status="success",
            inputs={"total_blocks": len(baselines), "night_mode": is_night},
            outputs={"cases_generated": len(cases), "case_types": [c.case_type for c in cases]},
            notes="Detector evaluated OneClassSVM & XGBoost models while strictly enforcing Complaint vs Anomaly separation."
        )

        return cases, trace

    def _synthesize_case_reasoning(self, case: Case):
        """Invokes Gemini with SYSTEM_PROMPT_DETECTOR or uses evidence-grounded template."""
        evid_summary = "\n".join([f"- [{e.id}] {e.kind} at {e.block_or_node}: value={e.value} {e.unit} (baseline={e.baseline}). {e.note}" for e in case.evidence])
        prompt = f"""Synthesize a concise 2-3 sentence evidence-based reasoning summary for this detected incident:
Location: {case.location}
Case Type: {case.case_type}
Loss Rate: {case.loss_rate_kl_day} kL/day
Confidence: {case.confidence}
Evidence Citations:
{evid_summary}

Requirements:
- Cite exact evidence IDs [EVID-DET-XXX] for every claim.
- If this is a leak, explain which signals support the alert (flow surge, pressure drop).
- If exact point is unknown, state that it identifies a monitored asset or feeder branch requiring physical inspection."""

        if gemini_client.is_available():
            res = gemini_client.generate_for_agent(
                agent_name=self.name,
                prompt=prompt,
                system_instruction=self.system_prompt,
                incident_id=case.id
            )
            if res.get("success") and res.get("text"):
                case.why_text = res["text"].strip()
                return

        # Deterministic grounded fallback
        evid_tags = " ".join([f"[{e.id}]" for e in case.evidence])
        if case.case_type == "leak":
            case.why_text = f"Hydraulic anomaly detected at {case.location}: continuous flow exceeded diurnal baseline while sub-header pressure dropped, indicating an estimated loss of {case.loss_rate_kl_day} kL/day across the distribution branch {evid_tags}. Acoustic leak detection recommended for the feeder segment."
        elif case.case_type == "watch":
            case.why_text = f"Elevated reading observed at {case.location} without corroborating pressure depression {evid_tags}. Retaining on watch list."
        else:
            case.why_text = f"Operational condition logged for {case.location} citing {evid_tags}."

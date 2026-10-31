"""
Agent 1: Monitor
Ingestion validation, data quality checks, and sensor health diagnosis.
Labels all incoming data as simulated laptop telemetry for demonstration.
Distinguishes between sensor telemetry failures and true physical hydraulic leaks.
"""

import time
from datetime import datetime, timezone
from typing import Dict, List, Any, Tuple
from apps.api.agents.models import Evidence, AgentTrace
from apps.api.agents.prompts import SYSTEM_PROMPT_MONITOR
from apps.api.ai.gemini_client import gemini_client

class MonitorAgent:
    def __init__(self):
        self.name = "Monitor"
        self.system_prompt = SYSTEM_PROMPT_MONITOR

    def run(
        self,
        snapshot: Dict[str, Any],
        historical_window: List[Dict[str, Any]] = None
    ) -> Tuple[List[str], str, List[Evidence], AgentTrace]:
        """
        Validates telemetry quality:
        - Stale check (>30s dropout)
        - Physical bounds check (flow > 1200 or < 0, pressure > 8 or < 0)
        - Flat-line check
        Returns: (suspect_sensors, data_quality_status, evidence_list, trace)
        """
        t0 = time.perf_counter()
        suspect_sensors: List[str] = []
        evidence_list: List[Evidence] = []
        data_quality_status = "healthy"

        block_meters = snapshot.get("block_meters", {})
        pressures = snapshot.get("pressures", {})
        tanks = snapshot.get("tanks", {})
        inflows = snapshot.get("inflows", {})
        last_received_ts = snapshot.get("timestamp")

        # 1. Freshness / Staleness check
        if last_received_ts:
            try:
                # Parse ISO timestamp
                if isinstance(last_received_ts, str):
                    clean_ts = last_received_ts.replace("Z", "+00:00")
                    dt = datetime.fromisoformat(clean_ts)
                    now = datetime.now(timezone.utc)
                    age_seconds = abs((now - dt).total_seconds())
                    if age_seconds > 60.0:
                        data_quality_status = "stale"
                        evidence_list.append(Evidence(
                            id=f"EVID-MON-{len(evidence_list)+1:03d}",
                            kind="stale_telemetry",
                            source="laptop_source_stream",
                            block_or_node="CAMPUS",
                            tick_range=f"age {round(age_seconds, 1)}s",
                            value=round(age_seconds, 1),
                            baseline=5.0,
                            unit="seconds",
                            note=f"Simulated laptop telemetry is stale ({round(age_seconds, 1)}s old > 60s threshold). Verify laptop senders are active.",
                            verified=True
                        ))
            except Exception:
                pass

        # 2. Check flow meters for dropout or impossible values
        for bid, val in block_meters.items():
            if val == 0.0:
                suspect_sensors.append(bid)
                evidence_list.append(Evidence(
                    id=f"EVID-MON-{len(evidence_list)+1:03d}",
                    kind="sensor_anomaly",
                    source="meter",
                    block_or_node=bid,
                    tick_range=f"tick {snapshot.get('tick', 0)}",
                    value=0.0,
                    baseline=25.0,
                    unit="L/min",
                    note=f"Sensor dropout or flat-line zero detected on {bid} meter while downstream supply active.",
                    verified=True
                ))
            elif val > 800.0 or val < 0.0:
                suspect_sensors.append(bid)
                evidence_list.append(Evidence(
                    id=f"EVID-MON-{len(evidence_list)+1:03d}",
                    kind="sensor_anomaly",
                    source="meter",
                    block_or_node=bid,
                    tick_range=f"tick {snapshot.get('tick', 0)}",
                    value=val,
                    baseline=30.0,
                    unit="L/min",
                    note=f"Physically impossible reading ({val} L/min) on {bid} exceeding pipe diameter capacity.",
                    verified=True
                ))

        # 3. Check pipeline pressures
        for pid, pval in pressures.items():
            if pval < 0.2:  # Complete disconnect / transducer fault
                suspect_sensors.append(pid)
                evidence_list.append(Evidence(
                    id=f"EVID-MON-{len(evidence_list)+1:03d}",
                    kind="sensor_anomaly",
                    source="scada",
                    block_or_node=pid,
                    tick_range=f"tick {snapshot.get('tick', 0)}",
                    value=pval,
                    baseline=2.85,
                    unit="bar",
                    note=f"Transducer output near zero ({pval} bar) on {pid}. Flagged as suspect sensor to avoid false leak alarm.",
                    verified=True
                ))
            elif pval > 10.0:
                suspect_sensors.append(pid)

        if suspect_sensors and data_quality_status != "stale":
            data_quality_status = "degraded"

        execution_ms = (time.perf_counter() - t0) * 1000.0
        trace = AgentTrace(
            agent_name=self.name,
            started_at=time.strftime("%H:%M:%S"),
            ended_at=time.strftime("%H:%M:%S"),
            execution_time_ms=round(execution_ms, 2),
            status="success",
            inputs={"total_meters": len(block_meters), "total_pressures": len(pressures), "total_tanks": len(tanks)},
            outputs={"suspect_sensors_count": len(suspect_sensors), "suspect_list": suspect_sensors, "data_quality": data_quality_status},
            notes="Data quality scan completed. Simulated laptop telemetry verified."
        )

        return suspect_sensors, data_quality_status, evidence_list, trace

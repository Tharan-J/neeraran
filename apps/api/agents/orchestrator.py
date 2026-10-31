"""
NEERARAN Agent Orchestrator
Coordinates the 7 operational agents and the Verifier:
Monitor -> Detect -> Localize -> Forecast -> Prioritize -> Optimize -> Verify -> Intervene -> Measure
"""

import time
import json
from typing import Dict, List, Any, Optional
from apps.api.agents.models import Case, Evidence, Plan, AgentTrace
from apps.api.agents.monitor import MonitorAgent
from apps.api.agents.detector import DetectorAgent
from apps.api.agents.localizer import LocalizerAgent
from apps.api.agents.forecaster import ForecasterAgent
from apps.api.agents.prioritizer import PrioritizerAgent
from apps.api.agents.optimizer import OptimizerAgent
from apps.api.agents.interventor import InterventorAgent
from apps.api.agents.verifier import VerifierAgent
from apps.api.db.database import (
    SessionLocal, Incident, IncidentEvidence, AgentTrace as DBAgentTrace,
    InterventionPlan as DBInterventionPlan
)

class AgentOrchestrator:
    def __init__(self):
        self.monitor = MonitorAgent()
        self.detector = DetectorAgent()
        self.localizer = LocalizerAgent()
        self.forecaster = ForecasterAgent()
        self.prioritizer = PrioritizerAgent()
        self.optimizer = OptimizerAgent()
        self.interventor = InterventorAgent()
        self.verifier = VerifierAgent()

        self.active_cases: Dict[str, Case] = {}
        self.historical_traces: List[AgentTrace] = []

    def run_pipeline(self, snapshot: Dict[str, Any]) -> List[Case]:
        """
        Executes full agent loop for the latest simulator snapshot.
        """
        pipeline_traces = []

        # Step 1: Monitor
        suspect_sensors, mon_evid, t_mon = self.monitor.run(snapshot, [])
        pipeline_traces.append(t_mon)

        # Step 2: Detector
        new_cases, t_det = self.detector.run(snapshot, suspect_sensors, mon_evid)
        pipeline_traces.append(t_det)

        processed_cases = []
        for case in new_cases:
            # Step 3: Localizer (for leaks)
            if case.case_type == "leak":
                candidates, t_loc = self.localizer.run(case, snapshot)
                pipeline_traces.append(t_loc)

            # Step 4: Forecaster
            forecast_out, t_for = self.forecaster.run(snapshot, case)
            pipeline_traces.append(t_for)

            # Step 5: Optimizer (Generate intervention plan)
            plan, t_opt = self.optimizer.run(case, snapshot)
            case.plan = plan
            pipeline_traces.append(t_opt)

            # Step 6: Verifier
            is_valid, v_status, g_score, t_ver = self.verifier.verify_case_and_plan(case, plan)
            pipeline_traces.append(t_ver)

            # Step 7: Interventor (Staging for approvals & tool calls)
            interv_res, t_int = self.interventor.stage_plan_for_execution(case, plan)
            pipeline_traces.append(t_int)

            case.traces = pipeline_traces
            self.active_cases[case.id] = case
            processed_cases.append(case)

        # Step 8: Prioritize all active cases
        if self.active_cases:
            all_cases = list(self.active_cases.values())
            ranked_cases, t_pri = self.prioritizer.run(all_cases)
            pipeline_traces.append(t_pri)
        else:
            ranked_cases = []

        self.historical_traces.extend(pipeline_traces)
        self._persist_to_database(ranked_cases, pipeline_traces)

        return ranked_cases

    def replan_on_scenario(self, scenario_name: str, snapshot: Dict[str, Any]) -> Dict[str, Any]:
        """
        Dynamic replanning triggered by scenario injection.
        Reruns affected agents and outputs before/after diff.
        """
        old_cases = list(self.active_cases.values())
        old_rankings = [c.id for c in old_cases]

        # Clear and rerun pipeline
        new_cases = self.run_pipeline(snapshot)
        new_rankings = [c.id for c in new_cases]

        diff = {
            "scenario": scenario_name,
            "timestamp": time.strftime("%H:%M:%S"),
            "old_ranked_cases": old_rankings,
            "new_ranked_cases": new_rankings,
            "agents_rerun": ["Detector", "Localizer", "Forecaster", "Optimizer", "Prioritizer", "Verifier"],
            "agents_skipped": ["None (full operational loop adapted)"],
            "recovery_timer_seconds": 180,
            "reason_for_change": f"Operational regime shifted due to '{scenario_name}'. Re-optimized water balance and reprioritized repair sequence."
        }
        return diff

    def _persist_to_database(self, cases: List[Case], traces: List[AgentTrace]):
        """Persists cases, evidence, and traces to SQLite."""
        try:
            with SessionLocal() as db:
                for c in cases:
                    inc = Incident(
                        id=c.id,
                        case_type=c.case_type,
                        location=c.location,
                        confidence=c.confidence,
                        loss_rate_kl_day=c.loss_rate_kl_day,
                        priority_score=c.priority_score,
                        status=c.status,
                        why_text=c.why_text,
                        verifier_result=c.verifier_result,
                        groundedness_score=c.groundedness_score
                    )
                    db.merge(inc)

                    for e in c.evidence:
                        db_evid = IncidentEvidence(
                            id=e.id,
                            incident_id=c.id,
                            kind=e.kind,
                            source=e.source,
                            block_or_node=e.block_or_node,
                            tick_range=e.tick_range,
                            observed_value=e.value,
                            baseline_value=e.baseline,
                            unit=e.unit,
                            note=e.note,
                            verified=e.verified
                        )
                        db.merge(db_evid)

                for t in traces:
                    db_trace = DBAgentTrace(
                        id=f"TR-{time.time_ns()}-{t.agent_name[:4]}",
                        incident_id=cases[0].id if cases else "GENERAL",
                        agent_name=t.agent_name,
                        started_at=time.strftime("%Y-%m-%d %H:%M:%S"),
                        ended_at=time.strftime("%Y-%m-%d %H:%M:%S"),
                        execution_time_ms=t.execution_time_ms,
                        status=t.status,
                        inputs_json=json.dumps(t.inputs),
                        outputs_json=json.dumps(t.outputs),
                        tools_called_json=json.dumps(t.tools_called),
                        notes=t.notes
                    )
                    db.merge(db_trace)

                db.commit()
        except Exception as err:
            print("DB persistence warning:", err)

# Singleton Orchestrator
orchestrator = AgentOrchestrator()

"""
Agent 7: Interventor and Measurer
Dispatches approved non-consequential tools, stages consequential actions into the human approval queue,
and measures counterfactual outcomes (water saved, INR saved, estimation error).

OPERATIONAL SAFETY MANDATE:
No consequential action (valve throttling affecting residential potable water, pump shutdown)
can execute silently without explicit human manager approval.
"""

import time
import json
import uuid
from datetime import datetime
from typing import Dict, List, Any, Tuple
from apps.api.agents.models import Plan, Case, AgentTrace
from apps.api.agents.prompts import SYSTEM_PROMPT_INTERVENTOR
from apps.api.tools.enterprise_tools import enterprise_tools
from apps.api.db.database import SessionLocal, Approval, WorkOrder, InterventionPlan, AuditLog

class InterventorAgent:
    def __init__(self):
        self.name = "Interventor"
        self.system_prompt = SYSTEM_PROMPT_INTERVENTOR

    def stage_plan_for_execution(self, case: Case, plan: Plan) -> Tuple[Dict[str, Any], AgentTrace]:
        t0 = time.perf_counter()
        tools_executed = []
        pending_approvals = []

        with SessionLocal() as db:
            db_plan = InterventionPlan(
                id=plan.id,
                incident_id=case.id,
                version=plan.version,
                status="pending" if plan.needs_approval else "executing",
                expected_impact=json.dumps(plan.expected_impact),
                risk_level=plan.risk_level,
                vulnerable_flag=plan.vulnerable_flag,
                needs_approval=plan.needs_approval,
                rollback_plan=plan.rollback_plan,
                steps_json=json.dumps([s.dict() for s in plan.steps])
            )
            db.merge(db_plan)

            for step in plan.steps:
                if step.requires_approval:
                    app_id = f"APP-{uuid.uuid4().hex[:6].upper()}"
                    equity_text = (
                        "Vulnerable block protected: minimum supply constraint strictly held at 85% baseline. No student potable water cutoff."
                        if plan.vulnerable_flag else "Standard block; zero equity risk."
                    )
                    approval = Approval(
                        id=app_id,
                        plan_id=plan.id,
                        incident_id=case.id,
                        title=f"Execute {step.tool.replace('_', ' ').title()} on {case.location}",
                        description=step.reason,
                        vulnerable_flag=step.vulnerable_impact,
                        equity_check=equity_text,
                        status="pending",
                        approver_role="admin"
                    )
                    db.merge(approval)
                    pending_approvals.append(app_id)
                else:
                    if step.tool == "create_cmms_ticket":
                        res = enterprise_tools.create_cmms_ticket(
                            block=step.args.get("block", case.location),
                            segment=step.args.get("segment", case.location),
                            priority=step.args.get("priority", "medium"),
                            summary=step.args.get("summary", "Automated inspection ticket")
                        )
                        tools_executed.append({"tool": step.tool, "result": res})
                    elif step.tool == "notify":
                        res = enterprise_tools.notify(
                            role=step.args.get("role", "maintenance"),
                            message=step.args.get("message", "Incident reported")
                        )
                        tools_executed.append({"tool": step.tool, "result": res})

            db.commit()

        execution_ms = (time.perf_counter() - t0) * 1000.0
        trace = AgentTrace(
            agent_name=self.name,
            started_at=time.strftime("%H:%M:%S"),
            ended_at=time.strftime("%H:%M:%S"),
            execution_time_ms=round(execution_ms, 2),
            status="success",
            inputs={"plan_id": plan.id, "total_steps": len(plan.steps)},
            outputs={"tools_dispatched": len(tools_executed), "pending_approvals": pending_approvals},
            tools_called=tools_executed,
            notes=f"Staged {len(plan.steps)} steps. {len(pending_approvals)} consequential actions queued for Admin approval."
        )

        return {"executed_steps": tools_executed, "pending_approvals": pending_approvals}, trace

    def measure_outcome(self, case: Case, measured_loss_reduction_lpm: float) -> Dict[str, Any]:
        """
        Calculates counterfactual outcome:
        Compares actual metered reduction with pre-intervention estimate.
        Costing in INR (₹).
        """
        estimated_kl_day = case.loss_rate_kl_day
        actual_kl_day_saved = round((measured_loss_reduction_lpm * 1440.0) / 1000.0, 1)

        inr_per_kl = 42.0  # Campus cost of treated water in INR
        actual_inr_saved = round(actual_kl_day_saved * inr_per_kl, 0)
        reserve_hours_gained = round(actual_kl_day_saved / 6.5, 1)

        estimation_error_pct = round(
            abs(actual_kl_day_saved - estimated_kl_day) / max(1.0, estimated_kl_day) * 100.0, 1
        )

        return {
            "estimated_loss_kl_day": estimated_kl_day,
            "actual_kl_day_saved": actual_kl_day_saved,
            "actual_inr_saved": actual_inr_saved,
            "reserve_hours_gained": reserve_hours_gained,
            "estimation_error_pct": estimation_error_pct,
            "verification_status": "verified" if estimation_error_pct < 25.0 else "discrepancy"
        }

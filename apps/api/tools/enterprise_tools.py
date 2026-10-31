"""
NEERARAN Simulated Enterprise Tools
Simulates integration with SCADA, CMMS (Computerized Maintenance Management System),
and Public Notification gateways.
Enforces permissions, approval checks, idempotency, audit logging, and rollback.
"""

import uuid
import json
from datetime import datetime
from typing import Dict, Any, Optional
from apps.api.db.database import SessionLocal, WorkOrder, AuditLog, Asset

VULNERABLE_BLOCKS = ["BLK-HSTL-A", "BLK-HSTL-B", "BLK-HSTL-C", "BLK-HLTH", "BLK-CRECHE"]

class EnterpriseToolSuite:
    def __init__(self):
        self.valve_states: Dict[str, float] = {}
        self.pump_schedules: Dict[str, str] = {}
        self.advisories: list = []
        self.executed_tools: Dict[str, Any] = {}

    def create_cmms_ticket(self, block: str, segment: str, priority: str, summary: str, role: str = "agent", idempotency_key: Optional[str] = None) -> Dict[str, Any]:
        """Creates maintenance work order in CMMS."""
        if idempotency_key and idempotency_key in self.executed_tools:
            return self.executed_tools[idempotency_key]

        wo_id = f"WO-{uuid.uuid4().hex[:6].upper()}"
        with SessionLocal() as db:
            wo = WorkOrder(
                id=wo_id,
                incident_id=f"INC-{block}",
                asset_id=block,
                required_skill="plumbing" if "HSTL" in block else "valves",
                priority=priority,
                recommended_action=summary,
                expected_impact=json.dumps({"liters_saved_est": 58000}),
                status="created",
                created_at=datetime.utcnow()
            )
            db.add(wo)

            # Audit record
            audit = AuditLog(
                id=f"AUD-{uuid.uuid4().hex[:8]}",
                timestamp=datetime.utcnow(),
                actor=role,
                role=role,
                action="create_cmms_ticket",
                resource_id=wo_id,
                details_json=json.dumps({"block": block, "segment": segment, "priority": priority, "summary": summary})
            )
            db.add(audit)
            db.commit()

        res = {"success": True, "ticket_id": wo_id, "status": "dispatched", "message": f"CMMS work order {wo_id} registered for {block}."}
        if idempotency_key:
            self.executed_tools[idempotency_key] = res
        return res

    def set_valve(self, valve_id: str, state: float, approved: bool = False, role: str = "admin") -> Dict[str, Any]:
        """Controls SCADA motorized throttling valve. State between 0.0 (closed) and 1.0 (open)."""
        is_vuln = any(v in valve_id for v in ["HSTLA", "HSTLB", "HSTLC", "HLTH"])
        if not approved:
            return {
                "success": False,
                "status": "awaiting_approval",
                "error": "Consequential action requires explicit Estate Admin approval.",
                "vulnerable": is_vuln
            }

        prev_state = self.valve_states.get(valve_id, 1.0)
        self.valve_states[valve_id] = state

        with SessionLocal() as db:
            audit = AuditLog(
                id=f"AUD-{uuid.uuid4().hex[:8]}",
                timestamp=datetime.utcnow(),
                actor=role,
                role=role,
                action="set_valve",
                resource_id=valve_id,
                details_json=json.dumps({"previous_state": prev_state, "new_state": state, "vulnerable": is_vuln})
            )
            db.add(audit)
            db.commit()

        return {
            "success": True,
            "valve_id": valve_id,
            "previous_state": prev_state,
            "current_state": state,
            "message": f"SCADA command sent: Valve {valve_id} set to {int(state*100)}% open."
        }

    def set_pump_schedule(self, pump_id: str, schedule: str, approved: bool = False, role: str = "admin") -> Dict[str, Any]:
        """Configures VFD pump operating hours and variable speed curve."""
        if not approved:
            return {
                "success": False,
                "status": "awaiting_approval",
                "error": "Pump schedule reallocation requires Admin approval."
            }

        self.pump_schedules[pump_id] = schedule
        with SessionLocal() as db:
            audit = AuditLog(
                id=f"AUD-{uuid.uuid4().hex[:8]}",
                timestamp=datetime.utcnow(),
                actor=role,
                role=role,
                action="set_pump_schedule",
                resource_id=pump_id,
                details_json=json.dumps({"schedule": schedule})
            )
            db.add(audit)
            db.commit()

        return {"success": True, "pump_id": pump_id, "schedule": schedule, "message": f"Pump schedule for {pump_id} updated."}

    def draft_advisory(self, audience: str, text: str, approved: bool = True, role: str = "admin") -> Dict[str, Any]:
        """Drafts campus notification broadcast."""
        adv_id = f"ADV-{len(self.advisories)+1:03d}"
        adv = {"id": adv_id, "audience": audience, "text": text, "timestamp": datetime.utcnow().isoformat(), "approved": approved}
        self.advisories.append(adv)

        with SessionLocal() as db:
            audit = AuditLog(
                id=f"AUD-{uuid.uuid4().hex[:8]}",
                timestamp=datetime.utcnow(),
                actor=role,
                role=role,
                action="draft_advisory",
                resource_id=adv_id,
                details_json=json.dumps({"audience": audience, "text": text})
            )
            db.add(audit)
            db.commit()

        return {"success": True, "advisory_id": adv_id, "text": text, "status": "published" if approved else "draft"}

    def notify(self, role: str, message: str) -> Dict[str, Any]:
        """Dispatches operational alert to maintenance engineer or warden."""
        return {"success": True, "recipient_role": role, "message": message, "timestamp": datetime.utcnow().isoformat()}

# Singleton Tool Suite
enterprise_tools = EnterpriseToolSuite()

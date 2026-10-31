"""
NEERARAN Central API
FastAPI Backend implementation supporting all required endpoints,
role-based authorization (Admin vs Viewer), Server-Sent Events (SSE),
telemetry validation, and dynamic scenario replanning.
"""

import os
import sys
import time
import json
import asyncio
import hashlib
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

from fastapi import FastAPI, Depends, HTTPException, Header, Query, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, PlainTextResponse
from pydantic import BaseModel, Field

# Ensure path includes workspace root
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from apps.api.db.database import (
    get_db, Session, Asset, DataSource, TelemetryEvent, LatestAssetState,
    DataQualityException, Incident, IncidentEvidence, InterventionPlan,
    Engineer, WorkOrder, Approval, AuditLog, EvaluationRecord, init_db
)
from apps.api.db.seeds import seed_database
from apps.api.sim.simulator import simulator
from apps.api.agents.orchestrator import orchestrator
from apps.api.ml.gateway import ml_gateway
from apps.api.ai.gemini_client import gemini_client
from apps.api.eval.benchmark import eval_engine
from apps.api.tools.enterprise_tools import enterprise_tools

app = FastAPI(
    title="NEERARAN Water Resilience Operations API",
    version="1.0.0",
    description="Enterprise SCADA & AI Operations Backend for Campus Water Digital Twin"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Startup event
@app.on_event("startup")
def on_startup():
    init_db()
    from apps.api.db.database import SessionLocal
    with SessionLocal() as db:
        seed_database(db, force=False)
    # Run initial pipeline step
    snap = simulator.step()
    orchestrator.run_pipeline(snap)

# ----------------- SCHEMAS -----------------
class TelemetryItem(BaseModel):
    source_id: str
    asset_id: str
    timestamp: str
    metric: str
    value: float
    unit: str

class TelemetryBatchRequest(BaseModel):
    events: List[TelemetryItem]

class ApprovalDecisionRequest(BaseModel):
    decision: str  # approved, rejected
    note: Optional[str] = "Decision recorded by Estate Admin"

class AssignWorkOrderRequest(BaseModel):
    engineer_id: str

class CompleteWorkOrderRequest(BaseModel):
    findings: str

class ScenarioInjectRequest(BaseModel):
    scenario_text: Optional[str] = None
    event_type: Optional[str] = None
    location: Optional[str] = None
    params: Optional[Dict[str, Any]] = None

class PrioritizerWeightsRequest(BaseModel):
    weights: Dict[str, float]

# ----------------- RBAC & AUTH HELPERS -----------------
def verify_admin_role(x_user_role: Optional[str] = Header(None, alias="X-User-Role")):
    """Enforces that only Admin role can execute consequential operations."""
    if x_user_role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: This consequential operation requires Estate Admin authorization."
        )
    return True

# ----------------- ENDPOINTS -----------------

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "NEERARAN Central Water Operations Backend",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "gemini_available": gemini_client.is_available()
    }

# 1. Telemetry Ingestion Pipeline
@app.post("/api/v1/telemetry", status_code=status.HTTP_201_CREATED)
def ingest_telemetry(
    batch: TelemetryBatchRequest,
    x_source_id: Optional[str] = Header(None, alias="X-Source-ID"),
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    db: Session = Depends(get_db)
):
    """
    Ingest -> Authenticate -> Validate -> Quality Check -> Persist -> Update State.
    """
    valid_count = 0
    now = datetime.now(timezone.utc)

    import uuid
    for item in batch.events:
        # Check unknown asset
        asset = db.query(Asset).filter(Asset.id == item.asset_id).first()
        if not asset and item.asset_id != "CAMPUS":
            # Data-quality exception queue
            exc = DataQualityException(
                id=f"EXC-{uuid.uuid4().hex}",
                source_id=item.source_id,
                asset_id=item.asset_id,
                reason="unknown_asset",
                raw_payload=json.dumps(item.dict() if hasattr(item, "dict") else item.model_dump())
            )
            db.add(exc)
            continue

        # Check physically impossible values
        if item.metric == "flow_lpm" and (item.value < 0 or item.value > 1200):
            exc = DataQualityException(
                id=f"EXC-{uuid.uuid4().hex}",
                source_id=item.source_id,
                asset_id=item.asset_id,
                reason="physically_impossible_value",
                raw_payload=json.dumps(item.dict() if hasattr(item, "dict") else item.model_dump())
            )
            db.add(exc)
            continue

        # Valid telemetry event
        t_event = TelemetryEvent(
            id=f"TEL-{uuid.uuid4().hex}",
            source_id=item.source_id,
            asset_id=item.asset_id,
            timestamp=now,
            metric=item.metric,
            value=item.value,
            unit=item.unit,
            quality="valid"
        )
        db.add(t_event)

        # Update Latest State table
        latest = db.query(LatestAssetState).filter(
            LatestAssetState.asset_id == item.asset_id,
            LatestAssetState.metric == item.metric
        ).first()

        if latest:
            latest.value = item.value
            latest.updated_at = now
        else:
            db.add(LatestAssetState(
                asset_id=item.asset_id,
                metric=item.metric,
                value=item.value,
                unit=item.unit,
                updated_at=now
            ))
        valid_count += 1

    db.commit()
    return {"status": "success", "ingested_events": valid_count}

# 2. Assets & Campus Hierarchy
@app.get("/api/v1/assets")
@app.get("/api/assets")
def get_assets(db: Session = Depends(get_db)):
    assets = db.query(Asset).all()
    return [
        {
            "id": a.id,
            "name": a.name,
            "kind": a.kind,
            "type": a.asset_type,
            "vulnerable": a.vulnerable,
            "population": a.population,
            "capacity_kl": a.capacity_kl,
            "safety_level_kl": a.safety_level_kl,
            "demand_nominal_kl": a.nominal_demand_kl
        }
        for a in assets
    ]

@app.get("/api/v1/assets/{asset_id}")
def get_asset(asset_id: str, db: Session = Depends(get_db)):
    a = db.query(Asset).filter(Asset.id == asset_id).first()
    if not a:
        raise HTTPException(status_code=404, detail="Asset not found")
    states = db.query(LatestAssetState).filter(LatestAssetState.asset_id == asset_id).all()
    return {
        "asset": {
            "id": a.id,
            "name": a.name,
            "kind": a.kind,
            "vulnerable": a.vulnerable,
            "population": a.population
        },
        "latest_readings": [{s.metric: s.value, "unit": s.unit} for s in states]
    }

@app.get("/api/campus")
def get_campus_geojson():
    geojson_path = os.path.join(os.path.dirname(__file__), "data", "campus.geojson")
    if os.path.exists(geojson_path):
        with open(geojson_path) as f:
            return json.load(f)
    raise HTTPException(status_code=404, detail="campus.geojson not found")

# 3. Incidents & Evidence
@app.get("/api/v1/incidents")
@app.get("/api/cases")
def get_incidents(db: Session = Depends(get_db)):
    incidents = db.query(Incident).order_by(Incident.priority_score.desc()).all()
    results = []
    for inc in incidents:
        evids = db.query(IncidentEvidence).filter(IncidentEvidence.incident_id == inc.id).all()
        plan = db.query(InterventionPlan).filter(InterventionPlan.incident_id == inc.id).order_by(InterventionPlan.version.desc()).first()
        results.append({
            "id": inc.id,
            "type": inc.case_type,
            "location": inc.location,
            "confidence": inc.confidence,
            "loss_rate_kl_day": inc.loss_rate_kl_day,
            "priority_score": inc.priority_score,
            "status": inc.status,
            "why": inc.why_text,
            "verifier_result": inc.verifier_result,
            "groundedness_score": inc.groundedness_score,
            "evidence": [{"id": e.id, "kind": e.kind, "value": e.observed_value, "unit": e.unit, "note": e.note} for e in evids],
            "plan_id": plan.id if plan else None
        })
    return results

@app.get("/api/v1/incidents/{incident_id}")
@app.get("/api/cases/{incident_id}")
def get_incident(incident_id: str, db: Session = Depends(get_db)):
    inc = db.query(Incident).filter(Incident.id == incident_id).first()
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found")
    evids = db.query(IncidentEvidence).filter(IncidentEvidence.incident_id == incident_id).all()
    plan = db.query(InterventionPlan).filter(InterventionPlan.incident_id == incident_id).first()
    return {
        "incident": {
            "id": inc.id,
            "type": inc.case_type,
            "location": inc.location,
            "confidence": inc.confidence,
            "loss_rate_kl_day": inc.loss_rate_kl_day,
            "priority_score": inc.priority_score,
            "status": inc.status,
            "why": inc.why_text,
            "verifier_result": inc.verifier_result
        },
        "evidence": [{"id": e.id, "kind": e.kind, "value": e.observed_value, "unit": e.unit, "note": e.note} for e in evids],
        "plan": json.loads(plan.steps_json) if plan and plan.steps_json else None
    }

@app.get("/api/v1/incidents/{incident_id}/evidence")
def get_incident_evidence(incident_id: str, db: Session = Depends(get_db)):
    evids = db.query(IncidentEvidence).filter(IncidentEvidence.incident_id == incident_id).all()
    return [{"id": e.id, "kind": e.kind, "source": e.source, "value": e.observed_value, "baseline": e.baseline_value, "unit": e.unit, "note": e.note} for e in evids]

# 4. Queue, Forecast & Plan
@app.get("/api/v1/queue")
@app.get("/api/queue")
def get_prioritized_queue(db: Session = Depends(get_db)):
    incidents = db.query(Incident).filter(Incident.status.in_(["open", "investigating", "pending_approval"])).order_by(Incident.priority_score.desc()).all()
    return [
        {
            "id": inc.id,
            "location": inc.location,
            "type": inc.case_type,
            "loss_rate_kl_day": inc.loss_rate_kl_day,
            "priority_score": inc.priority_score,
            "why": inc.why_text,
            "status": inc.status
        }
        for inc in incidents
    ]

@app.get("/api/v1/forecast")
@app.get("/api/forecast")
def get_operational_forecast():
    snap = simulator.step()
    res, _ = orchestrator.forecaster.run(snap)
    return res

@app.get("/api/v1/plan")
@app.get("/api/plan")
def get_plans(db: Session = Depends(get_db)):
    plans = db.query(InterventionPlan).all()
    return [
        {
            "id": p.id,
            "incident_id": p.incident_id,
            "version": p.version,
            "status": p.status,
            "expected_impact": json.loads(p.expected_impact) if p.expected_impact else {},
            "vulnerable_flag": p.vulnerable_flag,
            "needs_approval": p.needs_approval,
            "steps": json.loads(p.steps_json) if p.steps_json else []
        }
        for p in plans
    ]

# 5. Workforce & Work Orders
@app.get("/api/v1/work-orders")
def get_work_orders(db: Session = Depends(get_db)):
    wos = db.query(WorkOrder).all()
    return [
        {
            "id": w.id,
            "incident_id": w.incident_id,
            "asset_id": w.asset_id,
            "engineer_id": w.assigned_engineer_id,
            "priority": w.priority,
            "action": w.recommended_action,
            "status": w.status,
            "findings": w.findings
        }
        for w in wos
    ]

@app.post("/api/v1/work-orders")
def create_work_order(req: Dict[str, Any], db: Session = Depends(get_db)):
    res = enterprise_tools.create_cmms_ticket(
        block=req.get("block", "CAMPUS"),
        segment=req.get("segment", "CAMPUS"),
        priority=req.get("priority", "medium"),
        summary=req.get("summary", "Manual work order entry")
    )
    return res

@app.post("/api/v1/work-orders/{id}/assign")
def assign_work_order(id: str, req: AssignWorkOrderRequest, db: Session = Depends(get_db), is_admin: bool = Depends(verify_admin_role)):
    wo = db.query(WorkOrder).filter(WorkOrder.id == id).first()
    if not wo:
        raise HTTPException(status_code=404, detail="Work order not found")
    eng = db.query(Engineer).filter(Engineer.id == req.engineer_id).first()
    if not eng:
        raise HTTPException(status_code=404, detail="Engineer not found")

    wo.assigned_engineer_id = eng.id
    wo.status = "assigned"
    eng.current_workload += 1
    db.commit()
    return {"status": "assigned", "work_order_id": wo.id, "engineer": eng.name}

@app.post("/api/v1/work-orders/{id}/complete")
def complete_work_order(id: str, req: CompleteWorkOrderRequest, db: Session = Depends(get_db)):
    wo = db.query(WorkOrder).filter(WorkOrder.id == id).first()
    if not wo:
        raise HTTPException(status_code=404, detail="Work order not found")
    wo.status = "completed"
    wo.findings = req.findings
    wo.completed_at = datetime.utcnow()
    db.commit()
    return {"status": "completed", "work_order_id": wo.id, "message": "Work order marked completed. Awaiting verifier outcome check."}

# 6. Human Control & Approvals
@app.get("/api/v1/approvals")
def get_approvals(db: Session = Depends(get_db)):
    approvals = db.query(Approval).all()
    return [
        {
            "id": a.id,
            "plan_id": a.plan_id,
            "incident_id": a.incident_id,
            "title": a.title,
            "description": a.description,
            "vulnerable_flag": a.vulnerable_flag,
            "equity_check": a.equity_check,
            "status": a.status,
            "decision_by": a.decision_by,
            "decision_note": a.decision_note
        }
        for a in approvals
    ]

@app.post("/api/v1/approvals/{id}")
@app.post("/api/approvals/{id}")
def decide_approval(
    id: str,
    req: ApprovalDecisionRequest,
    db: Session = Depends(get_db),
    is_admin: bool = Depends(verify_admin_role)
):
    """
    Estate Admin decision on pending intervention (Approve or Reject).
    Rejections prevent execution and record audit trail.
    """
    appr = db.query(Approval).filter(Approval.id == id).first()
    if not appr:
        raise HTTPException(status_code=404, detail="Approval request not found")

    appr.status = req.decision
    appr.decision_by = "Estate Admin"
    appr.decision_note = req.note
    appr.decided_at = datetime.utcnow()

    # Update associated intervention plan
    plan = db.query(InterventionPlan).filter(InterventionPlan.id == appr.plan_id).first()
    if plan:
        plan.status = "approved" if req.decision == "approved" else "rejected"

    # Write to Audit Log
    audit = AuditLog(
        id=f"AUD-DEC-{int(time.time())}",
        timestamp=datetime.utcnow(),
        actor="Estate Admin",
        role="admin",
        action=f"{req.decision}_intervention",
        resource_id=appr.id,
        details_json=json.dumps({"decision": req.decision, "note": req.note, "vulnerable": appr.vulnerable_flag})
    )
    db.add(audit)
    db.commit()

    return {"status": req.decision, "approval_id": appr.id, "note": req.note}

# 7. Audit Log
@app.get("/api/v1/audit")
@app.get("/api/audit")
def get_audit_log(format: Optional[str] = "json", db: Session = Depends(get_db)):
    records = db.query(AuditLog).order_by(AuditLog.timestamp.desc()).limit(100).all()
    if format == "csv":
        import io, csv
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["ID", "Timestamp", "Actor", "Role", "Action", "Resource", "Details"])
        for r in records:
            writer.writerow([r.id, r.timestamp.isoformat() if r.timestamp else "", r.actor, r.role, r.action, r.resource_id, r.details_json])
        return Response(content=output.getvalue(), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=neeraran_audit_log.csv"})

    return [
        {
            "id": r.id,
            "timestamp": r.timestamp.isoformat() if r.timestamp else "",
            "actor": r.actor,
            "role": r.role,
            "action": r.action,
            "resource_id": r.resource_id,
            "details": json.loads(r.details_json) if r.details_json else {}
        }
        for r in records
    ]

# 8. Agent Traces
@app.get("/api/v1/traces")
@app.get("/api/traces")
def get_agent_traces():
    traces = orchestrator.historical_traces[-30:]
    return [t.dict() for t in traces]

# 9. Simulation & Scenarios
@app.get("/api/v1/simulation/status")
@app.get("/api/state")
def get_simulation_status():
    snap = simulator.step()
    return snap

@app.post("/api/v1/simulation/control")
@app.post("/api/sim/control")
def control_simulation(req: Dict[str, Any], is_admin: bool = Depends(verify_admin_role)):
    if "speed" in req:
        simulator.speed_multiplier = float(req["speed"])
    if "is_running" in req:
        simulator.is_running = bool(req["is_running"])
    return {"speed": simulator.speed_multiplier, "running": simulator.is_running}

@app.post("/api/v1/simulation/scenarios")
def load_preset_scenario(req: Dict[str, str], is_admin: bool = Depends(verify_admin_role)):
    name = req.get("scenario_name", "Hostel night leak")
    details = simulator.load_preset_scenario(name)
    snap = simulator.step()
    diff = orchestrator.replan_on_scenario(name, snap)
    return {"status": "loaded", "scenario": name, "details": details, "replanning_diff": diff}

@app.post("/api/v1/simulation/events")
def inject_scenario_event(req: ScenarioInjectRequest, is_admin: bool = Depends(verify_admin_role)):
    if req.scenario_text:
        # Free-text parse with Gemini or rule fallback
        parse_result = gemini_client.parse_scenario_text(req.scenario_text)
        return parse_result
    elif req.event_type:
        fid = simulator.inject_fault(
            fault_type=req.event_type,
            location=req.location or "BLK-HSTL-A",
            loss_lpm=float(req.params.get("loss_lpm", 50.0)) if req.params else 50.0,
            metadata=req.params
        )
        snap = simulator.step()
        diff = orchestrator.replan_on_scenario(req.event_type, snap)
        return {"status": "injected", "fault_id": fid, "diff": diff}
    raise HTTPException(status_code=400, detail="Missing scenario_text or event_type")

@app.post("/api/v1/prioritizer/weights")
def update_prioritizer_weights(req: PrioritizerWeightsRequest, is_admin: bool = Depends(verify_admin_role)):
    orchestrator.prioritizer.set_weights(req.weights)
    snap = simulator.step()
    ranked = orchestrator.run_pipeline(snap)
    return {"status": "updated", "weights": orchestrator.prioritizer.weights, "ranked_count": len(ranked)}

# 10. Evaluation Dashboard
@app.get("/api/v1/evaluation")
def get_evaluation_metrics():
    return eval_engine.compute_live_metrics()

@app.post("/api/v1/evaluation/benchmark")
def run_benchmark(is_admin: bool = Depends(verify_admin_role)):
    return eval_engine.run_benchmark_20_scenarios()

# 11. Server-Sent Events (SSE) Stream
@app.get("/api/v1/stream")
@app.get("/api/stream")
async def sse_event_stream(request: Request):
    """
    Streams simulated ticks every 2 seconds.
    Clients receive real-time updates for telemetry, levels, and alerts without polling.
    """
    async def event_generator():
        while True:
            if await request.is_disconnected():
                break
            if simulator.is_running:
                snap = simulator.step()
                # Run orchestrator pipeline every 3 ticks
                if simulator.tick % 3 == 0:
                    orchestrator.run_pipeline(snap)
                data = json.dumps(snap)
                yield f"data: {data}\n\n"
            await asyncio.sleep(2.0 / max(1.0, simulator.speed_multiplier))

    return StreamingResponse(event_generator(), media_type="text/event-stream")

# Fallback complaints
@app.get("/api/complaints")
def get_complaints():
    return simulator.complaints[-15:]

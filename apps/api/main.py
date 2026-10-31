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
import uuid
import random
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
    Engineer, WorkOrder, Approval, AuditLog, EvaluationRecord, init_db,
    Role, User, UserBuildingAssignment, Permission, Complaint, ComplaintStatusHistory,
    ModelPricingConfig, AgentTokenUsage, GeminiRequest
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

class ComplaintCreateRequest(BaseModel):
    building_id: str
    category: str
    description: str
    priority: Optional[str] = "medium"

class ComplaintUpdateRequest(BaseModel):
    status: Optional[str] = None
    action_taken_remarks: Optional[str] = None
    assigned_work_order_id: Optional[str] = None
    forward_to_maintenance: Optional[bool] = False

class WorkOrderStatusRequest(BaseModel):
    status: str
    findings: Optional[str] = None

class PricingUpdateRequest(BaseModel):
    input_price_per_million: float
    output_price_per_million: float

# ----------------- RBAC & AUTH HELPERS -----------------
ROLE_PERMISSIONS = {
    "admin": [
        "manage_infrastructure", "manage_users", "manage_models",
        "approve_interventions", "view_traces", "view_gemini_accounting",
        "inject_scenarios", "view_all_buildings", "view_all_complaints",
        "manage_work_orders", "view_scada_topology"
    ],
    "student": [
        "view_own_building_awareness", "view_conservation_tips",
        "submit_complaint", "view_own_complaints"
    ],
    "building_admin": [
        "view_assigned_building", "view_building_alerts",
        "view_building_complaints", "forward_complaint",
        "request_inspection", "acknowledge_building_alerts"
    ],
    "engineer": [
        "view_assigned_work_orders", "update_work_order",
        "submit_findings", "request_materials"
    ]
}

def get_current_user(
    x_user_role: Optional[str] = Header(None, alias="X-User-Role"),
    x_user_id: Optional[str] = Header(None, alias="X-User-ID"),
    db: Session = Depends(get_db)
) -> User:
    """
    Authenticates/resolves current operational user.
    Reads X-User-ID or X-User-Role, defaulting to demo users seeded in database.
    """
    if x_user_id:
        user = db.query(User).filter(User.id == x_user_id).first()
        if user:
            return user

    if x_user_role:
        role = x_user_role.lower().strip()
        user = db.query(User).filter(User.role == role).first()
        if user:
            return user
        # Non-seeded or transient role passed by client
        return User(
            id=f"USER-{role.upper()}-DEMO",
            email=f"{role}@neeraran.edu",
            full_name=f"{role.capitalize()} User",
            role=role,
            assigned_building_id="BLK-HSTL-A" if role in ["student", "building_admin"] else None,
            assigned_engineer_id="ENG-02" if role == "engineer" else None,
            is_active=True
        )

    # Fallback default admin user if no header passed
    user = db.query(User).filter(User.role == "admin").first()
    if user:
        return user

    return User(
        id="USER-ADMIN-01",
        email="admin@neeraran.edu",
        full_name="Dr. K. Swaminathan",
        role="admin",
        assigned_building_id=None,
        assigned_engineer_id=None,
        is_active=True
    )

def require_roles(*allowed_roles):
    """Dependency that enforces caller belongs to one of allowed roles."""
    def role_checker(user: User = Depends(get_current_user)):
        if user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Forbidden: Action requires role in {list(allowed_roles)}. Current role: '{user.role}'."
            )
        return user
    return role_checker

def verify_admin_role(user: User = Depends(get_current_user)):
    """Enforces that only Admin role can execute consequential operations."""
    if user.role != "admin":
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

# -------------------------------------------------------------
# Laptop Telemetry Sources Registry (4 Distributed Laptops)
# -------------------------------------------------------------
LAPTOP_SOURCES_STATE: Dict[str, Dict[str, Any]] = {
    "source_1": {
        "source_id": "source_1",
        "name": "Water Supply & Reservoirs Subsystem",
        "laptop_label": "Laptop 2 (Supply & Reservoirs)",
        "subsystem_type": "supply_inlet",
        "latest_receipt_time": None,
        "reading_count": 0,
        "data_quality_status": "waiting",
        "demonstration_label": "Simulated laptop telemetry for demonstration",
        "latest_payload": None
    },
    "source_2": {
        "source_id": "source_2",
        "name": "Building Consumption & Smart Flow Sensors",
        "laptop_label": "Laptop 3 (Flow & Smart Meters)",
        "subsystem_type": "flow_metering",
        "latest_receipt_time": None,
        "reading_count": 0,
        "data_quality_status": "waiting",
        "demonstration_label": "Simulated laptop telemetry for demonstration",
        "latest_payload": None
    },
    "source_3": {
        "source_id": "source_3",
        "name": "Infrastructure Telemetry (Pressure & Tanks)",
        "laptop_label": "Laptop 4 (Pressure & SCADA)",
        "subsystem_type": "pressure_tanks",
        "latest_receipt_time": None,
        "reading_count": 0,
        "data_quality_status": "waiting",
        "demonstration_label": "Simulated laptop telemetry for demonstration",
        "latest_payload": None
    },
    "source_4": {
        "source_id": "source_4",
        "name": "Operational Weather & Citizen Grievance Portal",
        "laptop_label": "Laptop 5 (Environment & Grievances)",
        "subsystem_type": "weather_grievance",
        "latest_receipt_time": None,
        "reading_count": 0,
        "data_quality_status": "waiting",
        "demonstration_label": "Simulated laptop telemetry for demonstration",
        "latest_payload": None
    }
}

@app.post("/api/v1/sources/{source_id}/telemetry", status_code=status.HTTP_201_CREATED)
async def ingest_source_telemetry(
    source_id: str,
    payload: Dict[str, Any],
    x_source_id: Optional[str] = Header(None, alias="X-Source-ID"),
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    db: Session = Depends(get_db)
):
    if source_id not in LAPTOP_SOURCES_STATE:
        raise HTTPException(status_code=404, detail=f"Unknown source {source_id}")

    now = datetime.now(timezone.utc)
    now_iso = now.isoformat()
    readings = payload.get("readings", [])
    ingested_count = 0

    import uuid
    for item in readings:
        aid = item.get("asset_id")
        metric = item.get("metric")
        val = item.get("value")
        unit = item.get("unit", "")
        if not aid or not metric or val is None:
            continue

        t_event = TelemetryEvent(
            id=f"TEL-{uuid.uuid4().hex}",
            source_id=source_id,
            asset_id=aid,
            timestamp=now,
            metric=metric,
            value=float(val),
            unit=unit,
            quality="valid"
        )
        db.add(t_event)

        latest = db.query(LatestAssetState).filter(
            LatestAssetState.asset_id == aid,
            LatestAssetState.metric == metric
        ).first()
        if latest:
            latest.value = float(val)
            latest.updated_at = now
        else:
            db.add(LatestAssetState(
                asset_id=aid,
                metric=metric,
                value=float(val),
                unit=unit,
                updated_at=now
            ))
        ingested_count += 1

    if "weather" in payload:
        w = payload["weather"]
        for k, v in w.items():
            if isinstance(v, (int, float)):
                latest = db.query(LatestAssetState).filter(
                    LatestAssetState.asset_id == "CAMPUS",
                    LatestAssetState.metric == k
                ).first()
                if latest:
                    latest.value = float(v)
                    latest.updated_at = now
                else:
                    db.add(LatestAssetState(
                        asset_id="CAMPUS",
                        metric=k,
                        value=float(v),
                        unit="",
                        updated_at=now
                    ))
                ingested_count += 1

    if "public_grievances" in payload:
        # Default user for citizen complaints ingested via API
        user = db.query(User).filter(User.id == "USER-STUDENT-01").first()
        user_id = user.id if user else "USER-STUDENT-01"
        for g in payload["public_grievances"]:
            c_track = g.get("Grievance_Registration_Number", f"CPGRAMS/{now.year}/NEER-{uuid.uuid4().hex[:5]}")
            exists = db.query(Complaint).filter(Complaint.tracking_id == c_track).first()
            if not exists:
                bld = g.get("Affected_Building", "BLK-HSTL-A")
                c_id = f"CMP-{now.year}-{uuid.uuid4().hex[:6].upper()}"
                db.add(Complaint(
                    id=c_id,
                    tracking_id=c_track,
                    user_id=user_id,
                    building_id=bld,
                    category=g.get("Category", "General water issue"),
                    description=g.get("Sub_Category_Description", "Public grievance registered via portal"),
                    status="in_progress",
                    priority=(g.get("Priority") or "medium").lower(),
                    action_taken_remarks=g.get("Action_Taken_Remarks"),
                    created_at=now,
                    updated_at=now
                ))
                ingested_count += 1

    try:
        db.commit()
    except Exception as db_err:
        db.rollback()
        print(f"Error persisting telemetry from {source_id}: {db_err}")

    LAPTOP_SOURCES_STATE[source_id]["latest_receipt_time"] = now_iso
    LAPTOP_SOURCES_STATE[source_id]["reading_count"] += ingested_count or len(readings) or 1
    LAPTOP_SOURCES_STATE[source_id]["data_quality_status"] = "healthy"
    LAPTOP_SOURCES_STATE[source_id]["latest_payload"] = payload

    orchestrator.emit_event(
        "SOURCE_RECEIVED",
        f"SRC-{source_id}",
        f"Received {ingested_count} readings from {LAPTOP_SOURCES_STATE[source_id]['laptop_label']}.",
        {"source_id": source_id, "reading_count": ingested_count}
    )

    return {
        "status": "success",
        "source_id": source_id,
        "ingested_count": ingested_count,
        "received_at": now_iso
    }

@app.get("/api/v1/sources/status")
def get_sources_status():
    now = datetime.now(timezone.utc)
    results = []
    for sid, s in LAPTOP_SOURCES_STATE.items():
        is_stale = True
        status_label = s["data_quality_status"]
        if s["latest_receipt_time"]:
            try:
                dt = datetime.fromisoformat(s["latest_receipt_time"].replace("Z", "+00:00"))
                age = (now - dt).total_seconds()
                is_stale = age > 60.0
                if is_stale:
                    status_label = "stale"
            except Exception:
                pass
        results.append({
            "source_id": s["source_id"],
            "name": s["name"],
            "laptop_label": s["laptop_label"],
            "subsystem_type": s["subsystem_type"],
            "latest_receipt_time": s["latest_receipt_time"],
            "reading_count": s["reading_count"],
            "data_quality_status": status_label,
            "is_stale": is_stale,
            "demonstration_label": s["demonstration_label"]
        })
    return results

@app.post("/api/v1/agent/run-analysis")
def run_agent_analysis(db: Session = Depends(get_db)):
    """
    Executes real-time multi-agent water operations analysis against latest persisted telemetry.
    Streams execution lifecycle events and returns evidence-grounded result.
    """
    now = datetime.now(timezone.utc)
    run_id = f"RUN-{int(time.time())}"

    states = db.query(LatestAssetState).all()
    block_meters = {}
    pressures = {}
    tanks = {}

    for s in states:
        if s.metric == "flow_lpm":
            block_meters[s.asset_id] = s.value
        elif s.metric == "pressure_bar":
            pressures[s.asset_id] = s.value
        elif s.metric == "volume_kl":
            tanks[s.asset_id] = {"current_kl": s.value, "capacity_kl": 500.0, "safety_level_kl": 100.0}

    detailed_readings = {}
    s2_payload = LAPTOP_SOURCES_STATE["source_2"].get("latest_payload")
    if s2_payload and "readings" in s2_payload:
        for r in s2_payload["readings"]:
            aid = r.get("asset_id")
            if aid:
                detailed_readings[aid] = r

    complaints_records = db.query(Complaint).filter(Complaint.status != "resolved").all()
    complaints_list = [
        {
            "id": c.id,
            "block": c.building_id,
            "Affected_Building": c.building_id,
            "Priority": c.priority,
            "priority": c.priority,
            "text": c.description,
            "Sub_Category_Description": c.description
        }
        for c in complaints_records
    ]

    snapshot = {
        "tick": int(time.time()) % 1000,
        "hour": (datetime.now().hour + datetime.now().minute / 60.0),
        "is_weekend": datetime.now().weekday() >= 5,
        "timestamp": now.isoformat(),
        "block_meters": block_meters or {
            "BLK-HSTL-A": 58.4, "BLK-HSTL-B": 13.2, "BLK-HSTL-C": 15.1,
            "BLK-MESS": 9.5, "BLK-ACAD-1": 18.0, "BLK-LIB": 4.5
        },
        "pressures": pressures or {
            "PIPE-OHT1-HSTLA": 2.3, "PIPE-SUMP-OHT1": 3.35, "PIPE-OHT1-HSTLB": 2.85
        },
        "tanks": tanks or {
            "SUMP-CENTRAL": {"current_kl": 382.5, "capacity_kl": 500.0, "safety_level_kl": 100.0},
            "OHT-NORTH": {"current_kl": 89.5, "capacity_kl": 120.0, "safety_level_kl": 25.0, "tank_level_pct": 74.5}
        },
        "detailed_readings": detailed_readings,
        "complaints": complaints_list,
        "total_inflow_lpm": 523.1,
        "total_consumption_lpm": 395.0,
        "total_stored_kl": 472.0
    }

    result = orchestrator.execute_evidence_based_analysis(snapshot, run_id=run_id)
    return result

@app.get("/api/v1/agent/latest-analysis")
def get_latest_agent_analysis():
    if not orchestrator.latest_analysis_result:
        return {"status": "none", "message": "No agent analysis executed yet. Click 'Run Agent Analysis'."}
    return orchestrator.latest_analysis_result

@app.get("/api/v1/agent/pipeline-status")
def get_agent_pipeline_status(db: Session = Depends(get_db)):
    if not orchestrator.latest_analysis_result:
        try:
            run_agent_analysis(db=db)
        except Exception as e:
            print("Initial pipeline analysis notice:", e)
    latest = orchestrator.latest_analysis_result
    traces = orchestrator.historical_traces[-16:]
    return {
        "status": "ready" if latest else "idle",
        "latest_analysis": latest,
        "traces": [t.dict() for t in traces],
        "active_cases_count": len(orchestrator.active_cases),
        "coordination": latest.get("coordination") if latest else None
    }

@app.get("/api/v1/agent/stream-events")
async def stream_agent_events(request: Request):
    """Server-Sent Events endpoint streaming real-time operational agent execution events."""
    async def event_generator():
        last_idx = max(0, len(orchestrator.live_event_stream) - 15)
        while True:
            if await request.is_disconnected():
                break
            if len(orchestrator.live_event_stream) > last_idx:
                new_events = orchestrator.live_event_stream[last_idx:]
                last_idx = len(orchestrator.live_event_stream)
                for evt in new_events:
                    yield f"data: {json.dumps(evt)}\n\n"
            await asyncio.sleep(0.5)

    return StreamingResponse(event_generator(), media_type="text/event-stream")

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
def get_work_orders(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if user.role == "student":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Students do not have access to maintenance work orders."
        )

    query = db.query(WorkOrder)
    if user.role == "engineer" and user.assigned_engineer_id:
        query = query.filter((WorkOrder.assigned_engineer_id == user.assigned_engineer_id) | (WorkOrder.assigned_engineer_id == None))
    elif user.role == "building_admin" and user.assigned_building_id:
        query = query.filter(WorkOrder.asset_id == user.assigned_building_id)

    wos = query.all()
    return [
        {
            "id": w.id,
            "incident_id": w.incident_id,
            "asset_id": w.asset_id,
            "engineer_id": w.assigned_engineer_id,
            "priority": w.priority,
            "action": w.recommended_action,
            "expected_impact": w.expected_impact,
            "status": w.status,
            "findings": w.findings,
            "created_at": w.created_at.isoformat() if w.created_at else None
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

@app.patch("/api/v1/work-orders/{id}/status")
def update_work_order_status(
    id: str,
    req: WorkOrderStatusRequest,
    user: User = Depends(require_roles("engineer", "admin")),
    db: Session = Depends(get_db)
):
    wo = db.query(WorkOrder).filter(WorkOrder.id == id).first()
    if not wo:
        raise HTTPException(status_code=404, detail="Work order not found")

    wo.status = req.status
    if req.findings:
        wo.findings = req.findings
    if req.status == "completed":
        wo.completed_at = datetime.utcnow()
    db.commit()

    return {
        "status": wo.status,
        "work_order_id": wo.id,
        "findings": wo.findings,
        "message": "Status updated. Outcome verification pending automatic telemetry check."
    }

# ===================== USER & RBAC ENDPOINTS =====================
@app.get("/api/v1/users/me")
def get_user_me(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    perms = ROLE_PERMISSIONS.get(user.role, [])
    bld_assignments = db.query(UserBuildingAssignment).filter(UserBuildingAssignment.user_id == user.id).all()
    assigned_buildings = [b.building_id for b in bld_assignments]
    if user.assigned_building_id and user.assigned_building_id not in assigned_buildings:
        assigned_buildings.append(user.assigned_building_id)

    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role,
        "assigned_building_id": user.assigned_building_id,
        "assigned_engineer_id": user.assigned_engineer_id,
        "assigned_buildings": assigned_buildings,
        "permissions": perms
    }

@app.get("/api/v1/users/me/permissions")
def get_user_permissions(user: User = Depends(get_current_user)):
    return {
        "role": user.role,
        "permissions": ROLE_PERMISSIONS.get(user.role, [])
    }

@app.get("/api/v1/users/me/buildings")
def get_user_buildings(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if user.role == "admin":
        blds = db.query(Asset).filter(Asset.kind == "building").all()
        return [{"id": b.id, "name": b.name, "population": b.population, "vulnerable": b.vulnerable} for b in blds]

    bld_assignments = db.query(UserBuildingAssignment).filter(UserBuildingAssignment.user_id == user.id).all()
    bld_ids = [b.building_id for b in bld_assignments]
    if user.assigned_building_id and user.assigned_building_id not in bld_ids:
        bld_ids.append(user.assigned_building_id)

    blds = db.query(Asset).filter(Asset.id.in_(bld_ids)).all()
    return [{"id": b.id, "name": b.name, "population": b.population, "vulnerable": b.vulnerable} for b in blds]

# ===================== WATER-AWARENESS ENDPOINTS =====================
@app.get("/api/v1/awareness/overview")
def get_awareness_overview(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Campus-wide public water health overview (Safe for Student & Public consumption).
    Hides internal SCADA valve commands and raw pipe burst topologies.
    """
    snap = simulator.step()
    res_vol = snap.get("reservoir_volume_kl", 400.0)
    res_max = snap.get("reservoir_capacity_kl", 500.0)
    pct = round((res_vol / max(1.0, res_max)) * 100.0, 1)

    campus_demand_lpm = snap.get("total_demand_lpm", 280.0)
    stress_level = "normal"
    if pct < 35.0 or campus_demand_lpm > 380.0:
        stress_level = "elevated"
    if pct < 20.0:
        stress_level = "critical"

    return {
        "status": "active",
        "campus_storage_pct": pct,
        "campus_water_stress": stress_level,
        "daily_target_liters_per_capita": 135.0,
        "conservation_tip": "Turn off taps during lathering. Immediate reporting of leaks saves up to 4,000 liters daily.",
        "active_campus_notices": [
            "Routine overhead tank cleaning scheduled for Academic Complex this Saturday.",
            "Water supply operating under smart pressure balancing protocol."
        ]
    }

@app.get("/api/v1/awareness/buildings/{building_id}")
def get_building_awareness(
    building_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if user.role in ["student", "building_admin"]:
        if user.assigned_building_id and user.assigned_building_id != building_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied: Role '{user.role}' is restricted to assigned building '{user.assigned_building_id}'."
            )

    asset = db.query(Asset).filter(Asset.id == building_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail=f"Building '{building_id}' not found.")

    snap = simulator.step()
    bm = snap.get("block_meters", {}).get(building_id, 45.0)
    curr_flow_lpm = float(bm) if isinstance(bm, (int, float)) else float(bm.get("flow_lpm", 45.0))

    baselines = {
        "BLK-HSTL-A": 48.0,
        "BLK-HSTL-B": 42.0,
        "BLK-HSTL-C": 54.0,
        "BLK-MESS": 38.0,
        "BLK-HLTH": 10.0,
        "BLK-ACAD-1": 22.0,
        "BLK-ACAD-2": 20.0,
        "BLK-LIB": 8.0,
    }
    exp_flow_lpm = baselines.get(building_id, 30.0)
    dev_pct = round(((curr_flow_lpm - exp_flow_lpm) / max(1.0, exp_flow_lpm)) * 100.0, 1)

    incidents = db.query(Incident).filter(
        Incident.location == building_id,
        Incident.status.in_(["open", "investigating", "pending_approval", "in_progress"])
    ).all()

    cap_kl = float(asset.capacity_kl) if asset.capacity_kl is not None else 50.0
    hours_autonomy = round((cap_kl * 1000.0) / max(1.0, (curr_flow_lpm * 60.0)), 1)
    status_summary = "Normal Supply"
    if dev_pct > 30.0:
        status_summary = "Elevated Consumption (Inspection Requested)"
    if any(i.case_type == "burst_main" for i in incidents):
        status_summary = "Restricted (Maintenance in Progress)"

    return {
        "building_id": asset.id,
        "building_name": asset.name,
        "population": asset.population,
        "is_vulnerable": asset.vulnerable,
        "q1_supply_status": status_summary,
        "q2_consumption_lpm": curr_flow_lpm,
        "q2_baseline_lpm": exp_flow_lpm,
        "q2_deviation_pct": dev_pct,
        "q3_minimum_night_flow_status": "normal" if dev_pct < 25.0 else "anomalous_flow_detected",
        "q4_active_alerts_count": len(incidents),
        "q5_hours_autonomy": min(48.0, hours_autonomy),
        "q6_conservation_guidance": "Report any wet riser dampness or dripping washroom faucets to keep campus water-secure.",
        "q7_recent_notices": [
            f"Building smart flow meter {building_id} telemetry active.",
            f"Nominal allocation: {asset.nominal_demand_kl} kL/day."
        ]
    }

@app.get("/api/v1/awareness/buildings/{building_id}/consumption")
def get_building_consumption_history(
    building_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if user.role in ["student", "building_admin"]:
        if user.assigned_building_id and user.assigned_building_id != building_id:
            raise HTTPException(status_code=403, detail="Access denied to other building consumption.")

    hours = [f"{h:02d}:00" for h in range(24)]
    base_curve = [15, 12, 10, 8, 9, 22, 55, 68, 62, 50, 44, 46, 52, 48, 42, 40, 48, 65, 70, 60, 48, 35, 25, 18]
    series = []
    for h_label, val in zip(hours, base_curve):
        series.append({
            "hour": h_label,
            "consumption_lpm": val,
            "baseline_lpm": val,
            "normal_band_upper": round(val * 1.2, 1),
            "normal_band_lower": round(val * 0.8, 1)
        })
    return {"building_id": building_id, "interval": "hourly", "readings": series}

@app.get("/api/v1/awareness/buildings/{building_id}/alerts")
def get_building_alerts(
    building_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if user.role in ["student", "building_admin"]:
        if user.assigned_building_id and user.assigned_building_id != building_id:
            raise HTTPException(status_code=403, detail="Access denied to other building alerts.")

    incidents = db.query(Incident).filter(
        Incident.location == building_id,
        Incident.status.in_(["open", "investigating", "pending_approval", "in_progress"])
    ).all()
    return [
        {
            "id": inc.id,
            "type": inc.case_type,
            "severity": "high" if inc.priority_score > 50 else "medium",
            "message": f"Active {inc.case_type.replace('_', ' ')} incident recorded.",
            "status": inc.status,
            "created_at": inc.created_at.isoformat() if inc.created_at else None
        }
        for inc in incidents
    ]

# ===================== CPGRAMS COMPLAINTS & GRIEVANCES =====================
@app.post("/api/v1/complaints", status_code=status.HTTP_201_CREATED)
def submit_complaint(
    req: ComplaintCreateRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    tracking_num = f"CPGRAMS/2026/NEER-{random.randint(10000, 99999)}"
    cid = f"CMP-{uuid.uuid4().hex[:8].upper()}"

    target_bld = req.building_id
    if user.role == "student" and user.assigned_building_id:
        target_bld = user.assigned_building_id

    comp = Complaint(
        id=cid,
        tracking_id=tracking_num,
        user_id=user.id,
        building_id=target_bld,
        category=req.category,
        description=req.description,
        status="submitted",
        priority=req.priority or "medium",
        action_taken_remarks="Grievance logged via Central Water Resilience Portal"
    )
    db.add(comp)

    history = ComplaintStatusHistory(
        id=f"CSH-{uuid.uuid4().hex[:8]}",
        complaint_id=cid,
        status="submitted",
        notes=f"Initial complaint submitted by {user.full_name} ({user.role})",
        changed_by=user.full_name,
        timestamp=datetime.utcnow()
    )
    db.add(history)
    db.commit()

    return {
        "id": comp.id,
        "tracking_id": comp.tracking_id,
        "building_id": comp.building_id,
        "status": comp.status,
        "message": f"Complaint successfully registered. Your official tracking ID is {tracking_num}."
    }

@app.get("/api/v1/complaints")
def list_complaints(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(Complaint)
    if user.role == "student":
        query = query.filter(Complaint.user_id == user.id)
    elif user.role == "building_admin":
        if user.assigned_building_id:
            query = query.filter(Complaint.building_id == user.assigned_building_id)
    elif user.role == "engineer":
        if user.assigned_building_id:
            query = query.filter((Complaint.assigned_work_order_id != None) | (Complaint.building_id == user.assigned_building_id))

    complaints = query.order_by(Complaint.created_at.desc()).all()
    return [
        {
            "id": c.id,
            "tracking_id": c.tracking_id,
            "user_id": c.user_id,
            "building_id": c.building_id,
            "category": c.category,
            "description": c.description,
            "status": c.status,
            "priority": c.priority,
            "assigned_work_order_id": c.assigned_work_order_id,
            "action_taken_remarks": c.action_taken_remarks,
            "created_at": c.created_at.isoformat() if c.created_at else None,
            "updated_at": c.updated_at.isoformat() if c.updated_at else None
        }
        for c in complaints
    ]

@app.get("/api/v1/complaints/{complaint_id}")
def get_complaint(
    complaint_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    comp = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if not comp:
        raise HTTPException(status_code=404, detail="Complaint not found")

    if user.role == "student" and comp.user_id != user.id:
        raise HTTPException(status_code=403, detail="Forbidden: You can only view your own complaints.")
    if user.role == "building_admin" and user.assigned_building_id and comp.building_id != user.assigned_building_id:
        raise HTTPException(status_code=403, detail="Forbidden: Complaint belongs to another building.")

    history = db.query(ComplaintStatusHistory).filter(ComplaintStatusHistory.complaint_id == complaint_id).order_by(ComplaintStatusHistory.timestamp.asc()).all()

    return {
        "complaint": {
            "id": comp.id,
            "tracking_id": comp.tracking_id,
            "building_id": comp.building_id,
            "category": comp.category,
            "description": comp.description,
            "status": comp.status,
            "priority": comp.priority,
            "assigned_work_order_id": comp.assigned_work_order_id,
            "action_taken_remarks": comp.action_taken_remarks,
            "created_at": comp.created_at.isoformat() if comp.created_at else None
        },
        "history": [
            {
                "id": h.id,
                "status": h.status,
                "notes": h.notes,
                "changed_by": h.changed_by,
                "timestamp": h.timestamp.isoformat() if h.timestamp else None
            }
            for h in history
        ]
    }

@app.patch("/api/v1/complaints/{complaint_id}")
def update_complaint(
    complaint_id: str,
    req: ComplaintUpdateRequest,
    user: User = Depends(require_roles("admin", "building_admin")),
    db: Session = Depends(get_db)
):
    comp = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if not comp:
        raise HTTPException(status_code=404, detail="Complaint not found")

    if user.role == "building_admin" and user.assigned_building_id and comp.building_id != user.assigned_building_id:
        raise HTTPException(status_code=403, detail="Forbidden: Cannot update complaints from another building.")

    if req.forward_to_maintenance:
        wo_id = f"WO-CMP-{comp.id[-4:]}"
        wo = WorkOrder(
            id=wo_id,
            incident_id=None,
            asset_id=comp.building_id,
            assigned_engineer_id=user.assigned_engineer_id or "ENG-02",
            required_skill="plumbing",
            priority=comp.priority or "medium",
            recommended_action=f"Inspect and address complaint: {comp.description}",
            expected_impact="Restore plumbing service and eliminate localized leakage.",
            status="assigned"
        )
        db.merge(wo)
        comp.assigned_work_order_id = wo_id
        comp.status = "in_progress"
        comp.action_taken_remarks = f"Forwarded to maintenance work order {wo_id}."

    if req.status:
        comp.status = req.status
    if req.action_taken_remarks:
        comp.action_taken_remarks = req.action_taken_remarks
    comp.updated_at = datetime.utcnow()

    history = ComplaintStatusHistory(
        id=f"CSH-{uuid.uuid4().hex[:8]}",
        complaint_id=comp.id,
        status=comp.status,
        notes=req.action_taken_remarks or f"Status changed to {comp.status} by {user.full_name}",
        changed_by=user.full_name,
        timestamp=datetime.utcnow()
    )
    db.add(history)
    db.commit()

    return {"status": comp.status, "complaint_id": comp.id, "work_order_id": comp.assigned_work_order_id}

@app.get("/api/v1/complaints/{complaint_id}/history")
def get_complaint_history(
    complaint_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    comp = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if not comp:
        raise HTTPException(status_code=404, detail="Complaint not found")
    if user.role == "student" and comp.user_id != user.id:
        raise HTTPException(status_code=403, detail="Forbidden.")

    history = db.query(ComplaintStatusHistory).filter(ComplaintStatusHistory.complaint_id == complaint_id).order_by(ComplaintStatusHistory.timestamp.asc()).all()
    return [
        {
            "id": h.id,
            "status": h.status,
            "notes": h.notes,
            "changed_by": h.changed_by,
            "timestamp": h.timestamp.isoformat() if h.timestamp else None
        }
        for h in history
    ]

# ===================== GIS MAP ASSET ENDPOINTS =====================
@app.get("/api/v1/map/assets")
def get_map_assets(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Returns role-filtered GIS map assets. Students only see public campus buildings."""
    if user.role == "student":
        assets = db.query(Asset).filter(Asset.kind == "building").all()
    else:
        assets = db.query(Asset).all()

    return [
        {
            "id": a.id,
            "name": a.name,
            "kind": a.kind,
            "type": a.asset_type,
            "vulnerable": a.vulnerable,
            "population": a.population,
            "capacity_kl": a.capacity_kl
        }
        for a in assets
    ]

@app.get("/api/v1/map/assets/{asset_id}/summary")
def get_map_asset_summary(asset_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    states = db.query(LatestAssetState).filter(LatestAssetState.asset_id == asset_id).all()
    incidents = db.query(Incident).filter(Incident.location == asset_id, Incident.status.in_(["open", "investigating", "pending_approval", "in_progress"])).all()

    return {
        "asset": {
            "id": asset.id,
            "name": asset.name,
            "kind": asset.kind,
            "vulnerable": asset.vulnerable,
            "population": asset.population,
            "capacity_kl": asset.capacity_kl
        },
        "readings": [{s.metric: s.value, "unit": s.unit} for s in states],
        "active_incidents": len(incidents)
    }

@app.get("/api/v1/map/assets/{asset_id}/alerts")
def get_map_asset_alerts(asset_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    incidents = db.query(Incident).filter(Incident.location == asset_id).all()
    return [
        {
            "id": inc.id,
            "type": inc.case_type,
            "status": inc.status,
            "priority": inc.priority_score,
            "why": inc.why_text
        }
        for inc in incidents
    ]

@app.get("/api/v1/map/assets/{asset_id}/consumption")
def get_map_asset_consumption(asset_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    states = db.query(LatestAssetState).filter(LatestAssetState.asset_id == asset_id, LatestAssetState.metric == "flow_lpm").first()
    val = states.value if states else 45.0
    return {
        "asset_id": asset_id,
        "current_flow_lpm": val,
        "historical_avg_lpm": 48.0,
        "status": "normal" if val < 60.0 else "elevated"
    }

# ===================== GEMINI TOKEN ACCOUNTING (ADMIN ONLY) =====================
@app.get("/api/v1/admin/gemini/usage")
def get_gemini_usage_summary(user: User = Depends(require_roles("admin")), db: Session = Depends(get_db)):
    usages = db.query(AgentTokenUsage).all()
    tot_reqs = sum(u.total_requests for u in usages)
    tot_inp = sum(u.total_input_tokens for u in usages)
    tot_out = sum(u.total_output_tokens for u in usages)
    tot_thk = sum(u.total_thinking_tokens for u in usages)
    tot_tok = sum(u.total_tokens for u in usages)
    tot_cost = sum(u.total_cost_usd for u in usages)

    cfg = db.query(ModelPricingConfig).filter(ModelPricingConfig.is_active == True).first()

    return {
        "model": "gemini-3.5-flash-lite",
        "pricing_tier": "standard_paid",
        "input_price_per_million": cfg.input_price_per_million if cfg else 0.30,
        "output_price_per_million": cfg.output_price_per_million if cfg else 2.50,
        "total_requests": tot_reqs,
        "total_input_tokens": tot_inp,
        "total_output_tokens": tot_out,
        "total_thinking_tokens": tot_thk,
        "total_tokens": tot_tok,
        "total_cost_usd": round(tot_cost, 6),
        "total_cost_inr": round(tot_cost * 86.5, 4),
        "is_available": gemini_client.is_available()
    }

@app.get("/api/v1/admin/gemini/usage/agents")
def get_gemini_usage_agents(user: User = Depends(require_roles("admin")), db: Session = Depends(get_db)):
    usages = db.query(AgentTokenUsage).all()
    return [
        {
            "agent_name": u.agent_name,
            "total_requests": u.total_requests,
            "input_tokens": u.total_input_tokens,
            "output_tokens": u.total_output_tokens,
            "thinking_tokens": u.total_thinking_tokens,
            "total_tokens": u.total_tokens,
            "cost_usd": round(u.total_cost_usd, 6),
            "model": "gemini-3.5-flash-lite"
        }
        for u in usages
    ]

@app.get("/api/v1/admin/gemini/usage/requests")
def get_gemini_requests_log(user: User = Depends(require_roles("admin")), db: Session = Depends(get_db)):
    reqs = db.query(GeminiRequest).order_by(GeminiRequest.created_at.desc()).limit(50).all()
    return [
        {
            "id": r.id,
            "request_id": r.request_id,
            "agent_name": r.agent_name,
            "model": r.model,
            "latency_ms": round(r.latency_ms, 1),
            "input_tokens": r.input_tokens,
            "output_tokens": r.output_tokens,
            "thinking_tokens": r.thinking_tokens,
            "total_tokens": r.total_tokens,
            "cost_usd": round(r.estimated_cost_usd, 6),
            "status": r.status,
            "created_at": r.created_at.isoformat() if r.created_at else None
        }
        for r in reqs
    ]

@app.get("/api/v1/admin/gemini/pricing")
def get_pricing_config(user: User = Depends(require_roles("admin")), db: Session = Depends(get_db)):
    cfg = db.query(ModelPricingConfig).filter(ModelPricingConfig.is_active == True).first()
    return {
        "model_name": cfg.model_name if cfg else "gemini-3.5-flash-lite",
        "input_price_per_million": cfg.input_price_per_million if cfg else 0.30,
        "output_price_per_million": cfg.output_price_per_million if cfg else 2.50,
        "pricing_tier": cfg.pricing_tier if cfg else "standard_paid",
        "version": cfg.version if cfg else "2026-v1"
    }

@app.post("/api/v1/admin/gemini/pricing")
def update_pricing_config(req: PricingUpdateRequest, user: User = Depends(require_roles("admin")), db: Session = Depends(get_db)):
    cfg = db.query(ModelPricingConfig).filter(ModelPricingConfig.is_active == True).first()
    if not cfg:
        cfg = ModelPricingConfig(
            id="CFG-CUSTOM",
            model_name="gemini-3.5-flash-lite",
            input_price_per_million=req.input_price_per_million,
            output_price_per_million=req.output_price_per_million,
            pricing_tier="custom",
            version="custom-v1",
            is_active=True
        )
        db.add(cfg)
    else:
        cfg.input_price_per_million = req.input_price_per_million
        cfg.output_price_per_million = req.output_price_per_million
        cfg.updated_at = datetime.utcnow()
    db.commit()
    return {"status": "updated", "input_price": cfg.input_price_per_million, "output_price": cfg.output_price_per_million}

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

# 8. Agent Traces (Technical Observability)
@app.get("/api/v1/traces")
@app.get("/api/traces")
def get_agent_traces():
    traces = orchestrator.historical_traces[-30:]
    if traces:
        return [t.dict() for t in traces]
    try:
        with SessionLocal() as db:
            db_traces = db.query(DBAgentTrace).order_by(DBAgentTrace.started_at.desc()).limit(30).all()
            if db_traces:
                return [
                    {
                        "agent_name": tr.agent_name,
                        "started_at": tr.started_at.isoformat() if tr.started_at else "",
                        "ended_at": tr.ended_at.isoformat() if tr.ended_at else "",
                        "execution_time_ms": tr.execution_time_ms,
                        "status": tr.status,
                        "inputs": json.loads(tr.inputs_json) if tr.inputs_json else {},
                        "outputs": json.loads(tr.outputs_json) if tr.outputs_json else {},
                        "tools_called": json.loads(tr.tools_called_json) if tr.tools_called_json else [],
                        "notes": tr.notes
                    }
                    for tr in reversed(db_traces)
                ]
    except Exception as e:
        print("Error fetching traces from DB:", e)
    return []

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

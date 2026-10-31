"""
NEERARAN Database Layer
SQLAlchemy ORM models for persistent SQLite system-of-record.
Hierarchy: Organization -> Zone -> Campus -> Building -> Asset
"""

import os
import json
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import (
    create_engine, Column, String, Integer, Float, Boolean, DateTime,
    Text, ForeignKey, Index, desc
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship, Session

DB_PATH = os.getenv("DB_PATH", "neeraran.db")
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Organization(Base):
    __tablename__ = "organizations"
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class Deployment(Base):
    __tablename__ = "deployments"
    id = Column(String, primary_key=True)
    org_id = Column(String, ForeignKey("organizations.id"))
    name = Column(String, nullable=False)
    location = Column(String)
    timezone = Column(String, default="Asia/Kolkata")
    created_at = Column(DateTime, default=datetime.utcnow)


class Asset(Base):
    __tablename__ = "assets"
    id = Column(String, primary_key=True)  # e.g. BLK-HSTL-A, OHT-NORTH, PIPE-SUMP-OHT1
    name = Column(String, nullable=False)
    kind = Column(String, nullable=False)  # block, tank, sump, borewell, pipe, valve, sensor
    asset_type = Column(String)  # hostel, academic, health, etc.
    parent_id = Column(String, ForeignKey("assets.id"), nullable=True)
    vulnerable = Column(Boolean, default=False)
    population = Column(Integer, default=0)
    capacity_kl = Column(Float, nullable=True)
    safety_level_kl = Column(Float, nullable=True)
    nominal_demand_kl = Column(Float, nullable=True)
    coordinates = Column(Text, nullable=True)  # JSON [lon, lat] or polygon
    created_at = Column(DateTime, default=datetime.utcnow)


class DataSource(Base):
    __tablename__ = "data_sources"
    id = Column(String, primary_key=True)  # source_1, source_2, source_3, source_4
    name = Column(String, nullable=False)
    api_key_hash = Column(String, nullable=False)
    source_type = Column(String)  # supply, consumption, telemetry, operations
    status = Column(String, default="online")  # online, stale, offline
    last_seen = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class TelemetryEvent(Base):
    __tablename__ = "telemetry_events"
    id = Column(String, primary_key=True)
    source_id = Column(String, ForeignKey("data_sources.id"), index=True)
    asset_id = Column(String, ForeignKey("assets.id"), index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    metric = Column(String, index=True)  # flow_lpm, pressure_bar, level_m, yield_lpm, rainfall_mm
    value = Column(Float, nullable=False)
    unit = Column(String, nullable=False)
    quality = Column(String, default="valid")  # valid, suspect, stale, flatline, impossible
    payload_json = Column(Text, nullable=True)


class LatestAssetState(Base):
    __tablename__ = "latest_asset_state"
    asset_id = Column(String, primary_key=True)
    metric = Column(String, primary_key=True)
    value = Column(Float, nullable=False)
    unit = Column(String, nullable=False)
    status = Column(String, default="normal")  # normal, watch, leak, fault
    updated_at = Column(DateTime, default=datetime.utcnow)
    data_quality = Column(String, default="valid")


class DataQualityException(Base):
    __tablename__ = "data_quality_exceptions"
    id = Column(String, primary_key=True)
    source_id = Column(String)
    asset_id = Column(String)
    reason = Column(String)  # unknown_asset, invalid_unit, dropout, flatline, physically_impossible
    raw_payload = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)


class MLPrediction(Base):
    __tablename__ = "ml_predictions"
    id = Column(String, primary_key=True)
    model_name = Column(String, index=True)  # anomaly_detector, demand_forecaster, shortage_forecaster
    model_version = Column(String)
    asset_id = Column(String, index=True)
    prediction_type = Column(String)
    prediction_value = Column(Float)
    confidence = Column(Float, nullable=True)
    features_json = Column(Text, nullable=True)
    execution_time_ms = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)


class GroundTruth(Base):
    __tablename__ = "ground_truth"
    id = Column(String, primary_key=True)
    event_type = Column(String)  # hostel_leak, pipe_burst, sensor_fault, heatwave, etc.
    location = Column(String)
    true_loss_lpm = Column(Float, default=0.0)
    start_tick = Column(Integer)
    end_tick = Column(Integer, nullable=True)
    resolved = Column(Boolean, default=False)
    metadata_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Incident(Base):
    __tablename__ = "incidents"
    id = Column(String, primary_key=True)  # CASE-XXXX
    case_type = Column(String, index=True)  # leak, shortage, demand_spike, sensor_fault, quality
    location = Column(String)  # asset or zone
    confidence = Column(Float, default=0.5)
    loss_rate_kl_day = Column(Float, default=0.0)
    priority_score = Column(Float, default=0.0)
    status = Column(String, default="open")  # open, investigating, pending_approval, intervening, verified, resolved, rejected
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)
    why_text = Column(Text, nullable=True)
    verifier_result = Column(String, default="unverified")  # verified, rejected, downgraded
    groundedness_score = Column(Float, default=1.0)


class IncidentEvidence(Base):
    __tablename__ = "incident_evidence"
    id = Column(String, primary_key=True)  # EVID-XXXX
    incident_id = Column(String, ForeignKey("incidents.id"), index=True)
    kind = Column(String)  # night_flow, pressure_drop, tank_depletion, sensor_anomaly, complaint
    source = Column(String)
    block_or_node = Column(String)
    tick_range = Column(String)
    observed_value = Column(Float)
    baseline_value = Column(Float)
    unit = Column(String)
    note = Column(Text)
    verified = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class AgentTrace(Base):
    __tablename__ = "agent_traces"
    id = Column(String, primary_key=True)
    incident_id = Column(String, index=True)
    agent_name = Column(String, index=True)  # monitor, detector, localizer, forecaster, prioritizer, optimizer, interventor, verifier
    started_at = Column(DateTime)
    ended_at = Column(DateTime)
    execution_time_ms = Column(Float)
    status = Column(String, default="success")  # success, error, fallback
    inputs_json = Column(Text)
    outputs_json = Column(Text)
    tools_called_json = Column(Text)
    notes = Column(Text, nullable=True)


class InterventionPlan(Base):
    __tablename__ = "intervention_plans"
    id = Column(String, primary_key=True)
    incident_id = Column(String, ForeignKey("incidents.id"), index=True)
    version = Column(Integer, default=1)
    status = Column(String, default="pending")  # pending, approved, rejected, executing, completed, superseded
    expected_impact = Column(Text)  # JSON: {liters_saved, inr_saved, reserve_hours}
    risk_level = Column(String, default="low")  # low, medium, high
    vulnerable_flag = Column(Boolean, default=False)
    needs_approval = Column(Boolean, default=True)
    rollback_plan = Column(Text)
    steps_json = Column(Text)  # ordered tool calls
    created_at = Column(DateTime, default=datetime.utcnow)


class Engineer(Base):
    __tablename__ = "engineers"
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    role = Column(String, default="Field Technician")
    skills = Column(Text)  # JSON list: ["plumbing", "valves", "scada", "pumps"]
    availability = Column(String, default="available")  # available, on_job, off_duty
    current_workload = Column(Integer, default=0)
    contact = Column(String)


class WorkOrder(Base):
    __tablename__ = "work_orders"
    id = Column(String, primary_key=True)  # WO-XXXX
    incident_id = Column(String, ForeignKey("incidents.id"), index=True)
    asset_id = Column(String, ForeignKey("assets.id"))
    assigned_engineer_id = Column(String, ForeignKey("engineers.id"), nullable=True)
    required_skill = Column(String)
    priority = Column(String, default="medium")  # low, medium, high, emergency
    recommended_action = Column(Text)
    expected_impact = Column(Text)
    status = Column(String, default="created")  # created, assigned, in_progress, completed, verified
    findings = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)


class Approval(Base):
    __tablename__ = "approvals"
    id = Column(String, primary_key=True)  # APP-XXXX
    plan_id = Column(String, ForeignKey("intervention_plans.id"))
    incident_id = Column(String, ForeignKey("incidents.id"))
    title = Column(String, nullable=False)
    description = Column(Text)
    vulnerable_flag = Column(Boolean, default=False)
    equity_check = Column(Text)
    status = Column(String, default="pending")  # pending, approved, rejected
    approver_role = Column(String, default="admin")
    decision_by = Column(String, nullable=True)
    decision_note = Column(Text, nullable=True)
    decided_at = Column(DateTime, nullable=True)
    execution_status = Column(String, default="not_executed")  # not_executed, executed, rolled_back


class AuditLog(Base):
    __tablename__ = "audit_log"
    id = Column(String, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    actor = Column(String, nullable=False)  # admin, viewer, agent:detector, system
    role = Column(String, default="system")
    action = Column(String, nullable=False)  # approve_plan, reject_plan, execute_tool, inject_scenario
    resource_id = Column(String)
    details_json = Column(Text)
    evidence_ids = Column(Text, nullable=True)


class EvaluationRecord(Base):
    __tablename__ = "evaluation_records"
    id = Column(String, primary_key=True)
    benchmark_name = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)
    metrics_json = Column(Text)  # precision, recall, f1, mttd, smape, etc.


# ===================== RBAC & USER MODELS =====================
class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True)
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=False)
    role = Column(String, default="student", index=True)  # admin, student, building_admin, engineer
    assigned_building_id = Column(String, ForeignKey("assets.id"), nullable=True)
    assigned_engineer_id = Column(String, ForeignKey("engineers.id"), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Role(Base):
    __tablename__ = "roles"
    id = Column(String, primary_key=True)  # admin, student, building_admin, engineer
    name = Column(String, nullable=False)
    description = Column(String)


class UserBuildingAssignment(Base):
    __tablename__ = "user_building_assignments"
    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), index=True)
    building_id = Column(String, ForeignKey("assets.id"), index=True)
    role = Column(String, default="building_admin")
    assigned_at = Column(DateTime, default=datetime.utcnow)


class Permission(Base):
    __tablename__ = "permissions"
    id = Column(String, primary_key=True)
    role_id = Column(String, ForeignKey("roles.id"), index=True)
    resource = Column(String, nullable=False)  # e.g. consumption, incidents, work_orders, approvals, settings
    action = Column(String, nullable=False)    # read, write, approve, execute


class AuthorizationEvent(Base):
    __tablename__ = "authorization_events"
    id = Column(String, primary_key=True)
    user_id = Column(String, index=True)
    role = Column(String)
    resource = Column(String)
    action = Column(String)
    allowed = Column(Boolean)
    reason = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)


# ===================== COMPLAINTS & GRIEVANCES =====================
class Complaint(Base):
    __tablename__ = "complaints"
    id = Column(String, primary_key=True)
    tracking_id = Column(String, unique=True, index=True)  # CPGRAMS/2026/NEER-00042
    user_id = Column(String, ForeignKey("users.id"), index=True)
    building_id = Column(String, ForeignKey("assets.id"), index=True)
    category = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    image_url = Column(String, nullable=True)
    status = Column(String, default="submitted", index=True)  # submitted, acknowledged, forwarded, in_progress, resolved, closed
    priority = Column(String, default="medium")  # low, medium, high, emergency
    assigned_work_order_id = Column(String, ForeignKey("work_orders.id"), nullable=True)
    action_taken_remarks = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)


class ComplaintStatusHistory(Base):
    __tablename__ = "complaint_status_history"
    id = Column(String, primary_key=True)
    complaint_id = Column(String, ForeignKey("complaints.id"), index=True)
    status = Column(String, nullable=False)
    notes = Column(Text)
    changed_by = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)


# ===================== GEMINI TOKEN & COST ACCOUNTING =====================
class GeminiRequest(Base):
    __tablename__ = "gemini_requests"
    id = Column(String, primary_key=True)
    request_id = Column(String, unique=True, index=True)
    agent_name = Column(String, index=True)
    agent_run_id = Column(String, index=True)
    incident_id = Column(String, nullable=True, index=True)
    model = Column(String, default="gemini-3.5-flash-lite")
    start_time = Column(DateTime, default=datetime.utcnow)
    completion_time = Column(DateTime, default=datetime.utcnow)
    latency_ms = Column(Float, default=0.0)
    input_tokens = Column(Integer, default=0)
    output_tokens = Column(Integer, default=0)
    thinking_tokens = Column(Integer, default=0)
    cached_tokens = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    estimated_cost_usd = Column(Float, default=0.0)
    status = Column(String, default="success")  # success, failed, fallback
    retry_count = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class AgentTokenUsage(Base):
    __tablename__ = "agent_token_usage"
    id = Column(String, primary_key=True)  # agent_name
    agent_name = Column(String, unique=True, index=True)
    total_requests = Column(Integer, default=0)
    total_input_tokens = Column(Integer, default=0)
    total_output_tokens = Column(Integer, default=0)
    total_thinking_tokens = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    total_cost_usd = Column(Float, default=0.0)
    updated_at = Column(DateTime, default=datetime.utcnow)


class ModelPricingConfig(Base):
    __tablename__ = "model_pricing_config"
    id = Column(String, primary_key=True)
    model_name = Column(String, unique=True)
    input_price_per_million = Column(Float, default=0.30)
    output_price_per_million = Column(Float, default=2.50)
    pricing_tier = Column(String, default="standard_paid")
    version = Column(String, default="2026-v1")
    is_active = Column(Boolean, default=True)
    updated_at = Column(DateTime, default=datetime.utcnow)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create all tables if not existing."""
    Base.metadata.create_all(bind=engine)

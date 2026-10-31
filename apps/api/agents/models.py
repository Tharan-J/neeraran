"""
Shared Pydantic Data Contracts for NEERARAN Operational Agents
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime

class Evidence(BaseModel):
    id: str  # EVID-XXXX
    kind: str  # night_flow, pressure_drop, tank_depletion, sensor_anomaly, complaint, water_balance
    source: str  # meter, scada, model, weather, operator
    block_or_node: str
    tick_range: str
    value: float
    baseline: float
    unit: str
    note: str
    verified: bool = True

class Step(BaseModel):
    order: int
    tool: str  # create_cmms_ticket, set_valve, set_pump_schedule, draft_advisory, notify
    args: Dict[str, Any]
    reason: str
    requires_approval: bool = False
    vulnerable_impact: bool = False

class Plan(BaseModel):
    id: str
    incident_id: str
    version: int = 1
    steps: List[Step]
    expected_impact: Dict[str, Any]  # {liters_saved, inr_saved, reserve_hours}
    risk_level: str = "low"  # low, medium, high
    needs_approval: bool = True
    vulnerable_flag: bool = False
    rollback_plan: str

class AgentTrace(BaseModel):
    agent_name: str
    started_at: str
    ended_at: str
    execution_time_ms: float
    status: str = "success"  # success, error, fallback
    inputs: Dict[str, Any]
    outputs: Dict[str, Any]
    tools_called: List[Dict[str, Any]] = []
    notes: Optional[str] = None

class Case(BaseModel):
    id: str  # CASE-XXXX
    case_type: str  # leak, shortage, demand_spike, sensor_fault, quality
    location: str  # block or pipe segment
    confidence: float = 0.5
    loss_rate_kl_day: float = 0.0
    priority_score: float = 0.0
    evidence: List[Evidence] = []
    plan: Optional[Plan] = None
    status: str = "open"  # open, investigating, pending_approval, intervening, verified, resolved
    why_text: Optional[str] = None
    verifier_result: str = "unverified"
    groundedness_score: float = 1.0
    traces: List[AgentTrace] = []
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

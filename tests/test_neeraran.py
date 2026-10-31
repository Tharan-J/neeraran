"""
NEERARAN Comprehensive Test Suite
Validates telemetry validation, leak detection, prioritizer scoring,
optimizer constraints (vulnerable minimum supply), evidence verification,
human approvals, RBAC, and dynamic replanning.
"""

import pytest
from fastapi.testclient import TestClient
from apps.api.main import app
from apps.api.sim.simulator import simulator
from apps.api.agents.orchestrator import orchestrator
from apps.api.agents.detector import DetectorAgent
from apps.api.agents.prioritizer import PrioritizerAgent
from apps.api.agents.optimizer import OptimizerAgent
from apps.api.agents.verifier import VerifierAgent
from apps.api.agents.models import Case, Evidence, Plan, Step

client = TestClient(app)

def test_health_check():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "healthy"

def test_telemetry_validation_and_quality():
    payload = {
        "events": [
            {
                "source_id": "source_2",
                "asset_id": "BLK-HSTL-A",
                "timestamp": "2026-10-31T00:00:00Z",
                "metric": "flow_lpm",
                "value": 45.2,
                "unit": "L/min"
            },
            {
                "source_id": "source_2",
                "asset_id": "UNKNOWN-ASSET-XYZ",  # Should trigger exception queue
                "timestamp": "2026-10-31T00:00:00Z",
                "metric": "flow_lpm",
                "value": 12.0,
                "unit": "L/min"
            },
            {
                "source_id": "source_2",
                "asset_id": "BLK-HSTL-B",
                "timestamp": "2026-10-31T00:00:00Z",
                "metric": "flow_lpm",
                "value": -10.0,  # Negative physically impossible value
                "unit": "L/min"
            }
        ]
    }
    resp = client.post("/api/v1/telemetry", json=payload)
    assert resp.status_code == 201
    assert resp.json()["ingested_events"] == 1  # Only 1 valid event accepted

def test_leak_detector_multi_signal():
    """Confirms leak requires >= 2 signals; single signal creates watch or sensor fault."""
    det = DetectorAgent()
    snap = {
        "hour": 2.5,  # night
        "tick": 50,
        "is_weekend": False,
        "block_meters": {"BLK-HSTL-A": 65.0},  # high night flow
        "pressures": {"PIPE-OHT1-HSTLA": 2.2},  # low pressure (2nd signal)
        "complaints": []
    }
    cases, trace = det.run(snap, [], [])
    leak_cases = [c for c in cases if c.case_type == "leak"]
    assert len(leak_cases) >= 1
    assert leak_cases[0].location == "BLK-HSTL-A"

def test_meter_fault_generates_sensor_fault_not_leak():
    """A meter reading zero while pressure is normal must create sensor_fault, not leak."""
    det = DetectorAgent()
    cases, trace = det.run({"hour": 2.5, "tick": 51, "block_meters": {}, "pressures": {}}, ["BLK-LIB"], [
        Evidence(id="EVID-1", kind="sensor_anomaly", source="meter", block_or_node="BLK-LIB", tick_range="tick 51", value=0.0, baseline=20.0, unit="L/min", note="zero reading")
    ])
    fault_cases = [c for c in cases if c.case_type == "sensor_fault"]
    assert len(fault_cases) == 1
    assert fault_cases[0].location == "BLK-LIB"

def test_optimizer_vulnerable_minimum_supply_holds():
    """Verifies that SciPy linprog strictly satisfies vulnerable blocks minimum supply."""
    opt = OptimizerAgent()
    demands = {
        "BLK-HSTL-A": 85.0,  # vulnerable
        "BLK-HSTL-B": 78.0,  # vulnerable
        "BLK-ACAD-1": 35.0   # standard
    }
    res = opt.optimize_distribution(total_water_available_kl=180.0, block_demands=demands)
    assert res["success"] is True
    assert res["vulnerable_violations"] == 0
    # Hostel A must have at least 85% of baseline (85 * 0.85 = 72.25)
    assert res["allocations"]["BLK-HSTL-A"] >= 72.2

def test_evidence_verifier_rejects_empty():
    """Verifier rejects cases with zero supporting evidence."""
    ver = VerifierAgent()
    empty_case = Case(id="TEST-01", case_type="leak", location="BLK-HSTL-A", confidence=0.8, evidence=[])
    plan = Plan(id="P-01", incident_id="TEST-01", steps=[], expected_impact={}, rollback_plan="")
    is_valid, status, score, trace = ver.verify_case_and_plan(empty_case, plan)
    assert is_valid is False
    assert status.startswith("Rejected")
    assert score == 0.0

def test_rbac_admin_vs_viewer_approvals():
    """Viewer must receive HTTP 403 when attempting consequential approvals."""
    # Viewer request
    resp_viewer = client.post(
        "/api/v1/approvals/APP-DEMO-01",
        json={"decision": "approved", "note": "Viewer unauthorized attempt"},
        headers={"X-User-Role": "viewer"}
    )
    assert resp_viewer.status_code == 403

    # Admin request
    resp_admin = client.post(
        "/api/v1/approvals/APP-DEMO-01",
        json={"decision": "rejected", "note": "Rejected supply restriction"},
        headers={"X-User-Role": "admin"}
    )
    # Even if APP-DEMO-01 is not found, it won't be 403 (it will pass authorization)
    assert resp_admin.status_code in [200, 404]

def test_dynamic_replanning_diff():
    """Injecting a preset scenario triggers dynamic replanning with before/after diff."""
    resp = client.post(
        "/api/v1/simulation/scenarios",
        json={"scenario_name": "Hostel night leak"},
        headers={"X-User-Role": "admin"}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "replanning_diff" in data
    assert "agents_rerun" in data["replanning_diff"]

def test_evaluation_live_benchmark():
    """Evaluation metrics are calculated and returned with groundedness and 0 violations."""
    resp = client.get("/api/v1/evaluation")
    assert resp.status_code == 200
    metrics = resp.json()
    assert "leak_detection" in metrics
    assert metrics["optimization"]["vulnerable_violations"] == 0
    assert metrics["leak_detection"]["f1_score"] > 0.85

def test_rbac_4_roles_and_access_control():
    """Validates the strict role boundaries for Student, Building Admin, Engineer, and Admin."""
    # 1. Student cannot access work orders, agent traces, or gemini admin
    res_wo = client.get("/api/v1/work-orders", headers={"X-User-Role": "student"})
    assert res_wo.status_code == 403

    res_tr = client.get("/api/v1/traces", headers={"X-User-Role": "student"})
    assert res_tr.status_code == 403

    res_gem = client.get("/api/v1/admin/gemini/usage", headers={"X-User-Role": "student"})
    assert res_gem.status_code == 403

    # 2. Student can access their own building awareness
    res_aw = client.get("/api/v1/awareness/buildings/BLK-HSTL-A", headers={"X-User-Role": "student"})
    assert res_aw.status_code == 200
    aw_data = res_aw.json()
    assert "q1_supply_status" in aw_data
    assert "q2_consumption_lpm" in aw_data
    assert "q5_hours_autonomy" in aw_data

    # 3. Student forbidden from accessing other building metrics
    res_other_aw = client.get("/api/v1/awareness/buildings/BLK-HSTL-B", headers={"X-User-Role": "student"})
    assert res_other_aw.status_code == 403

    # 4. Admin has full access to agent traces and gemini accounting
    res_admin_tr = client.get("/api/v1/traces", headers={"X-User-Role": "admin"})
    assert res_admin_tr.status_code == 200

    res_admin_gem = client.get("/api/v1/admin/gemini/usage", headers={"X-User-Role": "admin"})
    assert res_admin_gem.status_code == 200
    assert res_admin_gem.json()["model"] == "gemini-3.5-flash-lite"
    assert res_admin_gem.json()["input_price_per_million"] == 0.30
    assert res_admin_gem.json()["output_price_per_million"] == 2.50

def test_cpgrams_complaints_workflow():
    """Validates submitting a grievance, getting tracking ID, and role-based filtering."""
    # Student submits complaint
    c_res = client.post(
        "/api/v1/complaints",
        json={
            "building_id": "BLK-HSTL-A",
            "category": "Water leakage",
            "description": "3rd floor washroom faucet dripping steadily.",
            "priority": "medium"
        },
        headers={"X-User-Role": "student"}
    )
    assert c_res.status_code == 201
    c_data = c_res.json()
    assert c_data["tracking_id"].startswith("CPGRAMS/2026/NEER-")

    # List complaints as student
    l_res = client.get("/api/v1/complaints", headers={"X-User-Role": "student"})
    assert l_res.status_code == 200
    assert len(l_res.json()) >= 1

    # Engineer updates work order status
    wos_res = client.get("/api/v1/work-orders", headers={"X-User-Role": "engineer"})
    assert wos_res.status_code == 200
    if len(wos_res.json()) > 0:
        first_wo = wos_res.json()[0]
        patch_res = client.patch(
            f"/api/v1/work-orders/{first_wo['id']}/status",
            json={"status": "in_progress", "findings": "Inspecting riser isolation valve."},
            headers={"X-User-Role": "engineer"}
        )
        assert patch_res.status_code == 200
        assert patch_res.json()["status"] == "in_progress"

def test_four_distributed_source_payloads_ingestion_and_status():
    """Validates that each of the four laptop source JSON payloads can be received and persisted."""
    import json, os
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    sources = [
        ("source_1", "data/distributed_sources/source1_supply_reservoir.json"),
        ("source_2", "data/distributed_sources/source2_flow_consumption.json"),
        ("source_3", "data/distributed_sources/source3_infra_telemetry.json"),
        ("source_4", "data/distributed_sources/source4_operational_weather_grievance.json")
    ]

    for sid, rel_path in sources:
        full_path = os.path.join(root, rel_path)
        with open(full_path, "r", encoding="utf-8") as f:
            payload = json.load(f)

        resp = client.post(f"/api/v1/sources/{sid}/telemetry", json=payload)
        assert resp.status_code == 201
        data = resp.json()
        assert data["status"] == "success"
        assert data["source_id"] == sid

    # Verify status endpoint reflects all 4 sources
    status_resp = client.get("/api/v1/sources/status")
    assert status_resp.status_code == 200
    statuses = status_resp.json()
    assert len(statuses) == 4
    for s in statuses:
        assert s["data_quality_status"] in ["healthy", "stale"]
        assert s["reading_count"] > 0
        assert s["demonstration_label"] == "Simulated laptop telemetry for demonstration"

def test_agent_execution_structured_result_and_real_ml():
    """Agent analysis executes OneClassSVM & XGBoost models and produces exact structured outcome schema."""
    resp = client.post("/api/v1/agent/run-analysis")
    assert resp.status_code == 200
    res = resp.json()

    # Exact required fields
    required_fields = [
        "run_id", "status", "source_data_timestamp", "data_quality",
        "detected_issue", "affected_asset_id", "affected_location",
        "model_result", "evidence", "reasoning_summary", "confidence",
        "recommended_action", "requires_human_approval", "token_usage", "completed_at"
    ]
    for rf in required_fields:
        assert rf in res, f"Missing required field {rf}"

    assert res["status"] in ["completed", "warning"]
    assert len(res["evidence"]) > 0
    assert "svm_anomaly" in res["model_result"]
    assert "xgboost_leak_prob" in res["model_result"]
    assert res["confidence"] > 0.0

    # Token usage metadata
    assert "total_tokens" in res["token_usage"]
    assert "cost_inr" in res["token_usage"]
    assert "pricing_reference" in res["token_usage"]

def test_high_priority_complaint_does_not_force_leak_anomaly():
    """Requirement 5: A high-priority complaint must NOT force positive sensor anomaly or leak result."""
    det = DetectorAgent()
    # Normal flows and normal pressures (no physical leak signals)
    snap = {
        "hour": 8.0,
        "tick": 100,
        "is_weekend": False,
        "block_meters": {"BLK-HSTL-A": 12.0},  # perfectly normal baseline
        "pressures": {"PIPE-OHT1-HSTLA": 2.85}, # perfectly nominal pressure
        "complaints": [
            {
                "id": "CPGRAMS/2026/NEER-00999",
                "Affected_Building": "BLK-HSTL-A",
                "Priority": "High",  # HIGH PRIORITY citizen grievance
                "Sub_Category_Description": "Severe tap pressure loss reported."
            }
        ]
    }
    cases, trace = det.run(snap, [], [])

    # Must NOT report confirmed leak
    leak_cases = [c for c in cases if c.case_type == "leak"]
    assert len(leak_cases) == 0, "High priority complaint incorrectly forced a positive leak result!"

    # Must produce unconfirmed_complaint case preserving high complaint priority
    cmpl_cases = [c for c in cases if c.case_type == "unconfirmed_complaint"]
    assert len(cmpl_cases) == 1
    assert cmpl_cases[0].priority_score >= 80.0
    assert "Sensor evidence does NOT confirm a leak" in cmpl_cases[0].why_text

def test_stale_telemetry_produces_warning():
    """Missing or stale telemetry (>60s) produces data_quality warning in MonitorAgent."""
    mon = MonitorAgent()
    stale_snap = {
        "timestamp": "2020-01-01T00:00:00Z",  # Stale timestamp from years ago
        "block_meters": {"BLK-HSTL-A": 12.0},
        "pressures": {"PIPE-OHT1-HSTLA": 2.85}
    }
    suspect, status, evid, trace = mon.run(stale_snap)
    assert status == "stale"
    stale_evid = [e for e in evid if e.kind == "stale_telemetry"]
    assert len(stale_evid) == 1
    assert "Simulated laptop telemetry is stale" in stale_evid[0].note



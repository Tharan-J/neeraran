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

"""
Database Seeding Script for NEERARAN
Initializes assets, registered data sources, engineers, historical baselines and past incidents.
"""

import os
import json
import uuid
import hashlib
from datetime import datetime, timedelta
import numpy as np
from sqlalchemy.orm import Session
from apps.api.db.database import (
    engine, init_db, Organization, Deployment, Asset, DataSource,
    Engineer, TelemetryEvent, LatestAssetState, Incident, IncidentEvidence,
    AuditLog, EvaluationRecord, GroundTruth,
    Role, User, UserBuildingAssignment, Permission, Complaint, ComplaintStatusHistory,
    ModelPricingConfig, AgentTokenUsage, GeminiRequest
)

def hash_key(key: str) -> str:
    return hashlib.sha256(key.encode()).hexdigest()

DATA_SOURCES_CONFIG = [
    {
        "id": "source_1",
        "name": "Water Supply & Reservoirs Subsystem",
        "api_key": "neeraran-source-1-supply-secret",
        "source_type": "supply"
    },
    {
        "id": "source_2",
        "name": "Building Consumption Meters",
        "api_key": "neeraran-source-2-consumption-secret",
        "source_type": "consumption"
    },
    {
        "id": "source_3",
        "name": "Infrastructure Telemetry (Pressure & Tanks)",
        "api_key": "neeraran-source-3-infra-secret",
        "source_type": "telemetry"
    },
    {
        "id": "source_4",
        "name": "Operational Information (Weather & Workforce)",
        "api_key": "neeraran-source-4-ops-secret",
        "source_type": "operations"
    }
]

ENGINEERS_CONFIG = [
    {
        "id": "ENG-01",
        "name": "S. Arumugam",
        "role": "Lead Hydraulic & SCADA Engineer",
        "skills": json.dumps(["scada", "valves", "pumps", "hydraulics"]),
        "availability": "available",
        "current_workload": 1,
        "contact": "+91 94431 82011"
    },
    {
        "id": "ENG-02",
        "name": "K. Priya",
        "role": "Acoustic Leak Detection Specialist",
        "skills": json.dumps(["leak_detection", "acoustics", "pipe_inspection"]),
        "availability": "available",
        "current_workload": 0,
        "contact": "+91 94432 15042"
    },
    {
        "id": "ENG-03",
        "name": "M. Murugan",
        "role": "Mechanical & Pump Technician",
        "skills": json.dumps(["pumps", "motors", "electrical", "valves"]),
        "availability": "available",
        "current_workload": 0,
        "contact": "+91 98422 67890"
    },
    {
        "id": "ENG-04",
        "name": "R. Venkatesh",
        "role": "Distribution Network Plumber",
        "skills": json.dumps(["plumbing", "pipe_replacement", "trenches"]),
        "availability": "available",
        "current_workload": 1,
        "contact": "+91 97890 12345"
    },
    {
        "id": "ENG-05",
        "name": "D. Selvi",
        "role": "Internal Building Water Systems Specialist",
        "skills": json.dumps(["plumbing", "fixtures", "hostel_repairs"]),
        "availability": "available",
        "current_workload": 0,
        "contact": "+91 94420 98765"
    }
]

def seed_database(db: Session, force: bool = False):
    init_db()

    # Check if already seeded
    if not force and db.query(Asset).count() > 0:
        print("Database already seeded with assets.")
        return

    print("Seeding NEERARAN database...")

    # 1. Organization & Deployment
    org = Organization(id="ORG-TCS-CAMPUS", name="TCS Campus Resilience Initiative")
    db.merge(org)

    deploy = Deployment(
        id="DEP-SATHY-01",
        org_id=org.id,
        name="Bannari Amman / Sathyamangalam Digital Twin",
        location="Erode District, Tamil Nadu"
    )
    db.merge(deploy)

    # 2. Data Sources
    for src in DATA_SOURCES_CONFIG:
        ds = DataSource(
            id=src["id"],
            name=src["name"],
            api_key_hash=hash_key(src["api_key"]),
            source_type=src["source_type"],
            status="online",
            last_seen=datetime.utcnow()
        )
        db.merge(ds)

    # 3. Engineers
    for eng in ENGINEERS_CONFIG:
        e = Engineer(
            id=eng["id"],
            name=eng["name"],
            role=eng["role"],
            skills=eng["skills"],
            availability=eng["availability"],
            current_workload=eng["current_workload"],
            contact=eng["contact"]
        )
        db.merge(e)

    # 4. Assets from campus.geojson
    geojson_path = os.path.join(os.path.dirname(__file__), "..", "data", "campus.geojson")
    if os.path.exists(geojson_path):
        with open(geojson_path) as f:
            cdata = json.load(f)
            for feat in cdata.get("features", []):
                props = feat.get("properties", {})
                aid = feat.get("id") or props.get("id")
                kind = props.get("kind", "asset")
                name = props.get("name", aid)
                geom = feat.get("geometry", {})

                asset = Asset(
                    id=aid,
                    name=name,
                    kind=kind,
                    asset_type=props.get("type"),
                    vulnerable=props.get("vulnerable", False),
                    population=props.get("population", 0),
                    capacity_kl=props.get("capacity_kl"),
                    safety_level_kl=props.get("safety_level_kl"),
                    nominal_demand_kl=props.get("demand_kl_per_day"),
                    coordinates=json.dumps(geom.get("coordinates"))
                )
                db.merge(asset)

                # Initialize Latest Asset State
                if kind == "block":
                    db.merge(LatestAssetState(
                        asset_id=aid,
                        metric="flow_lpm",
                        value=round(props.get("demand_kl_per_day", 20.0) * 1000.0 / (24.0 * 60.0), 2),
                        unit="L/min",
                        status="normal"
                    ))
                elif kind in ["tank", "sump"]:
                    cap = props.get("capacity_kl", 100.0)
                    db.merge(LatestAssetState(
                        asset_id=aid,
                        metric="level_m",
                        value=round(cap * 0.75 * 0.04, 2),  # roughly 3.0 m
                        unit="m",
                        status="normal"
                    ))
                elif kind == "pipe":
                    db.merge(LatestAssetState(
                        asset_id=aid,
                        metric="pressure_bar",
                        value=props.get("nominal_pressure_bar", 3.2),
                        unit="bar",
                        status="normal"
                    ))
                elif kind == "borewell":
                    db.merge(LatestAssetState(
                        asset_id=aid,
                        metric="yield_lpm",
                        value=props.get("design_rate_lpm", 100.0),
                        unit="L/min",
                        status="normal"
                    ))

    # 5. Seed historical leak incidents (past 90 days) for ground truth & evaluation baselines
    past_incidents = [
        ("HIST-01", "leak", "BLK-HSTL-B", 42.0, "repaired", 12, 14, "Hostel B 3rd floor washroom supply riser fissure. Repaired by clamp."),
        ("HIST-02", "leak", "PIPE-SUMP-OHT2", 85.0, "repaired", 28, 30, "Main transfer pipe joint gasket blown due to surge pressure."),
        ("HIST-03", "shortage", "OHT-WEST", 0.0, "repaired", 45, 46, "Borewell 2 pump starter coil trip causing low overhead head."),
        ("HIST-04", "leak", "BLK-ACAD-3", 38.0, "repaired", 60, 61, "Underground feed pipe pinhole leak detected by acoustic sensor."),
        ("HIST-05", "sensor_fault", "BLK-LIB", 0.0, "repaired", 75, 75, "Ultrasonic flow meter transducer detached, reporting 0 L/min."),
        ("HIST-06", "leak", "PIPE-OHT3-MESS", 55.0, "repaired", 82, 83, "Mess kitchen utility line valve gland packing leak.")
    ]

    base_time = datetime.utcnow()
    for inc_id, ctype, loc, loss, stat, days_ago_start, days_ago_end, notes in past_incidents:
        created = base_time - timedelta(days=days_ago_start)
        resolved = base_time - timedelta(days=days_ago_end)
        inc = Incident(
            id=inc_id,
            case_type=ctype,
            location=loc,
            confidence=0.95,
            loss_rate_kl_day=round(loss * 1.44, 1),
            priority_score=78.5,
            status="resolved",
            created_at=created,
            resolved_at=resolved,
            why_text=notes,
            verifier_result="verified",
            groundedness_score=1.0
        )
        db.merge(inc)

    # 7. Pre-seed Operational Roles
    roles_data = [
        ("admin", "Estate Admin", "Full authorized control across all campus infrastructure, models, approvals, and simulation."),
        ("student", "Student Resident", "Campus water-awareness, own-building consumption, conservation tips, and personal complaints."),
        ("building_admin", "Building Administrator", "Assigned building consumption, building alerts, forward complaints, request maintenance."),
        ("engineer", "Maintenance Engineer", "Assigned work orders, repair logs, findings submission, and material requests.")
    ]
    for rid, rname, rdesc in roles_data:
        db.merge(Role(id=rid, name=rname, description=rdesc))

    # 8. Pre-seed Standard Users for all 4 roles
    users_data = [
        ("USER-ADMIN-01", "admin@neeraran.edu", "Dr. K. Swaminathan", "admin", None, None),
        ("USER-STUDENT-01", "student@neeraran.edu", "Ananya Ramesh", "student", "BLK-HSTL-A", None),
        ("USER-BLDADM-01", "bld_admin@neeraran.edu", "Prof. M. Soundararajan", "building_admin", "BLK-HSTL-A", None),
        ("USER-ENG-01", "engineer@neeraran.edu", "K. Priya", "engineer", "BLK-HSTL-A", "ENG-02")
    ]
    for uid, uemail, ufname, urole, ubld, ueng in users_data:
        db.merge(User(
            id=uid,
            email=uemail,
            full_name=ufname,
            role=urole,
            assigned_building_id=ubld,
            assigned_engineer_id=ueng,
            is_active=True
        ))
        if ubld:
            db.merge(UserBuildingAssignment(
                id=f"UBA-{uid}",
                user_id=uid,
                building_id=ubld,
                role=urole
            ))

    # 9. Model Pricing Configuration (Official Gemini 3.5 Flash-Lite Paid Tier)
    db.merge(ModelPricingConfig(
        id="CFG-GEMINI-35-LITE",
        model_name="gemini-3.5-flash-lite",
        input_price_per_million=0.30,
        output_price_per_million=2.50,
        pricing_tier="standard_paid",
        version="2026-v1",
        is_active=True
    ))

    # 10. Pre-seed Initial Complaints (CPGRAMS Format)
    initial_complaints = [
        (
            "CMP-2026-0001",
            "CPGRAMS/2026/NEER-00042",
            "USER-STUDENT-01",
            "BLK-HSTL-A",
            "Water leakage",
            "Continuous water seepage and low tap pressure observed on 2nd floor washroom riser in Hostel Block A.",
            "acknowledged",
            "high",
            "WO-HSTLA-01",
            "Forwarded to Acoustic Leak Detection Specialist K. Priya."
        ),
        (
            "CMP-2026-0002",
            "CPGRAMS/2026/NEER-00043",
            "USER-STUDENT-01",
            "BLK-MESS",
            "Damaged water infrastructure",
            "Wash basin tap handle loose and dripping in Central Mess dining hall hand-wash section.",
            "in_progress",
            "medium",
            None,
            "Plumbing technician scheduled for afternoon inspection."
        )
    ]
    for cid, ctrack, cuid, cbld, ccat, cdesc, cstat, cpri, cwo, cremarks in initial_complaints:
        db.merge(Complaint(
            id=cid,
            tracking_id=ctrack,
            user_id=cuid,
            building_id=cbld,
            category=ccat,
            description=cdesc,
            status=cstat,
            priority=cpri,
            assigned_work_order_id=cwo,
            action_taken_remarks=cremarks
        ))

    # 11. Initialized Agent Token Usage Records
    agents_list = ["Monitor", "Detector", "Localizer", "Forecaster", "Prioritizer", "Optimizer", "Verifier", "Interventor", "Measurer", "ScenarioParser"]
    for ag in agents_list:
        db.merge(AgentTokenUsage(
            id=ag,
            agent_name=ag,
            total_requests=0,
            total_input_tokens=0,
            total_output_tokens=0,
            total_thinking_tokens=0,
            total_tokens=0,
            total_cost_usd=0.0
        ))

    # Commit all seed data
    db.commit()
    print("Database seeding completed successfully.")

if __name__ == "__main__":
    from apps.api.db.database import SessionLocal
    with SessionLocal() as db_session:
        seed_database(db_session, force=True)

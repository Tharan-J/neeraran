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
    AuditLog, EvaluationRecord, GroundTruth
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

    # 6. Audit log initialization
    audit = AuditLog(
        id=f"AUDIT-{uuid.uuid4().hex[:8]}",
        timestamp=datetime.utcnow(),
        actor="system",
        role="system",
        action="database_initialized",
        resource_id="campus_twin",
        details_json=json.dumps({"message": "NEERARAN campus twin system initialized with 20 blocks, 5 storage units, 3 supply assets."})
    )
    db.merge(audit)

    db.commit()
    print("Database seeding completed successfully.")

if __name__ == "__main__":
    from apps.api.db.database import SessionLocal
    with SessionLocal() as db_session:
        seed_database(db_session, force=True)

"""
NEERARAN Distributed Data Source Simulators
Four independent producers matching the 5-laptop deployment architecture.
Each source authenticates using its API key, connects to the central API,
and transmits timestamped readings over HTTP.
"""

import os
import sys
import time
import argparse
import random
import json
from datetime import datetime, timezone
import requests

API_URL = os.getenv("NEERARAN_API_URL", "http://localhost:8000")

SOURCE_CONFIGS = {
    1: {
        "id": "source_1",
        "name": "Water Supply & Reservoirs Subsystem",
        "key": "neeraran-source-1-supply-secret",
        "type": "supply",
        "interval_sec": 3.0
    },
    2: {
        "id": "source_2",
        "name": "Building Consumption Meters",
        "key": "neeraran-source-2-consumption-secret",
        "type": "consumption",
        "interval_sec": 3.0
    },
    3: {
        "id": "source_3",
        "name": "Infrastructure Telemetry (Pressure & Tanks)",
        "key": "neeraran-source-3-infra-secret",
        "type": "telemetry",
        "interval_sec": 3.0
    },
    4: {
        "id": "source_4",
        "name": "Operational Information & Environment",
        "key": "neeraran-source-4-ops-secret",
        "type": "operations",
        "interval_sec": 5.0
    }
}

class SourceSimulator:
    def __init__(self, source_num: int, base_url: str = API_URL):
        if source_num not in SOURCE_CONFIGS:
            raise ValueError(f"Invalid source number {source_num}. Must be 1, 2, 3, or 4.")
        self.config = SOURCE_CONFIGS[source_num]
        self.source_id = self.config["id"]
        self.name = self.config["name"]
        self.api_key = self.config["key"]
        self.base_url = base_url.rstrip("/")
        self.interval = self.config["interval_sec"]
        self.is_running = True
        self.transmission_count = 0
        self.last_status = "initialized"

    def send_telemetry_batch(self, events: list) -> bool:
        """Sends batch of readings to POST /api/v1/telemetry with source credentials."""
        url = f"{self.base_url}/api/v1/telemetry"
        headers = {
            "Content-Type": "application/json",
            "X-Source-ID": self.source_id,
            "X-API-Key": self.api_key
        }
        try:
            resp = requests.post(url, json={"events": events}, headers=headers, timeout=4.0)
            if resp.status_code in [200, 201]:
                self.transmission_count += len(events)
                self.last_status = f"HTTP {resp.status_code} OK (sent {len(events)} events)"
                return True
            else:
                self.last_status = f"HTTP {resp.status_code} Error: {resp.text[:100]}"
                return False
        except Exception as e:
            self.last_status = f"Connection failed: {str(e)[:80]}"
            return False

    def generate_source_1_readings(self) -> list:
        """Source 1: Municipal supply, reservoir levels, inflow, borewell yield, pump readings."""
        now = datetime.now(timezone.utc).isoformat()
        events = [
            {"source_id": self.source_id, "asset_id": "INLET-MUNI", "timestamp": now, "metric": "flow_lpm", "value": round(random.uniform(280.0, 320.0), 1), "unit": "L/min"},
            {"source_id": self.source_id, "asset_id": "BORE-01", "timestamp": now, "metric": "yield_lpm", "value": round(random.uniform(115.0, 122.0), 1), "unit": "L/min"},
            {"source_id": self.source_id, "asset_id": "BORE-02", "timestamp": now, "metric": "yield_lpm", "value": round(random.uniform(92.0, 97.0), 1), "unit": "L/min"},
            {"source_id": self.source_id, "asset_id": "SUMP-CENTRAL", "timestamp": now, "metric": "level_m", "value": round(random.uniform(3.4, 3.8), 2), "unit": "m"},
            {"source_id": self.source_id, "asset_id": "SUMP-CENTRAL", "timestamp": now, "metric": "volume_kl", "value": round(random.uniform(360.0, 395.0), 1), "unit": "kL"},
        ]
        return events

    def generate_source_2_readings(self) -> list:
        """Source 2: Block consumption, minimum night flow, occupancy demand, meter readings."""
        now = datetime.now(timezone.utc).isoformat()
        blocks = [
            ("BLK-HSTL-A", 45.0, 65.0),
            ("BLK-HSTL-B", 40.0, 58.0),
            ("BLK-HSTL-C", 50.0, 72.0),
            ("BLK-MESS", 35.0, 50.0),
            ("BLK-HLTH", 8.0, 14.0),
            ("BLK-ACAD-1", 18.0, 26.0),
            ("BLK-ACAD-2", 16.0, 24.0),
            ("BLK-LIB", 6.0, 10.0),
        ]
        events = []
        for bid, min_flow, max_flow in blocks:
            flow = round(random.uniform(min_flow, max_flow), 1)
            events.append({
                "source_id": self.source_id,
                "asset_id": bid,
                "timestamp": now,
                "metric": "flow_lpm",
                "value": flow,
                "unit": "L/min"
            })
        return events

    def generate_source_3_readings(self) -> list:
        """Source 3: Pipeline pressure, overhead tank levels, pump status, valve status."""
        now = datetime.now(timezone.utc).isoformat()
        events = [
            {"source_id": self.source_id, "asset_id": "OHT-NORTH", "timestamp": now, "metric": "level_m", "value": round(random.uniform(2.8, 3.2), 2), "unit": "m"},
            {"source_id": self.source_id, "asset_id": "OHT-SOUTH", "timestamp": now, "metric": "level_m", "value": round(random.uniform(2.5, 2.9), 2), "unit": "m"},
            {"source_id": self.source_id, "asset_id": "OHT-EAST", "timestamp": now, "metric": "level_m", "value": round(random.uniform(3.0, 3.4), 2), "unit": "m"},
            {"source_id": self.source_id, "asset_id": "OHT-WEST", "timestamp": now, "metric": "level_m", "value": round(random.uniform(2.2, 2.6), 2), "unit": "m"},
            {"source_id": self.source_id, "asset_id": "PIPE-SUMP-OHT1", "timestamp": now, "metric": "pressure_bar", "value": round(random.uniform(3.1, 3.4), 2), "unit": "bar"},
            {"source_id": self.source_id, "asset_id": "PIPE-OHT1-HSTLA", "timestamp": now, "metric": "pressure_bar", "value": round(random.uniform(2.6, 2.9), 2), "unit": "bar"},
            {"source_id": self.source_id, "asset_id": "PIPE-OHT3-MESS", "timestamp": now, "metric": "pressure_bar", "value": round(random.uniform(2.8, 3.1), 2), "unit": "bar"},
        ]
        return events

    def generate_source_4_readings(self) -> list:
        """Source 4: Weather, rainfall, complaints, maintenance records, inspection findings."""
        now = datetime.now(timezone.utc).isoformat()
        events = [
            {"source_id": self.source_id, "asset_id": "CAMPUS", "timestamp": now, "metric": "temperature_c", "value": round(random.uniform(27.0, 32.0), 1), "unit": "C"},
            {"source_id": self.source_id, "asset_id": "CAMPUS", "timestamp": now, "metric": "rainfall_mm", "value": 0.0, "unit": "mm/h"},
            {"source_id": self.source_id, "asset_id": "CAMPUS", "timestamp": now, "metric": "humidity_pct", "value": round(random.uniform(55.0, 72.0), 1), "unit": "%"}
        ]
        return events

    def get_readings(self) -> list:
        if self.config["type"] == "supply":
            return self.generate_source_1_readings()
        elif self.config["type"] == "consumption":
            return self.generate_source_2_readings()
        elif self.config["type"] == "telemetry":
            return self.generate_source_3_readings()
        else:
            return self.generate_source_4_readings()

    def run_loop(self):
        print(f"[{self.source_id}] Starting simulator: {self.name}")
        print(f"Connecting to Central NEERARAN at: {self.base_url}")
        print("Press Ctrl+C to stop.\n")

        while self.is_running:
            readings = self.get_readings()
            success = self.send_telemetry_batch(readings)
            ts = datetime.now().strftime("%H:%M:%S")
            status_symbol = "✓" if success else "✗"
            print(f"[{ts}] {status_symbol} {self.source_id}: {self.last_status} (Total: {self.transmission_count})")
            time.sleep(self.interval)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="NEERARAN Distributed Data Source Simulator (Laptops 2-5)")
    parser.add_argument("--source", type=int, choices=[1, 2, 3, 4], default=1, help="Source number (1 to 4)")
    parser.add_argument("--url", type=str, default=API_URL, help="Central NEERARAN API base URL")
    args = parser.parse_args()

    sim = SourceSimulator(source_num=args.source, base_url=args.url)
    try:
        sim.run_loop()
    except KeyboardInterrupt:
        print(f"\n[{sim.source_id}] Simulator stopped by user.")

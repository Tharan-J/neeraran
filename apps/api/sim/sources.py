"""
NEERARAN Distributed Laptop Data Source Simulators
Four independent producers matching the 5-laptop demonstration architecture.

Source 1 (Laptop 2): Water Supply & Reservoirs (source1_supply_reservoir.json)
Source 2 (Laptop 3): Building Flow Meters & Diurnal Metrics (source2_flow_consumption.json)
Source 3 (Laptop 4): Infrastructure SCADA & Pipe Pressure (source3_infra_telemetry.json)
Source 4 (Laptop 5): Weather Radar & Citizen Grievance Portal (source4_operational_weather_grievance.json)
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
        "laptop_label": "Laptop 2 (Supply & Reservoirs)",
        "key": "neeraran-source-1-supply-secret",
        "type": "supply",
        "interval_sec": 3.0,
        "json_file": "data/distributed_sources/source1_supply_reservoir.json"
    },
    2: {
        "id": "source_2",
        "name": "Building Consumption & Smart Flow Sensors",
        "laptop_label": "Laptop 3 (Flow & Smart Meters)",
        "key": "neeraran-source-2-consumption-secret",
        "type": "consumption",
        "interval_sec": 3.0,
        "json_file": "data/distributed_sources/source2_flow_consumption.json"
    },
    3: {
        "id": "source_3",
        "name": "Infrastructure Telemetry (Pressure & Tanks)",
        "laptop_label": "Laptop 4 (Pressure & SCADA)",
        "key": "neeraran-source-3-infra-secret",
        "type": "telemetry",
        "interval_sec": 3.0,
        "json_file": "data/distributed_sources/source3_infra_telemetry.json"
    },
    4: {
        "id": "source_4",
        "name": "Operational Weather & Citizen Grievance Portal",
        "laptop_label": "Laptop 5 (Environment & Grievances)",
        "key": "neeraran-source-4-ops-secret",
        "type": "operations",
        "interval_sec": 5.0,
        "json_file": "data/distributed_sources/source4_operational_weather_grievance.json"
    }
}

class SourceSimulator:
    def __init__(self, source_num: int, base_url: str = API_URL):
        if source_num not in SOURCE_CONFIGS:
            raise ValueError(f"Invalid source number {source_num}. Must be 1, 2, 3, or 4.")
        self.config = SOURCE_CONFIGS[source_num]
        self.source_id = self.config["id"]
        self.name = self.config["name"]
        self.laptop_label = self.config["laptop_label"]
        self.api_key = self.config["key"]
        self.base_url = base_url.rstrip("/")
        self.interval = self.config["interval_sec"]
        self.json_file_path = self.config.get("json_file")
        self.raw_data = self._load_json_data()
        self.is_running = True
        self.transmission_count = 0
        self.last_status = "initialized"

    def _load_json_data(self) -> dict:
        if not self.json_file_path or not os.path.exists(self.json_file_path):
            # Try finding relative to workspace root
            root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", self.json_file_path))
            if os.path.exists(root_path):
                self.json_file_path = root_path
            else:
                print(f"Warning: JSON file not found at {self.json_file_path}")
                return {}

        try:
            with open(self.json_file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: Failed to load {self.json_file_path}: {e}")
            return {}

    def get_payload(self) -> dict:
        """Constructs fresh payload timestamped to current UTC second."""
        now = datetime.now(timezone.utc).isoformat()
        payload = dict(self.raw_data) if self.raw_data else {}
        payload["source_id"] = self.source_id
        payload["timestamp"] = now
        payload["laptop_label"] = self.laptop_label
        payload["demonstration_mode"] = "simulated_laptop_telemetry"

        # Update readings timestamps
        if "readings" in payload:
            for r in payload["readings"]:
                r["timestamp"] = now
                r["source_id"] = self.source_id

        return payload

    def send_payload(self) -> bool:
        """Transmits payload to POST /api/v1/sources/{source_id}/telemetry."""
        payload = self.get_payload()
        url = f"{self.base_url}/api/v1/sources/{self.source_id}/telemetry"
        headers = {
            "Content-Type": "application/json",
            "X-Source-ID": self.source_id,
            "X-API-Key": self.api_key
        }
        try:
            resp = requests.post(url, json=payload, headers=headers, timeout=5.0)
            if resp.status_code in [200, 201]:
                reading_count = len(payload.get("readings", [])) or (1 if "weather" in payload else 0)
                self.transmission_count += 1
                self.last_status = f"HTTP {resp.status_code} OK (sent {reading_count} items)"
                return True
            else:
                self.last_status = f"HTTP {resp.status_code} Error: {resp.text[:120]}"
                return False
        except Exception as e:
            self.last_status = f"Connection failed: {str(e)[:80]}"
            return False

    def run_loop(self):
        print(f"\033[1;34m===============================================================\033[0m")
        print(f"\033[1;32m  NEERARAN Distributed Sender: {self.laptop_label}\033[0m")
        print(f"  Source ID: {self.source_id} ({self.name})")
        print(f"  Target Central API: {self.base_url}")
        print(f"  JSON Source File: {self.json_file_path}")
        print(f"  Transmission Interval: {self.interval}s")
        print(f"\033[1;34m===============================================================\033[0m\n")

        while self.is_running:
            success = self.send_payload()
            ts = datetime.now().strftime("%H:%M:%S")
            status_symbol = "\033[1;32m✓\033[0m" if success else "\033[1;31m✗\033[0m"
            print(f"[{ts}] {status_symbol} [{self.source_id}] {self.last_status} | Batches transmitted: {self.transmission_count}")
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
        print(f"\n\033[1;33m[{sim.source_id}] Simulator stopped by user.\033[0m")

"""
NEERARAN Campus Water Network Physical Simulator
Deterministic digital twin with mass balance, diurnal rhythms, faults,
complaints generator, weather forecast, and hidden ground truth.
"""

import math
import random
import json
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any, Optional

class CampusSimulator:
    def __init__(self, seed: int = 42):
        self.seed = seed
        self.rng = random.Random(seed)
        self.tick = 0  # 1 tick = 5 minutes
        self.dt_minutes = 5.0
        self.speed_multiplier = 1.0  # 1x, 5x, 20x
        self.is_running = True
        self.base_time = datetime(2026, 10, 31, 0, 0, tzinfo=timezone.utc)

        # Campus Assets Storage (Volumes in kL, safety levels in kL)
        self.tanks = {
            "SUMP-CENTRAL": {"capacity": 500.0, "current": 380.0, "safety": 100.0, "inflow": 0.0, "outflow": 0.0},
            "OHT-NORTH": {"capacity": 120.0, "current": 92.0, "safety": 30.0, "inflow": 0.0, "outflow": 0.0},
            "OHT-SOUTH": {"capacity": 100.0, "current": 78.0, "safety": 25.0, "inflow": 0.0, "outflow": 0.0},
            "OHT-EAST": {"capacity": 140.0, "current": 105.0, "safety": 35.0, "inflow": 0.0, "outflow": 0.0},
            "OHT-WEST": {"capacity": 80.0, "current": 62.0, "safety": 20.0, "inflow": 0.0, "outflow": 0.0},
        }

        # Pumps state (True = running)
        self.pumps = {
            "PUMP-BORE1": {"running": True, "nominal_lpm": 120.0, "source": "BORE-01", "target": "SUMP-CENTRAL"},
            "PUMP-BORE2": {"running": True, "nominal_lpm": 95.0, "source": "BORE-02", "target": "SUMP-CENTRAL"},
            "PUMP-TRANSFER-N": {"running": False, "nominal_lpm": 300.0, "source": "SUMP-CENTRAL", "target": "OHT-NORTH"},
            "PUMP-TRANSFER-S": {"running": False, "nominal_lpm": 250.0, "source": "SUMP-CENTRAL", "target": "OHT-SOUTH"},
            "PUMP-TRANSFER-E": {"running": False, "nominal_lpm": 300.0, "source": "SUMP-CENTRAL", "target": "OHT-EAST"},
            "PUMP-TRANSFER-W": {"running": False, "nominal_lpm": 200.0, "source": "SUMP-CENTRAL", "target": "OHT-WEST"},
        }

        # Valves state (1.0 = fully open, 0.0 = closed)
        self.valves = {
            "VALVE-MUNI": 1.0,
            "VALVE-FEED-HSTLA": 1.0,
            "VALVE-FEED-HSTLB": 1.0,
            "VALVE-FEED-HSTLC": 1.0,
            "VALVE-FEED-MESS": 1.0,
            "VALVE-FEED-ACAD": 1.0,
            "VALVE-FEED-HLTH": 1.0,
        }

        # Active faults (Hidden Ground Truth)
        # item: {id, type, location, loss_lpm, start_tick, end_tick, active, metadata}
        self.faults: List[Dict[str, Any]] = []

        # Weather & Environmental State
        self.temperature_c = 28.5
        self.rainfall_mm_hr = 0.0
        self.heatwave_active = False
        self.heatwave_demand_pct = 0.0
        self.borewell_yield_multiplier = 1.0

        # Complaints backlog
        self.complaints: List[Dict[str, Any]] = []

        # Ground truth history for benchmark / evaluation
        self.historical_faults_ground_truth: List[Dict[str, Any]] = []

    def get_simulated_time(self) -> datetime:
        return self.base_time + timedelta(minutes=self.tick * self.dt_minutes)

    def inject_fault(self, fault_type: str, location: str, loss_lpm: float = 50.0, duration_ticks: int = 288, metadata: Optional[Dict] = None) -> str:
        fid = f"FAULT-{len(self.faults)+1:03d}"
        fault = {
            "id": fid,
            "type": fault_type,
            "location": location,
            "loss_lpm": loss_lpm,
            "start_tick": self.tick,
            "end_tick": self.tick + duration_ticks,
            "active": True,
            "metadata": metadata or {}
        }
        self.faults.append(fault)
        self.historical_faults_ground_truth.append(fault)
        return fid

    def remove_fault(self, fault_id: str):
        for f in self.faults:
            if f["id"] == fault_id:
                f["active"] = False

    def load_preset_scenario(self, scenario_name: str) -> Dict[str, Any]:
        """Loads one of the official benchmark scenarios."""
        self.faults.clear()
        details = {}

        if scenario_name == "Hostel night leak":
            # Leak starts at 2:00 AM in Hostel A riser
            fid = self.inject_fault("hostel_leak", "BLK-HSTL-A", loss_lpm=58.0, duration_ticks=144, metadata={"segment": "PIPE-OHT1-HSTLA", "description": "Hostel Block A 2nd floor supply pipe fissure"})
            details = {"scenario": scenario_name, "fault_id": fid, "target": "BLK-HSTL-A", "loss_lpm": 58.0}

        elif scenario_name == "Heatwave plus borewell decline":
            self.heatwave_active = True
            self.heatwave_demand_pct = 25.0
            self.borewell_yield_multiplier = 0.65
            fid = self.inject_fault("heatwave", "CAMPUS", loss_lpm=0.0, duration_ticks=500, metadata={"delta_temp": 4.5, "borewell_decline_pct": 35.0})
            details = {"scenario": scenario_name, "heatwave": True, "demand_surge": "+25%", "borewell_loss": "-35%"}

        elif scenario_name == "Monsoon failure":
            self.rainfall_mm_hr = 0.0
            self.borewell_yield_multiplier = 0.70
            fid = self.inject_fault("monsoon_failure", "CAMPUS", loss_lpm=0.0, duration_ticks=1000)
            details = {"scenario": scenario_name, "drought_conditions": True}

        elif scenario_name == "Fest weekend occupancy surge":
            fid = self.inject_fault("occupancy_surge", "BLK-HSTL-C", loss_lpm=0.0, duration_ticks=288, metadata={"surge_pct": 45.0})
            details = {"scenario": scenario_name, "surge_location": "Hostel C & Mess", "surge_pct": 45.0}

        elif scenario_name == "Main burst plus meter fault":
            fid1 = self.inject_fault("burst_main", "PIPE-SUMP-OHT1", loss_lpm=140.0, duration_ticks=72, metadata={"segment": "PIPE-SUMP-OHT1"})
            fid2 = self.inject_fault("sensor_fault", "BLK-LIB", loss_lpm=0.0, duration_ticks=200, metadata={"mode": "flat_zero", "sensor_metric": "flow_lpm"})
            details = {"scenario": scenario_name, "burst": fid1, "sensor_fault": fid2}

        elif scenario_name == "Pump failure":
            fid = self.inject_fault("pump_failure", "PUMP-BORE1", loss_lpm=0.0, duration_ticks=150, metadata={"pump": "PUMP-BORE1"})
            self.pumps["PUMP-BORE1"]["running"] = False
            details = {"scenario": scenario_name, "failed_pump": "PUMP-BORE1"}

        return details

    def step(self) -> Dict[str, Any]:
        """Advances the simulation by 1 tick (5 minutes)."""
        self.tick += 1
        sim_time = self.get_simulated_time()
        hour = sim_time.hour + (sim_time.minute / 60.0)
        day_of_week = sim_time.weekday()  # 0=Monday, 6=Sunday
        is_weekend = day_of_week >= 5

        # Update active faults
        active_faults = [f for f in self.faults if f["active"] and f["start_tick"] <= self.tick <= f["end_tick"]]

        # 1. Base Diurnal Demand Multiplier
        # Typical campus curve:
        # 0:00 - 5:00: Night baseline (~0.12 of peak)
        # 5:30 - 8:30: Morning peak (~1.0)
        # 9:00 - 12:00: Academic day (~0.55)
        # 12:00 - 14:00: Mess lunch bump (~0.85)
        # 14:00 - 17:00: Afternoon labs (~0.50)
        # 17:30 - 21:30: Evening hostel peak (~0.80)
        # 22:00 - 24:00: Night decay
        if 0.0 <= hour < 5.0:
            diurnal = 0.12 + 0.03 * math.sin(hour)
        elif 5.0 <= hour < 8.5:
            diurnal = 0.15 + 0.85 * math.sin((hour - 5.0) / 3.5 * math.pi)
        elif 8.5 <= hour < 12.0:
            diurnal = 0.55 + 0.05 * math.cos(hour)
        elif 12.0 <= hour < 14.0:
            diurnal = 0.85 + 0.08 * math.sin((hour - 12.0) / 2.0 * math.pi)
        elif 14.0 <= hour < 17.5:
            diurnal = 0.50 + 0.05 * math.sin(hour)
        elif 17.5 <= hour < 21.5:
            diurnal = 0.78 + 0.15 * math.sin((hour - 17.5) / 4.0 * math.pi)
        else:
            diurnal = 0.35 * (1.0 - (hour - 21.5) / 2.5) + 0.12

        if is_weekend:
            # Shift academic demand lower, hostel slightly higher
            diurnal *= 0.85

        if self.heatwave_active:
            diurnal *= (1.0 + self.heatwave_demand_pct / 100.0)

        # 2. Block consumption (L/min)
        # Nominal block design demand in kL/day -> average L/min = (demand * 1000) / (24 * 60)
        block_demands: Dict[str, float] = {}
        blocks_data = {
            "BLK-HSTL-A": {"nominal_kl": 85.0, "is_hostel": True},
            "BLK-HSTL-B": {"nominal_kl": 78.0, "is_hostel": True},
            "BLK-HSTL-C": {"nominal_kl": 95.0, "is_hostel": True},
            "BLK-MESS": {"nominal_kl": 60.0, "is_hostel": False},
            "BLK-HLTH": {"nominal_kl": 15.0, "is_hostel": False},
            "BLK-CRECHE": {"nominal_kl": 8.0, "is_hostel": False},
            "BLK-ACAD-1": {"nominal_kl": 35.0, "is_hostel": False},
            "BLK-ACAD-2": {"nominal_kl": 32.0, "is_hostel": False},
            "BLK-ACAD-3": {"nominal_kl": 34.0, "is_hostel": False},
            "BLK-ACAD-4": {"nominal_kl": 28.0, "is_hostel": False},
            "BLK-LIB": {"nominal_kl": 12.0, "is_hostel": False},
            "BLK-BIOTECH": {"nominal_kl": 25.0, "is_hostel": False},
            "BLK-MECHLAB": {"nominal_kl": 22.0, "is_hostel": False},
            "BLK-SPORTS": {"nominal_kl": 18.0, "is_hostel": False},
            "BLK-ADMIN": {"nominal_kl": 10.0, "is_hostel": False},
            "BLK-SAC": {"nominal_kl": 16.0, "is_hostel": False},
            "BLK-GUEST": {"nominal_kl": 20.0, "is_hostel": False},
            "BLK-STP": {"nominal_kl": 10.0, "is_hostel": False},
            "BLK-LAUNDRY": {"nominal_kl": 30.0, "is_hostel": False},
            "BLK-CAFE": {"nominal_kl": 18.0, "is_hostel": False},
        }

        total_campus_outflow_lpm = 0.0
        for bid, binfo in blocks_data.items():
            base_lpm = (binfo["nominal_kl"] * 1000.0) / 1440.0
            mult = diurnal
            if binfo["is_hostel"] and (hour < 5.0 or hour > 22.0):
                # Night flow baseline: ~0.10 - 0.15 of average
                mult = max(0.12, mult)
            elif not binfo["is_hostel"] and (hour < 6.0 or hour > 21.0):
                mult = 0.04  # Very low night flow in academic blocks

            noise = self.rng.gauss(0, base_lpm * 0.04)
            current_lpm = max(1.0, (base_lpm * mult) + noise)

            # Apply active leaks
            for f in active_faults:
                if f["location"] == bid or f.get("metadata", {}).get("block") == bid:
                    current_lpm += f["loss_lpm"]

            # Check sensor faults (flat zero)
            for f in active_faults:
                if f["type"] == "sensor_fault" and f["location"] == bid:
                    if f.get("metadata", {}).get("mode") == "flat_zero":
                        current_lpm = 0.0

            block_demands[bid] = round(current_lpm, 2)
            total_campus_outflow_lpm += current_lpm

        # 3. Supply inflows (Borewells + Municipal Cauvery supply)
        bore1_lpm = self.pumps["PUMP-BORE1"]["nominal_lpm"] * self.borewell_yield_multiplier if self.pumps["PUMP-BORE1"]["running"] else 0.0
        bore2_lpm = self.pumps["PUMP-BORE2"]["nominal_lpm"] * self.borewell_yield_multiplier if self.pumps["PUMP-BORE2"]["running"] else 0.0

        # Municipal Cauvery pipeline: 300 L/min between 4:00 AM and 10:00 AM
        muni_lpm = 320.0 * self.valves["VALVE-MUNI"] if (4.0 <= hour <= 10.0) else 40.0 * self.valves["VALVE-MUNI"]

        total_inflow_sump_lpm = bore1_lpm + bore2_lpm + muni_lpm

        # 4. Tank and Sump Water Balance (Mass Conservation)
        # Sump: V_next = V_current + (inflow_lpm - pumped_to_tanks_lpm) * (dt_min / 1000)
        pumped_from_sump_lpm = 0.0

        # Auto-replenishment logic for Overhead Tanks:
        # If OHT level drops below 65% capacity, turn on transfer pump until 90%
        for oht_id, pump_id, target_blocks in [
            ("OHT-NORTH", "PUMP-TRANSFER-N", ["BLK-HSTL-A", "BLK-HSTL-B"]),
            ("OHT-SOUTH", "PUMP-TRANSFER-S", ["BLK-ACAD-1", "BLK-ACAD-2", "BLK-ACAD-3", "BLK-ACAD-4", "BLK-LIB", "BLK-BIOTECH", "BLK-MECHLAB"]),
            ("OHT-EAST", "PUMP-TRANSFER-E", ["BLK-HSTL-C", "BLK-MESS", "BLK-LAUNDRY"]),
            ("OHT-WEST", "PUMP-TRANSFER-W", ["BLK-HLTH", "BLK-CRECHE", "BLK-ADMIN", "BLK-GUEST", "BLK-SAC", "BLK-SPORTS", "BLK-CAFE", "BLK-STP"]),
        ]:
            tank = self.tanks[oht_id]
            fill_pct = tank["current"] / tank["capacity"]
            pump = self.pumps[pump_id]

            # Burst on transfer pipe?
            transfer_loss = 0.0
            for f in active_faults:
                if f["type"] == "burst_main" and f.get("metadata", {}).get("segment") == f"PIPE-SUMP-{oht_id.split('-')[1]}":
                    transfer_loss += f["loss_lpm"]

            if fill_pct < 0.65 and self.tanks["SUMP-CENTRAL"]["current"] > 50.0:
                pump["running"] = True
            elif fill_pct > 0.90 or self.tanks["SUMP-CENTRAL"]["current"] <= 50.0:
                pump["running"] = False

            pump_flow = (pump["nominal_lpm"] if pump["running"] else 0.0)
            pumped_from_sump_lpm += pump_flow

            # Demand downstream of this OHT
            oht_outflow_lpm = sum(block_demands.get(b, 0.0) for b in target_blocks)
            oht_inflow_lpm = max(0.0, pump_flow - transfer_loss)

            # Mass balance update: V_next = V_curr + (inflow - outflow) * dt / 1000 (convert L to kL)
            delta_kl = (oht_inflow_lpm - oht_outflow_lpm) * (self.dt_minutes / 1000.0)
            tank["current"] = max(0.0, min(tank["capacity"], tank["current"] + delta_kl))
            tank["inflow"] = round(oht_inflow_lpm, 1)
            tank["outflow"] = round(oht_outflow_lpm, 1)

        # Update Central Sump
        delta_sump_kl = (total_inflow_sump_lpm - pumped_from_sump_lpm) * (self.dt_minutes / 1000.0)
        sump = self.tanks["SUMP-CENTRAL"]
        sump["current"] = max(0.0, min(sump["capacity"], sump["current"] + delta_sump_kl))
        sump["inflow"] = round(total_inflow_sump_lpm, 1)
        sump["outflow"] = round(pumped_from_sump_lpm, 1)

        # 5. Pressure Sensors at Pipe Nodes (bar)
        # Nominal pressure ~3.2 bar. Higher flow or leaks cause pressure drop (hydraulic gradient)
        pressures: Dict[str, float] = {}
        pipe_nodes = [
            ("PIPE-MUNI-SUMP", 3.8, muni_lpm),
            ("PIPE-BORE1-SUMP", 3.4, bore1_lpm),
            ("PIPE-BORE2-SUMP", 3.3, bore2_lpm),
            ("PIPE-SUMP-OHT1", 3.5, self.pumps["PUMP-TRANSFER-N"]["nominal_lpm"] if self.pumps["PUMP-TRANSFER-N"]["running"] else 1.2),
            ("PIPE-SUMP-OHT2", 3.5, self.pumps["PUMP-TRANSFER-S"]["nominal_lpm"] if self.pumps["PUMP-TRANSFER-S"]["running"] else 1.2),
            ("PIPE-SUMP-OHT3", 3.5, self.pumps["PUMP-TRANSFER-E"]["nominal_lpm"] if self.pumps["PUMP-TRANSFER-E"]["running"] else 1.2),
            ("PIPE-SUMP-OHT4", 3.2, self.pumps["PUMP-TRANSFER-W"]["nominal_lpm"] if self.pumps["PUMP-TRANSFER-W"]["running"] else 1.2),
            ("PIPE-OHT1-HSTLA", 2.8, block_demands["BLK-HSTL-A"]),
            ("PIPE-OHT1-HSTLB", 2.8, block_demands["BLK-HSTL-B"]),
            ("PIPE-OHT3-HSTLC", 2.9, block_demands["BLK-HSTL-C"]),
            ("PIPE-OHT3-MESS", 3.0, block_demands["BLK-MESS"]),
            ("PIPE-OHT2-ACAD1", 2.7, block_demands["BLK-ACAD-1"]),
            ("PIPE-OHT4-HLTH", 2.6, block_demands["BLK-HLTH"]),
        ]

        for pid, base_p, flow in pipe_nodes:
            # Friction drop delta_p ~ k * flow^1.85 (Hazen-Williams simplification)
            p_drop = (flow / 300.0) ** 1.6 * 0.45
            p_val = max(0.5, base_p - p_drop + self.rng.gauss(0, 0.04))

            # If there is an active leak along this segment, sharp pressure drop
            for f in active_faults:
                if f.get("metadata", {}).get("segment") == pid or (f["location"] in pid and f["loss_lpm"] > 20):
                    p_val -= (f["loss_lpm"] / 80.0) * 0.75

            pressures[pid] = round(max(0.4, p_val), 2)

        # 6. Weather & Environmental Telemetry
        self.temperature_c = round(24.0 + 8.5 * math.sin((hour - 9.0) / 12.0 * math.pi) + (4.0 if self.heatwave_active else 0.0), 1)

        # 7. Generate User Complaints (Lagged operational signal)
        for f in active_faults:
            # Low pressure complaint or visible wet patch
            if self.tick - f["start_tick"] > 18 and self.rng.random() < 0.08:
                loc = f["location"]
                msg = f"Low water pressure reported on 2nd floor bathrooms at {loc}." if "HSTL" in loc else f"Persistent damp ground and bubbling detected near {loc} service chamber."
                self.complaints.append({
                    "id": f"CMP-{len(self.complaints)+1:04d}",
                    "tick": self.tick,
                    "timestamp": sim_time.isoformat(),
                    "block": loc,
                    "category": "pressure_drop" if "HSTL" in loc else "visible_seepage",
                    "text": msg
                })

        # Calculate Total Days of Reserve
        total_stored_kl = sum(t["current"] for t in self.tanks.values())
        daily_consumption_kl = (total_campus_outflow_lpm * 1440.0) / 1000.0
        days_of_reserve = round(total_stored_kl / max(10.0, daily_consumption_kl), 1)

        snapshot = {
            "tick": self.tick,
            "timestamp": sim_time.isoformat(),
            "formatted_time": sim_time.strftime("%A, %d %b %Y %H:%M UTC"),
            "hour": round(hour, 2),
            "is_weekend": is_weekend,
            "speed_multiplier": self.speed_multiplier,
            "diurnal_multiplier": round(diurnal, 3),
            "total_consumption_lpm": round(total_campus_outflow_lpm, 1),
            "total_inflow_lpm": round(total_inflow_sump_lpm, 1),
            "total_stored_kl": round(total_stored_kl, 1),
            "days_of_reserve": days_of_reserve,
            "weather": {
                "temperature_c": self.temperature_c,
                "rainfall_mm_hr": self.rainfall_mm_hr,
                "heatwave": self.heatwave_active
            },
            "tanks": {k: {"current_kl": round(v["current"], 1), "capacity_kl": v["capacity"], "fill_pct": round(v["current"]/v["capacity"]*100, 1), "safety_level_kl": v["safety"]} for k, v in self.tanks.items()},
            "block_meters": block_demands,
            "pressures": pressures,
            "borewells": {
                "BORE-01": {"yield_lpm": round(bore1_lpm, 1), "running": self.pumps["PUMP-BORE1"]["running"]},
                "BORE-02": {"yield_lpm": round(bore2_lpm, 1), "running": self.pumps["PUMP-BORE2"]["running"]}
            },
            "active_faults_ground_truth": active_faults,
            "complaints": self.complaints[-5:]
        }
        return snapshot

# Global singleton simulator instance
simulator = CampusSimulator()

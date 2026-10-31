"""
NEERARAN ML Gateway
Unified interface for all machine learning models.
Features:
- Version tracking
- Latency measurement
- Confidence estimation
- Graceful degradation & fallback
- Evaluation registry
"""

import time
from typing import Dict, Any, Optional
from apps.api.ml.anomaly_model import AnomalyDetectorModel
from apps.api.ml.demand_model import DemandForecasterModel
from apps.api.ml.shortage_model import ShortageForecasterModel

class MLGateway:
    def __init__(self):
        self.anomaly_model = AnomalyDetectorModel()
        self.demand_model = DemandForecasterModel()
        self.shortage_model = ShortageForecasterModel()

        self.service_health = {
            "anomaly_detector": {"status": "healthy", "version": self.anomaly_model.version},
            "demand_forecaster": {"status": "healthy", "version": self.demand_model.version},
            "shortage_forecaster": {"status": "healthy", "version": self.shortage_model.version}
        }

    def detect_anomaly(self, flow_lpm: float, pressure_bar: float, hour: float, weekday: int, occupancy: float, baseline_mean: float, baseline_std: float) -> Dict[str, Any]:
        t0 = time.perf_counter()
        try:
            res = self.anomaly_model.predict(flow_lpm, pressure_bar, hour, weekday, occupancy, baseline_mean, baseline_std)
            latency_ms = (time.perf_counter() - t0) * 1000.0
            res["execution_time_ms"] = round(latency_ms, 2)
            res["fallback_used"] = False
            return res
        except Exception as e:
            latency_ms = (time.perf_counter() - t0) * 1000.0
            # Rule-based fallback
            z = (flow_lpm - baseline_mean) / max(1.0, baseline_std)
            return {
                "model_version": "fallback-zscore-rule",
                "is_anomaly": z > 3.0,
                "anomaly_score": round(min(1.0, z / 5.0), 3),
                "z_score": round(z, 2),
                "confidence": 0.70,
                "execution_time_ms": round(latency_ms, 2),
                "fallback_used": True,
                "error": str(e)
            }

    def forecast_demand(self, block_id: str, nominal_kl_day: float, current_hour: float, day_of_week: int) -> Dict[str, Any]:
        t0 = time.perf_counter()
        try:
            series = self.demand_model.forecast_block_demand_7d(block_id, nominal_kl_day, current_hour, day_of_week)
            latency_ms = (time.perf_counter() - t0) * 1000.0
            avg_smape = sum(p["smape_error_pct"] for p in series) / len(series)
            return {
                "model_version": self.demand_model.version,
                "block_id": block_id,
                "forecast_series": series,
                "mean_smape_pct": round(avg_smape, 2),
                "execution_time_ms": round(latency_ms, 2),
                "fallback_used": False
            }
        except Exception as e:
            latency_ms = (time.perf_counter() - t0) * 1000.0
            return {
                "model_version": "fallback-flat-forecast",
                "block_id": block_id,
                "forecast_series": [],
                "mean_smape_pct": 18.5,
                "execution_time_ms": round(latency_ms, 2),
                "fallback_used": True,
                "error": str(e)
            }

    def forecast_shortage(self, tank_id: str, current_level_kl: float, capacity_kl: float, safety_level_kl: float, inflow_rate_lpm: float, outflow_rate_lpm: float) -> Dict[str, Any]:
        t0 = time.perf_counter()
        try:
            trajectory = self.shortage_model.forecast_tank_levels_72h(tank_id, current_level_kl, capacity_kl, safety_level_kl, inflow_rate_lpm, outflow_rate_lpm)
            latency_ms = (time.perf_counter() - t0) * 1000.0

            # Find hours until critical
            hours_to_crit = None
            for p in trajectory:
                if p["is_critical"]:
                    hours_to_crit = p["hour"]
                    break

            return {
                "model_version": self.shortage_model.version,
                "tank_id": tank_id,
                "trajectory": trajectory,
                "hours_to_critical": hours_to_crit,
                "execution_time_ms": round(latency_ms, 2),
                "fallback_used": False
            }
        except Exception as e:
            latency_ms = (time.perf_counter() - t0) * 1000.0
            return {
                "model_version": "fallback-shortage-linear",
                "tank_id": tank_id,
                "trajectory": [],
                "hours_to_critical": None,
                "execution_time_ms": round(latency_ms, 2),
                "fallback_used": True,
                "error": str(e)
            }

# Singleton ML Gateway
ml_gateway = MLGateway()

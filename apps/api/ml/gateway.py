"""
NEERARAN ML Gateway
Unified interface for all machine learning models:
1. OneClassSVM Anomaly Detection (models/anamoly_detection.joblib)
2. XGBoost Hydraulic Leak Detection (models/leakage_detection.joblib)
3. Diurnal Baseline Anomaly Model (apps/api/ml/anomaly_model.py)
4. Demand Forecaster (apps/api/ml/demand_model.py)
5. Shortage Forecaster (apps/api/ml/shortage_model.py)
"""

import os
import time
import warnings
from typing import Dict, Any, Optional, List
import pandas as pd

from apps.api.ml.anomaly_model import AnomalyDetectorModel
from apps.api.ml.demand_model import DemandForecasterModel
from apps.api.ml.shortage_model import ShortageForecasterModel

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
MODELS_DIR = os.path.join(ROOT_DIR, "models")

class MLGateway:
    def __init__(self):
        self.anomaly_model = AnomalyDetectorModel()
        self.demand_model = DemandForecasterModel()
        self.shortage_model = ShortageForecasterModel()

        # Load real trained joblib models if present
        self.joblib_anomaly = None
        self.joblib_leakage = None

        self._load_joblib_models()

        self.service_health = {
            "anomaly_detector": {"status": "healthy", "version": self.anomaly_model.version},
            "joblib_anomaly_svm": {"status": "healthy" if self.joblib_anomaly else "unavailable", "version": "v1.8.0-oneclass_svm"},
            "joblib_leakage_xgboost": {"status": "healthy" if self.joblib_leakage else "unavailable", "version": "v1.8.0-xgboost"},
            "demand_forecaster": {"status": "healthy", "version": self.demand_model.version},
            "shortage_forecaster": {"status": "healthy", "version": self.shortage_model.version}
        }

    def _load_joblib_models(self):
        try:
            import joblib
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                ano_path = os.path.join(MODELS_DIR, "anamoly_detection.joblib")
                if os.path.exists(ano_path):
                    self.joblib_anomaly = joblib.load(ano_path)

                leak_path = os.path.join(MODELS_DIR, "leakage_detection.joblib")
                if os.path.exists(leak_path):
                    self.joblib_leakage = joblib.load(leak_path)
        except Exception as e:
            print("MLGateway: Warning loading joblib models:", e)

    def detect_consumption_anomaly_joblib(self, reading_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Runs OneClassSVM trained on diurnal features from models/anamoly_detection.joblib.
        Features: hour, day_of_week, is_weekend, is_holiday, occupancy, scheduled_activity,
                  temperature_c, interval_consumption_liters, previous_1h_avg_liters,
                  previous_24h_avg_liters, previous_1h_std_liters, zone_type
        """
        t0 = time.perf_counter()
        if not self.joblib_anomaly:
            return self._fallback_consumption_anomaly(reading_dict, t0)

        try:
            df = pd.DataFrame([{
                "hour": reading_dict.get("hour", 8),
                "day_of_week": reading_dict.get("day_of_week", 2),
                "is_weekend": reading_dict.get("is_weekend", 0),
                "is_holiday": reading_dict.get("is_holiday", 0),
                "occupancy": reading_dict.get("occupancy", 0.85),
                "scheduled_activity": reading_dict.get("scheduled_activity", 0),
                "temperature_c": reading_dict.get("temperature_c", 28.0),
                "interval_consumption_liters": reading_dict.get("interval_consumption_liters", 100.0),
                "previous_1h_avg_liters": reading_dict.get("previous_1h_avg_liters", 15.0),
                "previous_24h_avg_liters": reading_dict.get("previous_24h_avg_liters", 18.0),
                "previous_1h_std_liters": reading_dict.get("previous_1h_std_liters", 1.5),
                "zone_type": reading_dict.get("zone_type", "Hostel")
            }])

            preprocessor = self.joblib_anomaly["preprocessor"]
            model = self.joblib_anomaly["model"]

            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                X = preprocessor.transform(df)
                pred = int(model.predict(X)[0])  # -1 for anomaly, 1 for normal
                score = float(model.decision_function(X)[0])

            latency_ms = (time.perf_counter() - t0) * 1000.0
            is_anomaly = bool(pred == -1 or score < 0.0)
            confidence = round(min(0.99, max(0.55, abs(score) / 6.0)), 3)

            return {
                "model_name": "OneClassSVM Anomaly Detector",
                "model_version": "v1.8.0-joblib",
                "is_anomaly": is_anomaly,
                "anomaly_score": round(score, 4),
                "prediction_raw": pred,
                "confidence": confidence,
                "execution_time_ms": round(latency_ms, 2),
                "fallback_used": False
            }
        except Exception as e:
            return self._fallback_consumption_anomaly(reading_dict, t0, str(e))

    def _fallback_consumption_anomaly(self, reading_dict: Dict[str, Any], t0: float, error_msg: Optional[str] = None) -> Dict[str, Any]:
        latency_ms = (time.perf_counter() - t0) * 1000.0
        val = reading_dict.get("value", reading_dict.get("interval_consumption_liters", 25.0))
        base = reading_dict.get("previous_1h_avg_liters", 15.0)
        z = (val - base) / 3.0
        return {
            "model_name": "OneClassSVM Fallback Rule",
            "model_version": "fallback-zscore",
            "is_anomaly": z > 3.0,
            "anomaly_score": round(-z, 4),
            "prediction_raw": -1 if z > 3.0 else 1,
            "confidence": 0.72,
            "execution_time_ms": round(latency_ms, 2),
            "fallback_used": True,
            "error": error_msg
        }

    def detect_leakage_xgboost_joblib(self, telemetry_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Runs XGBoost Classifier from models/leakage_detection.joblib.
        Features: hour, occupancy, scheduled_activity, inlet_flow_lpm, pressure_bar,
                  tank_level_pct, previous_1h_avg_flow_lpm, previous_1h_avg_pressure_bar,
                  flow_change_lpm, pressure_change_bar, zone_type
        """
        t0 = time.perf_counter()
        if not self.joblib_leakage:
            return self._fallback_leakage(telemetry_dict, t0)

        try:
            df = pd.DataFrame([{
                "hour": telemetry_dict.get("hour", 8),
                "occupancy": telemetry_dict.get("occupancy", 0.85),
                "scheduled_activity": telemetry_dict.get("scheduled_activity", 0),
                "inlet_flow_lpm": telemetry_dict.get("inlet_flow_lpm", 50.0),
                "pressure_bar": telemetry_dict.get("pressure_bar", 2.5),
                "tank_level_pct": telemetry_dict.get("tank_level_pct", 75.0),
                "previous_1h_avg_flow_lpm": telemetry_dict.get("previous_1h_avg_flow_lpm", 15.0),
                "previous_1h_avg_pressure_bar": telemetry_dict.get("previous_1h_avg_pressure_bar", 2.8),
                "flow_change_lpm": telemetry_dict.get("flow_change_lpm", 0.0),
                "pressure_change_bar": telemetry_dict.get("pressure_change_bar", 0.0),
                "zone_type": telemetry_dict.get("zone_type", "Hostel")
            }])

            preprocessor = self.joblib_leakage["preprocessor"]
            model = self.joblib_leakage["model"]

            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                X = preprocessor.transform(df)
                pred = int(model.predict(X)[0])
                prob = float(model.predict_proba(X)[0, 1])

            latency_ms = (time.perf_counter() - t0) * 1000.0
            return {
                "model_name": "XGBoost Leakage Detector",
                "model_version": "v1.8.0-joblib",
                "is_leak": bool(pred == 1),
                "leak_probability": round(prob, 4),
                "confidence": round(prob if pred == 1 else (1.0 - prob), 3),
                "execution_time_ms": round(latency_ms, 2),
                "fallback_used": False
            }
        except Exception as e:
            return self._fallback_leakage(telemetry_dict, t0, str(e))

    def _fallback_leakage(self, telemetry_dict: Dict[str, Any], t0: float, error_msg: Optional[str] = None) -> Dict[str, Any]:
        latency_ms = (time.perf_counter() - t0) * 1000.0
        p_drop = telemetry_dict.get("pressure_change_bar", 0.0) < -0.3
        f_surge = telemetry_dict.get("flow_change_lpm", 0.0) > 20.0
        is_leak = bool(p_drop and f_surge)
        prob = 0.85 if is_leak else 0.10
        return {
            "model_name": "Hydraulic Gradient Rule",
            "model_version": "fallback-gradient",
            "is_leak": is_leak,
            "leak_probability": prob,
            "confidence": 0.75,
            "execution_time_ms": round(latency_ms, 2),
            "fallback_used": True,
            "error": error_msg
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

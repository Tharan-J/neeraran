"""
NEERARAN ML Model 1: Anomaly Detection
Combines 90-day rolling baseline z-score with Isolation Forest
trained on [flow_lpm, pressure_bar, hour, weekday, occupancy_flag].
"""

import numpy as np
from sklearn.ensemble import IsolationForest
from typing import Dict, Any, Tuple

class AnomalyDetectorModel:
    def __init__(self, version: str = "v1.4.2-ensemble"):
        self.version = version
        self.model = IsolationForest(
            n_estimators=100,
            contamination=0.03,
            random_state=42
        )
        # Train baseline on synthetic normal campus diurnal samples
        self._fit_initial_baseline()

    def _fit_initial_baseline(self):
        """Fit model on synthetic diurnal feature samples."""
        X = []
        for hour in np.linspace(0, 24, 200):
            for weekday in [0, 2, 5]:
                occ = 1.0 if weekday < 5 else 0.6
                base_flow = 15.0 if hour < 5 else (60.0 if (6 < hour < 9 or 18 < hour < 21) else 35.0)
                flow = base_flow * occ + np.random.normal(0, 3.0)
                pressure = 3.2 - (flow / 120.0) * 0.4 + np.random.normal(0, 0.05)
                X.append([flow, pressure, hour, weekday, occ])
        self.model.fit(np.array(X))

    def predict(self, flow_lpm: float, pressure_bar: float, hour: float, weekday: int, occupancy_flag: float, baseline_mean: float = 20.0, baseline_std: float = 4.0) -> Dict[str, Any]:
        """
        Returns anomaly status, anomaly score (0 to 1), and z-score against night baseline.
        """
        features = np.array([[flow_lpm, pressure_bar, hour, weekday, occupancy_flag]])
        raw_pred = self.model.predict(features)[0]  # -1 for anomaly, 1 for normal
        raw_score = -self.model.score_samples(features)[0]  # higher score = more anomalous

        # Baseline z-score (crucial for minimum night flow detection)
        z_score = (flow_lpm - baseline_mean) / max(0.5, baseline_std) if baseline_std > 0 else 0.0

        is_anomaly = bool(raw_pred == -1 or z_score > 3.0)
        confidence = float(np.clip((raw_score - 0.45) / 0.35, 0.5, 0.98)) if is_anomaly else float(np.clip(1.0 - raw_score, 0.6, 0.99))

        return {
            "model_version": self.version,
            "is_anomaly": is_anomaly,
            "anomaly_score": round(float(raw_score), 4),
            "z_score": round(float(z_score), 2),
            "confidence": round(confidence, 3),
            "features": {
                "flow_lpm": flow_lpm,
                "pressure_bar": pressure_bar,
                "hour": hour,
                "weekday": weekday,
                "occupancy": occupancy_flag
            }
        }

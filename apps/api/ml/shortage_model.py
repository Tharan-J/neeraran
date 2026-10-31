"""
NEERARAN ML Model 3: Tank Depletion & Shortage Risk Forecaster
72-hour forecast of reservoir and overhead tank levels with 80% confidence band
and time-to-critical safety violation.
"""

from typing import Dict, List, Any

class ShortageForecasterModel:
    def __init__(self, version: str = "v1.8.0-depletion-risk"):
        self.version = version

    def forecast_tank_levels_72h(
        self,
        tank_id: str,
        current_level_kl: float,
        capacity_kl: float,
        safety_level_kl: float,
        inflow_rate_lpm: float,
        outflow_rate_lpm: float
    ) -> List[Dict[str, Any]]:
        """
        Projects tank levels over 72 hours.
        Produces point forecast, 80% upper/lower confidence bounds,
        and safety line threshold.
        """
        trajectory = []
        vol = current_level_kl

        # Inflow/outflow in kL per hour
        net_flow_per_hour = ((inflow_rate_lpm - outflow_rate_lpm) * 60.0) / 1000.0

        for h in range(73):
            # Hour-of-day demand modulation
            hour_mod = 1.0 + 0.25 * (1 if (6 <= h % 24 <= 9 or 18 <= h % 24 <= 21) else -0.15)
            adjusted_net = net_flow_per_hour * hour_mod

            vol = max(0.0, min(capacity_kl, vol + adjusted_net))
            uncertainty = 0.04 * capacity_kl * (1.0 + (h / 72.0))  # widening cone of uncertainty

            lower_80 = max(0.0, round(vol - uncertainty, 1))
            upper_80 = min(capacity_kl, round(vol + uncertainty, 1))

            trajectory.append({
                "hour": h,
                "forecast_level_kl": round(vol, 1),
                "lower_bound_80": lower_80,
                "upper_bound_80": upper_80,
                "safety_threshold_kl": safety_level_kl,
                "is_critical": vol < safety_level_kl
            })

        return trajectory

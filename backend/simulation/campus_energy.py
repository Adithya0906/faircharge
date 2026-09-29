import math
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict

SLOT_DURATION_MIN = 15
SLOT_DURATION_H = SLOT_DURATION_MIN / 60.0


def tou_grid_tariff(dt: datetime) -> Dict[str, float]:
    """
    Dynamic Time-of-Use (ToU) Grid Tariff ($/kWh)
    - On-Peak (14:00 - 20:00): $0.35 / kWh (high demand penalty)
    - Mid-Peak (08:00 - 14:00, 20:00 - 22:00): $0.20 / kWh (standard work rate)
    - Off-Peak (22:00 - 08:00): $0.10 / kWh (overnight incentive)
    """
    hour = dt.hour + dt.minute / 60.0
    if 14.0 <= hour < 20.0:
        rate = 0.35
        tier = "On-Peak"
    elif (8.0 <= hour < 14.0) or (20.0 <= hour < 22.0):
        rate = 0.20
        tier = "Mid-Peak"
    else:
        rate = 0.10
        tier = "Off-Peak"
    return {"rate_usd_per_kwh": rate, "tier": tier}


def solar_power_kw(dt: datetime, scenario: str = "normal", peak_kw: float = 80.0) -> Dict[str, float]:
    """
    Solar generation model with realistic intermittency profiles:
    - Normal: Clear sky smooth Gaussian curve + minor ambient noise.
    - Low Solar: Overcast sky (85% reduction).
    - Cloudy / Cloud Ramp: Stochastic passing cloud ramps (40-70% drop during peak hours).
    """
    hour = dt.hour + dt.minute / 60.0
    if hour < 6 or hour > 19:
        return {"solar_kw": 0.0, "intermittency_factor": 1.0}

    mu, sigma = 12.5, 2.5
    raw = peak_kw * math.exp(-0.5 * ((hour - mu) / sigma) ** 2)

    intermittency_factor = 1.0
    if scenario == "cloudy" or scenario == "cloud_ramp":
        # Cloud ramp drop event between 11:00 and 14:00
        if 11.0 <= hour <= 14.0:
            # Drop intensity fluctuates between 40% and 70%
            intermittency_factor = 0.35 + 0.15 * math.sin(math.pi * (hour - 11.0) / 1.5)
        elif 14.0 < hour <= 16.0:
            intermittency_factor = 0.60
    elif scenario == "low_solar":
        intermittency_factor = 0.15

    noise = float(np.random.normal(0, max(0.1, raw * 0.04)))
    final_kw = max(0.0, (raw * intermittency_factor) + noise)

    return {
        "solar_kw": round(final_kw, 2),
        "intermittency_factor": round(intermittency_factor, 2),
    }


def campus_base_load_kw(dt: datetime) -> float:
    hour = dt.hour
    if 8 <= hour < 18:
        base = 30.0 + 10.0 * math.sin(math.pi * (hour - 8) / 10)
    elif 18 <= hour < 22:
        base = 20.0
    else:
        base = 10.0
    noise = float(np.random.normal(0, 2))
    return round(max(5.0, base + noise), 2)


class CampusEnergySimulator:
    def __init__(
        self,
        battery_capacity_kwh: float = 150.0,
        battery_max_power_kw: float = 40.0,
        battery_min_reserve_pct: float = 0.20,
        grid_limit_kw: float = 60.0,
        campus_power_limit_kw: float = 120.0,
        scenario: str = "normal",
        seed: int = 42,
    ):
        self.battery_capacity_kwh = battery_capacity_kwh
        self.battery_max_power_kw = battery_max_power_kw
        self.battery_min_reserve_kwh = battery_capacity_kwh * battery_min_reserve_pct
        self.grid_limit_kw = grid_limit_kw
        self.campus_power_limit_kw = campus_power_limit_kw
        self.scenario = scenario
        self.battery_soc_kwh = battery_capacity_kwh * 0.5
        np.random.seed(seed)

    def get_available_power_kw(self, dt: datetime, ev_demand_kw: float = 0.0) -> Dict:
        solar_info = solar_power_kw(dt, self.scenario)
        solar = solar_info["solar_kw"]
        intermittency = solar_info["intermittency_factor"]
        tariff_info = tou_grid_tariff(dt)
        campus_load = campus_base_load_kw(dt)
        grid_limit = 0.0 if self.scenario == "grid_constraint" else self.grid_limit_kw

        usable_battery = max(0.0, self.battery_soc_kwh - self.battery_min_reserve_kwh)
        max_battery_discharge = min(self.battery_max_power_kw, usable_battery / SLOT_DURATION_H)
        if self.scenario == "battery_low":
            self.battery_soc_kwh = self.battery_min_reserve_kwh + 5.0
            max_battery_discharge = min(self.battery_max_power_kw, 5.0 / SLOT_DURATION_H)

        net_solar = max(0.0, solar - campus_load)
        total_available = net_solar + max_battery_discharge + grid_limit
        total_available = min(total_available, self.campus_power_limit_kw - campus_load)

        return {
            "solar_kw": solar,
            "intermittency_factor": intermittency,
            "campus_load_kw": campus_load,
            "battery_available_kw": round(max_battery_discharge, 2),
            "grid_available_kw": grid_limit,
            "net_solar_kw": round(net_solar, 2),
            "total_ev_capacity_kw": round(max(0.0, total_available), 2),
            "battery_soc_kwh": round(self.battery_soc_kwh, 2),
            "battery_soc_pct": round(self.battery_soc_kwh / self.battery_capacity_kwh, 4),
            "tou_tariff_rate": tariff_info["rate_usd_per_kwh"],
            "tou_tier": tariff_info["tier"],
        }

    def update_battery(self, ev_charging_kw: float, dt: datetime):
        solar = solar_power_kw(dt, self.scenario)["solar_kw"]
        campus_load = campus_base_load_kw(dt)
        net_solar = solar - campus_load
        if net_solar > ev_charging_kw:
            charge_power = min(net_solar - ev_charging_kw, self.battery_max_power_kw)
            self.battery_soc_kwh = min(
                self.battery_capacity_kwh,
                self.battery_soc_kwh + charge_power * SLOT_DURATION_H,
            )
        elif net_solar < ev_charging_kw:
            discharge_needed = ev_charging_kw - max(0.0, net_solar)
            discharge_power = min(discharge_needed, self.battery_max_power_kw)
            self.battery_soc_kwh = max(
                self.battery_min_reserve_kwh,
                self.battery_soc_kwh - discharge_power * SLOT_DURATION_H,
            )

    def generate_day_profile(self, date: datetime, num_slots: int = 96) -> List[Dict]:
        profile = []
        for i in range(num_slots):
            dt = date.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(
                minutes=15 * i
            )
            energy = self.get_available_power_kw(dt)
            energy["timestamp"] = dt.isoformat()
            profile.append(energy)
        return profile

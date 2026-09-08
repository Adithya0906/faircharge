import math
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict

SLOT_DURATION_MIN = 15
SLOT_DURATION_H = SLOT_DURATION_MIN / 60.0


def solar_power_kw(dt: datetime, scenario: str = "normal", peak_kw: float = 80.0) -> float:
    hour = dt.hour + dt.minute / 60.0
    if hour < 6 or hour > 19:
        return 0.0
    mu, sigma = 12.5, 2.5
    raw = peak_kw * math.exp(-0.5 * ((hour - mu) / sigma) ** 2)
    noise = np.random.normal(0, max(0.1, raw * 0.05))
    val = max(0.0, raw + noise)
    if scenario == "low_solar":
        val *= 0.15
    elif scenario == "cloudy":
        val *= 0.5
    return round(val, 2)


def campus_base_load_kw(dt: datetime) -> float:
    hour = dt.hour
    if 8 <= hour < 18:
        base = 30.0 + 10.0 * math.sin(math.pi * (hour - 8) / 10)
    elif 18 <= hour < 22:
        base = 20.0
    else:
        base = 10.0
    noise = np.random.normal(0, 2)
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
        solar = solar_power_kw(dt, self.scenario)
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
            "campus_load_kw": campus_load,
            "battery_available_kw": max_battery_discharge,
            "grid_available_kw": grid_limit,
            "net_solar_kw": net_solar,
            "total_ev_capacity_kw": max(0.0, total_available),
            "battery_soc_kwh": self.battery_soc_kwh,
            "battery_soc_pct": self.battery_soc_kwh / self.battery_capacity_kwh,
        }

    def update_battery(self, ev_charging_kw: float, dt: datetime):
        solar = solar_power_kw(dt, self.scenario)
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

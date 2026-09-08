"""
FairCharge Dataset Generator
Generates 1000 realistic EV charging requests over commercial campus working scenarios.
"""
import json
import math
import random
import csv
from datetime import datetime, timedelta
from pathlib import Path
import uuid
import numpy as np

RANDOM_SEED = 42
random.seed(RANDOM_SEED)
np.random.seed(RANDOM_SEED)

VEHICLE_SPECS = [
    {"type": "Tesla Model 3", "capacity_kwh": 75, "max_power_kw": 50, "charger_type": "DC"},
    {"type": "Tesla Model Y", "capacity_kwh": 82, "max_power_kw": 50, "charger_type": "DC"},
    {"type": "Nissan Leaf", "capacity_kwh": 40, "max_power_kw": 22, "charger_type": "AC"},
    {"type": "BMW i3", "capacity_kwh": 42, "max_power_kw": 22, "charger_type": "AC"},
    {"type": "Hyundai Ioniq 5", "capacity_kwh": 77, "max_power_kw": 50, "charger_type": "DC"},
    {"type": "VW ID.4", "capacity_kwh": 77, "max_power_kw": 50, "charger_type": "DC"},
    {"type": "Renault Zoe", "capacity_kwh": 52, "max_power_kw": 22, "charger_type": "AC"},
    {"type": "Kia EV6", "capacity_kwh": 77, "max_power_kw": 50, "charger_type": "DC"},
]

NUM_EMPLOYEES = 80
EMPLOYEES = [
    {
        "user_id": f"EMP-{i:03d}",
        "vehicle_id": f"EV-{i:03d}",
        "vehicle_spec": VEHICLE_SPECS[i % len(VEHICLE_SPECS)],
        "priority": random.choices(["standard", "priority", "emergency"], weights=[80, 15, 5])[0],
    }
    for i in range(1, NUM_EMPLOYEES + 1)
]

BASE_DATE = datetime(2024, 3, 11)
WORKING_DAYS = [BASE_DATE + timedelta(days=d) for d in range(5)]


def arrival_time(base: datetime) -> datetime:
    weights = [0.35, 0.25, 0.20, 0.12, 0.08]
    periods = [(7, 9), (9, 11), (11, 13), (13, 15), (15, 18)]
    p = random.choices(periods, weights=weights)[0]
    hour = random.uniform(p[0], p[1])
    return base.replace(hour=0, minute=0) + timedelta(minutes=int(hour * 60))


def departure_time(arr: datetime) -> datetime:
    dur = random.uniform(1.5, 9.0)
    cap = arr.replace(hour=21, minute=0)
    return min(arr + timedelta(hours=dur), cap)


def generate_request(emp: dict, base: datetime, scenario: str) -> dict:
    arr = arrival_time(base)
    dep = departure_time(arr)
    spec = emp["vehicle_spec"]
    soc = round(random.uniform(0.10, 0.75), 2)
    missing = spec["capacity_kwh"] * (1 - soc)
    required = round(missing * random.uniform(0.5, 1.0), 1)
    required = max(2.0, min(required, spec["capacity_kwh"]))
    window_h = (dep - arr).total_seconds() / 3600
    max_possible = window_h * spec["max_power_kw"]
    if scenario == "tight_departure" or random.random() < 0.05:
        required = round(max_possible * 1.2, 1)
    return {
        "request_id": f"REQ-{uuid.uuid4().hex[:8].upper()}",
        "vehicle_id": emp["vehicle_id"],
        "user_id": emp["user_id"],
        "arrival_time": arr.isoformat(),
        "departure_time": dep.isoformat(),
        "battery_capacity_kwh": spec["capacity_kwh"],
        "initial_soc": soc,
        "required_energy_kwh": required,
        "max_charging_power_kw": spec["max_power_kw"],
        "charger_type": spec["charger_type"],
        "priority_category": emp["priority"],
        "scenario": scenario,
        "request_timestamp": (arr - timedelta(hours=random.uniform(0.5, 12))).isoformat(),
        "vehicle_type": spec["type"],
    }


def generate_energy(base: datetime, scenario: str) -> list:
    records = []
    battery_soc = 75.0
    for slot in range(96):
        dt = base.replace(hour=0, minute=0) + timedelta(minutes=15 * slot)
        hour = dt.hour + dt.minute / 60.0
        if 6 <= hour <= 19:
            solar = 80 * math.exp(-0.5 * ((hour - 12.5) / 2.5) ** 2)
            if scenario == "low_solar":
                solar *= 0.15
        else:
            solar = 0.0
        solar = round(max(0, solar + float(np.random.normal(0, max(0.1, solar * 0.05)))), 2)
        campus_load = round(
            max(
                5,
                (
                    30 + 10 * math.sin(math.pi * (hour - 8) / 10)
                    if 8 <= hour < 18
                    else 20 if 18 <= hour < 22 else 10
                )
                + float(np.random.normal(0, 2)),
            ),
            2,
        )
        ev_load = round(
            random.uniform(10, 50) if 8 <= hour < 18 else random.uniform(0, 15), 2
        )
        grid_limit = 10.0 if scenario == "grid_constraint" else 60.0
        net_solar = solar - campus_load
        if net_solar > ev_load:
            battery_soc = min(150.0, battery_soc + (net_solar - ev_load) * 0.25)
            battery_charging, battery_discharging, grid_import = (
                min(net_solar - ev_load, 40.0),
                0.0,
                0.0,
            )
        else:
            deficit = ev_load - max(0, net_solar)
            battery_discharge = min(deficit, 40.0, max(0, (battery_soc - 30.0) * 4))
            battery_soc = max(30.0, battery_soc - battery_discharge * 0.25)
            battery_charging, battery_discharging = 0.0, battery_discharge
            grid_import = min(max(0, deficit - battery_discharge), grid_limit)
        if scenario == "battery_low":
            battery_soc = 32.0
        records.append(
            {
                "timestamp": dt.isoformat(),
                "solar_generation_kw": solar,
                "campus_load_kw": campus_load,
                "battery_soc_kwh": round(battery_soc, 2),
                "battery_charging_kw": round(battery_charging, 2),
                "battery_discharging_kw": round(battery_discharging, 2),
                "grid_import_kw": round(grid_import, 2),
                "ev_charging_load_kw": ev_load,
                "scenario": scenario,
            }
        )
    return records


def generate_all():
    out = Path(__file__).parent / "generated"
    out.mkdir(exist_ok=True)
    scenarios = [
        ("normal", 200),
        ("high_demand", 150),
        ("low_solar", 100),
        ("grid_constraint", 100),
        ("tight_departure", 100),
        ("battery_low", 100),
        ("charger_failure", 100),
        ("normal", 150),
    ]
    all_requests, all_energy = [], []
    for i, (scenario, count) in enumerate(scenarios):
        base = WORKING_DAYS[i % len(WORKING_DAYS)]
        emps = random.choices(EMPLOYEES, k=count)
        for emp in emps:
            all_requests.append(generate_request(emp, base, scenario))
        all_energy.extend(generate_energy(base, scenario))

    with open(out / "charging_requests.json", "w") as f:
        json.dump(all_requests, f, indent=2)
    with open(out / "charging_requests.csv", "w", newline="") as f:
        if all_requests:
            writer = csv.DictWriter(f, fieldnames=all_requests[0].keys())
            writer.writeheader()
            writer.writerows(all_requests)
    with open(out / "campus_energy.json", "w") as f:
        json.dump(all_energy, f, indent=2, default=str)
    with open(out / "campus_energy.csv", "w", newline="") as f:
        if all_energy:
            writer = csv.DictWriter(f, fieldnames=all_energy[0].keys())
            writer.writeheader()
            writer.writerows(all_energy)
    print(f"Generated {len(all_requests)} requests and saved to {out}")
    return all_requests, all_energy


if __name__ == "__main__":
    generate_all()

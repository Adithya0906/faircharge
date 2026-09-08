"""
FairCharge Experiment Runner
Runs FCFS, Urgency, and Fairness policies on identical datasets across multiple scenarios.
Generates experiment_results.json and summary.md.
"""
import sys
import json
import time
import random
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict

import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.scheduler.engine import run_scheduler
from backend.scheduler.models import VehicleRequest, Charger

RANDOM_SEED = 42
random.seed(RANDOM_SEED)
np.random.seed(RANDOM_SEED)

CAMPUS_CONFIG = {
    "battery_capacity_kwh": 150.0,
    "battery_max_power_kw": 40.0,
    "battery_min_reserve_pct": 0.20,
    "grid_limit_kw": 60.0,
    "campus_power_limit_kw": 120.0,
}

CHARGERS = [
    Charger("CHARGER-DC-01", "DC", 50.0, True),
    Charger("CHARGER-DC-02", "DC", 50.0, True),
    Charger("CHARGER-AC-01", "AC", 22.0, True),
    Charger("CHARGER-AC-02", "AC", 22.0, True),
]

VEHICLE_SPECS = [
    {"cap": 75, "power": 50, "type": "DC"},
    {"cap": 40, "power": 22, "type": "AC"},
    {"cap": 77, "power": 50, "type": "DC"},
    {"cap": 42, "power": 22, "type": "AC"},
]


def generate_test_requests(n: int, scenario: str, base_date: datetime) -> List[VehicleRequest]:
    rng = random.Random(RANDOM_SEED)
    np.random.seed(RANDOM_SEED)
    requests = []
    for i in range(n):
        spec = VEHICLE_SPECS[i % len(VEHICLE_SPECS)]
        hour_offset = rng.uniform(0, 8)
        arrival = base_date + timedelta(hours=hour_offset)
        depart_h = (
            rng.uniform(1.5, 3.0)
            if scenario in ["tight_departure"]
            else rng.uniform(3.0, 9.0)
        )
        departure = arrival + timedelta(hours=depart_h)
        initial_soc = round(rng.uniform(0.10, 0.70), 2)
        required = round(spec["cap"] * (1 - initial_soc) * rng.uniform(0.5, 1.0), 1)
        if scenario == "tight_departure" and i % 5 == 0:
            required = round(depart_h * spec["power"] * 1.8, 1)
        priority = rng.choices(["standard", "priority", "emergency"], weights=[75, 20, 5])[0]
        requests.append(
            VehicleRequest(
                request_id=f"REQ-{i+1:04d}",
                vehicle_id=f"EV-{i+1:03d}",
                user_id=f"EMP-{i+1:03d}",
                arrival_time=arrival,
                departure_time=departure,
                battery_capacity_kwh=spec["cap"],
                initial_soc=initial_soc,
                required_energy_kwh=required,
                max_charging_power_kw=spec["power"],
                charger_type=spec["type"],
                priority_category=priority,
                request_timestamp=arrival - timedelta(hours=rng.uniform(0.5, 6)),
            )
        )
    return requests


def run_comparison(n: int, scenario: str) -> Dict:
    base = datetime(2024, 3, 11, 7, 0, 0)
    requests = generate_test_requests(n, scenario, base)
    now = base
    results = {}
    for policy in ["fcfs", "urgency", "fairness"]:
        t0 = time.time()
        result = run_scheduler(
            requests=requests,
            chargers=CHARGERS,
            policy=policy,
            scenario=scenario,
            campus_config=CAMPUS_CONFIG,
            now=now,
        )
        elapsed = (time.time() - t0) * 1000
        results[policy] = {
            "metrics": result.metrics,
            "scheduling_time_ms": round(elapsed, 2),
            "session_count": len(result.sessions),
            "error_count": len(result.error_analysis),
            "errors": result.error_analysis[:3],
        }
    return results


def run_all_experiments():
    results_dir = Path(__file__).parent / "results"
    results_dir.mkdir(exist_ok=True)
    scenarios = [
        ("normal", 20),
        ("high_demand", 25),
        ("low_solar", 20),
        ("grid_constraint", 20),
        ("tight_departure", 20),
        ("battery_low", 20),
    ]
    all_results = {}

    print("\n" + "=" * 75)
    print("FAIRCHARGE EXPERIMENT RESULTS -- BASELINE (FCFS) VS URGENCY VS FAIRNESS")
    print("=" * 75)

    for scenario, n in scenarios:
        print(f"\n- Scenario: {scenario.upper()} ({n} vehicles competing)")
        results = run_comparison(n, scenario)
        all_results[scenario] = results
        print(
            f"  {'Policy':<12} {'Served':>7} {'Energy %':>9} {'Fairness (JFI)':>14} {'Wait (min)':>11} {'Time (ms)':>10}"
        )
        print(f"  {'-'*66}")
        for policy, r in results.items():
            m = r["metrics"]
            print(
                f"  {policy:<12} {m.get('fully_served',0):>7} {m.get('energy_delivery_rate',0)*100:>8.1f}% {m.get('jains_fairness_index',0):>14.4f} {m.get('avg_waiting_time_min',0):>11.1f} {r['scheduling_time_ms']:>10.1f}"
            )

    with open(results_dir / "experiment_results.json", "w") as f:
        json.dump(all_results, f, indent=2, default=str)

    lines = [
        "# FairCharge Experiment Summary Report\n\n",
        "## Core Principles & Target Metrics\n",
        "- **Primary Goal**: Met charging needs with fair access to limited capacity (not energy cost minimization).\n",
        "- **Target Metrics**:\n",
        "  - Energy delivery rate >= 80% of feasible requests\n",
        "  - Jain's Fairness Index >= 0.85 under fairness policy\n",
        "  - Zero hard constraint violations\n",
        "  - Clear priority explanations for every session\n\n",
        "## Summary Results Table\n\n",
        "| Scenario | Policy | Requests | Fully Served | Energy Delivery Rate | Jain's Index | Avg Wait (min) | Runtime (ms) |\n",
        "|---|---|---|---|---|---|---|---|\n",
    ]
    for scenario, results in all_results.items():
        for policy, r in results.items():
            m = r["metrics"]
            lines.append(
                f"| {scenario} | {policy} | {m.get('total_requests',0)} | {m.get('fully_served',0)} | {m.get('energy_delivery_rate',0)*100:.1f}% | {m.get('jains_fairness_index',0):.4f} | {m.get('avg_waiting_time_min',0):.1f} | {r['scheduling_time_ms']:.1f} |\n"
            )

    with open(results_dir / "summary.md", "w") as f:
        f.writelines(lines)

    print(f"\nAll experiment results saved to: {results_dir}")
    return all_results


if __name__ == "__main__":
    run_all_experiments()

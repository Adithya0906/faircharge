from datetime import datetime, timedelta
from typing import List, Dict, Optional

from backend.scheduler.models import VehicleRequest, Charger, TimeSlot, ScheduleResult
from backend.scheduler.fcfs import run_fcfs_scheduler
from backend.scheduler.optimized import run_optimized_scheduler
from backend.simulation.campus_energy import CampusEnergySimulator
from backend.scheduler.metrics import calculate_metrics

SLOT_DURATION_MIN = 15


def build_time_slots(
    start_dt: datetime, end_dt: datetime, campus_sim: CampusEnergySimulator
) -> List[TimeSlot]:
    slots = []
    current = start_dt.replace(second=0, microsecond=0)
    # align to 15-min boundary
    current = current - timedelta(minutes=current.minute % SLOT_DURATION_MIN)
    while current < end_dt:
        energy = campus_sim.get_available_power_kw(current)
        slots.append(
            TimeSlot(
                start=current,
                end=current + timedelta(minutes=SLOT_DURATION_MIN),
                available_power_kw=energy["total_ev_capacity_kw"],
                solar_kw=energy["solar_kw"],
                battery_kw=energy["battery_available_kw"],
                grid_kw=energy["grid_available_kw"],
                battery_soc_kwh=energy["battery_soc_kwh"],
            )
        )
        campus_sim.update_battery(0.0, current)
        current += timedelta(minutes=SLOT_DURATION_MIN)
    return slots


def run_scheduler(
    requests: List[VehicleRequest],
    chargers: List[Charger],
    policy: str = "urgency",
    scenario: str = "normal",
    now: Optional[datetime] = None,
    historical_allocations: Optional[Dict[str, float]] = None,
    campus_config: Optional[Dict] = None,
) -> ScheduleResult:
    if now is None:
        now = datetime.utcnow()
    if campus_config is None:
        campus_config = {}

    sim = CampusEnergySimulator(
        battery_capacity_kwh=campus_config.get("battery_capacity_kwh", 150.0),
        battery_max_power_kw=campus_config.get("battery_max_power_kw", 40.0),
        battery_min_reserve_pct=campus_config.get("battery_min_reserve_pct", 0.20),
        grid_limit_kw=campus_config.get("grid_limit_kw", 60.0),
        campus_power_limit_kw=campus_config.get("campus_power_limit_kw", 120.0),
        scenario=scenario,
        seed=42,
    )

    if not requests:
        return ScheduleResult(
            policy=policy,
            sessions=[],
            scheduling_time_ms=0.0,
            metrics=calculate_metrics([], [], policy),
            error_analysis=[],
        )

    min_arrival = min(r.arrival_time for r in requests)
    max_departure = max(r.departure_time for r in requests)
    energy_slots = build_time_slots(min_arrival, max_departure, sim)

    if policy == "fcfs":
        return run_fcfs_scheduler(requests, chargers, energy_slots, now)
    else:
        return run_optimized_scheduler(
            requests, chargers, energy_slots, now, policy, historical_allocations
        )

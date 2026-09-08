from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict


@dataclass
class VehicleRequest:
    request_id: str
    vehicle_id: str
    user_id: str
    arrival_time: datetime
    departure_time: datetime
    battery_capacity_kwh: float
    initial_soc: float
    required_energy_kwh: float
    max_charging_power_kw: float
    charger_type: str
    priority_category: str
    priority_score: float = 0.0
    request_timestamp: Optional[datetime] = None

    @property
    def window_hours(self) -> float:
        return (self.departure_time - self.arrival_time).total_seconds() / 3600

    @property
    def max_deliverable_kwh(self) -> float:
        return min(self.window_hours * self.max_charging_power_kw, self.required_energy_kwh)

    @property
    def is_feasible(self) -> bool:
        return self.max_deliverable_kwh >= self.required_energy_kwh * 0.5


@dataclass
class Charger:
    charger_id: str
    charger_type: str
    max_power_kw: float
    is_available: bool = True


@dataclass
class TimeSlot:
    start: datetime
    end: datetime
    available_power_kw: float
    solar_kw: float = 0.0
    battery_kw: float = 0.0
    grid_kw: float = 0.0
    battery_soc_kwh: float = 0.0


@dataclass
class ScheduledSession:
    request_id: str
    vehicle_id: str
    charger_id: str
    start_time: datetime
    end_time: datetime
    planned_energy_kwh: float
    priority_score: float
    explanation: str
    is_fully_served: bool
    failure_reason: Optional[str] = None
    slot_allocations: Dict[str, float] = field(default_factory=dict)
    policy: str = "fcfs"
    is_admin_override: bool = False


@dataclass
class ScheduleResult:
    policy: str
    sessions: List[ScheduledSession]
    scheduling_time_ms: float
    metrics: Dict
    error_analysis: List[Dict]

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator


class ChargingRequestCreate(BaseModel):
    vehicle_id: str = Field(..., examples=["EV-042"])
    user_id: str = Field(..., examples=["EMP-042"])
    arrival_time: datetime
    departure_time: datetime
    battery_capacity_kwh: float = Field(..., gt=0, le=300)
    initial_soc: float = Field(..., ge=0, le=1)
    required_energy_kwh: float = Field(..., gt=0)
    max_charging_power_kw: float = Field(..., gt=0, le=350)
    charger_type: str = Field(default="AC")
    priority_category: str = Field(default="standard")

    @field_validator("departure_time")
    @classmethod
    def departure_after_arrival(cls, v, info):
        arrival = info.data.get("arrival_time")
        if arrival and v <= arrival:
            raise ValueError("departure_time must be after arrival_time")
        return v

    @field_validator("priority_category")
    @classmethod
    def valid_priority(cls, v):
        if v not in ["standard", "priority", "emergency"]:
            raise ValueError("priority_category must be standard, priority, or emergency")
        return v


class ChargingRequestResponse(BaseModel):
    request_id: str
    vehicle_id: str
    status: str
    message: str
    validation_warnings: List[str] = []


class ScheduleRunRequest(BaseModel):
    policy: str = Field(default="urgency")
    scenario: str = Field(default="normal")
    request_ids: Optional[List[str]] = None


class AdminOverrideRequest(BaseModel):
    admin_id: str
    admin_name: str
    admin_password: str
    vehicle_id: str
    request_id: str
    reason: str
    new_priority_score: float = Field(..., ge=0, le=1)
    new_charger_id: Optional[str] = None


class ScenarioRequest(BaseModel):
    scenario: str
    policy: str = Field(default="urgency")
    num_vehicles: int = Field(default=10, ge=1, le=50)

from datetime import datetime
from typing import Optional
from sqlalchemy import String, Float, Integer, Boolean, DateTime, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class CampusConfig(Base):
    __tablename__ = "campus_config"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    num_chargers: Mapped[int] = mapped_column(Integer, default=4)
    charger_power_kw: Mapped[float] = mapped_column(Float, default=22.0)
    dc_chargers: Mapped[int] = mapped_column(Integer, default=2)
    dc_power_kw: Mapped[float] = mapped_column(Float, default=50.0)
    campus_power_limit_kw: Mapped[float] = mapped_column(Float, default=120.0)
    battery_capacity_kwh: Mapped[float] = mapped_column(Float, default=150.0)
    battery_max_power_kw: Mapped[float] = mapped_column(Float, default=40.0)
    battery_min_reserve_pct: Mapped[float] = mapped_column(Float, default=0.20)
    battery_soc_kwh: Mapped[float] = mapped_column(Float, default=75.0)
    grid_limit_kw: Mapped[float] = mapped_column(Float, default=60.0)
    active_policy: Mapped[str] = mapped_column(String(20), default="urgency")
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class ChargingRequest(Base):
    __tablename__ = "charging_requests"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    request_id: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    vehicle_id: Mapped[str] = mapped_column(String(50), index=True)
    user_id: Mapped[str] = mapped_column(String(50))
    arrival_time: Mapped[datetime] = mapped_column(DateTime)
    departure_time: Mapped[datetime] = mapped_column(DateTime)
    battery_capacity_kwh: Mapped[float] = mapped_column(Float)
    initial_soc: Mapped[float] = mapped_column(Float)
    required_energy_kwh: Mapped[float] = mapped_column(Float)
    max_charging_power_kw: Mapped[float] = mapped_column(Float)
    charger_type: Mapped[str] = mapped_column(String(10), default="AC")
    priority_category: Mapped[str] = mapped_column(String(20), default="standard")
    status: Mapped[str] = mapped_column(String(20), default="pending")
    priority_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    scenario: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    request_timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class ChargingSession(Base):
    __tablename__ = "charging_sessions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(String(50), unique=True)
    request_id: Mapped[str] = mapped_column(String(50), index=True)
    vehicle_id: Mapped[str] = mapped_column(String(50))
    charger_id: Mapped[str] = mapped_column(String(20))
    policy: Mapped[str] = mapped_column(String(20))
    start_time: Mapped[datetime] = mapped_column(DateTime)
    end_time: Mapped[datetime] = mapped_column(DateTime)
    planned_energy_kwh: Mapped[float] = mapped_column(Float)
    delivered_energy_kwh: Mapped[float] = mapped_column(Float, default=0.0)
    priority_score: Mapped[float] = mapped_column(Float, default=0.0)
    explanation: Mapped[str] = mapped_column(Text, default="")
    is_fully_served: Mapped[bool] = mapped_column(Boolean, default=False)
    is_admin_override: Mapped[bool] = mapped_column(Boolean, default=False)
    failure_reason: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class AdminOverride(Base):
    __tablename__ = "admin_overrides"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    override_id: Mapped[str] = mapped_column(String(50), unique=True)
    admin_id: Mapped[str] = mapped_column(String(50))
    admin_name: Mapped[str] = mapped_column(String(100))
    vehicle_id: Mapped[str] = mapped_column(String(50))
    request_id: Mapped[str] = mapped_column(String(50))
    reason: Mapped[str] = mapped_column(Text)
    old_priority: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    new_priority: Mapped[float] = mapped_column(Float)
    old_charger: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    new_charger: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class EnergyDataPoint(Base):
    __tablename__ = "energy_data"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, index=True)
    solar_generation_kw: Mapped[float] = mapped_column(Float, default=0.0)
    campus_load_kw: Mapped[float] = mapped_column(Float, default=0.0)
    battery_soc_kwh: Mapped[float] = mapped_column(Float, default=0.0)
    battery_charging_kw: Mapped[float] = mapped_column(Float, default=0.0)
    battery_discharging_kw: Mapped[float] = mapped_column(Float, default=0.0)
    grid_import_kw: Mapped[float] = mapped_column(Float, default=0.0)
    ev_charging_load_kw: Mapped[float] = mapped_column(Float, default=0.0)
    scenario: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)


class ExperimentResult(Base):
    __tablename__ = "experiment_results"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    experiment_id: Mapped[str] = mapped_column(String(50))
    policy: Mapped[str] = mapped_column(String(20))
    scenario: Mapped[str] = mapped_column(String(50))
    total_requests: Mapped[int] = mapped_column(Integer)
    fully_served: Mapped[int] = mapped_column(Integer)
    partially_served: Mapped[int] = mapped_column(Integer)
    unserved: Mapped[int] = mapped_column(Integer)
    total_energy_requested_kwh: Mapped[float] = mapped_column(Float)
    total_energy_delivered_kwh: Mapped[float] = mapped_column(Float)
    avg_waiting_time_min: Mapped[float] = mapped_column(Float)
    jains_fairness_index: Mapped[float] = mapped_column(Float)
    departure_success_rate: Mapped[float] = mapped_column(Float)
    solar_utilisation_pct: Mapped[float] = mapped_column(Float)
    grid_energy_kwh: Mapped[float] = mapped_column(Float)
    constraint_violations: Mapped[int] = mapped_column(Integer, default=0)
    scheduling_time_ms: Mapped[float] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

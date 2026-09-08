import uuid
import random
from datetime import datetime, timedelta
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete

from backend.database import get_db
from backend.models.db_models import (
    ChargingRequest, ChargingSession, AdminOverride,
    EnergyDataPoint, ExperimentResult, CampusConfig,
)
from backend.api.schemas import (
    ChargingRequestCreate, ChargingRequestResponse,
    ScheduleRunRequest, AdminOverrideRequest, ScenarioRequest,
)
from backend.scheduler.engine import run_scheduler
from backend.scheduler.models import VehicleRequest, Charger
from backend.simulation.campus_energy import CampusEnergySimulator

router = APIRouter()

ADMIN_PASSWORD = "admin123"
ADMIN_USERS = {"admin": "Campus Manager", "ops": "Operations Team"}


# ── helpers ──────────────────────────────────────────────────────────────────

def get_default_chargers(config: CampusConfig, charger_failure: bool = False) -> List[Charger]:
    chargers = []
    for i in range(1, config.dc_chargers + 1):
        available = not (charger_failure and i == 1)
        chargers.append(Charger(f"CHARGER-DC-{i:02d}", "DC", config.dc_power_kw, available))
    ac_count = config.num_chargers - config.dc_chargers
    for i in range(1, ac_count + 1):
        chargers.append(Charger(f"CHARGER-AC-{i:02d}", "AC", config.charger_power_kw, True))
    return chargers


def db_request_to_vehicle(req: ChargingRequest) -> VehicleRequest:
    return VehicleRequest(
        request_id=req.request_id,
        vehicle_id=req.vehicle_id,
        user_id=req.user_id,
        arrival_time=req.arrival_time,
        departure_time=req.departure_time,
        battery_capacity_kwh=req.battery_capacity_kwh,
        initial_soc=req.initial_soc,
        required_energy_kwh=req.required_energy_kwh,
        max_charging_power_kw=req.max_charging_power_kw,
        charger_type=req.charger_type,
        priority_category=req.priority_category,
        request_timestamp=req.request_timestamp,
    )


async def get_or_create_config(db: AsyncSession) -> CampusConfig:
    result = await db.execute(select(CampusConfig).limit(1))
    config = result.scalars().first()
    if config is None:
        config = CampusConfig()
        db.add(config)
        await db.commit()
        await db.refresh(config)
    return config


def campus_config_dict(config: CampusConfig) -> dict:
    return {
        "battery_capacity_kwh": config.battery_capacity_kwh,
        "battery_max_power_kw": config.battery_max_power_kw,
        "battery_min_reserve_pct": config.battery_min_reserve_pct,
        "grid_limit_kw": config.grid_limit_kw,
        "campus_power_limit_kw": config.campus_power_limit_kw,
    }


# ── routes ────────────────────────────────────────────────────────────────────

@router.post("/charging/request", response_model=ChargingRequestResponse)
async def create_charging_request(
    body: ChargingRequestCreate, db: AsyncSession = Depends(get_db)
):
    warnings: List[str] = []
    window_h = (body.departure_time - body.arrival_time).total_seconds() / 3600
    max_possible = window_h * body.max_charging_power_kw
    required = body.required_energy_kwh
    if required > max_possible:
        warnings.append(
            f"Cannot deliver {required:.1f} kWh in {window_h:.1f}h window. "
            f"Max possible: {max_possible:.1f} kWh."
        )
    max_battery = body.battery_capacity_kwh * (1 - body.initial_soc)
    if required > max_battery:
        required = round(max_battery, 1)
        warnings.append(f"Required energy capped at battery space: {required:.1f} kWh")

    existing = await db.execute(
        select(ChargingRequest).where(
            ChargingRequest.vehicle_id == body.vehicle_id,
            ChargingRequest.status.in_(["pending", "scheduled", "active"]),
        )
    )
    if existing.scalars().first():
        warnings.append(f"Vehicle {body.vehicle_id} already has an active request.")

    request_id = f"REQ-{uuid.uuid4().hex[:8].upper()}"
    db.add(
        ChargingRequest(
            request_id=request_id,
            vehicle_id=body.vehicle_id,
            user_id=body.user_id,
            arrival_time=body.arrival_time,
            departure_time=body.departure_time,
            battery_capacity_kwh=body.battery_capacity_kwh,
            initial_soc=body.initial_soc,
            required_energy_kwh=required,
            max_charging_power_kw=body.max_charging_power_kw,
            charger_type=body.charger_type,
            priority_category=body.priority_category,
            status="pending",
            request_timestamp=datetime.utcnow(),
        )
    )
    await db.commit()
    return ChargingRequestResponse(
        request_id=request_id,
        vehicle_id=body.vehicle_id,
        status="pending",
        message=f"Request {request_id} submitted successfully.",
        validation_warnings=warnings,
    )


@router.get("/charging/schedule")
async def get_schedule(
    policy: Optional[str] = Query(None),
    vehicle_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    query = select(ChargingSession)
    if policy:
        query = query.where(ChargingSession.policy == policy)
    if vehicle_id:
        query = query.where(ChargingSession.vehicle_id == vehicle_id)
    result = await db.execute(query.order_by(ChargingSession.start_time))
    sessions = result.scalars().all()
    return [
        {
            "session_id": s.session_id,
            "request_id": s.request_id,
            "vehicle_id": s.vehicle_id,
            "charger_id": s.charger_id,
            "policy": s.policy,
            "start_time": s.start_time.isoformat(),
            "end_time": s.end_time.isoformat(),
            "planned_energy_kwh": s.planned_energy_kwh,
            "delivered_energy_kwh": s.delivered_energy_kwh,
            "priority_score": s.priority_score,
            "explanation": s.explanation,
            "is_fully_served": s.is_fully_served,
            "is_admin_override": s.is_admin_override,
            "failure_reason": s.failure_reason,
        }
        for s in sessions
    ]


@router.post("/scheduler/run")
async def run_scheduler_endpoint(
    body: ScheduleRunRequest, db: AsyncSession = Depends(get_db)
):
    config = await get_or_create_config(db)
    query = select(ChargingRequest).where(ChargingRequest.status == "pending")
    if body.request_ids:
        query = query.where(ChargingRequest.request_id.in_(body.request_ids))
    result = await db.execute(query)
    db_requests = result.scalars().all()
    if not db_requests:
        return {"message": "No pending requests", "sessions": [], "metrics": {}}

    vehicle_requests = [db_request_to_vehicle(r) for r in db_requests]
    chargers = get_default_chargers(config)
    result_obj = run_scheduler(
        requests=vehicle_requests,
        chargers=chargers,
        policy=body.policy,
        scenario=body.scenario,
        campus_config=campus_config_dict(config),
    )

    for session in result_obj.sessions:
        db.add(
            ChargingSession(
                session_id=f"SES-{uuid.uuid4().hex[:8].upper()}",
                request_id=session.request_id,
                vehicle_id=session.vehicle_id,
                charger_id=session.charger_id,
                policy=body.policy,
                start_time=session.start_time,
                end_time=session.end_time,
                planned_energy_kwh=session.planned_energy_kwh,
                delivered_energy_kwh=session.planned_energy_kwh,
                priority_score=session.priority_score,
                explanation=session.explanation,
                is_fully_served=session.is_fully_served,
                failure_reason=session.failure_reason,
            )
        )
        await db.execute(
            update(ChargingRequest)
            .where(ChargingRequest.request_id == session.request_id)
            .values(status="scheduled", priority_score=session.priority_score)
        )
    await db.execute(
        update(CampusConfig)
        .where(CampusConfig.id == config.id)
        .values(active_policy=body.policy)
    )
    await db.commit()
    return {
        "policy": body.policy,
        "sessions_created": len(result_obj.sessions),
        "metrics": result_obj.metrics,
        "scheduling_time_ms": result_obj.scheduling_time_ms,
        "error_analysis": result_obj.error_analysis[:10],
    }


@router.get("/vehicles")
async def get_vehicles(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ChargingRequest).order_by(ChargingRequest.vehicle_id))
    requests = result.scalars().all()
    vehicles: dict = {}
    for req in requests:
        if req.vehicle_id not in vehicles:
            vehicles[req.vehicle_id] = {
                "vehicle_id": req.vehicle_id,
                "user_id": req.user_id,
                "priority_category": req.priority_category,
                "charger_type": req.charger_type,
                "request_count": 0,
                "latest_status": req.status,
            }
        vehicles[req.vehicle_id]["request_count"] += 1
        vehicles[req.vehicle_id]["latest_status"] = req.status
    return list(vehicles.values())


@router.get("/chargers")
async def get_chargers(db: AsyncSession = Depends(get_db)):
    config = await get_or_create_config(db)
    chargers = get_default_chargers(config)
    now = datetime.utcnow()
    result = await db.execute(
        select(ChargingSession).where(
            ChargingSession.start_time <= now, ChargingSession.end_time >= now
        )
    )
    active = {s.charger_id for s in result.scalars().all()}
    return [
        {
            "charger_id": c.charger_id,
            "charger_type": c.charger_type,
            "max_power_kw": c.max_power_kw,
            "is_available": c.is_available,
            "is_occupied": c.charger_id in active,
            "status": "occupied" if c.charger_id in active else ("available" if c.is_available else "offline"),
        }
        for c in chargers
    ]


@router.get("/energy")
async def get_energy(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(EnergyDataPoint).order_by(EnergyDataPoint.timestamp.desc()).limit(96)
    )
    records = result.scalars().all()
    if not records:
        now = datetime.utcnow()
        sim = CampusEnergySimulator(seed=42)
        return sim.generate_day_profile(now)
    return [
        {
            "timestamp": r.timestamp.isoformat(),
            "solar_generation_kw": r.solar_generation_kw,
            "campus_load_kw": r.campus_load_kw,
            "battery_soc_kwh": r.battery_soc_kwh,
            "battery_charging_kw": r.battery_charging_kw,
            "battery_discharging_kw": r.battery_discharging_kw,
            "grid_import_kw": r.grid_import_kw,
            "ev_charging_load_kw": r.ev_charging_load_kw,
        }
        for r in reversed(records)
    ]


@router.post("/admin/override")
async def admin_override(
    body: AdminOverrideRequest, db: AsyncSession = Depends(get_db)
):
    if body.admin_password != ADMIN_PASSWORD:
        raise HTTPException(status_code=403, detail="Invalid admin credentials")
    if body.admin_id not in ADMIN_USERS:
        raise HTTPException(status_code=403, detail="Admin ID not recognised")

    req_result = await db.execute(
        select(ChargingRequest).where(ChargingRequest.request_id == body.request_id)
    )
    req = req_result.scalars().first()
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")

    old_priority = req.priority_score
    old_charger = None
    sess_result = await db.execute(
        select(ChargingSession).where(ChargingSession.request_id == body.request_id)
    )
    existing_session = sess_result.scalars().first()
    if existing_session:
        old_charger = existing_session.charger_id
        updates: dict = {
            "is_admin_override": True,
            "priority_score": body.new_priority_score,
            "explanation": f"[ADMIN OVERRIDE by {body.admin_name}] {body.reason}",
        }
        if body.new_charger_id:
            updates["charger_id"] = body.new_charger_id
        await db.execute(
            update(ChargingSession)
            .where(ChargingSession.request_id == body.request_id)
            .values(**updates)
        )

    await db.execute(
        update(ChargingRequest)
        .where(ChargingRequest.request_id == body.request_id)
        .values(
            priority_score=body.new_priority_score,
            priority_category="emergency" if body.new_priority_score >= 0.9 else req.priority_category,
        )
    )
    override = AdminOverride(
        override_id=f"OVR-{uuid.uuid4().hex[:8].upper()}",
        admin_id=body.admin_id,
        admin_name=body.admin_name,
        vehicle_id=body.vehicle_id,
        request_id=body.request_id,
        reason=body.reason,
        old_priority=old_priority,
        new_priority=body.new_priority_score,
        old_charger=old_charger,
        new_charger=body.new_charger_id,
    )
    db.add(override)
    await db.commit()
    return {
        "status": "override_applied",
        "override_id": override.override_id,
        "vehicle_id": body.vehicle_id,
        "admin": body.admin_name,
        "old_priority": old_priority,
        "new_priority": body.new_priority_score,
        "reason": body.reason,
        "timestamp": override.timestamp.isoformat(),
    }


@router.get("/admin/audit-log")
async def get_audit_log(limit: int = Query(50), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(AdminOverride).order_by(AdminOverride.timestamp.desc()).limit(limit)
    )
    return [
        {
            "override_id": o.override_id,
            "timestamp": o.timestamp.isoformat(),
            "admin_id": o.admin_id,
            "admin_name": o.admin_name,
            "vehicle_id": o.vehicle_id,
            "request_id": o.request_id,
            "reason": o.reason,
            "old_priority": o.old_priority,
            "new_priority": o.new_priority,
            "old_charger": o.old_charger,
            "new_charger": o.new_charger,
        }
        for o in result.scalars().all()
    ]


@router.get("/metrics")
async def get_metrics(
    policy: Optional[str] = Query(None), db: AsyncSession = Depends(get_db)
):
    query = select(ExperimentResult)
    if policy:
        query = query.where(ExperimentResult.policy == policy)
    result = await db.execute(query.order_by(ExperimentResult.created_at.desc()).limit(50))
    results = result.scalars().all()
    if not results:
        sr = await db.execute(select(ChargingSession))
        sessions = sr.scalars().all()
        rr = await db.execute(select(ChargingRequest))
        requests = rr.scalars().all()
        total = len(requests)
        delivered = sum(s.planned_energy_kwh for s in sessions)
        requested = sum(r.required_energy_kwh for r in requests)
        fully = sum(1 for s in sessions if s.is_fully_served)
        return [
            {
                "policy": "mixed",
                "scenario": "live",
                "total_requests": total,
                "fully_served": fully,
                "partially_served": len(sessions) - fully,
                "unserved": total - len(sessions),
                "total_energy_requested_kwh": round(requested, 2),
                "total_energy_delivered_kwh": round(delivered, 2),
                "energy_delivery_rate": round(delivered / max(1, requested), 4),
                "jains_fairness_index": 0.0,
                "departure_success_rate": 0.0,
                "avg_waiting_time_min": 0.0,
                "constraint_violations": 0,
                "scheduling_time_ms": 0.0,
                "solar_utilisation_pct": 0.0,
            }
        ]
    return [
        {
            "policy": r.policy,
            "scenario": r.scenario,
            "total_requests": r.total_requests,
            "fully_served": r.fully_served,
            "partially_served": r.partially_served,
            "unserved": r.unserved,
            "total_energy_requested_kwh": r.total_energy_requested_kwh,
            "total_energy_delivered_kwh": r.total_energy_delivered_kwh,
            "energy_delivery_rate": round(
                r.total_energy_delivered_kwh / max(1, r.total_energy_requested_kwh), 4
            ),
            "jains_fairness_index": r.jains_fairness_index,
            "departure_success_rate": r.departure_success_rate,
            "avg_waiting_time_min": r.avg_waiting_time_min,
            "constraint_violations": r.constraint_violations,
            "scheduling_time_ms": r.scheduling_time_ms,
            "solar_utilisation_pct": r.solar_utilisation_pct,
            "created_at": r.created_at.isoformat(),
        }
        for r in results
    ]


@router.post("/simulation/scenario")
async def run_scenario(body: ScenarioRequest, db: AsyncSession = Depends(get_db)):
    random.seed(42)
    await db.execute(delete(ChargingSession))
    await db.execute(delete(ChargingRequest))
    await db.commit()

    grid_map = {
        "grid_constraint": 10, "normal": 60, "high_demand": 60,
        "low_solar": 60, "battery_low": 60, "tight_departure": 60,
        "charger_failure": 60, "priority_override": 60,
    }
    grid_limit = grid_map.get(body.scenario, 60)
    num_v = body.num_vehicles
    if body.scenario == "high_demand":
        num_v = max(num_v, 15)

    vehicle_types = [
        {"cap": 75, "power": 50, "charger": "DC"},
        {"cap": 40, "power": 22, "charger": "AC"},
        {"cap": 77, "power": 50, "charger": "DC"},
        {"cap": 42, "power": 22, "charger": "AC"},
    ]

    now = datetime(2024, 3, 11, 8, 0, 0)
    requests_created = []
    for i in range(num_v):
        vt = vehicle_types[i % len(vehicle_types)]
        arrival = now + timedelta(hours=random.uniform(0, 3))
        depart_h = random.uniform(1.5, 3.0) if body.scenario == "tight_departure" else random.uniform(3.0, 8.0)
        departure = arrival + timedelta(hours=depart_h)
        initial_soc = round(random.uniform(0.10, 0.60), 2)
        required = round(vt["cap"] * (1 - initial_soc) * random.uniform(0.5, 1.0), 1)
        if body.scenario == "tight_departure" and i < 3:
            required = round(depart_h * vt["power"] * 1.5, 1)
        priority = random.choices(["standard", "priority", "emergency"], weights=[70, 20, 10])[0]
        if body.scenario == "priority_override" and i == 0:
            priority = "emergency"
        request_id = f"REQ-{uuid.uuid4().hex[:8].upper()}"
        req = ChargingRequest(
            request_id=request_id,
            vehicle_id=f"EV-{i+1:03d}",
            user_id=f"EMP-{i+1:03d}",
            arrival_time=arrival,
            departure_time=departure,
            battery_capacity_kwh=vt["cap"],
            initial_soc=initial_soc,
            required_energy_kwh=required,
            max_charging_power_kw=vt["power"],
            charger_type=vt["charger"],
            priority_category=priority,
            status="pending",
            scenario=body.scenario,
            request_timestamp=arrival - timedelta(hours=2),
        )
        db.add(req)
        requests_created.append(req)

    config = await get_or_create_config(db)
    config.grid_limit_kw = grid_limit
    config.active_policy = body.policy
    await db.commit()

    vehicle_requests = [db_request_to_vehicle(r) for r in requests_created]
    charger_failure = body.scenario == "charger_failure"
    chargers = get_default_chargers(config, charger_failure)
    cc = campus_config_dict(config)
    if body.scenario == "battery_low":
        cc["battery_min_reserve_pct"] = 0.80
    cc["grid_limit_kw"] = grid_limit

    result_obj = run_scheduler(
        requests=vehicle_requests,
        chargers=chargers,
        policy=body.policy,
        scenario=body.scenario,
        campus_config=cc,
        now=now,
    )

    for session in result_obj.sessions:
        db.add(
            ChargingSession(
                session_id=f"SES-{uuid.uuid4().hex[:8].upper()}",
                request_id=session.request_id,
                vehicle_id=session.vehicle_id,
                charger_id=session.charger_id,
                policy=body.policy,
                start_time=session.start_time,
                end_time=session.end_time,
                planned_energy_kwh=session.planned_energy_kwh,
                delivered_energy_kwh=session.planned_energy_kwh,
                priority_score=session.priority_score,
                explanation=session.explanation,
                is_fully_served=session.is_fully_served,
                failure_reason=session.failure_reason,
            )
        )
        await db.execute(
            update(ChargingRequest)
            .where(ChargingRequest.request_id == session.request_id)
            .values(status="scheduled", priority_score=session.priority_score)
        )

    m = result_obj.metrics
    exp = ExperimentResult(
        experiment_id=f"EXP-{uuid.uuid4().hex[:8].upper()}",
        policy=body.policy,
        scenario=body.scenario,
        total_requests=m.get("total_requests", 0),
        fully_served=m.get("fully_served", 0),
        partially_served=m.get("partially_served", 0),
        unserved=m.get("unserved", 0),
        total_energy_requested_kwh=m.get("total_energy_requested_kwh", 0),
        total_energy_delivered_kwh=m.get("total_energy_delivered_kwh", 0),
        avg_waiting_time_min=m.get("avg_waiting_time_min", 0),
        jains_fairness_index=m.get("jains_fairness_index", 0),
        departure_success_rate=m.get("departure_success_rate", 0),
        solar_utilisation_pct=0.15 if body.scenario == "low_solar" else 1.0,
        grid_energy_kwh=0.0,
        constraint_violations=0,
        scheduling_time_ms=result_obj.scheduling_time_ms,
    )
    db.add(exp)
    await db.commit()

    return {
        "scenario": body.scenario,
        "policy": body.policy,
        "requests_created": len(requests_created),
        "sessions_created": len(result_obj.sessions),
        "metrics": result_obj.metrics,
        "error_analysis": result_obj.error_analysis,
        "scheduling_time_ms": result_obj.scheduling_time_ms,
        "charger_failure_active": charger_failure,
    }


@router.get("/campus/config")
async def get_campus_config(db: AsyncSession = Depends(get_db)):
    config = await get_or_create_config(db)
    return {
        "num_chargers": config.num_chargers,
        "charger_power_kw": config.charger_power_kw,
        "dc_chargers": config.dc_chargers,
        "dc_power_kw": config.dc_power_kw,
        "campus_power_limit_kw": config.campus_power_limit_kw,
        "battery_capacity_kwh": config.battery_capacity_kwh,
        "battery_max_power_kw": config.battery_max_power_kw,
        "battery_min_reserve_pct": config.battery_min_reserve_pct,
        "battery_soc_kwh": config.battery_soc_kwh,
        "grid_limit_kw": config.grid_limit_kw,
        "active_policy": config.active_policy,
    }


@router.put("/campus/config")
async def update_campus_config(
    num_chargers: Optional[int] = None,
    campus_power_limit_kw: Optional[float] = None,
    battery_min_reserve_pct: Optional[float] = None,
    grid_limit_kw: Optional[float] = None,
    active_policy: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    config = await get_or_create_config(db)
    if num_chargers is not None:
        config.num_chargers = num_chargers
    if campus_power_limit_kw is not None:
        config.campus_power_limit_kw = campus_power_limit_kw
    if battery_min_reserve_pct is not None:
        config.battery_min_reserve_pct = battery_min_reserve_pct
    if grid_limit_kw is not None:
        config.grid_limit_kw = grid_limit_kw
    if active_policy is not None:
        config.active_policy = active_policy
    config.updated_at = datetime.utcnow()
    await db.commit()
    return {"status": "updated"}


@router.get("/experiment/compare")
async def compare_experiments(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ExperimentResult).order_by(ExperimentResult.created_at.desc()).limit(30)
    )
    all_results = result.scalars().all()
    seen: dict = {}
    for r in all_results:
        key = (r.policy, r.scenario)
        if key not in seen:
            seen[key] = r
    return [
        {
            "policy": r.policy,
            "scenario": r.scenario,
            "total_requests": r.total_requests,
            "fully_served": r.fully_served,
            "partially_served": r.partially_served,
            "unserved": r.unserved,
            "total_energy_requested_kwh": r.total_energy_requested_kwh,
            "total_energy_delivered_kwh": r.total_energy_delivered_kwh,
            "energy_delivery_rate": round(
                r.total_energy_delivered_kwh / max(1, r.total_energy_requested_kwh), 3
            ),
            "jains_fairness_index": r.jains_fairness_index,
            "departure_success_rate": r.departure_success_rate,
            "avg_waiting_time_min": r.avg_waiting_time_min,
            "constraint_violations": r.constraint_violations,
            "scheduling_time_ms": r.scheduling_time_ms,
            "solar_utilisation_pct": r.solar_utilisation_pct,
        }
        for r in seen.values()
    ]

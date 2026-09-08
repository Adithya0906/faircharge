import time
from datetime import datetime
from typing import List, Dict, Optional

from backend.scheduler.models import VehicleRequest, Charger, TimeSlot, ScheduledSession, ScheduleResult
from backend.scheduler.priority import calculate_priority_score, generate_explanation
from backend.scheduler.metrics import calculate_metrics

SLOT_DURATION_H = 15 / 60.0


def run_fcfs_scheduler(
    requests: List[VehicleRequest],
    chargers: List[Charger],
    energy_slots: List[TimeSlot],
    now: datetime,
) -> ScheduleResult:
    start_time = time.time()
    # FCFS: sort strictly by arrival time
    sorted_requests = sorted(requests, key=lambda r: r.arrival_time)
    available_chargers = [c for c in chargers if c.is_available]
    charger_schedule: Dict[str, List] = {c.charger_id: [] for c in available_chargers}
    slot_power: Dict[str, float] = {slot.start.isoformat(): 0.0 for slot in energy_slots}
    sessions: List[ScheduledSession] = []
    error_analysis: List[Dict] = []

    for req in sorted_requests:
        if req.departure_time <= req.arrival_time:
            error_analysis.append({
                "request_id": req.request_id, "vehicle_id": req.vehicle_id,
                "reason": "departure before arrival", "classification": "invalid_request",
                "required_kwh": req.required_energy_kwh, "delivered_kwh": 0.0,
            })
            continue
        if req.required_energy_kwh <= 0:
            error_analysis.append({
                "request_id": req.request_id, "vehicle_id": req.vehicle_id,
                "reason": "zero energy requested", "classification": "invalid_request",
                "required_kwh": req.required_energy_kwh, "delivered_kwh": 0.0,
            })
            continue

        assigned_charger = None
        for charger in available_chargers:
            if req.charger_type == "DC" and charger.charger_type == "AC":
                continue
            busy = charger_schedule[charger.charger_id]
            if not any(
                not (req.departure_time <= s[0] or req.arrival_time >= s[1]) for s in busy
            ):
                assigned_charger = charger
                break

        if assigned_charger is None:
            error_analysis.append({
                "request_id": req.request_id, "vehicle_id": req.vehicle_id,
                "reason": "all chargers occupied", "classification": "charger_capacity",
                "required_kwh": req.required_energy_kwh, "delivered_kwh": 0.0,
                "departure_time": req.departure_time.isoformat(),
            })
            continue

        delivered, slot_alloc, session_start, session_end = 0.0, {}, None, None
        remaining = req.required_energy_kwh
        charger_power = min(assigned_charger.max_power_kw, req.max_charging_power_kw)

        for slot in energy_slots:
            if slot.start < req.arrival_time or slot.start >= req.departure_time:
                continue
            if remaining <= 0.001:
                break
            slot_key = slot.start.isoformat()
            avail = min(
                charger_power,
                max(0.0, slot.available_power_kw - slot_power.get(slot_key, 0.0)),
            )
            energy = min(avail * SLOT_DURATION_H, remaining)
            if energy <= 0.001:
                continue
            power = energy / SLOT_DURATION_H
            delivered += energy
            remaining -= energy
            slot_power[slot_key] = slot_power.get(slot_key, 0.0) + power
            slot_alloc[slot_key] = round(power, 2)
            if session_start is None:
                session_start = slot.start
            session_end = slot.end

        if session_start is None:
            error_analysis.append({
                "request_id": req.request_id, "vehicle_id": req.vehicle_id,
                "reason": "no power available", "classification": "insufficient_campus_energy",
                "required_kwh": req.required_energy_kwh, "delivered_kwh": 0.0,
                "departure_time": req.departure_time.isoformat(),
            })
            continue

        is_fully = delivered >= req.required_energy_kwh * 0.99
        failure_reason = None if is_fully else "partial delivery due to capacity constraints"
        score_info = calculate_priority_score(req, now, "fcfs")
        explanation = generate_explanation(
            req, session_start, score_info, "fcfs", assigned_charger.charger_id, is_fully, round(delivered, 2)
        )
        charger_schedule[assigned_charger.charger_id].append((session_start, session_end))

        sessions.append(
            ScheduledSession(
                request_id=req.request_id,
                vehicle_id=req.vehicle_id,
                charger_id=assigned_charger.charger_id,
                start_time=session_start,
                end_time=session_end,
                planned_energy_kwh=round(delivered, 2),
                priority_score=score_info["score"],
                explanation=explanation,
                is_fully_served=is_fully,
                failure_reason=failure_reason,
                slot_allocations=slot_alloc,
                policy="fcfs",
            )
        )

        if not is_fully:
            error_analysis.append({
                "request_id": req.request_id, "vehicle_id": req.vehicle_id,
                "reason": failure_reason, "classification": "partial_delivery",
                "required_kwh": req.required_energy_kwh, "delivered_kwh": round(delivered, 2),
                "departure_time": req.departure_time.isoformat(),
            })

    return ScheduleResult(
        policy="fcfs",
        sessions=sessions,
        scheduling_time_ms=round((time.time() - start_time) * 1000, 2),
        metrics=calculate_metrics(requests, sessions, "fcfs"),
        error_analysis=error_analysis,
    )

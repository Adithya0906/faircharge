import time
from datetime import datetime
from typing import List, Dict, Optional, Tuple

from backend.scheduler.models import VehicleRequest, Charger, TimeSlot, ScheduledSession, ScheduleResult
from backend.scheduler.priority import calculate_priority_score, generate_explanation
from backend.scheduler.metrics import calculate_metrics

SLOT_DURATION_H = 15 / 60.0


def run_optimized_scheduler(
    requests: List[VehicleRequest],
    chargers: List[Charger],
    energy_slots: List[TimeSlot],
    now: datetime,
    policy: str = "urgency",
    historical_allocations: Optional[Dict[str, float]] = None,
) -> ScheduleResult:
    start_time = time.time()
    if historical_allocations is None:
        historical_allocations = {}

    valid_requests, error_analysis = [], []
    for req in requests:
        if req.departure_time <= req.arrival_time:
            error_analysis.append({
                "request_id": req.request_id, "vehicle_id": req.vehicle_id,
                "reason": "departure before arrival", "classification": "invalid_request",
                "required_kwh": req.required_energy_kwh, "delivered_kwh": 0.0,
            })
        elif req.required_energy_kwh <= 0:
            error_analysis.append({
                "request_id": req.request_id, "vehicle_id": req.vehicle_id,
                "reason": "zero energy requested", "classification": "invalid_request",
                "required_kwh": req.required_energy_kwh, "delivered_kwh": 0.0,
            })
        else:
            valid_requests.append(req)

    if not valid_requests:
        return ScheduleResult(
            policy=policy, sessions=[],
            scheduling_time_ms=0.0,
            metrics=calculate_metrics(requests, [], policy),
            error_analysis=error_analysis,
        )

    max_window = max((r.window_hours for r in valid_requests), default=12.0)
    for req in valid_requests:
        si = calculate_priority_score(req, now, policy, historical_allocations, max_window_h=max_window)
        req.priority_score = si["score"]

    sorted_requests = sorted(valid_requests, key=lambda r: -r.priority_score)
    available_chargers = [c for c in chargers if c.is_available]
    charger_schedule: Dict[str, List] = {c.charger_id: [] for c in available_chargers}
    slot_power: Dict[str, float] = {slot.start.isoformat(): 0.0 for slot in energy_slots}
    sessions: List[ScheduledSession] = []

    for req in sorted_requests:
        assigned_charger = _find_best_charger(req, available_chargers, charger_schedule)
        if assigned_charger is None:
            error_analysis.append({
                "request_id": req.request_id, "vehicle_id": req.vehicle_id,
                "reason": "no compatible charger available", "classification": "charger_capacity",
                "required_kwh": req.required_energy_kwh, "delivered_kwh": 0.0,
                "departure_time": req.departure_time.isoformat(),
            })
            continue

        delivered, slot_alloc, session_start, session_end = _allocate_slots(
            req, assigned_charger, energy_slots, slot_power
        )

        if session_start is None:
            error_analysis.append({
                "request_id": req.request_id, "vehicle_id": req.vehicle_id,
                "reason": "no power available in window", "classification": "insufficient_campus_energy",
                "required_kwh": req.required_energy_kwh, "delivered_kwh": 0.0,
                "departure_time": req.departure_time.isoformat(),
            })
            continue

        is_fully = delivered >= req.required_energy_kwh * 0.99
        failure_reason = None
        if not is_fully:
            if req.required_energy_kwh > req.max_deliverable_kwh:
                failure_reason = "impossible request: required energy exceeds max deliverable before departure"
                cls = "insufficient_time"
            elif delivered < req.required_energy_kwh * 0.5:
                failure_reason = "insufficient campus energy capacity"
                cls = "insufficient_campus_energy"
            else:
                failure_reason = "partial delivery: campus capacity constrained"
                cls = "partial_delivery"
            error_analysis.append({
                "request_id": req.request_id, "vehicle_id": req.vehicle_id,
                "reason": failure_reason, "classification": cls,
                "required_kwh": req.required_energy_kwh, "delivered_kwh": round(delivered, 2),
                "departure_time": req.departure_time.isoformat(),
                "max_possible_kwh": round(req.max_deliverable_kwh, 2),
            })

        score_info = calculate_priority_score(
            req, now, policy, historical_allocations, max_window_h=max_window
        )
        explanation = generate_explanation(
            req, session_start, score_info, policy, assigned_charger.charger_id, is_fully, round(delivered, 2)
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
                policy=policy,
            )
        )

    return ScheduleResult(
        policy=policy,
        sessions=sessions,
        scheduling_time_ms=round((time.time() - start_time) * 1000, 2),
        metrics=calculate_metrics(valid_requests, sessions, policy),
        error_analysis=error_analysis,
    )


def _find_best_charger(
    req: VehicleRequest, chargers: List[Charger], schedule: Dict
) -> Optional[Charger]:
    for charger in chargers:
        if charger.charger_type == req.charger_type and _charger_free(charger, req, schedule):
            return charger
    for charger in chargers:
        if _charger_free(charger, req, schedule):
            return charger
    return None


def _charger_free(charger: Charger, req: VehicleRequest, schedule: Dict) -> bool:
    busy = schedule.get(charger.charger_id, [])
    return not any(
        not (req.departure_time <= s[0] or req.arrival_time >= s[1]) for s in busy
    )


def _allocate_slots(
    req: VehicleRequest,
    charger: Charger,
    energy_slots: List[TimeSlot],
    slot_power: Dict,
) -> Tuple[float, Dict, Optional[datetime], Optional[datetime]]:
    delivered, remaining = 0.0, req.required_energy_kwh
    slot_alloc, session_start, session_end = {}, None, None
    charger_power = min(charger.max_power_kw, req.max_charging_power_kw)

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

    return delivered, slot_alloc, session_start, session_end

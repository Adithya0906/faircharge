from datetime import datetime
from typing import Dict, Optional
from backend.scheduler.models import VehicleRequest

WEIGHTS = {
    "urgency": {"urgency": 0.40, "energy_need": 0.30, "waiting_time": 0.20, "priority_category": 0.10},
    "fairness": {
        "urgency": 0.20,
        "energy_need": 0.20,
        "waiting_time": 0.30,
        "priority_category": 0.10,
        "fairness_adjustment": 0.20,
    },
    "fcfs": {"urgency": 0.0, "energy_need": 0.0, "waiting_time": 1.0, "priority_category": 0.0},
}

PRIORITY_CATEGORY_SCORE = {"emergency": 1.0, "priority": 0.6, "standard": 0.2}


def calculate_priority_score(
    request: VehicleRequest,
    now: datetime,
    policy: str = "urgency",
    historical_allocations: Optional[Dict[str, float]] = None,
    max_window_h: float = 12.0,
    max_wait_h: float = 12.0,
) -> Dict:
    if historical_allocations is None:
        historical_allocations = {}
    weights = WEIGHTS.get(policy, WEIGHTS["urgency"])

    time_remaining_h = max(0.0, (request.departure_time - now).total_seconds() / 3600)
    urgency_score = 1.0 - min(1.0, time_remaining_h / max(0.01, max_window_h))

    energy_need_score = min(1.0, request.required_energy_kwh / max(1.0, request.battery_capacity_kwh))

    if request.request_timestamp:
        wait_h = max(0.0, (now - request.request_timestamp).total_seconds() / 3600)
    else:
        wait_h = 0.0
    waiting_score = min(1.0, wait_h / max(0.01, max_wait_h))

    category_score = PRIORITY_CATEGORY_SCORE.get(request.priority_category, 0.2)

    hist_ratio = historical_allocations.get(request.user_id, 0.5)
    fairness_adj = 1.0 - hist_ratio

    if policy == "fcfs":
        score = waiting_score
    else:
        score = (
            weights.get("urgency", 0) * urgency_score
            + weights.get("energy_need", 0) * energy_need_score
            + weights.get("waiting_time", 0) * waiting_score
            + weights.get("priority_category", 0) * category_score
            + weights.get("fairness_adjustment", 0) * fairness_adj
        )

    return {
        "score": round(score, 4),
        "factors": {
            "urgency_score": round(urgency_score, 3),
            "energy_need_score": round(energy_need_score, 3),
            "waiting_score": round(waiting_score, 3),
            "category_score": round(category_score, 3),
            "fairness_adjustment": round(fairness_adj, 3),
            "time_remaining_h": round(time_remaining_h, 2),
            "wait_h": round(wait_h, 2),
            "required_energy_kwh": request.required_energy_kwh,
        },
    }


def generate_explanation(
    request: VehicleRequest,
    session_start: datetime,
    score_info: Dict,
    policy: str,
    charger_id: str,
    is_fully_served: bool,
    delivered_kwh: float,
) -> str:
    factors = score_info["factors"]
    score = score_info["score"]
    time_remaining = factors["time_remaining_h"]

    delivery_str = (
        f"Full {delivered_kwh:.1f} kWh delivered before departure."
        if is_fully_served
        else f"Partial delivery: {delivered_kwh:.1f}/{request.required_energy_kwh:.1f} kWh due to capacity constraints."
    )

    if policy == "fcfs":
        return (
            f"Vehicle {request.vehicle_id} was scheduled at {session_start.strftime('%H:%M')} "
            f"using First-Come-First-Served (arrival order). Charger {charger_id} assigned. {delivery_str}"
        )
    elif policy == "urgency":
        return (
            f"Vehicle {request.vehicle_id} scheduled at {session_start.strftime('%H:%M')} "
            f"(priority score: {score:.3f}). Departure in {time_remaining:.1f}h, requiring "
            f"{request.required_energy_kwh:.1f} kWh. Urgency: {factors['urgency_score']:.2f}, "
            f"Energy need: {factors['energy_need_score']:.2f}, Category: {request.priority_category}. "
            f"Charger {charger_id} assigned. {delivery_str}"
        )
    else:
        return (
            f"Vehicle {request.vehicle_id} scheduled at {session_start.strftime('%H:%M')} "
            f"under fairness-first policy (score: {score:.3f}). "
            f"Wait factor: {factors['waiting_score']:.2f}, Fairness adj: {factors['fairness_adjustment']:.2f}. "
            f"Charger {charger_id}. {delivery_str}"
        )

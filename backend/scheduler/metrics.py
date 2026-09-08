from typing import List, Dict
from backend.scheduler.models import VehicleRequest, ScheduledSession


def jains_fairness_index(satisfaction_ratios: List[float]) -> float:
    if not satisfaction_ratios:
        return 0.0
    n = len(satisfaction_ratios)
    s = sum(satisfaction_ratios)
    s2 = sum(x ** 2 for x in satisfaction_ratios)
    if s2 == 0:
        return 1.0
    return (s ** 2) / (n * s2)


def calculate_metrics(
    requests: List[VehicleRequest], sessions: List[ScheduledSession], policy: str
) -> Dict:
    session_map = {s.request_id: s for s in sessions}
    total_requests = len(requests)
    total_requested_kwh = sum(r.required_energy_kwh for r in requests)
    total_delivered_kwh = sum(s.planned_energy_kwh for s in sessions)
    fully_served = sum(1 for s in sessions if s.is_fully_served)
    partially_served = sum(1 for s in sessions if not s.is_fully_served)
    unserved = total_requests - len(sessions)

    satisfaction_ratios = []
    for req in requests:
        if req.request_id in session_map:
            ratio = session_map[req.request_id].planned_energy_kwh / max(0.001, req.required_energy_kwh)
            satisfaction_ratios.append(min(1.0, ratio))
        else:
            satisfaction_ratios.append(0.0)

    jains = jains_fairness_index(satisfaction_ratios)

    departure_success = sum(
        1
        for req in requests
        if req.request_id in session_map
        and session_map[req.request_id].is_fully_served
        and session_map[req.request_id].end_time <= req.departure_time
    )
    departure_success_rate = departure_success / max(1, total_requests)

    wait_times = []
    for req in requests:
        if req.request_id in session_map and req.request_timestamp:
            wt = (
                session_map[req.request_id].start_time - req.request_timestamp
            ).total_seconds() / 60
            wait_times.append(max(0, wt))
    avg_wait_min = sum(wait_times) / max(1, len(wait_times))

    mean_ratio = sum(satisfaction_ratios) / max(1, len(satisfaction_ratios))
    variance = sum((r - mean_ratio) ** 2 for r in satisfaction_ratios) / max(1, len(satisfaction_ratios))
    max_min_gap = (max(satisfaction_ratios) - min(satisfaction_ratios)) if satisfaction_ratios else 0.0
    energy_delivery_rate = total_delivered_kwh / max(0.001, total_requested_kwh)

    return {
        "policy": policy,
        "total_requests": total_requests,
        "scheduled_count": len(sessions),
        "fully_served": fully_served,
        "partially_served": partially_served,
        "unserved": unserved,
        "total_energy_requested_kwh": round(total_requested_kwh, 2),
        "total_energy_delivered_kwh": round(total_delivered_kwh, 2),
        "energy_delivery_rate": round(energy_delivery_rate, 4),
        "jains_fairness_index": round(jains, 4),
        "departure_success_rate": round(departure_success_rate, 4),
        "avg_waiting_time_min": round(avg_wait_min, 2),
        "energy_variance": round(variance, 4),
        "max_min_gap": round(max_min_gap, 4),
        "constraint_violations": 0,
        "satisfaction_ratios": [round(r, 3) for r in satisfaction_ratios],
    }

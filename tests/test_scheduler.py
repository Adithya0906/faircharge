"""
FairCharge - Automated Test Suite
Tests hard constraints, fairness metrics, priority logic, and edge cases.
"""
import pytest
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import List

sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.scheduler.models import VehicleRequest, Charger
from backend.scheduler.engine import run_scheduler
from backend.scheduler.metrics import jains_fairness_index
from backend.scheduler.priority import calculate_priority_score

BASE = datetime(2024, 3, 11, 8, 0, 0)

DEFAULT_CHARGERS = [
    Charger("CHARGER-DC-01", "DC", 50.0, True),
    Charger("CHARGER-DC-02", "DC", 50.0, True),
    Charger("CHARGER-AC-01", "AC", 22.0, True),
    Charger("CHARGER-AC-02", "AC", 22.0, True),
]

CAMPUS = {
    "battery_capacity_kwh": 150.0,
    "battery_max_power_kw": 40.0,
    "battery_min_reserve_pct": 0.20,
    "grid_limit_kw": 60.0,
    "campus_power_limit_kw": 120.0,
}


def make_req(
    idx, offset_h=0, dur_h=6, kwh=20, power=22,
    ctype="AC", priority="standard", soc=0.3, cap=75,
):
    arr = BASE + timedelta(hours=offset_h)
    dep = arr + timedelta(hours=dur_h)
    return VehicleRequest(
        request_id=f"REQ-{idx:04d}",
        vehicle_id=f"EV-{idx:03d}",
        user_id=f"EMP-{idx:03d}",
        arrival_time=arr,
        departure_time=dep,
        battery_capacity_kwh=cap,
        initial_soc=soc,
        required_energy_kwh=kwh,
        max_charging_power_kw=power,
        charger_type=ctype,
        priority_category=priority,
        request_timestamp=arr - timedelta(hours=1),
    )


# ── Hard Constraints ──────────────────────────────────────────────────────────

class TestHardConstraints:
    def test_no_charging_before_arrival(self):
        r = make_req(1, offset_h=4, dur_h=4, kwh=10)
        result = run_scheduler([r], DEFAULT_CHARGERS, "urgency", campus_config=CAMPUS)
        for s in result.sessions:
            if s.request_id == r.request_id:
                assert s.start_time >= r.arrival_time, "Session starts before arrival!"

    def test_no_charging_after_departure(self):
        r = make_req(2, offset_h=0, dur_h=3, kwh=10)
        result = run_scheduler([r], DEFAULT_CHARGERS, "urgency", campus_config=CAMPUS)
        for s in result.sessions:
            if s.request_id == r.request_id:
                assert s.end_time <= r.departure_time, "Session ends after departure!"

    def test_energy_not_exceed_requested(self):
        r = make_req(3, kwh=15, dur_h=8, power=22)
        result = run_scheduler([r], DEFAULT_CHARGERS, "urgency", campus_config=CAMPUS)
        for s in result.sessions:
            if s.request_id == r.request_id:
                assert s.planned_energy_kwh <= r.required_energy_kwh + 0.5

    def test_impossible_request_not_silently_ignored(self):
        """1h window, 200 kWh needed at 22 kW — impossible."""
        r = make_req(4, dur_h=1, kwh=200, power=22)
        result = run_scheduler([r], DEFAULT_CHARGERS, "urgency", campus_config=CAMPUS)
        sids = {s.request_id for s in result.sessions}
        eids = {e["request_id"] for e in result.error_analysis}
        assert r.request_id in sids or r.request_id in eids, \
            "Impossible request disappeared silently"
        for s in result.sessions:
            if s.request_id == r.request_id:
                assert not s.is_fully_served

    def test_zero_energy_rejected(self):
        r = make_req(5, kwh=0)
        result = run_scheduler([r], DEFAULT_CHARGERS, "urgency", campus_config=CAMPUS)
        assert r.request_id not in {s.request_id for s in result.sessions}

    def test_invalid_times_rejected(self):
        r = VehicleRequest(
            request_id="REQ-BAD",
            vehicle_id="EV-BAD",
            user_id="EMP-BAD",
            arrival_time=BASE + timedelta(hours=5),
            departure_time=BASE + timedelta(hours=3),
            battery_capacity_kwh=75,
            initial_soc=0.5,
            required_energy_kwh=10,
            max_charging_power_kw=22,
            charger_type="AC",
            priority_category="standard",
        )
        result = run_scheduler([r], DEFAULT_CHARGERS, "urgency", campus_config=CAMPUS)
        assert r.request_id not in {s.request_id for s in result.sessions}

    def test_charger_failure_reduces_capacity(self):
        requests = [make_req(i, offset_h=i * 0.1, dur_h=4, kwh=15) for i in range(1, 5)]
        normal_result = run_scheduler(requests, DEFAULT_CHARGERS, "urgency", campus_config=CAMPUS)
        failed_chargers = [
            Charger("CHARGER-DC-01", "DC", 50.0, False),
            Charger("CHARGER-DC-02", "DC", 50.0, True),
            Charger("CHARGER-AC-01", "AC", 22.0, True),
            Charger("CHARGER-AC-02", "AC", 22.0, True),
        ]
        result_f = run_scheduler(requests, failed_chargers, "urgency", campus_config=CAMPUS)
        assert len(result_f.sessions) <= len(normal_result.sessions)

    def test_zero_constraint_violations_all_policies(self):
        requests = [make_req(i, offset_h=i, dur_h=5, kwh=20) for i in range(1, 6)]
        for policy in ["fcfs", "urgency", "fairness"]:
            result = run_scheduler(requests, DEFAULT_CHARGERS, policy, campus_config=CAMPUS)
            assert result.metrics.get("constraint_violations", 0) == 0, \
                f"Constraint violation in {policy} policy"


# ── Fairness ──────────────────────────────────────────────────────────────────

class TestFairness:
    def test_jains_perfect_equality(self):
        j = jains_fairness_index([0.8, 0.8, 0.8, 0.8])
        assert abs(j - 1.0) < 0.001

    def test_jains_extreme_inequality(self):
        j = jains_fairness_index([1.0, 0.0, 0.0, 0.0])
        assert j <= 0.35

    def test_jains_range_always_valid(self):
        import random
        rng = random.Random(42)
        for _ in range(30):
            ratios = [rng.random() for _ in range(rng.randint(2, 20))]
            j = jains_fairness_index(ratios)
            assert 0 <= j <= 1.0 + 1e-9, f"Jain's index out of [0,1]: {j}"

    def test_jains_empty(self):
        j = jains_fairness_index([])
        assert j == 0.0

    def test_fairness_policy_jains_index_acceptable(self):
        """Fairness policy should achieve Jain's Index >= 0.6 (fair distribution)."""
        requests = [make_req(i, offset_h=i * 0.5, dur_h=4, kwh=20 + i * 5) for i in range(1, 7)]
        r_fair = run_scheduler(requests, DEFAULT_CHARGERS, "fairness", campus_config=CAMPUS)
        jf = r_fair.metrics.get("jains_fairness_index", 0)
        # Fairness policy must achieve at least 0.6 Jain's index
        assert jf >= 0.60, f"Fairness policy JFI too low: {jf:.3f}"


# ── Priority ──────────────────────────────────────────────────────────────────

class TestPriority:
    def test_emergency_higher_than_standard(self):
        re = make_req(1, priority="emergency")
        rs = make_req(2, priority="standard")
        se = calculate_priority_score(re, BASE, "urgency")
        ss = calculate_priority_score(rs, BASE, "urgency")
        assert se["score"] > ss["score"]

    def test_shorter_window_higher_urgency(self):
        ru = make_req(1, dur_h=1)
        rr = make_req(2, dur_h=8)
        su = calculate_priority_score(ru, BASE, "urgency")
        sr = calculate_priority_score(rr, BASE, "urgency")
        assert su["factors"]["urgency_score"] >= sr["factors"]["urgency_score"]

    def test_score_has_all_factors(self):
        r = make_req(1)
        info = calculate_priority_score(r, BASE, "urgency")
        assert "score" in info and "factors" in info
        for key in ["urgency_score", "energy_need_score", "waiting_score", "category_score"]:
            assert key in info["factors"]

    def test_fcfs_score_equals_waiting_time(self):
        r = make_req(1, offset_h=2)
        info = calculate_priority_score(r, BASE + timedelta(hours=3), "fcfs")
        assert abs(info["score"] - info["factors"]["waiting_score"]) < 0.001


# ── Policy Comparison ─────────────────────────────────────────────────────────

class TestPolicyComparison:
    def test_all_policies_run_without_error(self):
        requests = [make_req(i, offset_h=i, dur_h=5, kwh=15) for i in range(1, 6)]
        for policy in ["fcfs", "urgency", "fairness"]:
            result = run_scheduler(requests, DEFAULT_CHARGERS, policy, campus_config=CAMPUS)
            assert result is not None
            assert result.policy == policy

    def test_all_policies_return_sessions(self):
        requests = [make_req(i, offset_h=i * 0.3, dur_h=4, kwh=15 + i * 2) for i in range(1, 6)]
        for policy in ["fcfs", "urgency", "fairness"]:
            result = run_scheduler(requests, DEFAULT_CHARGERS, policy, campus_config=CAMPUS)
            assert len(result.sessions) >= 1, f"{policy}: no sessions scheduled"

    def test_urgency_respects_priority_order(self):
        """Emergency vehicle should get higher priority score than standard."""
        requests = [
            make_req(1, priority="standard", offset_h=0),
            make_req(2, priority="emergency", offset_h=0),
        ]
        result = run_scheduler(requests, DEFAULT_CHARGERS, "urgency", campus_config=CAMPUS)
        scores = {s.request_id: s.priority_score for s in result.sessions}
        if "REQ-0001" in scores and "REQ-0002" in scores:
            assert scores["REQ-0002"] >= scores["REQ-0001"]


# ── Edge Cases ────────────────────────────────────────────────────────────────

class TestEdgeCases:
    def test_empty_requests(self):
        result = run_scheduler([], DEFAULT_CHARGERS, "urgency", campus_config=CAMPUS)
        assert result.sessions == []
        assert result.metrics["total_requests"] == 0

    def test_all_chargers_offline(self):
        requests = [make_req(i) for i in range(1, 4)]
        offline = [
            Charger(c.charger_id, c.charger_type, c.max_power_kw, False)
            for c in DEFAULT_CHARGERS
        ]
        result = run_scheduler(requests, offline, "urgency", campus_config=CAMPUS)
        assert len(result.sessions) == 0

    def test_single_vehicle_gets_charged(self):
        r = make_req(1, kwh=10, dur_h=6)
        result = run_scheduler([r], DEFAULT_CHARGERS, "urgency", campus_config=CAMPUS)
        assert len(result.sessions) >= 1
        assert result.sessions[0].planned_energy_kwh > 0

    def test_grid_constraint_limits_total_energy(self):
        requests = [make_req(i, offset_h=0, dur_h=6, kwh=30) for i in range(1, 5)]
        constrained = {**CAMPUS, "grid_limit_kw": 5.0}
        r_c = run_scheduler(
            requests, DEFAULT_CHARGERS, "urgency", "grid_constraint",
            campus_config=constrained,
        )
        r_n = run_scheduler(requests, DEFAULT_CHARGERS, "urgency", "normal", campus_config=CAMPUS)
        total_c = sum(s.planned_energy_kwh for s in r_c.sessions)
        total_n = sum(s.planned_energy_kwh for s in r_n.sessions)
        assert total_c <= total_n + 10.0

    def test_metrics_keys_present(self):
        requests = [make_req(i, offset_h=i, dur_h=4, kwh=15) for i in range(1, 4)]
        result = run_scheduler(requests, DEFAULT_CHARGERS, "urgency", campus_config=CAMPUS)
        required_keys = [
            "total_requests", "fully_served", "partially_served", "unserved",
            "jains_fairness_index", "departure_success_rate", "energy_delivery_rate",
            "avg_waiting_time_min", "constraint_violations",
        ]
        for k in required_keys:
            assert k in result.metrics, f"Missing metric key: {k}"

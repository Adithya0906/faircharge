# FairCharge — Granular Technical Specification: Unit Testing & Error Boundaries

## 1. Overview
This document provides a granular technical reference for the unit testing architecture, test suite categorization, and error boundary isolation mechanisms built into **FairCharge**.

---

## 2. Unit Testing Suite Breakdown (`tests/test_scheduler.py`)

The automated Pytest test suite contains **25 test cases** organized into 5 distinct functional test classes. All tests execute in under 1 second with 100% pass rate.

### 2.1 Class: `TestHardConstraints` (8 Tests)
Validates physical, temporal, and capacity safety constraints.

1. **`test_no_charging_before_arrival`**: Verifies that for every scheduled session $s$, $s.\text{start\_time} \ge r.\text{arrival\_time}$.
2. **`test_no_charging_after_departure`**: Verifies that $s.\text{end\_time} \le r.\text{departure\_time}$.
3. **`test_energy_not_exceed_requested`**: Confirms planned energy delivered never exceeds $r.\text{required\_energy\_kwh} + 0.5$.
4. **`test_impossible_request_not_silently_ignored`**: Ensures requests with impossible time windows (e.g., 200 kWh in 1 hour) are captured in `error_analysis` rather than vanishing silently.
5. **`test_zero_energy_rejected`**: Validates that zero or negative energy requests are rejected before slot allocation.
6. **`test_invalid_times_rejected`**: Ensures requests with departure time prior to arrival time are flagged and rejected.
7. **`test_charger_failure_reduces_capacity`**: Verifies that marking a charger as offline (`is_available = False`) gracefully scales down campus scheduling capacity.
8. **`test_zero_constraint_violations_all_policies`**: Asserts that `metrics["constraint_violations"] == 0` across FCFS, Urgency, and Fairness policies.

### 2.2 Class: `TestFairness` (5 Tests)
Validates mathematical equity properties and Jain's Fairness Index ($\mathcal{J}$).

9. **`test_jains_perfect_equality`**: Asserts $\mathcal{J}([0.8, 0.8, 0.8, 0.8]) = 1.0$.
10. **`test_jains_extreme_inequality`**: Asserts $\mathcal{J}([1.0, 0.0, 0.0, 0.0]) \le 0.35$.
11. **`test_jains_range_always_valid`**: Runs 30 randomized trials ensuring $0 \le \mathcal{J} \le 1.0$.
12. **`test_jains_empty`**: Returns $\mathcal{J} = 0.0$ for empty lists without raising division-by-zero exceptions.
13. **`test_fairness_policy_jains_index_acceptable`**: Asserts that the Fairness policy maintains $\mathcal{J} \ge 0.60$ under competing workloads.

### 2.3 Class: `TestPriority` (4 Tests)
Validates multi-criteria priority scoring formulas and weighting logic.

14. **`test_emergency_higher_than_standard`**: Confirms Emergency category vehicles receive higher priority scores than Standard category vehicles under identical arrival conditions.
15. **`test_shorter_window_higher_urgency`**: Verifies urgency score decays inversely with remaining time to departure.
16. **`test_score_has_all_factors`**: Asserts composite priority score dictionary contains all required sub-factors (`urgency_score`, `energy_need_score`, `waiting_score`, `category_score`).
17. **`test_fcfs_score_equals_waiting_time`**: Confirms FCFS policy priority score depends solely on waiting duration.

### 2.4 Class: `TestPolicyComparison` (3 Tests)
Validates multi-policy execution and queue handling.

18. **`test_all_policies_run_without_error`**: Runs FCFS, Urgency, and Fairness policies sequentially on identical requests without throwing exceptions.
19. **`test_all_policies_return_sessions`**: Confirms all policies produce non-empty session allocations for valid workloads.
20. **`test_urgency_respects_priority_order`**: Asserts that higher-scoring requests receive charger assignments prior to lower-scoring requests under Urgency policy.

### 2.5 Class: `TestEdgeCases` (5 Tests)
Validates system resilience under extreme conditions.

21. **`test_empty_requests`**: Handles empty request lists gracefully without crashing.
22. **`test_all_chargers_offline`**: Validates behavior when 100% of campus chargers are marked offline.
23. **`test_single_vehicle_gets_charged`**: Verifies single-vehicle boundary condition.
24. **`test_grid_constraint_limits_total_energy`**: Asserts that a severe grid limit (e.g., 10 kW) caps total campus energy delivered.
25. **`test_metrics_keys_present`**: Ensures all 10 required metric keys are returned in output dictionaries.

---

## 3. Error Boundaries & Isolation Architecture

FairCharge implements a multi-layered error boundary strategy across FastAPI endpoints, Pydantic validation models, scheduling algorithms, and React UI components.

```
┌─────────────────────────────────────────────────────────────┐
│                    REACT FRONTEND LAYER                     │
│  • Component Error Boundaries (ErrorBanner.jsx)             │
│  • Axios HTTP Interceptors & Token Expiry Catchers         │
└──────────────────────────────┬──────────────────────────────┘
                               │ HTTP REST Requests
┌──────────────────────────────▼──────────────────────────────┐
│                    FASTAPI GATEWAY LAYER                    │
│  • Pydantic v2 Schema Field Validators (@field_validator)  │
│  • HTTP Exception Boundaries (401, 403, 404, 422)           │
│  • JWT Bearer Token Security Verification                   │
└──────────────────────────────┬──────────────────────────────┘
                               │ Internal Engine Calls
┌──────────────────────────────▼──────────────────────────────┐
│                   SCHEDULER ENGINE LAYER                    │
│  • Non-Silent Error Analysis Pipeline (error_analysis)     │
│  • Invalid Time Window & Zero-Energy Filtering              │
│  • Battery SoC Minimum Reserve Floor (20% Protection)       │
└─────────────────────────────────────────────────────────────┘
```

### 3.1 Schema Validation Boundaries (Pydantic v2)
- **`departure_after_arrival`**: Rejects requests where `departure_time <= arrival_time` with HTTP 422 Unprocessable Entity.
- **`valid_priority`**: Rejects invalid priority strings outside `standard`, `priority`, or `emergency`.
- **`gt=0` Constraints**: Enforces positive battery capacity, max charging power, and required energy.

### 3.2 Security & Authentication Boundaries
- **JWT Signature Verification**: HMAC-SHA256 signature checking on Bearer tokens in `backend/core/security.py`.
- **Expired Token Isolation**: Automatically returns HTTP 401 Unauthorized with `WWW-Authenticate: Bearer` header.

### 3.3 Non-Silent Scheduler Error Pipeline (`error_analysis`)
Rather than silently dropping unfulfilled or partial requests, the scheduling engine captures detailed diagnostic records in the `error_analysis` list:

```json
{
  "request_id": "REQ-0042",
  "vehicle_id": "EV-042",
  "reason": "impossible request: required energy exceeds max deliverable before departure",
  "classification": "insufficient_time",
  "required_kwh": 75.0,
  "delivered_kwh": 22.5,
  "departure_time": "2024-03-11T12:00:00",
  "max_possible_kwh": 22.5
}
```

### 3.4 React UI Error Boundaries (`ErrorBanner.jsx`)
- Catches network connection drops, API 500 errors, and missing token states without unmounting the main dashboard component tree.

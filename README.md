# FairCharge — Transparent Shared EV Charging Scheduler

**FairCharge** is an explainable, full-stack EV charging scheduler for commercial enterprise campuses. It prioritizes **fairness, departure urgency, and queue transparency** over simple energy cost minimization while strictly enforcing dynamic campus grid limits, solar generation profiles, battery energy storage reserves, and charger physical limits.

---

## 🌟 Key Features

- **Multi-Policy Engine**: Switch dynamically between **FCFS (First-Come-First-Served)**, **Urgency-First**, and **Fairness-First** policies.
- **Role-Based JWT Security**: Secure environment-variable-backed admin login and HMAC-SHA256 JWT Bearer token authentication (`backend/core/security.py`).
- **Dynamic Energy Economics**: Time-of-Use (ToU) electricity grid tariffs ($0.10 Off-Peak, $0.20 Mid-Peak, $0.35 On-Peak) and stochastic solar intermittency profiles (cloud ramps).
- **Explainable Decisions**: Every session receives an automated natural-language explanation (e.g., *"Scheduled at 08:30 due to departure in 2.5h with 35.0 kWh need. Category: Priority. Full 35.0 kWh delivered"*).
- **Hard Constraint Safety**: Guarantees zero charging before arrival or after departure, zero capacity overruns, and respects battery reserve limits (20% minimum reserve protection).
- **Admin Overrides & Audit Log**: Facilities managers can intervene with password/JWT protection and full audit trail logging.
- **Scenario Stress Testing**: 8 pre-configured campus operational stress tests (Normal, High Demand, Low Solar, Grid Constraint, Tight Departure, Battery Low, Charger Failure, Priority Override).
- **Interactive Dashboards**: Operational control center, Gantt timeline view, Jain's Fairness Index analytics, dynamic ToU tariff charts, and stakeholder feedback evaluation.

---

## 🗄️ Database Schema Reference (SQLAlchemy 2.0 ORM)

FairCharge uses SQLite with asynchronous SQLAlchemy 2.0 ORM models (`backend/models/db_models.py`):

| Table Name | Primary Key | Key Fields & Types | Description |
|---|---|---|---|
| **`campus_config`** | `id` (int) | `num_chargers` (int), `dc_chargers` (int), `dc_power_kw` (float), `battery_capacity_kwh` (float), `battery_min_reserve_pct` (float), `grid_limit_kw` (float), `active_policy` (str) | Campus infrastructure configuration & power limits |
| **`charging_requests`** | `id` (int) | `request_id` (str, unique), `vehicle_id` (str), `user_id` (str), `arrival_time` (datetime), `departure_time` (datetime), `required_energy_kwh` (float), `charger_type` (str), `priority_category` (str), `status` (str), `priority_score` (float) | Ingested EV charging demand requests |
| **`charging_sessions`** | `id` (int) | `session_id` (str, unique), `request_id` (str), `vehicle_id` (str), `charger_id` (str), `policy` (str), `start_time` (datetime), `end_time` (datetime), `planned_energy_kwh` (float), `explanation` (text), `is_fully_served` (bool), `is_admin_override` (bool) | Scheduled charging slot allocations with explanations |
| **`admin_overrides`** | `id` (int) | `override_id` (str, unique), `admin_id` (str), `admin_name` (str), `vehicle_id` (str), `request_id` (str), `reason` (text), `old_priority` (float), `new_priority` (float), `timestamp` (datetime) | Immutable audit trail for admin interventions |
| **`energy_data`** | `id` (int) | `timestamp` (datetime), `solar_generation_kw` (float), `campus_load_kw` (float), `battery_soc_kwh` (float), `grid_import_kw` (float), `ev_charging_load_kw` (float) | 96-slot daily campus energy generation & demand logs |
| **`experiment_results`** | `id` (int) | `experiment_id` (str), `policy` (str), `scenario` (str), `total_requests` (int), `fully_served` (int), `energy_delivery_rate` (float), `jains_fairness_index` (float), `avg_waiting_time_min` (float), `scheduling_time_ms` (float) | Benchmark comparison metric results |

---

## 🔌 REST API Endpoints Specification

Base URL: `http://localhost:8000/api`

| Method | Endpoint Path | Auth Required | Description / Payload |
|---|---|---|---|
| `POST` | `/api/admin/login` | None | Admin authentication endpoint. Returns HMAC-SHA256 JWT Bearer access token. |
| `POST` | `/api/charging/request` | None | Submit a new EV charging request with time window & energy requirements. |
| `GET` | `/api/charging/schedule` | None | Retrieve active & historical scheduled sessions with natural-language explanations. |
| `POST` | `/api/scheduler/run` | None | Trigger multi-policy scheduling engine on pending requests (`policy: FCFS/Urgency/Fairness`). |
| `GET` | `/api/vehicles` | None | List registered vehicles, user IDs, and request status summary. |
| `GET` | `/api/chargers` | None | Query status of campus AC & DC chargers (available, occupied, offline). |
| `GET` | `/api/energy` | None | Retrieve 96-slot energy profile with dynamic ToU grid tariffs & solar intermittency factors. |
| `POST` | `/api/admin/override` | Bearer / Env Pass | Perform manual vehicle priority override or charger re-assignment. Logs to audit trail. |
| `GET` | `/api/admin/audit-log` | Bearer / Admin | Query historical admin override audit trail records. |
| `GET` | `/api/metrics` | None | Retrieve aggregated policy benchmark metrics. |
| `POST` | `/api/simulation/scenario` | None | Run synthetic campus stress test scenario (e.g. `high_demand`, `cloudy`, `grid_constraint`). |
| `GET` | `/api/campus/config` | None | Retrieve active campus power limits, charger counts & battery storage settings. |
| `PUT` | `/api/campus/config` | Admin | Update campus power limits, grid import caps, or default scheduling policy. |
| `GET` | `/api/experiment/compare` | None | Retrieve scenario benchmark comparison results across FCFS, Urgency, and Fairness. |

---

## 🧪 Unit Testing & Error Boundaries Summary

Automated test suite (`tests/test_scheduler.py`): **25 / 25 tests passing (100% pass rate)**.

- **`TestHardConstraints` (8 tests)**: Arrival/departure bounds, zero energy rejection, charger offline recovery.
- **`TestFairness` (5 tests)**: Jain's Fairness Index bounds ($\mathcal{J} \in [0, 1]$), equality properties.
- **`TestPriority` (4 tests)**: Emergency category weightings, urgency decay curves.
- **`TestPolicyComparison` (3 tests)**: Multi-policy execution & priority sorting.
- **`TestEdgeCases` (5 tests)**: Grid limit enforcement, empty queue handling, single-vehicle bounds.

*For full technical breakdown, see [`docs/unit_testing_and_error_boundaries.md`](file:///d:/New%20folder/faircharge/docs/unit_testing_and_error_boundaries.md).*

---

## 🚀 Quick Start & Installation

```bash
# 1. Install dependencies
python -m pip install -r requirements.txt

# 2. Run automated test suite (25 passing)
python -m pytest tests/test_scheduler.py -v

# 3. Generate 1,000 request synthetic dataset
python -m data.generate_dataset

# 4. Run scenario benchmark experiments
python experiments/run_experiment.py

# 5. Start FastAPI backend server
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload

# 6. Start React frontend (in separate terminal)
cd frontend
npm install
npm run dev
```

- **Frontend App**: `http://localhost:5173`
- **API Docs (Swagger)**: `http://localhost:8000/docs`

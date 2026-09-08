# FairCharge — Requirements & Specification Document

## 1. System Overview
**FairCharge** is an explainable, transparent shared Electric Vehicle (EV) charging scheduler designed for commercial campuses and workplace environments. Unlike traditional EV charging systems that optimize purely for energy cost or operate on a naive First-Come-First-Served (FCFS) basis, FairCharge focuses on **fairness, urgency-aware allocation, transparent explanations, and administrative override capabilities** under campus grid and solar/battery constraints.

---

## 2. Functional Requirements (FR)

### FR-1: Request Intake & Pre-Validation
- **FR-1.1**: The system shall accept charging requests containing: `vehicle_id`, `user_id`, `arrival_time`, `departure_time`, `battery_capacity_kwh`, `initial_soc`, `required_energy_kwh`, `max_charging_power_kw`, `charger_type` (AC/DC), and `priority_category` (`standard`, `priority`, `emergency`).
- **FR-1.2**: The system shall perform real-time pre-validation checks:
  - Verify that `departure_time` > `arrival_time`.
  - Cap requested energy to the physical maximum battery headroom: `battery_capacity_kwh * (1 - initial_soc)`.
  - Flag impossible requests where `required_energy_kwh > window_hours * max_charging_power_kw` with explicit warnings.
  - Detect duplicate active requests for the same vehicle ID.

### FR-2: Multi-Policy Scheduling Engine
- **FR-2.1**: The system shall support three distinct scheduling policies:
  1. **FCFS (First-Come-First-Served)**: Schedules purely by request arrival time.
  2. **Urgency-First**: Prioritizes vehicles with impending departure times, high energy deficit, and elevated priority categories.
  3. **Fairness-First**: Incorporates historical allocation metrics and Jain's Fairness Index to prevent starvation of low-priority vehicles.
- **FR-2.2**: The scheduling engine shall discretize the timeline into 15-minute time slots (96 slots per 24-hour window).
- **FR-2.3**: The engine shall enforce hard constraints:
  - No vehicle receives charging prior to its `arrival_time`.
  - No vehicle receives charging after its `departure_time`.
  - Energy delivered per slot cannot exceed the charger's max power or vehicle's max charging rate.
  - Total campus power draw per slot cannot exceed the dynamic campus power limit or grid limit.

### FR-3: Transparent Explanations
- **FR-3.1**: For every scheduled session, the system shall generate a clear, natural-language explanation detailing:
  - Assigned charger and scheduled time slot.
  - Priority score and factors (urgency factor, energy need, waiting duration, category weighting).
  - Delivered energy vs requested energy (full delivery vs partial delivery rationale).

### FR-4: Administrative Control & Audit Logging
- **FR-4.1**: Admins shall be able to manually override session priorities, assign specific chargers, or re-order queues.
- **FR-4.2**: The system shall require admin authentication (`admin_id` + password).
- **FR-4.3**: Every admin action shall be recorded in an immutable audit log containing timestamp, admin identity, vehicle ID, old priority, new priority, and rationale.

### FR-5: Scenario & Experimentation Runner
- **FR-5.1**: The system shall execute 8 pre-configured scenario stress tests (Normal, High Demand, Low Solar, Grid Constraint, Tight Departure, Battery Low, Charger Failure, Priority Override).
- **FR-5.2**: The system shall collect benchmark metrics comparing FCFS, Urgency, and Fairness policies across all scenarios.

---

## 3. Non-Functional Requirements (NFR)

### NFR-1: Performance & Scalability
- **NFR-1.1**: The scheduling algorithm shall solve requests for up to 50 concurrent vehicles in under 500 ms.
- **NFR-1.2**: API response time for request submission and schedule querying shall remain under 100 ms.

### NFR-2: Explainability & Trust
- **NFR-2.1**: 100% of scheduled sessions must include an auto-generated explanation string explaining allocation decisions.
- **NFR-2.2**: Users must be notified of partial fulfillment reasons (e.g., campus capacity constraint vs insufficient time window).

### NFR-3: Reliability & Safety
- **NFR-3.1**: Zero hard constraint violations permitted under any policy or scenario.
- **NFR-3.2**: Battery minimum reserve limits (20% default) must be respected to avoid deep battery degradation.

---

## 4. Requirement Traceability Matrix

| Requirement | Module / Component | Verification Method |
|---|---|---|
| **FR-1.1, FR-1.2** | `backend/api/routes.py`, `backend/api/schemas.py` | Unit tests (`TestHardConstraints`) |
| **FR-2.1, FR-2.2, FR-2.3** | `backend/scheduler/fcfs.py`, `backend/scheduler/optimized.py` | Unit tests (`TestPolicyComparison`) |
| **FR-3.1** | `backend/scheduler/priority.py` | Unit tests (`TestPriority`) |
| **FR-4.1 - FR-4.3** | `backend/api/routes.py` (`/admin/override`) | API integration tests |
| **FR-5.1, FR-5.2** | `experiments/run_experiment.py` | Experiment execution script |
| **NFR-1.1** | `backend/scheduler/engine.py` | Benchmark timing logs (< 5 ms achieved) |
| **NFR-3.1** | `tests/test_scheduler.py` | Pytest test suite (25/25 passing) |

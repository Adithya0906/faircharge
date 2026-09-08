# FairCharge — REST API Documentation

Base URL: `http://localhost:8000/api`

---

## Endpoints

### 1. `POST /api/charging/request`
Submit a new EV charging request.
- **Request Body**:
  ```json
  {
    "vehicle_id": "EV-042",
    "user_id": "EMP-042",
    "arrival_time": "2024-03-11T08:00:00",
    "departure_time": "2024-03-11T17:00:00",
    "battery_capacity_kwh": 75.0,
    "initial_soc": 0.30,
    "required_energy_kwh": 35.0,
    "max_charging_power_kw": 22.0,
    "charger_type": "AC",
    "priority_category": "standard"
  }
  ```
- **Response**: `200 OK`
  ```json
  {
    "request_id": "REQ-7F9A1B2C",
    "vehicle_id": "EV-042",
    "status": "pending",
    "message": "Request REQ-7F9A1B2C submitted successfully.",
    "validation_warnings": []
  }
  ```

---

### 2. `GET /api/charging/schedule`
Retrieve active and historical scheduled sessions.
- **Query Params**: `policy` (optional), `vehicle_id` (optional)
- **Response**: List of scheduled session objects with full explanation strings.

---

### 3. `POST /api/scheduler/run`
Trigger the multi-policy scheduling engine on pending requests.
- **Request Body**:
  ```json
  {
    "policy": "urgency",
    "scenario": "normal"
  }
  ```
- **Response**: Metrics summary, session count, scheduling runtime in ms.

---

### 4. `POST /api/admin/override`
Admin manual priority override & charger re-assignment.
- **Request Body**:
  ```json
  {
    "admin_id": "admin",
    "admin_name": "Campus Manager",
    "admin_password": "admin123",
    "vehicle_id": "EV-042",
    "request_id": "REQ-7F9A1B2C",
    "reason": "Executive VIP meeting at 10 AM",
    "new_priority_score": 0.95
  }
  ```

---

### 5. `GET /api/admin/audit-log`
Retrieve admin override history.

---

### 6. `POST /api/simulation/scenario`
Execute stress test scenario benchmark (e.g., `high_demand`, `low_solar`, `grid_constraint`).

---

### 7. `GET /api/experiment/compare`
Retrieve stored policy comparison benchmarks across all scenarios.

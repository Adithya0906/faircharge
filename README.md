# FairCharge — Transparent Shared EV Charging Scheduler

**FairCharge** is a full-stack, explainable EV charging scheduler for commercial campuses. It prioritizes **fairness, departure urgency, and queue transparency** over simple energy cost minimization.

---

## Key Features

- **Multi-Policy Engine**: Switch dynamically between **FCFS (First-Come-First-Served)**, **Urgency-First**, and **Fairness-First** policies.
- **Explainable Decisions**: Every session receives an automated natural-language explanation (e.g., *"Scheduled at 08:30 due to departure in 2.5h with 35 kWh need"*).
- **Hard Constraint Safety**: Guarantees zero charging before arrival or after departure, zero capacity overruns, and respects battery reserve limits.
- **Admin Overrides & Audit Log**: Facilities managers can intervene with password protection (`admin123`) and full audit trail logging.
- **Scenario Stress Testing**: 8 pre-configured campus operational stress tests (Normal, High Demand, Low Solar, Grid Constraint, Tight Departure, Battery Low, Charger Failure, Priority Override).
- **Interactive Dashboards**: Operational control center, Gantt timeline view, Jain's Fairness Index analytics, and energy storage trends.

---

## Quick Start

### 1. Backend Server
```bash
# Install dependencies
python -m pip install -r requirements.txt

# Run automated tests (25 passing)
python -m pytest tests/

# Generate 1,000 request dataset
python -m data.generate_dataset

# Run 6-scenario benchmark experiments
python experiments/run_experiment.py

# Start FastAPI backend
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```
API Documentation: `http://localhost:8000/docs`

---

## Project Structure

```
faircharge/
├── backend/
│   ├── api/          # FastAPI REST endpoints & schemas
│   ├── models/       # SQLAlchemy 2.0 ORM database models
│   ├── scheduler/    # FCFS, Urgency, Fairness engines & Jain's index
│   └── simulation/   # Solar, battery, base load energy simulator
├── data/
│   ├── generate_dataset.py  # Synthesizes 1,000 realistic EV requests
│   └── generated/           # CSV/JSON datasets
├── docs/             # Requirements, Algorithm, Validation, Limitations, API
├── experiments/      # Benchmark comparison scripts & results
├── frontend/         # React + Vite + Tailwind + Recharts UI
└── tests/            # Automated test suite (25/25 passing)
```

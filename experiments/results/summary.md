# FairCharge Experiment Summary Report

## Core Principles & Target Metrics
- **Primary Goal**: Met charging needs with fair access to limited capacity (not energy cost minimization).
- **Target Metrics**:
  - Energy delivery rate >= 80% of feasible requests
  - Jain's Fairness Index >= 0.85 under fairness policy
  - Zero hard constraint violations
  - Clear priority explanations for every session

## Summary Results Table

| Scenario | Policy | Requests | Fully Served | Energy Delivery Rate | Jain's Index | Avg Wait (min) | Runtime (ms) |
|---|---|---|---|---|---|---|---|
| normal | fcfs | 20 | 16 | 81.8% | 0.8000 | 204.6 | 1.6 |
| normal | urgency | 20 | 12 | 61.9% | 0.6000 | 200.5 | 1.5 |
| normal | fairness | 20 | 12 | 61.9% | 0.6000 | 200.5 | 1.4 |
| high_demand | fcfs | 25 | 16 | 62.2% | 0.6400 | 195.0 | 1.4 |
| high_demand | urgency | 25 | 13 | 57.0% | 0.5200 | 203.4 | 1.6 |
| high_demand | fairness | 25 | 13 | 57.0% | 0.5200 | 203.4 | 1.6 |
| low_solar | fcfs | 20 | 16 | 81.8% | 0.8000 | 204.6 | 1.3 |
| low_solar | urgency | 20 | 12 | 61.9% | 0.6000 | 200.5 | 1.7 |
| low_solar | fairness | 20 | 12 | 61.9% | 0.6000 | 200.5 | 2.5 |
| grid_constraint | fcfs | 20 | 16 | 79.2% | 0.8000 | 210.6 | 1.5 |
| grid_constraint | urgency | 20 | 12 | 61.9% | 0.6000 | 200.5 | 1.8 |
| grid_constraint | fairness | 20 | 12 | 61.9% | 0.6000 | 200.5 | 1.4 |
| tight_departure | fcfs | 20 | 11 | 46.6% | 0.6683 | 205.5 | 1.1 |
| tight_departure | urgency | 20 | 8 | 57.2% | 0.6174 | 206.6 | 1.3 |
| tight_departure | fairness | 20 | 8 | 57.9% | 0.6174 | 219.9 | 1.3 |
| battery_low | fcfs | 20 | 16 | 81.8% | 0.8000 | 204.6 | 1.4 |
| battery_low | urgency | 20 | 12 | 61.9% | 0.6000 | 200.5 | 1.6 |
| battery_low | fairness | 20 | 12 | 61.9% | 0.6000 | 200.5 | 1.7 |

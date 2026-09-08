# FairCharge — System Limitations & Assumptions

## 1. Overview
FairCharge is a functional prototype built for commercial campus workplace EV charging scheduling. While mathematically sound and fully operational, several realistic limitations and engineering trade-offs apply.

---

## 2. Technical & Modeling Limitations

### 2.1 Charging Battery Degradation & Non-Linear Curves
- **Current Model**: Assumes constant charging power $P_{\text{max}}$ throughout the session up to target state of charge (SoC).
- **Reality**: Real EV battery management systems (BMS) taper charging power significantly above 80% SoC (CC-CV charging curve).

### 2.2 Solar Generation Forecasting
- **Current Model**: Uses a bell-curve solar profile with synthetic Gaussian noise.
- **Reality**: Real-world solar generation exhibits abrupt drops due to passing cloud cover requiring real-time sub-minute control loops.

### 2.3 Hardware Protocol Integration (OCPP)
- **Current Model**: Simulates charger states internally via API endpoints.
- **Reality**: Physical campus deployments require Open Charge Point Protocol (OCPP 1.6J/2.0.1) websockets to send remote start/stop commands to physical EVSE hardware.

### 2.4 Single-Campus Power Constraint
- **Current Model**: Optimizes for a single site/transformer node with static grid power limit.
- **Reality**: Large commercial enterprise campuses often feature multi-building microgrids with phase-balancing requirements.

---

## 3. Recommended Future Extensions
1. **OCPP 2.0.1 Driver**: Connect to actual physical hardware or simulated Steve/MaEVe OCPP brokers.
2. **Dynamic Tariff Integration**: Incorporate Time-of-Use (ToU) electricity tariffs to balance fairness with energy cost.
3. **Driver Mobile App (PWA)**: Push notifications when charging begins, completes, or gets re-allocated.

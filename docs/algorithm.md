# FairCharge — Algorithm & Optimization Specification

## 1. Overview
FairCharge implements a multi-policy scheduling engine designed for shared workplace EV charging. The core objective is **maximizing fair energy delivery** while respecting dynamic grid capacity, solar generation profiles, battery storage reserves, charger physical limits, and vehicle arrival/departure bounds.

---

## 2. Mathematical Formulation & Time Discretization

The operating timeline is discretized into uniform 15-minute time slots $t \in \{1, 2, \dots, T\}$, where slot duration $\Delta t = 0.25 \text{ hours}$.

### Decision Variables
For each vehicle request $i \in V$ and charger $c \in C$ at time slot $t$:
- $p_{i,c,t} \ge 0$: Charging power (kW) allocated to vehicle $i$ on charger $c$ at slot $t$.
- $x_{i,c,t} \in \{0, 1\}$: Binary variable indicating if vehicle $i$ is connected to charger $c$ at slot $t$.

---

## 3. Objective Function

The scheduling objective balances priority score, urgency, and fairness:

$$\max \sum_{i \in V} \sum_{c \in C} \sum_{t \in T} S_i \cdot p_{i,c,t} \cdot \Delta t$$

where $S_i \in [0, 1]$ is the composite priority score computed for request $i$.

---

## 4. Multi-Criteria Priority Scoring Formula

The priority score $S_i$ for a request under policy $P \in \{\text{Urgency}, \text{Fairness}, \text{FCFS}\}$ is calculated as:

$$S_i = w_u \cdot U_i + w_e \cdot E_i + w_w \cdot W_i + w_c \cdot C_i + w_f \cdot F_i$$

### Score Component Definitions:
1. **Urgency Score ($U_i$)**:
   $$U_i = 1 - \min\left(1.0, \frac{T_{\text{dep}, i} - t_{\text{now}}}{T_{\text{max\_window}}}\right)$$
2. **Energy Need Score ($E_i$)**:
   $$E_i = \min\left(1.0, \frac{E_{\text{req}, i}}{E_{\text{cap}, i}}\right)$$
3. **Waiting Time Score ($W_i$)**:
   $$W_i = \min\left(1.0, \frac{t_{\text{now}} - t_{\text{req}, i}}{T_{\text{max\_wait}}}\right)$$
4. **Category Score ($C_i$)**:
   $$C_i = \begin{cases} 1.0 & \text{if category = Emergency} \\ 0.6 & \text{if category = Priority} \\ 0.2 & \text{if category = Standard} \end{cases}$$
5. **Fairness Adjustment ($F_i$)**:
   $$F_i = 1.0 - H_i$$
   where $H_i \in [0, 1]$ represents the user's historical satisfaction ratio.

### Policy Weights Matrix ($w_u, w_e, w_w, w_c, w_f$):

| Policy | Urgency ($w_u$) | Energy Need ($w_e$) | Wait Time ($w_w$) | Priority Category ($w_c$) | Fairness Adj ($w_f$) |
|---|---|---|---|---|---|
| **FCFS** | 0.0 | 0.0 | 1.0 | 0.0 | 0.0 |
| **Urgency-First** | 0.40 | 0.30 | 0.20 | 0.10 | 0.0 |
| **Fairness-First** | 0.20 | 0.20 | 0.30 | 0.10 | 0.20 |

---

## 5. Hard Constraints

1. **Window Boundaries**:
   $$p_{i,c,t} = 0 \quad \forall t < t_{\text{arr}, i} \quad \text{or} \quad t \ge t_{\text{dep}, i}$$
2. **Energy Ceiling**:
   $$\sum_{c \in C} \sum_{t \in T} p_{i,c,t} \cdot \Delta t \le E_{\text{req}, i}$$
3. **Charger Power Rating**:
   $$p_{i,c,t} \le \min(P_{\text{charger}, c}, P_{\text{vehicle}, i})$$
4. **Charger Exclusivity**:
   $$\sum_{i \in V} x_{i,c,t} \le 1 \quad \forall c \in C, \forall t \in T$$
5. **Campus Power Capacity Limit**:
   $$\sum_{i \in V} \sum_{c \in C} p_{i,c,t} \le P_{\text{solar}, t} + P_{\text{battery\_max}, t} + P_{\text{grid\_limit}, t} - P_{\text{base\_load}, t}$$

---

## 6. Jain's Fairness Index Formulation

To measure satisfaction equity across all $N$ vehicles:

$$\mathcal{J}(x_1, x_2, \dots, x_N) = \frac{\left( \sum_{i=1}^N x_i \right)^2}{N \sum_{i=1}^N x_i^2}$$

where $x_i = \frac{E_{\text{delivered}, i}}{E_{\text{required}, i}} \in [0, 1]$ is the satisfaction ratio for vehicle $i$.

- $\mathcal{J} = 1.0$: Complete equality across all vehicles.
- $\mathcal{J} = 1/N$: Severe inequality (only 1 vehicle served, others starved).

---

## 7. Natural Language Explanation Engine

The explanation builder inspects allocation outputs and generates human-readable rationales:

```python
# Example generated explanation string:
"Vehicle EV-042 scheduled at 08:30 under urgency-first policy (priority score: 0.8420). "
"Departure in 2.5h, requiring 35.0 kWh. Urgency: 0.79, Energy need: 0.47, Category: priority. "
"Charger CHARGER-DC-01 assigned. Full 35.0 kWh delivered before departure."
```

If a partial delivery occurs, the failure reason is explicitly appended:
```python
"Partial delivery: 22.5/40.0 kWh delivered due to campus power capacity constraints."
```

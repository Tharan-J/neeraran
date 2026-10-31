# NEERARAN (நீர்Aran)
### Enterprise AI Water Resilience and Smart Resource Management Platform
> *“Every drop accounted for.”*

NEERARAN is an enterprise-style autonomous water utility operations platform for institutional campuses, municipal zones, and industrial facilities. Built for **TCS Tech Day (Challenge 12: AI for Water Resilience & Smart Resource Management)**.

---

## 5-Line Quick Start

```bash
git clone <repo-url> && cd neeraran
cp .env.example .env
PYTHONPATH=. python3 apps/api/db/seeds.py
npm install --prefix apps/web && npm run build --prefix apps/web
npm run dev
```
Open `http://localhost:5173` in your browser.

---

## 5-Laptop Distributed Demonstration Architecture

NEERARAN natively supports a five-laptop distributed network topology:

- **Laptop 1 (Central Control Center)**:
  Runs the FastAPI Backend, SQLite system-of-record, and Vite Frontend:
  ```bash
  # Start central backend (accessible to other laptops on the local network)
  python3 -m uvicorn apps.api.main:app --host 0.0.0.0 --port 8000
  ```
  *(Find Laptop 1's local IP address, e.g., `192.168.1.50`)*

- **Laptop 2 (Source 1: Water Supply & Reservoirs)**:
  ```bash
  python3 apps/api/sim/sources.py --source 1 --url http://192.168.1.50:8000
  ```
  Generates Cauvery bulk supply, sump levels, borewell yields, and pump status.

- **Laptop 3 (Source 2: Building Consumption)**:
  ```bash
  python3 apps/api/sim/sources.py --source 2 --url http://192.168.1.50:8000
  ```
  Generates 20 block ultrasonic meter readings, diurnal rhythms, and minimum night flow.

- **Laptop 4 (Source 3: Infrastructure Telemetry)**:
  ```bash
  python3 apps/api/sim/sources.py --source 3 --url http://192.168.1.50:8000
  ```
  Generates pipeline node pressures, overhead tank levels, and sensor anomalies.

- **Laptop 5 (Source 4: Operations & Environment)**:
  ```bash
  python3 apps/api/sim/sources.py --source 4 --url http://192.168.1.50:8000
  ```
  Generates weather forecasts, temperature, resident complaints, and maintenance logs.

---

## Demonstration Safe Mode

During live presentations with unpredictable network conditions, press **Shift + D** at any time to activate **Demo Safe Mode**. The application continues operating seamlessly from cached offline datasets in `/public/fallback` without throwing unhandled exceptions.

---

## The Seven TCS AI Engineering Capabilities

1. **Reason across sources**: Fuses bulk supply, tanks, block meters, pipe pressure, acoustic sensors, and complaints.
2. **Plan multiple steps**: Formulates versioned ordered plans with tool dispatches, expected impacts, and rollback procedures.
3. **Act through enterprise tools**: Dispatches `create_cmms_ticket`, `set_valve`, `set_pump_schedule`, `draft_advisory`, and `notify`.
4. **Verify against evidence**: Dedicated Verifier rejects ungrounded claims and mandates evidence citations `[EVID-XXXX]`.
5. **Adapt dynamically**: Scenario injector takes natural language scenarios from the jury and executes real-time replanning.
6. **Maintain human control**: Consequential interventions affecting potable supply require Estate Admin approval.
7. **Evaluate against ground truth**: Computes F1 (96.0%), localization (97.8%), sMAPE (8.4%), and 0 vulnerable violations.

---

## Testing

Run the automated backend test suite:
```bash
PYTHONPATH=. pytest tests/ -v
```

---

## Documentation Links

- [System Master Specification](/docs/MASTER.md)
- [System Architecture & Reasoning Flow](/docs/ARCHITECTURE.md)
- [API Specification & Endpoints](/docs/API.md)
- [Evaluation Formulas & Baselines](/docs/EVAL.md)
- [5-Minute Jury Demonstration Script & 5 Slides](/docs/DEMO.md)
- [Known Limitations & Assumptions](/docs/KNOWN_LIMITS.md)

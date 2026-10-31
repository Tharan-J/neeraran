# NEERARAN System Architecture

## 1. High-Level Architecture Overview

NEERARAN is an enterprise-grade AI Water Resilience and Smart Resource Management operational platform designed for institutional campuses, industrial facilities, and municipal utility networks.

The architecture strictly follows the closed-loop operational flow:
```
[Distributed Ingestion (Laptops 1-5)]
                │
                ▼
      ┌──────────────────┐
      │  Monitor Agent   │  ── Data Quality, Dropout & Flat-line checks
      └──────────────────┘
                │
                ▼
      ┌──────────────────┐
      │  Detector Agent  │  ── Anomaly Model + Night Flow z-score (>=2 signals)
      └──────────────────┘
                │
                ▼
      ┌──────────────────┐
      │ Localizer Agent  │  ── Pipe graph, Mass Balance, Hydraulic gradient
      └──────────────────┘
                │
                ▼
      ┌──────────────────┐
      │ Forecaster Agent │  ── 7-day Demand & 72h Tank Depletion (80% band)
      └──────────────────┘
                │
                ▼
      ┌──────────────────┐
      │ Prioritizer Agent│  ── Transparent mathematical score breakdown
      └──────────────────┘
                │
                ▼
      ┌──────────────────┐
      │ Optimizer Agent  │  ── SciPy linprog (0 vulnerable violations)
      └──────────────────┘
                │
                ▼
      ┌──────────────────┐
      │  Verifier Agent  │  ── Grounding: Validates Evidence IDs & checks
      └──────────────────┘
                │
       [Consequential Gate]
                │
      ┌──────────────────┐
      │  Human Control   │  ── Estate Admin sign-off (Approvals Queue)
      └──────────────────┘
                │
                ▼
      ┌──────────────────┐
      │Interventor/Measur│  ── Enterprise SCADA & CMMS tools + Impact Error
      └──────────────────┘
```

## 2. The Seven TCS AI Engineering Capabilities

| # | Capability | Implementation in NEERARAN |
|---|---|---|
| **1** | **Reason across multiple sources** | Fuses bulk Cauvery inlet meters, borewell yields, tank level sensors, block smart meters, sub-header pressure transducers, acoustic leak sensors, and weather forecasts. |
| **2** | **Plan multiple steps toward an objective** | Generates versioned, ordered plans: CMMS maintenance ticket -> throttling valves -> rescheduling VFD pumps -> drafting public advisories -> verified rollback step. |
| **3** | **Act through tools, APIs & functions** | Exposes simulated enterprise tool suite (`create_cmms_ticket`, `set_valve`, `set_pump_schedule`, `draft_advisory`, `notify`) with idempotency and audit logs. |
| **4** | **Verify conclusions against evidence** | Dedicated Verifier validates evidence citations `[EVID-XXXX]`, checks numerical consistency, and downgrades uncorroborated single-signal alerts. |
| **5** | **Adapt when circumstances change** | Scenario replanning engine handles unexpected conditions (heatwaves, pipe bursts, droughts) by re-running affected agents and computing before/after diffs. |
| **6** | **Maintain human control over consequential decisions** | Consequential operations (valve throttling, pump rescheduling, hostel restrictions) are queued for Estate Admin approval; Viewers receive HTTP 403. |
| **7** | **Evaluate performance using measurable metrics** | Computes precision, recall, F1, MTTD, top-1/top-3 localization, sMAPE vs naive baseline, and vulnerable minimum supply violations (=0) against hidden simulator ground truth. |

## 3. Technology Stack

- **Frontend**: React 18, Vite, TypeScript, Tailwind CSS with strict custom tokens, Framer Motion, Recharts.
- **Backend**: Python 3.14 / FastAPI, Pydantic v2, SQLAlchemy 2, SQLite (`neeraran.db`).
- **Optimization**: SciPy `linprog` (Highs simplex & interior point solver).
- **ML Services**: Scikit-Learn `IsolationForest`, Holt-Winters exponential smoothing, multi-horizon depletion trajectory.
- **Generative AI**: Google Gemini API via official `google.genai` SDK with deterministic template/regex fallback.
- **Real-Time Delivery**: Server-Sent Events (SSE) streaming on `/api/v1/stream`.

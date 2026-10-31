# NEERARAN Jury Demonstration Guide & 5-Slide Presentation Outline

## 1. Five-Minute Live Demonstration Script (Step-by-Step)

### Minute 0:00 - 0:20 | Landing Page & Identity
1. Show the landing page with the water-filled **நீர்** (Neer) glyph and the headline: *"Your all-in-one fortress for smarter campus water"*.
2. Scroll through the Seven-Step Operational Loop.
3. Click **"Open control center"** to trigger the water-rise transition.

### Minute 0:20 - 0:40 | Viewer Gate & RBAC Enforcement
1. On the login gate, click **"Enter as Viewer"**.
2. Show the Overview dashboard with the **Warden Lens** active.
3. Attempt to approve an action: show that the Approve buttons are disabled and label reads *"Awaiting Estate Admin"*.
4. Emphasize: *"A viewer can inspect telemetry and advisories, but cannot dispatch physical valve commands."*

### Minute 0:40 - 1:40 | Switch to Admin & Detect Fissure
1. Switch role to **Estate Admin** in the navbar.
2. In Simulation settings, set speed to **20x** and trigger the seeded **"Hostel night leak"**.
3. Point out the KPI update: Active Leaks turns coral (1 verified).
4. Navigate to `/app/map`: show the **pulsing coral leak marker** at Hostel Block A.
5. Click on the marker to open the **Side Drawer**:
   - Open the **Why tab**: read the plain-language reasoning derived from telemetry.
   - Click the evidence chips `[EVID-101]` and `[EVID-102]` to view the underlying night flow surge (58.4 L/min vs 12 L/min baseline) and sub-header depressurization (2.3 bar).

### Minute 1:40 - 2:30 | Multi-Step Reasoning & Optimization
1. Navigate to `/app/agents`:
   - Walk through the 7-step timeline trace (Monitor -> Detect -> Localize -> Forecast -> Prioritize -> Optimize -> Verify -> Intervene).
   - Point out execution latencies (all under 25 ms).
   - Show the Optimizer's mathematical plan: throttling the feeder valve to 40% while preserving the 85% potable water baseline for all 650 hostel residents (**0 vulnerable violations**).

### Minute 2:30 - 3:00 | Human Control & Approvals
1. Navigate to `/app/approvals`:
   - Show pending approval: *"Throttle Feeder Valve on Hostel A"*.
   - Point out the **Equity Impact Check** and the **Rollback Procedure**.
   - Click **Approve**: show the toast confirmation and explain that the SCADA tool command has executed and written an immutable entry to the audit log.

### Minute 3:00 - 3:45 | Measurable Proof & Benchmarks
1. Navigate to `/app/evaluation`:
   - Click **"Run Benchmark (20 Scenarios)"**.
   - Show the progress bar.
   - Walk through the live metrics: F1-Score (96.0% vs 79.5% baseline), Top-3 Localization (97.8%), sMAPE (8.4% vs 24.6% naive), and Vulnerable Violations (**0**).

### Minute 3:45 - 5:00 | Jury Surprise Scenario (Adaptability)
1. Navigate to `/app/simulation`:
   - Ask the jury for an unseen emergency scenario (e.g., *"Heatwave for 4 days with Borewell 1 pump tripping"*).
   - Type or paste the sentence into the Jury Free-Text Scenario Injector.
   - Click **"Parse Scenario with Gemini"**: show the structured Confirmation Card.
   - Click **"Run & Adapt Plan"**: show the **What Changed Panel**, displaying the agents rerun, updated prioritized repair sequence, and the recovery countdown.

---

## 2. Five-Slide Presentation Outline (TCS Tech Day)

### Slide 1: The Problem & Stakeholders
- **Title**: *Water Resilience Crisis at Campus & City Scale*
- **Challenge**: Physical loss, aging distribution infrastructure, and sudden climate droughts threaten institutional resilience.
- **Why Dashboards Fail**: Dashboards only display historical consumption; they cannot diagnose whether elevated flow is a fissure or students showering, and they cannot orchestrate field interventions.
- **Stakeholders**: Estate Offices, Wardens, Maintenance Crews, and Campus Inhabitants.

### Slide 2: AI Architecture & Seven Operational Capabilities
- **Title**: *From Sensor Ticks to Verifiable Decisions*
- **Architecture Diagram**: Input -> Ingestion -> 7 Agents -> Tools -> SQLite System of Record -> Human Approval Gate -> Output.
- **The Seven Capabilities**: Reasoning across sources, Multi-step planning, Tool execution, Evidence verification, Dynamic adaptation, Human-in-the-loop control, and Ground-truth evaluation.

### Slide 3: Working Prototype & Digital Twin
- **Title**: *A Living Digital Twin in Sathyamangalam*
- **System Dimensions**: 20 campus blocks, 4 overhead tanks, central ground reservoir, 2 deep aquifer borewells, Cauvery municipal inlet.
- **Screenshots / Highlights**: GIS Map with localized candidate cones, Bento Overview dashboard with 5 live KPIs, and the 7-agent execution trace timeline.

### Slide 4: Measurable Proof, Responsible AI & Guardrails
- **Title**: *Grounded Proof: Zero Hallucinations, Zero Vulnerability Violations*
- **Evaluation Numbers**:
  - Detection F1: 96.0% (vs 79.5% baseline)
  - Forecasting sMAPE: 8.4% (vs 24.6% naive baseline)
  - Equity Violations: 0 across all benchmark regimes
- **Responsible AI Pillars**: Privacy by design (block-level aggregation), immutable audit log, and role-based access.

### Slide 5: Dynamic Adaptation & Scale to Municipalities
- **Title**: *Adapting to the Unforeseen: From Campuses to Smart Cities*
- **Surprise Scenario Replay**: Natural language jury parser to typed SCADA events.
- **Scalability**: Hierarchical network schema (Organization -> District -> City -> Zone -> Facility) allows NEERARAN to scale from educational campuses to industrial corridors and metropolitan water utilities.

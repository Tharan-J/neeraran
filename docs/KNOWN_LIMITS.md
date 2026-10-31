# NEERARAN Known Limitations and System Assumptions

## 1. Ground Truth and Synthetic Twin
- The campus water network is modelled as a synthetic digital twin inspired by engineering institutions in South India (Erode / Sathyamangalam footprint).
- All sensor readings and fault signatures are generated using physical hydraulic mass-balance equations ($V_{\text{next}} = V_{\text{current}} + Q_{\text{in}}\Delta t - Q_{\text{out}}\Delta t$) and diurnal curves.

## 2. Sensor Quality & Contamination Boundary
- The current digital twin is instrumented with flow meters, level transducers, pressure gauges, and weather telemetry.
- **Water Contamination Boundary**: In the event of a resident report alleging contamination (odor or discoloration), NEERARAN explicitly recognizes the absence of chemical/biological water-quality spectrophotometers. The system explicitly refrains from pretending to detect bacteria or chemical toxins; instead, it flags a High-Priority Quality Incident and immediately generates a CMMS work order for an on-site manual grab sample and lab test.

## 3. Human Authority Over Consequential Acts
- NEERARAN is an operational decision-support and automation orchestrator, not an autonomous dictator.
- Consequential interventions (throttling feeder valves to residential blocks, altering pump schedules, or issuing boil-water advisories) strictly require explicit Estate Admin digital sign-off.
- The AI cannot bypass permissions or execute consequential tools without authorization.

## 4. Hardware Connectivity in Multi-Laptop Demonstration
- For the distributed 5-laptop demonstration, all machines must reside on the same local subnet or hotspot.
- If Wi-Fi or API server connectivity drops, client laptops gracefully cache unsent readings and retry with exponential backoff.
- On the central laptop, **Shift+D** activates Demo Safe Mode, which serves all operational views from local offline datasets (`/public/fallback`).

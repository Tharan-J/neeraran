# NEERARAN API Specification

Base URL: `http://localhost:8000` (or `http://<SERVER_IP>:8000` on local area network)

All endpoints accept and return JSON unless specified otherwise.
Role authorization header: `X-User-Role: admin` or `X-User-Role: viewer`.

---

## 1. Telemetry Ingestion

### `POST /api/v1/telemetry`
Ingests distributed telemetry readings.
- **Headers**:
  - `X-Source-ID: source_1`
  - `X-API-Key: neeraran-source-1-supply-secret`
- **Request Body**:
```json
{
  "events": [
    {
      "source_id": "source_1",
      "asset_id": "SUMP-CENTRAL",
      "timestamp": "2026-10-31T03:15:00Z",
      "metric": "level_m",
      "value": 3.75,
      "unit": "m"
    }
  ]
}
```
- **Response**: `201 Created`
```json
{
  "status": "success",
  "ingested_events": 1
}
```

---

## 2. Digital Twin Assets

### `GET /api/v1/assets`
Returns all registered campus blocks, storage tanks, borewells, and pipeline segments.

### `GET /api/v1/assets/{asset_id}`
Returns asset hierarchy metadata and latest validated telemetry readings.

### `GET /api/campus`
Returns GeoJSON FeatureCollection of campus polygons and pipe line networks.

---

## 3. Incidents & Evidence

### `GET /api/v1/incidents`
Returns all open, investigating, and resolved incidents ranked by priority score.

### `GET /api/v1/incidents/{incident_id}`
Returns incident details, plain-language Why block, and attached evidence.

### `GET /api/v1/incidents/{incident_id}/evidence`
Returns all supporting and corroborating evidence items `[EVID-XXXX]`.

---

## 4. Human Control & Approvals

### `GET /api/v1/approvals`
Lists all pending and resolved consequential action approvals.

### `POST /api/v1/approvals/{id}`
Approve or reject a consequential action. **Admin only** (Viewers receive HTTP 403).
```bash
curl -X POST http://localhost:8000/api/v1/approvals/APP-01 \
  -H "Content-Type: application/json" \
  -H "X-User-Role: admin" \
  -d '{"decision": "approved", "note": "Verified by Estate Office"}'
```

---

## 5. Simulation & Re-Planning

### `POST /api/v1/simulation/scenarios`
Loads a preset benchmark scenario and runs dynamic replanning.
```bash
curl -X POST http://localhost:8000/api/v1/simulation/scenarios \
  -H "Content-Type: application/json" \
  -H "X-User-Role: admin" \
  -d '{"scenario_name": "Hostel night leak"}'
```

### `POST /api/v1/simulation/events`
Injects free-text natural language or typed scenario event.
```json
{
  "scenario_text": "Hostel Block A 2nd floor pipe fissure losing 60 liters per min"
}
```

---

## 6. Real-Time Streaming

### `GET /api/v1/stream`
Server-Sent Events (SSE) stream delivering real-time simulator state every tick.
```bash
curl -N http://localhost:8000/api/v1/stream
```

---

## 7. Evaluation & Benchmark

### `GET /api/v1/evaluation`
Returns live metrics computed against ground truth.

### `POST /api/v1/evaluation/benchmark`
Runs 20 seeded scenario benchmark.

# 🚀 SOAR Platform Backend

A production-style backend for a **SOAR (Security Orchestration, Automation, and Response)** platform built using FastAPI, Celery, PostgreSQL, and Docker.

---

## 📌 Overview

This project automates the processing and response to security alerts.
It ingests alerts from external systems, processes them asynchronously using playbooks, and stores execution results for auditing and analysis.

---

## 🧠 Key Features

* 🔹 **Alert Ingestion API** – Receive alerts via REST endpoint
* 🔹 **Incident Management** – Store alerts as structured incidents
* 🔹 **Asynchronous Processing** – Background task execution using Celery
* 🔹 **Playbook Automation** – Execute response workflows on incidents
* 🔹 **Execution Tracking** – Full audit logs for every playbook run
* 🔹 **Scalable Architecture** – Redis-based message queue
* 🔹 **Dockerized Setup** – Easy deployment using Docker Compose

---

## 🏗️ Architecture

```text
Client → FastAPI → PostgreSQL → Celery Worker → Playbook Engine → Database
                ↓
              Redis (Message Broker)
```

---

## ⚙️ Tech Stack

* **Backend:** FastAPI (Python)
* **Database:** PostgreSQL + SQLAlchemy
* **Migrations:** Alembic
* **Task Queue:** Celery
* **Broker:** Redis
* **Containerization:** Docker & Docker Compose

---

## 📂 Project Structure

```
backend/
├── app/
│   ├── api/          # API routes
│   ├── core/         # Config & settings
│   ├── models/       # Database models
│   ├── schemas/      # Pydantic schemas
│   ├── services/     # Business logic
│   ├── tasks/        # Celery tasks
│   └── main.py       # Entry point
├── alembic/          # Database migrations
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```

---

## 🔄 Workflow

1. Alert is sent to `/api/v1/alerts`
2. Stored as an **Incident** in PostgreSQL
3. Celery enqueues a background task
4. Worker processes the incident
5. Playbook is executed
6. Results and logs are stored in `PlaybookExecution`

### Simulation Workflow

1. Simulation is triggered via `/api/v1/simulations/{simulation_type}`
2. Synthetic alerts are converted into incidents
3. Incidents are queued with Celery
4. Worker executes the mapped SOAR playbook
5. Result metadata is persisted in `incident.playbook_result`
6. Aggregated state is available via `/api/v1/simulations/summary`

Contracted flow value returned by simulation endpoints:

```json
"pipeline_flow": ["simulation", "incident", "queue", "playbook", "result"]
```

---

## 🚀 Getting Started

### 🔧 Prerequisites

* Docker
* Docker Compose

---

### ▶️ Run the Project

```bash
docker compose up --build -d
```

---

### 📦 Run Migrations

```bash
docker compose exec api alembic upgrade head
```

---

### 🧪 Test API

```bash
POST http://localhost:8000/api/v1/alerts
```

### Simulation Endpoints

```http
POST /api/v1/simulations/{simulation_type}?count=10
GET  /api/v1/simulations/summary?limit=10
```

Allowed `simulation_type` values:

- `brute-force`
- `phishing`
- `malware`
- `network-anomaly`
- `all`

---

## 📘 API Contract (Phase 3)

Simulation API responses now include contract metadata so frontend and clients can rely on stable fields.

### Contract Fields

- `contract_version`: fixed to `v1`
- `pipeline_flow`: fixed ordered list of the async processing path
- `lifecycle_states`: explicit allowed values for status fields

### Lifecycle States

```json
{
  "incident_status": ["open", "closed", "failed"],
  "playbook_status": ["pending", "running", "success", "failed"]
}
```

### Example: POST /api/v1/simulations/brute-force

```json
{
  "success": true,
  "message": "Simulation executed and incidents queued for playbook processing",
  "data": {
    "contract_version": "v1",
    "pipeline_flow": ["simulation", "incident", "queue", "playbook", "result"],
    "lifecycle_states": {
      "incident_status": ["open", "closed", "failed"],
      "playbook_status": ["pending", "running", "success", "failed"]
    },
    "simulation_type": "brute-force",
    "requested_count": 10,
    "alerts_generated": 1,
    "incidents_created": 1,
    "incidents": []
  }
}
```

### Example: GET /api/v1/simulations/summary

```json
{
  "success": true,
  "message": "Simulation incident summary fetched successfully",
  "data": {
    "contract_version": "v1",
    "pipeline_flow": ["simulation", "incident", "queue", "playbook", "result"],
    "lifecycle_states": {
      "incident_status": ["open", "closed", "failed"],
      "playbook_status": ["pending", "running", "success", "failed"]
    },
    "source": "option2_simulation",
    "total_incidents": 32,
    "severity_breakdown": {"critical": 24, "high": 8},
    "playbook_status_breakdown": {"success": 32},
    "incident_status_breakdown": {"closed": 32},
    "recent_count": 5,
    "recent_incidents": []
  }
}
```

### Degraded/Fault Interpretation

`playbook_result` may include operational metadata for resilience and debugging:

- `execution_duration_ms`
- `degraded_threat_intel`
- `provider_errors`

When API keys are not configured, execution can still succeed while `degraded_threat_intel` is `true` and provider-specific reasons appear in `provider_errors`.

---

## 📊 Example Use Case

* Detect phishing email
* Extract IP
* Check reputation (e.g., VirusTotal)
* Block IP if malicious
* Log all actions

---

## ⚠️ Current Limitations

* Frontend UI not included
* Threat intel quality depends on configured API keys and provider availability
* Simulator endpoint throughput should be rate-limited for production exposure

---

## 🔮 Future Improvements

* Role-based access control (RBAC)
* Web dashboard for monitoring
* Advanced scheduling & automation

---

## ✅ Phase 4 Release Readiness

Phase 4 assets are included for deployment-safe operation and handoff:

1. CI pipeline
  - File: `.github/workflows/backend-ci.yml`
  - Runs critical lint checks, tests, and containerized smoke validation.
2. Operations runbook
  - File: `backend/RUNBOOK.md`
  - Covers start, migration, health checks, logs, rollback, and shutdown.
3. Demo data seeding utility
  - File: `backend/scripts/seed_demo_data.py`
  - Seeds simulation incidents and prints a summary snapshot.

### Phase 4 Commands

```bash
cd backend
python -m pytest
python scripts/seed_demo_data.py --base-url http://localhost:8000 --count 20
```

---

## 👨‍💻 Author

* Your Name

---

## ⭐ Contribution

Feel free to fork, improve, and contribute!

---

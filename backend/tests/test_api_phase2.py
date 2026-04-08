from __future__ import annotations

from datetime import datetime, timezone

import pytest

from app.services.playbook_service import execute_playbook_for_incident


def test_health_endpoint(client):
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert "X-Correlation-ID" in response.headers
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("X-Frame-Options") == "DENY"
    assert response.headers.get("Referrer-Policy") == "no-referrer"
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["status"] == "ok"


def test_validate_production_safety_rejects_insecure_defaults(monkeypatch):
    from app.core import config as app_config

    monkeypatch.setattr(app_config.settings, "ENVIRONMENT", "production")
    monkeypatch.setattr(app_config.settings, "DEBUG", True)
    monkeypatch.setattr(app_config.settings, "JWT_SECRET", "change-me-in-production-min-32-chars")
    monkeypatch.setattr(app_config.settings, "BACKEND_CORS_ORIGINS", "*")

    with pytest.raises(RuntimeError):
        app_config.validate_production_safety()


def test_production_safety_issues_empty_for_safe_production(monkeypatch):
    from app.core import config as app_config

    monkeypatch.setattr(app_config.settings, "ENVIRONMENT", "production")
    monkeypatch.setattr(app_config.settings, "DEBUG", False)
    monkeypatch.setattr(app_config.settings, "JWT_SECRET", "super-strong-production-secret-0123456789")
    monkeypatch.setattr(app_config.settings, "BACKEND_CORS_ORIGINS", "https://soc.example.com")

    assert app_config.production_safety_issues(app_config.settings) == []


def test_observability_metrics_endpoint(client):
    # Generate a couple requests so metrics include traffic data.
    _ = client.get("/api/v1/health")
    _ = client.get("/api/v1/playbooks")

    response = client.get("/api/v1/observability/metrics")
    assert response.status_code == 200
    payload = response.json()["data"]["metrics"]
    assert "total_requests" in payload
    assert "avg_latency_ms" in payload
    assert "requests_by_status" in payload
    assert "requests_by_route" in payload
    assert "recent_events" in payload
    assert isinstance(payload["recent_events"], list)
    assert payload["recent_events"]
    assert "correlation_id" in payload["recent_events"][0]
    assert "recent_trace_events" in payload
    assert isinstance(payload["recent_trace_events"], list)


def test_observability_prometheus_metrics_endpoint(client):
    _ = client.get("/api/v1/health")

    response = client.get("/api/v1/observability/metrics/prometheus")
    assert response.status_code == 200
    assert "soar_requests_total" in response.text
    assert "soar_request_latency_avg_ms" in response.text
    assert "soar_requests_by_status_total" in response.text


def test_simulation_endpoint_creates_incident_and_returns_201(client, monkeypatch):
    from app.api.v1.endpoints import simulations
    from app.services import alert_service

    fake_alert = {
        "alert_type": "BRUTE_FORCE_DETECTED",
        "severity": "CRITICAL",
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
        "source": "option2_simulation",
        "details": {
            "attacker_ip": "10.10.10.10",
            "target_ip": "192.168.1.1",
            "target_port": 22,
            "failed_attempts": 12,
            "usernames_tried": ["admin", "root", "user", "test"],
            "risk_score": 90,
            "reasons": ["[HIGH] test reason"],
            "protocol": "SSH",
        },
    }

    monkeypatch.setattr(simulations, "sim_bruteforce", lambda num_attempts: ([], [fake_alert]))

    class NoopTask:
        @staticmethod
        def delay(_: int) -> None:
            return None

        @staticmethod
        def apply_async(args=(), queue=None):
            return None

    monkeypatch.setattr(alert_service, "process_incident", NoopTask())

    response = client.post("/api/v1/simulations/brute-force?count=10")

    assert response.status_code == 201
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["contract_version"] == "v1"
    assert payload["data"]["pipeline_flow"] == ["simulation", "incident", "queue", "playbook", "result"]
    assert payload["data"]["lifecycle_states"]["playbook_status"] == ["pending", "running", "success", "failed"]
    assert payload["data"]["alerts_generated"] == 1
    assert payload["data"]["incidents_created"] == 1
    assert len(payload["data"]["incident_ids"]) == 1
    assert payload["data"]["latest_incident_id"] == payload["data"]["incident_ids"][-1]
    assert payload["data"]["incidents"][0]["playbook_status"] == "pending"
    assert "queue" in payload["data"]
    assert "backlog" in payload["data"]["queue"]


def test_simulation_summary_aggregation(client, monkeypatch):
    from app.api.v1.endpoints import simulations
    from app.services import alert_service

    fake_alerts = [
        {
            "alert_type": "BRUTE_FORCE_DETECTED",
            "severity": "CRITICAL",
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
            "source": "option2_simulation",
            "details": {
                "attacker_ip": "10.10.10.10",
                "target_ip": "192.168.1.1",
                "target_port": 22,
                "failed_attempts": 12,
                "usernames_tried": ["admin", "root", "user", "test"],
                "risk_score": 90,
                "reasons": ["[HIGH] test reason"],
                "protocol": "SSH",
            },
        },
        {
            "alert_type": "PHISHING_EMAIL_DETECTED",
            "severity": "HIGH",
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
            "source": "option2_simulation",
            "details": {
                "sender": "alert@test.com",
                "recipient": "user@company.com",
                "subject": "Urgent",
                "url": "http://bad.example",
                "risk_score": 65,
                "reasons": ["[MEDIUM] test reason"],
                "has_attachment": False,
            },
        },
    ]

    monkeypatch.setattr(simulations, "sim_bruteforce", lambda num_attempts: ([], fake_alerts))

    class NoopTask:
        @staticmethod
        def delay(_: int) -> None:
            return None

        @staticmethod
        def apply_async(args=(), queue=None):
            return None

    monkeypatch.setattr(alert_service, "process_incident", NoopTask())

    create_response = client.post("/api/v1/simulations/brute-force?count=10")
    assert create_response.status_code == 201

    summary_response = client.get("/api/v1/simulations/summary?limit=10")
    assert summary_response.status_code == 200

    summary = summary_response.json()["data"]
    assert summary["contract_version"] == "v1"
    assert summary["pipeline_flow"] == ["simulation", "incident", "queue", "playbook", "result"]
    assert summary["lifecycle_states"]["incident_status"] == ["open", "closed", "failed"]
    assert summary["total_incidents"] == 2
    assert summary["severity_breakdown"]["critical"] == 1
    assert summary["severity_breakdown"]["high"] == 1
    assert summary["playbook_status_breakdown"]["pending"] == 2
    assert summary["incident_status_breakdown"]["open"] == 2
    assert "queue" in summary


def test_simulation_queue_metrics_endpoint(client, monkeypatch):
    from app.api.v1.endpoints import simulations
    from app.services import alert_service

    fake_alert = {
        "alert_type": "BRUTE_FORCE_DETECTED",
        "severity": "CRITICAL",
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
        "source": "option2_simulation",
        "details": {
            "attacker_ip": "10.10.10.10",
            "target_ip": "192.168.1.1",
            "target_port": 22,
            "failed_attempts": 12,
            "usernames_tried": ["admin", "root", "user", "test"],
            "risk_score": 90,
            "reasons": ["[HIGH] test reason"],
            "protocol": "SSH",
        },
    }

    monkeypatch.setattr(simulations, "sim_bruteforce", lambda num_attempts: ([], [fake_alert]))

    class NoopTask:
        @staticmethod
        def delay(_: int) -> None:
            return None

        @staticmethod
        def apply_async(args=(), queue=None):
            return None

    monkeypatch.setattr(alert_service, "process_incident", NoopTask())

    create_response = client.post("/api/v1/simulations/brute-force?count=10")
    assert create_response.status_code == 201

    queue_response = client.get("/api/v1/simulations/queue-metrics?window_hours=24")
    assert queue_response.status_code == 200
    queue_payload = queue_response.json()["data"]["queue"]
    assert "pending" in queue_payload
    assert "running" in queue_payload
    assert "backlog" in queue_payload
    assert "capacity" in queue_payload
    assert "pressure" in queue_payload
    assert "queues" in queue_payload
    assert "task_max_retries" in queue_payload
    assert "per_queue" in queue_payload
    assert "worker_runbook" in queue_payload
    assert queue_payload["window_hours"] == 24


def test_async_processing_transition_persists_playbook_result(client, db_session_factory, monkeypatch):
    from app.api.v1.endpoints import simulations
    from app.services import alert_service

    fake_alert = {
        "alert_type": "BRUTE_FORCE_DETECTED",
        "severity": "CRITICAL",
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
        "source": "option2_simulation",
        "details": {
            "attacker_ip": "10.10.10.11",
            "target_ip": "192.168.1.1",
            "target_port": 22,
            "failed_attempts": 13,
            "usernames_tried": ["admin", "root", "user", "test"],
            "risk_score": 95,
            "reasons": ["[HIGH] test reason"],
            "protocol": "SSH",
        },
    }

    monkeypatch.setattr(simulations, "sim_bruteforce", lambda num_attempts: ([], [fake_alert]))

    class SyncTask:
        @staticmethod
        def delay(incident_id: int) -> dict:
            db = db_session_factory()
            try:
                return execute_playbook_for_incident(db=db, incident_id=incident_id, task_id="test-task")
            finally:
                db.close()

    monkeypatch.setattr(alert_service, "process_incident", SyncTask())

    response = client.post("/api/v1/simulations/brute-force?count=10")
    assert response.status_code == 201

    summary_response = client.get("/api/v1/simulations/summary?limit=1")
    assert summary_response.status_code == 200

    recent = summary_response.json()["data"]["recent_incidents"][0]
    assert recent["playbook_status"] == "success"
    assert recent["status"] == "closed"
    assert recent["playbook_result"]["success"] is True
    assert "execution_duration_ms" in recent["playbook_result"]
    assert "provider_errors" in recent["playbook_result"]


def test_incidents_list_and_detail_endpoints(client, db_session_factory, monkeypatch):
    from app.api.v1.endpoints import simulations
    from app.services import alert_service

    fake_alert = {
        "alert_type": "BRUTE_FORCE_DETECTED",
        "severity": "CRITICAL",
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
        "source": "option2_simulation",
        "details": {
            "attacker_ip": "10.10.10.20",
            "target_ip": "192.168.1.1",
            "target_port": 22,
            "failed_attempts": 11,
            "usernames_tried": ["admin", "root", "user", "test"],
            "risk_score": 88,
            "reasons": ["[HIGH] test reason"],
            "protocol": "SSH",
        },
    }

    monkeypatch.setattr(simulations, "sim_bruteforce", lambda num_attempts: ([], [fake_alert]))

    class SyncTask:
        @staticmethod
        def delay(incident_id: int) -> dict:
            db = db_session_factory()
            try:
                return execute_playbook_for_incident(db=db, incident_id=incident_id, task_id="detail-test-task")
            finally:
                db.close()

    monkeypatch.setattr(alert_service, "process_incident", SyncTask())

    create_response = client.post("/api/v1/simulations/brute-force?count=10")
    assert create_response.status_code == 201
    incident_id = create_response.json()["data"]["latest_incident_id"]

    list_response = client.get("/api/v1/incidents?page=1&page_size=10&severity=critical&q=brute")
    assert list_response.status_code == 200
    list_payload = list_response.json()["data"]
    assert list_payload["total"] >= 1
    assert len(list_payload["items"]) >= 1

    detail_response = client.get(f"/api/v1/incidents/{incident_id}")
    assert detail_response.status_code == 200
    detail_payload = detail_response.json()["data"]
    assert detail_payload["incident"]["id"] == incident_id
    assert len(detail_payload["timeline"]) == 4
    assert "current_status" in detail_payload["playbook_execution"]
    assert isinstance(detail_payload["playbook_execution"].get("steps"), list)
    assert "risk_scoring" in detail_payload

    executions_response = client.get(f"/api/v1/incidents/{incident_id}/executions")
    assert executions_response.status_code == 200
    assert executions_response.json()["data"]["total"] >= 1


def test_playbooks_endpoints(client):
    list_response = client.get("/api/v1/playbooks")
    assert list_response.status_code == 200
    payload = list_response.json()["data"]
    assert payload["total"] == 4
    assert len(payload["items"]) == 4
    assert "version" in payload["items"][0]

    stats_response = client.get("/api/v1/playbooks/brute-force-detection/stats")
    assert stats_response.status_code == 200
    stats = stats_response.json()["data"]
    assert stats["id"] == "brute-force-detection"
    assert "steps" in stats
    assert "version" in stats

    executions_response = client.get("/api/v1/playbooks/brute-force-detection/executions")
    assert executions_response.status_code == 200
    executions = executions_response.json()["data"]
    assert "items" in executions
    assert "latest_success" in executions
    assert "latest_failed" in executions

    filtered_executions_response = client.get(
        "/api/v1/playbooks/brute-force-detection/executions?status=success&since_hours=24&page=1&page_size=5"
    )
    assert filtered_executions_response.status_code == 200
    filtered_payload = filtered_executions_response.json()["data"]
    assert filtered_payload["filters"]["status"] == "success"
    assert filtered_payload["filters"]["since_hours"] == 24
    assert filtered_payload["filters"]["page"] == 1
    assert filtered_payload["filters"]["page_size"] == 5
    assert "total_all" in filtered_payload


def test_threat_intel_query_endpoint(client, monkeypatch):
    from app.api.v1.endpoints import threat_intel

    monkeypatch.setattr(
        threat_intel,
        "enrich_ip",
        lambda indicator: {
            "ip": indicator,
            "virustotal": {"malicious": 1},
            "abuseipdb": {"abuse_score": 40},
            "alienvault": {"pulse_count": 2},
            "provider_errors": {},
            "degraded": False,
        },
    )

    response = client.post(
        "/api/v1/threat-intel/query",
        json={"indicator": "1.1.1.1", "indicator_type": "ip"},
    )
    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["indicator"] == "1.1.1.1"
    assert payload["indicator_type"] == "ip"
    assert "risk_summary" in payload
    assert payload["risk_summary"]["label"] in {"low", "medium", "high"}

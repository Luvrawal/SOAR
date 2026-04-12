from __future__ import annotations

from app.soar.utils.reporter import apply_report_profile, resolve_report_profile


def _sample_report() -> dict:
    return {
        "incident_id": "INC-20260412193000",
        "playbook_name": "Brute Force Detection Playbook",
        "alert_type": "BRUTE_FORCE_DETECTED",
        "severity": "CRITICAL",
        "risk_score": 95,
        "status": "CLOSED",
        "alert_details": {
            "attacker_ip": "10.10.10.20",
            "target_ip": "192.168.1.1",
            "usernames_tried": ["admin", "root"],
            "protocol": "SSH",
        },
        "threat_intel": {
            "virustotal": {
                "ip": "10.10.10.20",
                "summary": "1/94 engines flagged as malicious",
            },
            "abuseipdb": {
                "ip": "10.10.10.20",
                "country": "US",
                "isp": "Example ISP",
            },
        },
        "response_taken": [
            {
                "action": "BLOCK IP 10.10.10.20 on firewall immediately",
                "timestamp": "2026-04-12 19:30:00",
                "status": "COMPLETED",
            }
        ],
    }


def test_resolve_report_profile_defaults_to_full_on_invalid_input():
    assert resolve_report_profile(None) == "full"
    assert resolve_report_profile("invalid") == "full"


def test_apply_report_profile_full_keeps_sensitive_fields():
    report = _sample_report()

    profiled = apply_report_profile(report, profile="full")

    assert profiled["report_profile"] == "full"
    assert profiled["alert_details"]["attacker_ip"] == "10.10.10.20"
    assert profiled["alert_details"]["usernames_tried"] == ["admin", "root"]
    assert profiled["threat_intel"]["abuseipdb"]["country"] == "US"


def test_apply_report_profile_redacted_masks_sensitive_fields():
    report = _sample_report()

    profiled = apply_report_profile(report, profile="redacted")

    assert profiled["report_profile"] == "redacted"
    assert profiled["alert_details"]["attacker_ip"] == "10.10.10.x"
    assert profiled["alert_details"]["target_ip"] == "192.168.1.x"
    assert profiled["alert_details"]["usernames_tried"] == "[redacted]"
    assert profiled["alert_details"]["protocol"] == "SSH"
    assert profiled["threat_intel"]["virustotal"]["ip"] == "10.10.10.x"
    assert profiled["threat_intel"]["abuseipdb"]["country"] == "[redacted]"
    assert profiled["threat_intel"]["abuseipdb"]["isp"] == "[redacted]"
    assert profiled["response_taken"][0]["action"] == "[redacted]"

def _safe_int(value: object, default: int = 0) -> int:
    try:
        return int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return default


def build_threat_score(result: dict) -> dict:
    provider_errors = result.get("provider_errors", {}) if isinstance(result, dict) else {}
    degraded = bool(result.get("degraded")) if isinstance(result, dict) else False

    vt = result.get("virustotal", {}) if isinstance(result, dict) else {}
    aipdb = result.get("abuseipdb", {}) if isinstance(result, dict) else {}
    otx = result.get("alienvault", {}) if isinstance(result, dict) else {}
    mb = result.get("malwarebazaar", {}) if isinstance(result, dict) else {}

    vt_malicious = _safe_int(vt.get("malicious", 0)) if isinstance(vt, dict) else 0
    aipdb_score = _safe_int(aipdb.get("abuse_score", 0)) if isinstance(aipdb, dict) else 0
    otx_pulse = _safe_int(otx.get("pulse_count", 0)) if isinstance(otx, dict) else 0
    mb_match = bool(mb.get("found")) if isinstance(mb, dict) else False

    score = 0
    factors: list[str] = []

    if vt_malicious > 0:
        score += min(50, 15 + vt_malicious * 5)
        factors.append(f"VirusTotal flagged malicious by {vt_malicious} engines")

    if aipdb_score > 0:
        score += min(30, max(5, aipdb_score // 3))
        factors.append(f"AbuseIPDB abuse confidence is {aipdb_score}%")

    if otx_pulse > 0:
        score += min(20, max(5, otx_pulse * 2))
        factors.append(f"AlienVault OTX reports {otx_pulse} pulse hits")

    if mb_match:
        score += 10
        factors.append("MalwareBazaar has a positive malware hash match")

    score = max(0, min(100, score))

    if score >= 75:
        severity = "high"
    elif score >= 40:
        severity = "medium"
    else:
        severity = "low"

    if score >= 80 and not degraded:
        confidence = "strong"
    elif score >= 45:
        confidence = "moderate"
    else:
        confidence = "weak"

    if degraded and confidence == "strong":
        confidence = "moderate"
    elif degraded and confidence == "moderate":
        confidence = "weak"

    if not factors:
        factors.append("No strong threat indicators were detected from configured providers")

    return {
        "score": score,
        "severity": severity,
        "label": severity,
        "confidence": confidence,
        "degraded": degraded,
        "factors": factors,
        "provider_errors": provider_errors,
    }

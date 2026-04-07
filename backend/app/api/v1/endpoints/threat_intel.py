from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.schemas.common import ApiResponse
from app.soar.utils.threat_intel import enrich_hash, enrich_ip, enrich_url

router = APIRouter(prefix="/threat-intel")


class ThreatIntelQuery(BaseModel):
    indicator: str = Field(..., min_length=2, max_length=2048)
    indicator_type: Literal["ip", "domain", "url", "hash"]


def _risk_summary(result: dict) -> dict:
    provider_errors = result.get("provider_errors", {}) if isinstance(result, dict) else {}
    degraded = bool(result.get("degraded")) if isinstance(result, dict) else False

    score = 0
    vt = result.get("virustotal", {}) if isinstance(result, dict) else {}
    aipdb = result.get("abuseipdb", {}) if isinstance(result, dict) else {}
    otx = result.get("alienvault", {}) if isinstance(result, dict) else {}

    if isinstance(vt, dict):
        score += min(int(vt.get("malicious", 0)) * 10, 50)
    if isinstance(aipdb, dict):
        score += min(int(aipdb.get("abuse_score", 0)) // 2, 30)
    if isinstance(otx, dict):
        score += min(int(otx.get("pulse_count", 0)) * 2, 20)

    score = max(0, min(100, score))

    if score >= 70:
        label = "high"
    elif score >= 35:
        label = "medium"
    else:
        label = "low"

    return {
        "score": score,
        "label": label,
        "degraded": degraded,
        "provider_errors": provider_errors,
    }


@router.post("/query", response_model=ApiResponse)
def query_threat_intel(payload: ThreatIntelQuery) -> ApiResponse:
    indicator_type = payload.indicator_type
    indicator = payload.indicator.strip()

    if indicator_type == "ip":
        result = enrich_ip(indicator)
    elif indicator_type == "hash":
        result = enrich_hash(indicator)
    else:
        normalized = indicator if indicator_type == "url" else f"http://{indicator}"
        result = enrich_url(normalized)

    return ApiResponse(
        message="Threat intelligence fetched successfully",
        data={
            "indicator": indicator,
            "indicator_type": indicator_type,
            "results": result,
            "risk_summary": _risk_summary(result),
        },
    )

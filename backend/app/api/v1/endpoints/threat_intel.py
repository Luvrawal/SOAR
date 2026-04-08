from typing import Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.core.auth import require_roles
from app.schemas.common import ApiResponse
from app.services.threat_scoring_service import build_threat_score
from app.soar.utils.threat_intel import enrich_hash, enrich_ip, enrich_url

router = APIRouter(prefix="/threat-intel", dependencies=[Depends(require_roles("admin", "analyst"))])


class ThreatIntelQuery(BaseModel):
    indicator: str = Field(..., min_length=2, max_length=2048)
    indicator_type: Literal["ip", "domain", "url", "hash"]
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
            "risk_summary": build_threat_score(result),
        },
    )

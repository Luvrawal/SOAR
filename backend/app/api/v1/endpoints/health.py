from datetime import datetime, timezone

from fastapi import APIRouter

from app.schemas.common import ApiResponse

router = APIRouter()


@router.get("/health")
def health_check() -> ApiResponse:
    return ApiResponse(
        message="Service is healthy",
        data={
            "status": "ok",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )

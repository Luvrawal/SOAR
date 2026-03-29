from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.alert import AlertCreate, IncidentResponse
from app.schemas.common import ApiResponse
from app.services.alert_service import create_incident_from_alert

router = APIRouter(prefix="/alerts")


@router.post("", response_model=ApiResponse, status_code=status.HTTP_201_CREATED)
def ingest_alert(payload: AlertCreate, db: Session = Depends(get_db)) -> ApiResponse:
    incident = create_incident_from_alert(db=db, alert=payload)
    serialized = IncidentResponse.model_validate(incident)
    return ApiResponse(
        message="Alert ingested successfully",
        data={"incident": serialized.model_dump(mode="json")},
    )

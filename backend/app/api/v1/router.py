from fastapi import APIRouter

from app.api.v1.endpoints.alerts import router as alerts_router
from app.api.v1.endpoints.health import router as health_router
from app.api.v1.endpoints.incidents import router as incidents_router
from app.api.v1.endpoints.playbooks import router as playbooks_router
from app.api.v1.endpoints.simulations import router as simulations_router
from app.api.v1.endpoints.threat_intel import router as threat_intel_router

router = APIRouter()
router.include_router(health_router, tags=["health"])
router.include_router(alerts_router, tags=["alerts"])
router.include_router(incidents_router, tags=["incidents"])
router.include_router(playbooks_router, tags=["playbooks"])
router.include_router(simulations_router, tags=["simulations"])
router.include_router(threat_intel_router, tags=["threat-intel"])

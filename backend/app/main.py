from time import perf_counter
from uuid import uuid4

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.requests import Request

from app.api.router import api_router
from app.core.config import get_cors_origins, settings, validate_production_safety
from app.core.error_handlers import register_exception_handlers
from app.core.observability import observability_store, set_correlation_id


def create_application() -> FastAPI:
    validate_production_safety()

    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.API_VERSION,
        docs_url="/docs",
        redoc_url="/redoc",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=get_cors_origins(),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def request_observability_middleware(request: Request, call_next):
        started = perf_counter()
        correlation_id = request.headers.get("X-Correlation-ID") or str(uuid4())
        set_correlation_id(correlation_id)

        response = await call_next(request)

        route_template = request.scope.get("route").path if request.scope.get("route") else request.url.path
        observability_store.record(
            method=request.method,
            route=str(route_template),
            status_code=response.status_code,
            latency_ms=(perf_counter() - started) * 1000,
            correlation_id=correlation_id,
        )
        response.headers["X-Correlation-ID"] = correlation_id
        return response

    @app.middleware("http")
    async def security_headers_middleware(request: Request, call_next):
        response = await call_next(request)
        if settings.SECURITY_HEADERS_ENABLED:
            response.headers.setdefault("X-Content-Type-Options", "nosniff")
            response.headers.setdefault("X-Frame-Options", "DENY")
            response.headers.setdefault("Referrer-Policy", "no-referrer")
            response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
            if settings.FORCE_HTTPS_HSTS:
                response.headers.setdefault("Strict-Transport-Security", "max-age=63072000; includeSubDomains; preload")
        return response

    register_exception_handlers(app)
    app.include_router(api_router, prefix=settings.API_V1_PREFIX)
    return app


app = create_application()

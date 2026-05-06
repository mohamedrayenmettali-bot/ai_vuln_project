import asyncio
import sys
from pathlib import Path
from contextlib import asynccontextmanager

# Add parent directory to sys.path to allow importing 'ai' module
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import structlog

from app.config import settings
from app.api.v1.router import api_router
from app.core.middleware import RequestIDMiddleware, RequestTimingMiddleware
from app.core.exceptions import (
    AIServiceException, 
    ResourceNotFoundException, 
    ai_service_exception_handler, 
    resource_not_found_exception_handler
)
from app.services.predictor import PredictorService
from app.core.logging import setup_logging

setup_logging(settings.LOG_LEVEL)
logger = structlog.get_logger(__name__)

@asynccontextmanager
async def lifespan(_: FastAPI):
    logger.info("service_startup", service=settings.API_TITLE)
    service = PredictorService.get()
    try:
        logger.info("loading_model")
        service.load()
    except Exception as e:
        logger.exception("startup_failed", error=str(e))
        raise
    try:
        logger.info("warming_nlp_encoder")
        await asyncio.get_running_loop().run_in_executor(None, service.warm_encoder)
    except Exception as e:
        logger.warning("encoder_warmup_failed", error=str(e))
    yield
    logger.info("service_shutdown", service=settings.API_TITLE)

def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.API_TITLE,
        description=settings.API_DESCRIPTION,
        version=settings.API_VERSION,
        docs_url=settings.DOCS_URL,
        redoc_url=settings.REDOC_URL,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ALLOW_ORIGINS,
        allow_methods=settings.DEFAULT_CORS_ALLOW_METHODS,
        allow_headers=settings.DEFAULT_CORS_ALLOW_HEADERS,
    )
    
    app.add_middleware(RequestIDMiddleware)
    app.add_middleware(RequestTimingMiddleware)

    app.add_exception_handler(AIServiceException, ai_service_exception_handler)
    app.add_exception_handler(ResourceNotFoundException, resource_not_found_exception_handler)

    app.include_router(api_router, include_in_schema=False)
    app.include_router(api_router, prefix="/api", include_in_schema=False)
    app.include_router(api_router, prefix="/api/v1")

    @app.get("/", tags=["Root"])
    def root() -> dict[str, str]:
        return {
            "service": settings.API_TITLE,
            "name": settings.API_TITLE,
            "version": settings.API_VERSION,
            "docs": settings.DOCS_URL,
            "health": settings.HEALTH_PATH,
            "api_health": "/api/v1" + settings.HEALTH_PATH,
            "api_public_health": "/api" + settings.HEALTH_PATH,
            "api_v1_health": "/api/v1" + settings.HEALTH_PATH,
        }

    return app

app = create_app()

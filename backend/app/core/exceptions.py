from fastapi import Request
from fastapi.responses import JSONResponse
import structlog

logger = structlog.get_logger(__name__)

class AIServiceException(Exception):
    """Base class for AI service exceptions"""
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)

async def ai_service_exception_handler(request: Request, exc: AIServiceException):
    logger.error("ai_service_error", message=exc.message, path=request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": exc.message},
    )

class ResourceNotFoundException(Exception):
    """Resource not found"""
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)

async def resource_not_found_exception_handler(request: Request, exc: ResourceNotFoundException):
    logger.warning("resource_not_found", message=exc.message, path=request.url.path)
    return JSONResponse(
        status_code=404,
        content={"detail": exc.message},
    )

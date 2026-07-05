"""Meeting AI FastAPI Main Application Entrypoint"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_v1_router
from app.core.config import settings
from app.core.exceptions import HealthSetuException
from app.core.logging import logger
from app.db.base import Base
from app.db.database import engine
from app.schemas.common import ApiResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context: initialize database tables and handle clean shutdown"""
    logger.info("Starting Meeting AI Intelligence Backend Service...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    logger.info("Shutting down Meeting AI Service...")
    await engine.dispose()


app = FastAPI(
    title=settings.APP_NAME,
    description="Production-quality AI-powered meeting intelligence platform for transcription, speaker diarization, summaries, decisions, and action items.",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS if isinstance(settings.CORS_ORIGINS, list) else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception Handlers
@app.exception_handler(HealthSetuException)
async def domain_exception_handler(request: Request, exc: HealthSetuException):
    logger.warning(f"Domain exception: {exc.code} - {exc.message}")
    response = ApiResponse.fail(
        code=exc.code,
        message=exc.message,
        details=exc.details,
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=response.model_dump(mode="json"),
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = []
    for err in exc.errors():
        field = " -> ".join([str(loc) for loc in err.get("loc", [])])
        msg = err.get("msg", "Invalid value")
        errors.append({"field": field, "message": msg})

    logger.warning(f"Validation error on {request.url.path}: {errors}")
    response = ApiResponse.fail(
        code="VALIDATION_ERROR",
        message="Request payload failed validation schema.",
        details=errors,
    )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=response.model_dump(mode="json"),
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    response = ApiResponse.fail(
        code="HTTP_ERROR",
        message=str(exc.detail),
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=response.model_dump(mode="json"),
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error on {request.url.path}: {str(exc)}", exc_info=True)
    response = ApiResponse.fail(
        code="INTERNAL_SERVER_ERROR",
        message="An unexpected internal server error occurred.",
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=response.model_dump(mode="json"),
    )


# Mount API Routes
app.include_router(api_v1_router, prefix=settings.API_V1_STR)


@app.get("/", tags=["Root"])
async def root():
    return {
        "name": settings.APP_NAME,
        "description": "AI-Powered Meeting Intelligence Platform API",
        "documentation": "/docs",
        "version": "0.1.0",
        "api_v1": settings.API_V1_STR,
    }

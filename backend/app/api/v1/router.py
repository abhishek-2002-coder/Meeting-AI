"""Meeting AI API v1 Aggregator Router"""
from fastapi import APIRouter

from app.api.v1.action_items import router as action_items_router
from app.api.v1.auth import router as auth_router
from app.api.v1.meetings import router as meetings_router
from app.api.v1.processing import router as processing_router
from app.api.v1.search import router as search_router
from app.api.v1.summary import router as summary_router
from app.api.v1.transcript import router as transcript_router
from app.api.v1.upload import router as upload_router

api_v1_router = APIRouter()


@api_v1_router.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "healthy",
        "service": "Meeting AI Intelligence Platform",
        "version": "0.1.0",
    }


api_v1_router.include_router(auth_router)
api_v1_router.include_router(meetings_router)
api_v1_router.include_router(upload_router)
api_v1_router.include_router(processing_router)
api_v1_router.include_router(transcript_router)
api_v1_router.include_router(summary_router)
api_v1_router.include_router(action_items_router)
api_v1_router.include_router(search_router)

"""
Health check and store reset endpoints.
"""
from fastapi import APIRouter

from app.db.memory_store import store

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check():
    """Simple health check endpoint."""
    return {
        "status": "healthy",
        "version": "0.1.0",
        "seam": "mutation-seam",
    }


@router.post("/reset")
async def reset_store():
    """
    Reset the in-memory store to seed data.
    Used by the integration test harness between scenario runs.
    Prototype-only — not present in production.
    """
    store.reset()
    return {"status": "reset", "message": "Store reset to seed data"}

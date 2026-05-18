"""
Production tracking mutation router.
"""
from fastapi import APIRouter, Depends

from app.auth.jwt import Actor, get_current_actor
from app.envelope.request import MutationRequest
from app.envelope.response import MutationResponse
from app.production_tracking_persistence import persist_production_tracking_record

router = APIRouter(prefix="/api/v1/mutations", tags=["production-tracking"])


@router.post("/production-tracking", response_model=MutationResponse)
async def mutate_production_tracking(
    request: MutationRequest,
    actor: Actor = Depends(get_current_actor),
) -> MutationResponse:
    """Persist one governed production tracking baseline record."""
    return persist_production_tracking_record(request=request, actor=actor)

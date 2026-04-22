"""
Hours tracking mutation router.
"""
from fastapi import APIRouter, Depends

from app.auth.jwt import Actor, get_current_actor
from app.envelope.request import MutationRequest
from app.envelope.response import MutationResponse
from app.services.mutation_pipeline import execute_mutation

router = APIRouter(prefix="/api/v1/mutations", tags=["hours"])


@router.post("/hours", response_model=MutationResponse)
async def mutate_hours(
    request: MutationRequest,
    actor: Actor = Depends(get_current_actor),
) -> MutationResponse:
    """
    Execute a mutation for hours tracking.
    
    Supports actions like log_hours.
    """
    return await execute_mutation(
        request=request,
        actor=actor,
        entity_type="hours",
    )

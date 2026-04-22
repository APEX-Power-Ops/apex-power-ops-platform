"""
Assignment mutation router.
"""
from fastapi import APIRouter, Depends

from app.auth.jwt import Actor, get_current_actor
from app.envelope.request import MutationRequest
from app.envelope.response import MutationResponse
from app.services.mutation_pipeline import execute_mutation

router = APIRouter(prefix="/api/v1/mutations", tags=["assignments"])


@router.post("/assignments", response_model=MutationResponse)
async def mutate_assignments(
    request: MutationRequest,
    actor: Actor = Depends(get_current_actor),
) -> MutationResponse:
    """
    Execute a mutation on an assignment entity.
    Supports: assign, reassign, reprioritize.
    """
    return await execute_mutation(
        request=request,
        actor=actor,
        entity_type="assignment",
    )

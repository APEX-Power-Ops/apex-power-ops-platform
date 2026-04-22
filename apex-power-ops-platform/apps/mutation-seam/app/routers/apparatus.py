"""
Apparatus mutation router.
"""
from fastapi import APIRouter, Depends

from app.auth.jwt import Actor, get_current_actor
from app.envelope.request import MutationRequest
from app.envelope.response import MutationResponse
from app.services.mutation_pipeline import execute_mutation

router = APIRouter(prefix="/api/v1/mutations", tags=["apparatus"])


@router.post("/apparatus", response_model=MutationResponse)
async def mutate_apparatus(
    request: MutationRequest,
    actor: Actor = Depends(get_current_actor),
) -> MutationResponse:
    """
    Execute a mutation on an apparatus entity.
    
    Accepts any registered apparatus action (update_status, assign, unassign, etc.)
    through the governed mutation pipeline.
    """
    return await execute_mutation(
        request=request,
        actor=actor,
        entity_type="apparatus",
    )

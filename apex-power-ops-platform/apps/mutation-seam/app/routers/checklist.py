"""
Checklist item mutation router.
"""
from fastapi import APIRouter, Depends

from app.auth.jwt import Actor, get_current_actor
from app.envelope.request import MutationRequest
from app.envelope.response import MutationResponse
from app.services.mutation_pipeline import execute_mutation

router = APIRouter(prefix="/api/v1/mutations", tags=["checklist"])


@router.post("/checklist", response_model=MutationResponse)
async def mutate_checklist(
    request: MutationRequest,
    actor: Actor = Depends(get_current_actor),
) -> MutationResponse:
    """
    Execute a mutation on a checklist item.
    
    Supports actions like complete_checklist_item, reopen_checklist_item.
    """
    return await execute_mutation(
        request=request,
        actor=actor,
        entity_type="checklist_item",
    )

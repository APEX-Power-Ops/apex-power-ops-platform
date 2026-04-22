"""
Router for ProgressSnapshot mutations.
POST /api/v1/mutations/snapshots
"""
from fastapi import APIRouter, Depends

from app.auth.jwt import Actor, get_current_actor
from app.envelope.request import MutationRequest
from app.envelope.response import MutationResponse
from app.services.mutation_pipeline import execute_mutation

router = APIRouter(prefix="/api/v1/mutations", tags=["mutations"])


@router.post("/snapshots")
async def mutate_snapshot(
    request: MutationRequest,
    actor: Actor = Depends(get_current_actor),
) -> MutationResponse:
    """Handle ProgressSnapshot mutations (approve/reject)."""
    return await execute_mutation(request, actor, entity_type="snapshot")

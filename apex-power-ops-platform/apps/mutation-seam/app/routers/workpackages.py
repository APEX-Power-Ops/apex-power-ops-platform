"""
WorkPackage mutation router.
"""
from fastapi import APIRouter, Depends

from app.auth.jwt import Actor, get_current_actor
from app.envelope.request import MutationRequest
from app.envelope.response import MutationResponse
from app.services.mutation_pipeline import execute_mutation

router = APIRouter(prefix="/api/v1/mutations", tags=["workpackages"])


@router.post("/workpackages", response_model=MutationResponse)
async def mutate_workpackages(
    request: MutationRequest,
    actor: Actor = Depends(get_current_actor),
) -> MutationResponse:
    """
    Execute a mutation on a WorkPackage entity.
    Supports: submit_for_review, withdraw_submission, approve, reject, escalate_review.
    """
    return await execute_mutation(
        request=request,
        actor=actor,
        entity_type="workpackage",
    )

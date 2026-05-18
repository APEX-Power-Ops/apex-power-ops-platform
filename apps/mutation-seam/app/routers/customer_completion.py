"""
Customer completion mutation router.
"""
from fastapi import APIRouter, Depends

from app.auth.jwt import Actor, get_current_actor
from app.customer_completion_persistence import persist_customer_completion_record
from app.envelope.request import MutationRequest
from app.envelope.response import MutationResponse

router = APIRouter(prefix="/api/v1/mutations", tags=["customer-completion"])


@router.post("/customer-completion", response_model=MutationResponse)
async def mutate_customer_completion(
    request: MutationRequest,
    actor: Actor = Depends(get_current_actor),
) -> MutationResponse:
    """Persist one governed customer completion baseline record."""
    return persist_customer_completion_record(request=request, actor=actor)

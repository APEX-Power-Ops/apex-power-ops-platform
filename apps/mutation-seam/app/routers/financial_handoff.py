"""
Financial handoff mutation router.
"""
from fastapi import APIRouter, Depends

from app.auth.jwt import Actor, get_current_actor
from app.envelope.request import MutationRequest
from app.envelope.response import MutationResponse
from app.financial_handoff_persistence import persist_financial_handoff_record

router = APIRouter(prefix="/api/v1/mutations", tags=["financial-handoff"])


@router.post("/financial-handoff", response_model=MutationResponse)
async def mutate_financial_handoff(
    request: MutationRequest,
    actor: Actor = Depends(get_current_actor),
) -> MutationResponse:
    """Persist one governed financial handoff baseline record."""
    return persist_financial_handoff_record(request=request, actor=actor)

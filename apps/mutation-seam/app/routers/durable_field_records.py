"""
Durable field record mutation router.
"""
from fastapi import APIRouter, Depends

from app.auth.jwt import Actor, get_current_actor
from app.durable_field_record_persistence import persist_durable_field_record
from app.envelope.request import MutationRequest
from app.envelope.response import MutationResponse

router = APIRouter(prefix="/api/v1/mutations", tags=["durable-field-records"])


@router.post("/durable-field-records", response_model=MutationResponse)
async def mutate_durable_field_records(
    request: MutationRequest,
    actor: Actor = Depends(get_current_actor),
) -> MutationResponse:
    """Persist one governed durable field record."""
    return persist_durable_field_record(request=request, actor=actor)

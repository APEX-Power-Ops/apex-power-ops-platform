"""
Temp Power customer-facing delivery execution persistence router.
"""
from fastapi import APIRouter, Depends

from app.auth.jwt import Actor, get_current_actor
from app.envelope.request import MutationRequest
from app.envelope.response import MutationResponse
from app.temp_power_customer_delivery_event_persistence import persist_temp_power_customer_delivery_event

router = APIRouter(prefix="/api/v1/mutations", tags=["temp-power-customer-delivery-events"])


@router.post("/temp-power-customer-delivery-events", response_model=MutationResponse)
async def mutate_temp_power_customer_delivery_events(
    request: MutationRequest,
    actor: Actor = Depends(get_current_actor),
) -> MutationResponse:
    """Persist one governed Temp Power customer-facing delivery execution event."""
    return await persist_temp_power_customer_delivery_event(request=request, actor=actor)
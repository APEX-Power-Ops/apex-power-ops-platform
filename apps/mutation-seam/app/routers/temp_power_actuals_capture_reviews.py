"""
Temp Power actuals-capture review persistence router.
"""
from fastapi import APIRouter, Depends

from app.auth.jwt import Actor, get_current_actor
from app.envelope.request import MutationRequest
from app.envelope.response import MutationResponse
from app.temp_power_actuals_capture_review_persistence import persist_temp_power_actuals_capture_review

router = APIRouter(prefix="/api/v1/mutations", tags=["temp-power-actuals-capture-reviews"])


@router.post("/temp-power-actuals-capture-reviews", response_model=MutationResponse)
async def mutate_temp_power_actuals_capture_reviews(
    request: MutationRequest,
    actor: Actor = Depends(get_current_actor),
) -> MutationResponse:
    """Persist one governed Temp Power actuals-capture review record."""
    return await persist_temp_power_actuals_capture_review(request=request, actor=actor)
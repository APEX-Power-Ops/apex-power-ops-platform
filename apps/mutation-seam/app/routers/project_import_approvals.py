"""
Project Miner import-candidate approval persistence router.
"""
from fastapi import APIRouter, Depends

from app.auth.jwt import Actor, get_current_actor
from app.envelope.request import MutationRequest
from app.envelope.response import MutationResponse
from app.project_import_approval_persistence import persist_project_import_approval

router = APIRouter(prefix="/api/v1/mutations", tags=["project-import-approvals"])


@router.post("/project-import-approvals", response_model=MutationResponse)
async def mutate_project_import_approvals(
    request: MutationRequest,
    actor: Actor = Depends(get_current_actor),
) -> MutationResponse:
    """Persist one governed Project Miner import approval record."""
    return await persist_project_import_approval(request=request, actor=actor)

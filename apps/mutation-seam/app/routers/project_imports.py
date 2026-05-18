"""
Project Miner import mutation router.
"""
from fastapi import APIRouter, Depends

from app.auth.jwt import Actor, get_current_actor
from app.envelope.request import MutationRequest
from app.envelope.response import MutationResponse
from app.project_import_persistence import persist_project_import

router = APIRouter(prefix="/api/v1/mutations", tags=["project-imports"])


@router.post("/project-imports", response_model=MutationResponse)
async def mutate_project_imports(
    request: MutationRequest,
    actor: Actor = Depends(get_current_actor),
) -> MutationResponse:
    """Persist the approved Project Miner import into governed seam rows."""
    return await persist_project_import(request=request, actor=actor)

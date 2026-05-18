from fastapi import APIRouter, Depends

from app.auth.jwt import Actor, get_current_actor
from app.envelope.request import MutationRequest
from app.envelope.response import MutationResponse
from app.project_import_task_plan_persistence import persist_project_import_task_plan

router = APIRouter(prefix="/api/v1/mutations", tags=["project-import-task-plans"])


@router.post("/project-import-task-plans", response_model=MutationResponse)
async def mutate_project_import_task_plans(
    request: MutationRequest,
    actor: Actor = Depends(get_current_actor),
) -> MutationResponse:
    """Persist one governed Project Miner manual task plan."""
    return await persist_project_import_task_plan(request=request, actor=actor)
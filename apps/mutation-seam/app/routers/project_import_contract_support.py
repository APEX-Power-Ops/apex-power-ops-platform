from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from fastapi.responses import JSONResponse

from app.auth.jwt import Actor, get_current_actor, is_dev_fallback_actor
from app.project_import_contract_support_models import (
    ProjectImportContractSupportMutationRequest,
    ProjectImportContractSupportReadbackQuery,
)
from app.project_import_contract_support_persistence import (
    CONTRACT_SUPPORT_ALLOWED_ROLES,
    CONTRACT_SUPPORT_RUNTIME_FIELD_ROLE,
    load_project_import_contract_support_status,
    persist_project_import_contract_support,
)


router = APIRouter(tags=["project-import-contract-support"])


async def get_strict_current_actor(
    authorization: Optional[str] = Header(None),
) -> Actor:
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header required",
        )

    actor = await get_current_actor(authorization=authorization)
    if is_dev_fallback_actor(actor):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )
    return actor


def _ensure_route_role(actor: Actor) -> None:
    if actor.actor_role not in CONTRACT_SUPPORT_ALLOWED_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "UNAUTHORIZED_ROLE",
                "actor_role": actor.actor_role,
                "blocked_runtime_field_role": CONTRACT_SUPPORT_RUNTIME_FIELD_ROLE,
                "allowed_roles": sorted(CONTRACT_SUPPORT_ALLOWED_ROLES),
            },
        )


@router.post("/api/v1/mutations/project-import-contract-support")
async def mutate_project_import_contract_support(
    request: ProjectImportContractSupportMutationRequest,
    actor: Actor = Depends(get_strict_current_actor),
):
    _ensure_route_role(actor)
    response = persist_project_import_contract_support(request.model_dump(), actor)
    return JSONResponse(status_code=int(response.get("http_status", 200)), content=response)


@router.get("/api/v1/reads/project-import-contract-support-status")
async def read_project_import_contract_support_status(
    project_id: str = Query(...),
    candidate_id: str = Query(...),
    source_fingerprint: str = Query(...),
    actor: Actor = Depends(get_strict_current_actor),
):
    _ensure_route_role(actor)
    query = ProjectImportContractSupportReadbackQuery(
        project_id=project_id,
        candidate_id=candidate_id,
        source_fingerprint=source_fingerprint,
    )
    response = load_project_import_contract_support_status(query, actor)
    return JSONResponse(status_code=int(response.get("http_status", 200)), content=response)

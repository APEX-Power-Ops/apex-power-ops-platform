from fastapi import APIRouter, Query

from learning_resolver import resolve

from .schemas import ResolvedResourceOut, ResourcesContext, ResourcesResponse

router = APIRouter(prefix="/api/v1/learning", tags=["learning"])


@router.get("/resources", response_model=ResourcesResponse)
def get_resources(
    neta_section: str = Query(..., min_length=1),
    level: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
) -> ResourcesResponse:
    items = resolve(neta_section, level=level, limit=limit)
    return ResourcesResponse(
        context=ResourcesContext(neta_section=neta_section, level=level, limit=limit),
        resources=[ResolvedResourceOut(**vars(r)) for r in items],
    )

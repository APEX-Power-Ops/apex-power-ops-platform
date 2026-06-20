from fastapi import APIRouter, HTTPException, Query, status

from learning_resolver import list_sections, resolve

from .schemas import ResolvedResourceOut, ResourcesContext, ResourcesResponse, SectionsResponse

router = APIRouter(prefix="/api/v1/learning", tags=["learning"])


@router.get("/resources", response_model=ResourcesResponse)
def get_resources(
    neta_section: str | None = Query(default=None),
    level: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
) -> ResourcesResponse:
    if not neta_section or not neta_section.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="neta_section is required")
    if level is not None and level not in {"II", "III", "IV"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="level must be II, III, or IV")
    section = neta_section.strip()
    items = resolve(section, level=level, limit=limit)
    return ResourcesResponse(
        context=ResourcesContext(neta_section=section, level=level, limit=limit),
        resources=[ResolvedResourceOut(**vars(r)) for r in items],
    )


@router.get("/sections", response_model=SectionsResponse)
def get_sections(limit: int = Query(default=500, ge=1, le=2000)) -> SectionsResponse:
    return SectionsResponse(sections=list_sections(limit=limit))

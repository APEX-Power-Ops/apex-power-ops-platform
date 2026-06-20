from pydantic import BaseModel


class ResolvedResourceOut(BaseModel):
    resource_type: str
    title: str
    source: str
    reference: dict
    is_primary: bool
    is_mandatory: bool
    cert_level: str | None = None
    score: float
    why: str


class ResourcesContext(BaseModel):
    neta_section: str
    level: str | None = None
    limit: int


class ResourcesResponse(BaseModel):
    context: ResourcesContext
    resources: list[ResolvedResourceOut]

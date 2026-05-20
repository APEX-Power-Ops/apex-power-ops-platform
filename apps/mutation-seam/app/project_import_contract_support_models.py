from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field


class ScopeLaborDetailRow(BaseModel):
    quoted_hours: float
    scope_id: str = Field(..., min_length=1)
    scope_name: str = Field(..., min_length=1)
    scope_pool_amount: float


class ApparatusFinancialRow(BaseModel):
    apparatus_id: str = Field(..., min_length=1)
    apparatus_name: str = Field(..., min_length=1)
    quoted_hours: float
    quoted_revenue: float
    recognition_rate_per_hour_snapshot: float
    scope_id: str = Field(..., min_length=1)


class ProjectImportContractSupportPayload(BaseModel):
    apparatus_financials: list[ApparatusFinancialRow]
    candidate_id: str = Field(..., min_length=1)
    contract_value: float
    idempotency_key: str = Field(..., min_length=1)
    mutation_id: str = Field(..., min_length=1)
    project_id: str = Field(..., min_length=1)
    scope_labor_details: list[ScopeLaborDetailRow]
    snapshot_kind: str = Field(..., min_length=1)
    source_fingerprint: str = Field(..., min_length=1)
    total_quoted_hours: float


class ProjectImportContractSupportMutationRequest(BaseModel):
    idempotency_key: str = Field(..., min_length=1)
    mutation_class: Literal["A", "B", "C"]
    action_type: str = Field(..., min_length=1)
    entity_id: Optional[str] = None
    payload: ProjectImportContractSupportPayload
    reason: Optional[str] = None
    source: Literal["online", "offline_queue"] = "online"
    client_timestamp: str = Field(..., min_length=1)
    dry_run: bool = False
    force_failure: Optional[str] = None


class ProjectImportContractSupportReadbackQuery(BaseModel):
    project_id: str = Field(..., min_length=1)
    candidate_id: str = Field(..., min_length=1)
    source_fingerprint: str = Field(..., min_length=1)

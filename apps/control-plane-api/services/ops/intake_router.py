"""
Ops Intake Router — skeleton (Task 12).

Routes are filled in Task 13 after ops-intake is installed in the venv.
This module is import-gated: it is only imported when OPS_DEV_DSN is set
(see main.py _ops_intake_enabled block), so heavy ops_intake imports belong
in Task 13, not here.
"""

from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/ops/intake", tags=["ops-intake"])

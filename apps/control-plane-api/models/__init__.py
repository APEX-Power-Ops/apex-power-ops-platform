"""
TCC v5.0 Models Package
=======================
SQLAlchemy ORM models for TCC v5.0 Supabase PostgreSQL database.

This package contains models for the 33-table active ORM-backed backend slice.

The live Supabase database currently contains additional accepted TCC tables,
including EMT tables and `tcc.etu_settings`, that remain intentionally outside
this active model package until Phase 3 reconciliation or later runtime work
requires ORM coverage.

The active model package contains:

Reference Tables (3):
- Manufacturer
- TripType
- TripStyle

Breaker Type Tables (3):
- BrkICCB
- BrkMCCB
- BrkPCB

Breaker Style Tables (3):
- BrkICCBStyle
- BrkMCCBStyle
- BrkPCBStyle

TMT Tables (5):
- TMTFrame
- TMTAmp
- TMTCurve
- TMTSetting
- TMTThermalAdj

ETU Core Tables (2):
- ETUPlug
- ETUSensor

ETU Pickups Tables (5):
- ETULTPUPickup
- ETULTPUMultiplier
- ETUSTPUPickup
- ETUInstPickup
- ETUGFPUPickup

ETU Delay Band Tables (3):
- ETULTDBand
- ETUSTDBand
- ETUGFDBand

ETU Equation Tables (2):
- ETUSTDEquation
- ETUGFDEquation

ETU Curve/Parameter Tables (5):
- ETUInstCurve
- ETUSensorParam
- ETULTDParam
- ETUSTPUOverride
- ETUSensorMaint

User Data Tables (2):
- TestPlan
- TestResult

The user-data ORM slice is aligned to the live UUID-backed demo persistence
tables, including JSON snapshot columns, while final authenticated ownership
enforcement remains a separate Phase 5 runtime and migration task.

Total: 33 models for 2,475,137 database rows
"""

# Base declarative class
from .base import Base

# Reference Models (3)
from .reference import (
    Manufacturer,
    TripType,
    TripStyle
)

# Breaker Models (6)
from .breakers import (
    BrkICCB,
    BrkMCCB,
    BrkPCB,
    BrkICCBStyle,
    BrkMCCBStyle,
    BrkPCBStyle
)

# TMT Models (5)
from .tmt import (
    TMTFrame,
    TMTAmp,
    TMTCurve,
    TMTSetting,
    TMTThermalAdj
)

# ETU Core Models (2)
from .etu_core import (
    ETUPlug,
    ETUSensor
)

# ETU Pickups Models (5)
from .etu_pickups import (
    ETULTPUPickup,
    ETULTPUMultiplier,
    ETUSTPUPickup,
    ETUInstPickup,
    ETUGFPUPickup
)

# ETU Delay Band Models (3)
from .etu_bands import (
    ETULTDBand,
    ETUSTDBand,
    ETUGFDBand
)

# ETU Equation Models (2)
from .etu_equations import (
    ETUSTDEquation,
    ETUGFDEquation
)

# ETU Curve/Parameter Models (5)
from .etu_curves import (
    ETUInstCurve,
    ETUSensorParam,
    ETULTDParam,
    ETUSTPUOverride,
    ETUSensorMaint
)

# User Data Models (2)
from .user import (
    TestPlan,
    TestResult
)

# PM/Work Domain Enums (16)
from .work_enums import (
    ProvenanceSource,
    ProvenanceStatus,
    ProjectStatus,
    WPLifecycle,
    WorkType,
    Priority,
    BillingState,
    TaskLifecycle,
    TaskType,
    DependencyType,
    AssignmentRole,
    IssueType,
    Severity,
    IssueStatus,
    ResolutionType,
    SnapshotStatus,
    WORK_ENUM_REGISTRY,
)

# Org Domain Models (4) — packet 011e
from .org import (
    Client,
    Site,
    BusinessUnit,
    Contract,
    ORG_MODEL_REGISTRY,
)

# Identity Domain Models (3) — packet 012e
from .identity import (
    User,
    Employee,
    Crew,
    IDENTITY_MODEL_REGISTRY,
)

# PM/Work Domain Models (8)
from .work import (
    Project,
    WBSNode,
    WorkPackage,
    Task,
    Dependency,
    Assignment,
    ExecutionIssue,
    ProgressSnapshot,
    WORK_MODEL_REGISTRY,
)

# Export all models
__all__ = [
    # Base
    'Base',

    # Reference (3)
    'Manufacturer',
    'TripType',
    'TripStyle',

    # Breakers (6)
    'BrkICCB',
    'BrkMCCB',
    'BrkPCB',
    'BrkICCBStyle',
    'BrkMCCBStyle',
    'BrkPCBStyle',

    # TMT (5)
    'TMTFrame',
    'TMTAmp',
    'TMTCurve',
    'TMTSetting',
    'TMTThermalAdj',

    # ETU Core (2)
    'ETUPlug',
    'ETUSensor',

    # ETU Pickups (5)
    'ETULTPUPickup',
    'ETULTPUMultiplier',
    'ETUSTPUPickup',
    'ETUInstPickup',
    'ETUGFPUPickup',

    # ETU Delay Bands (3)
    'ETULTDBand',
    'ETUSTDBand',
    'ETUGFDBand',

    # ETU Equations (2)
    'ETUSTDEquation',
    'ETUGFDEquation',

    # ETU Curves/Parameters (5)
    'ETUInstCurve',
    'ETUSensorParam',
    'ETULTDParam',
    'ETUSTPUOverride',
    'ETUSensorMaint',

    # User Data (2)
    'TestPlan',
    'TestResult',

    # PM/Work Domain Enums (16)
    'ProvenanceSource',
    'ProvenanceStatus',
    'ProjectStatus',
    'WPLifecycle',
    'WorkType',
    'Priority',
    'BillingState',
    'TaskLifecycle',
    'TaskType',
    'DependencyType',
    'AssignmentRole',
    'IssueType',
    'Severity',
    'IssueStatus',
    'ResolutionType',
    'SnapshotStatus',
    'WORK_ENUM_REGISTRY',

    # Org Domain Models (4)
    'Client',
    'Site',
    'BusinessUnit',
    'Contract',
    'ORG_MODEL_REGISTRY',

    # Identity Domain Models (3)
    'User',
    'Employee',
    'Crew',
    'IDENTITY_MODEL_REGISTRY',

    # PM/Work Domain Models (8)
    'Project',
    'WBSNode',
    'WorkPackage',
    'Task',
    'Dependency',
    'Assignment',
    'ExecutionIssue',
    'ProgressSnapshot',
    'WORK_MODEL_REGISTRY',
]

# Model count verification
# Base (1) + TCC models (33) + Work enums (16) + enum registry (1)
# + Org models (4) + org registry (1) + Identity models (3) + identity registry (1)
# + Work models (8) + model registry (1) = 69
assert len(__all__) == 69, f"Expected 69 exports, got {len(__all__)}"

print("TCC v5.0 + PM/Work Models Package Loaded Successfully (Supabase Schema)")
print(f"Total Exports: {len(__all__)}")
print(f"  TCC Models: 33 tables")
print(f"  PM/Work Enums: 16 enum types")
print(f"  PM/Work Models: 8 tables")
print("Database: PostgreSQL (Supabase)")

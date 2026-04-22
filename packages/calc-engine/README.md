# Apex Calc Engine

This package is the first extracted shared-domain snapshot of the legacy TCC calculation engine.

Current posture:
- historically extracted from the `tcc_v5_backend` lineage and now maintained from the platform root
- focused on reusable calculation logic and the ETU/TMT ORM surface it currently depends on
- now the intended implementation authority for the calc domain used by `apps/control-plane-api`

Included in this phase:
- ETU pickup, LTD, IEEE, merge, and TMT calculation modules
- the minimal ORM models those modules require today, including the reference and user-data relationships needed for ETU mapper configuration
- offline golden-fixture tests for the package boundary

Deferred for later planning:
- schema remapping into the canonical platform entity model
- elimination of remaining app-local ORM duplication outside the calc-domain boundary
- service contract hardening for non-SQLAlchemy consumers

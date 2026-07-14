"""PM/Ops Phase-0 emergency-containment tooling (design-only until per-action GO).

This package holds the operator-run tooling for the PM/Ops P0 containment lane:

* ``binding``          -- shared target-binding discipline (``bind_target`` +
                          helpers). Imported IDENTICALLY by P0-A's evidence
                          script and P0-E's readiness probes so both bind to the
                          production project ``fxoyniqnrlkxfligbxmg``.
* ``preserve_evidence`` -- P0-A read-only evidence capture (single guarded
                          ``REPEATABLE READ, READ ONLY`` transaction).

Nothing in this package mutates production, changes secrets, or repairs
connectivity. Execution against production requires an explicit, per-action
operator GO; the tooling itself is design-only.
"""

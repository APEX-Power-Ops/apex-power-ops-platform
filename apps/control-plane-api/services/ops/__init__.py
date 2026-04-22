"""Operator-facing maintenance + observability surface.

Packet 2026-04-16-pm-schema-019g introduces this package as the home for
ops-lane endpoints that are NOT part of the PM write surface.  The first
resident is the minimal PM idempotency stats surface — strictly read-only
and strictly outside ``/api/v1/work/*``.
"""

"""Recognition-math integration test against a seeded public slice (dev only).

Runs the SAME SQL constant the endpoint runs, so the derivation is proven
end-to-end. Skipped unless RECOGNITION_TEST_DSN points at the seeded slice.
"""
from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text  # noqa: E402

RECOGNITION_TEST_DSN = os.environ.get("RECOGNITION_TEST_DSN")

pytestmark = pytest.mark.integration


@pytest.mark.skipif(not RECOGNITION_TEST_DSN, reason="RECOGNITION_TEST_DSN not set")
def test_recognition_math_against_seeded_slice():
    from services.ops.router import REVENUE_RECOGNITION_SQL

    engine = create_engine(RECOGNITION_TEST_DSN)
    with engine.connect() as conn:
        rows = conn.execute(text(REVENUE_RECOGNITION_SQL), {"limit": 25}).mappings().all()

    by_scope = {r["scope_name"]: r for r in rows}

    one = by_scope["Scope One"]
    assert float(one["quoted_revenue"]) == 6000.0
    assert float(one["recognized_revenue"]) == 3000.0
    assert float(one["recognition_percent"]) == 50.0
    assert float(one["billable_now"]) == 3000.0
    assert one["total_apparatus"] == 3
    assert one["completed_apparatus"] == 2

    two = by_scope["Scope Two"]
    assert float(two["quoted_revenue"]) == 5000.0
    assert float(two["recognized_revenue"]) == 0.0
    assert float(two["recognition_percent"]) == 0.0
    assert two["completed_apparatus"] == 0

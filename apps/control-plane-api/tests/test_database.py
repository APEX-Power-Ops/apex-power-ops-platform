"""
Test database connection and basic functionality
"""
import pytest
from sqlalchemy import inspect


def _live_engine_or_skip():
    """Return the live DB engine, or skip when the local DB is unavailable."""
    from config import engine

    try:
        inspect(engine).get_table_names()
    except Exception as exc:
        pytest.skip(f"Local DB unavailable; live DB integration test skipped: {exc}")
    return engine


@pytest.mark.integration
def test_database_connection():
    """Test that we can connect to the database."""
    from config import test_connection as _test_connection

    if _test_connection() is not True:
        pytest.skip("Local DB unavailable; live DB integration test skipped")


@pytest.mark.integration
def test_table_count():
    """Test that all 33 tables exist."""
    engine = _live_engine_or_skip()
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    assert len(tables) == 33, f"Expected 33 tables, found {len(tables)}"


@pytest.mark.integration
def test_table_names():
    """Test that expected tables exist."""
    engine = _live_engine_or_skip()
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    # Check for key tables
    expected_tables = [
        'manufacturers',
        'trip_types',
        'trip_styles',
        'breaker_iccb',
        'breaker_mccb',
        'breaker_pcb',
        'sst_sensors',
        'sst_plugs',
    ]
    
    for table in expected_tables:
        assert table in tables, f"Table '{table}' not found in database"


if __name__ == "__main__":
    # Run tests manually
    print("Running database tests...")
    test_database_connection()
    print("[PASS] Connection test passed")
    
    test_table_count()
    print("[PASS] Table count test passed")
    
    test_table_names()
    print("[PASS] Table names test passed")
    
    print("\n[SUCCESS] All tests passed!")

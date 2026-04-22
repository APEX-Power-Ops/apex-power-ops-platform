"""
Test database connection and basic functionality
"""
import pytest
from config import engine, test_connection
from sqlalchemy import inspect


def test_database_connection():
    """Test that we can connect to the database."""
    assert test_connection() is True


def test_table_count():
    """Test that all 33 tables exist."""
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    assert len(tables) == 33, f"Expected 33 tables, found {len(tables)}"


def test_table_names():
    """Test that expected tables exist."""
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

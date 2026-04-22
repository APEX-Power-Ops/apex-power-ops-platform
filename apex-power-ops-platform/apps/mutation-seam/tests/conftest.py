"""
Pytest configuration and fixtures.
"""
import pytest
from fastapi.testclient import TestClient

from app.db.memory_store import store
from app.main import app


@pytest.fixture
def client():
    """Provide a test client."""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_store():
    """Reset the memory store before each test."""
    store.reset()
    yield
    # Cleanup after test
    store.reset()


@pytest.fixture
def sample_apparatus_id():
    """Return a sample apparatus ID from the seeded data."""
    return "app-001"


@pytest.fixture
def sample_task_id():
    """Return a sample task ID from the seeded data."""
    return "task-001"


@pytest.fixture
def sample_project_id():
    """Return the sample project ID."""
    return "proj-001"


@pytest.fixture
def field_tech_token():
    """Return a base64-encoded token for a field tech."""
    import base64
    import json

    payload = {
        "actor_id": "tech-001",
        "actor_role": "field_tech",
        "project_scope": ["proj-001"],
    }
    encoded = base64.b64encode(json.dumps(payload).encode()).decode()
    return f"Bearer {encoded}"


@pytest.fixture
def task_lead_token():
    """Return a base64-encoded token for a task lead."""
    import base64
    import json

    payload = {
        "actor_id": "lead-001",
        "actor_role": "task_lead",
        "project_scope": ["proj-001"],
    }
    encoded = base64.b64encode(json.dumps(payload).encode()).decode()
    return f"Bearer {encoded}"

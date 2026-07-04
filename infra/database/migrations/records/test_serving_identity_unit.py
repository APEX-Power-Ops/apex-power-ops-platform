import os, sys
import pytest
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from serving_identity import assert_serving_identity, ServingIdentityError  # noqa: E402


class _FakeCur:
    def __init__(self, row): self._row = row
    def execute(self, *a, **k): pass
    def fetchone(self): return self._row
    def __enter__(self): return self
    def __exit__(self, *a): return False


class _FakeConn:
    def __init__(self, row): self._row = row
    def cursor(self): return _FakeCur(self._row)


def test_pass_sanctioned():
    assert_serving_identity(_FakeConn(("records_api", "records_api", False, False)))


def test_fail_set_role_masks_login():
    with pytest.raises(ServingIdentityError):
        assert_serving_identity(_FakeConn(("postgres", "records_api", True, False)))


def test_fail_superuser():
    with pytest.raises(ServingIdentityError):
        assert_serving_identity(_FakeConn(("postgres", "postgres", True, False)))


def test_fail_bypassrls():
    with pytest.raises(ServingIdentityError):
        assert_serving_identity(_FakeConn(("service_role", "service_role", False, True)))


def test_fail_owner_role():
    with pytest.raises(ServingIdentityError):
        assert_serving_identity(_FakeConn(("records_owner", "records_owner", False, False)))


def test_fail_unsanctioned():
    with pytest.raises(ServingIdentityError):
        assert_serving_identity(_FakeConn(("some_role", "some_role", False, False)))

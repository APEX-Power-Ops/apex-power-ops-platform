# infra/database/migrations/records/conftest.py
"""Thin pytest shim: env defaults now live in _dbtest.py (the single source).

Kept so standalone per-file pytest runs stay portable on host and laptop; the
validation runner exports fully-resolved values into child environments and
never relies on these setdefaults.
"""
import os

import _dbtest

os.environ.setdefault("PSQL_EXE", _dbtest.psql_exe())

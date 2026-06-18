"""Host-portable defaults for the records migration tests.

pytest imports conftest.py BEFORE the test modules, so setting these env DEFAULTS
here makes every test's module-level os.environ.get(...) resolve portably on
either the Olares host or the laptop — without editing each test file. Existing
env values always win (setdefault).

The NETA extracts are external study material: provisioned on the host at
~/neta-source/NETA-Data (NOT committed to this public repo).
"""
import os
import shutil

# psql binary — prefer one on PATH (host: /usr/bin/psql), else the Windows install.
os.environ.setdefault(
    "PSQL_EXE",
    shutil.which("psql") or r"C:\Program Files\PostgreSQL\18\bin\psql.exe",
)

# NETA source extracts — host mirror if provisioned, else the laptop OneDrive checkout.
_WIN = r"C:\Users\jjswe\OneDrive\Documents\GitHub\neta-ett-study-material\Development\NETA-Data"
_HOST = os.path.expanduser("~/neta-source/NETA-Data")
_DATA = _HOST if os.path.isdir(_HOST) else _WIN
os.environ.setdefault("NETA_DATA_DIR", _DATA)
os.environ.setdefault(
    "NETA_JSON",
    os.path.join(_DATA, "NETA-Master-Equipment-Table-Enhanced.json"),
)

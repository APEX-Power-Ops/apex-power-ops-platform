"""Offline tests for disposition_provenance.py (git HEAD / clean-worktree checks)."""

import os
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import disposition_provenance as dp  # noqa: E402


def _git(d, *args):
    subprocess.run(["git", "-C", d, *args], check=True, capture_output=True, text=True)


def _init_repo(d):
    _git(d, "init", "-q")
    _git(d, "config", "user.email", "t@example.com")
    _git(d, "config", "user.name", "t")
    with open(os.path.join(d, "f.txt"), "w", encoding="utf-8") as fh:
        fh.write("x\n")
    _git(d, "add", "f.txt")
    _git(d, "-c", "commit.gpgsign=false", "commit", "-q", "-m", "init")
    return subprocess.run(["git", "-C", d, "rev-parse", "HEAD"], check=True,
                          capture_output=True, text=True).stdout.strip()


def test_head_sha_returns_commit():
    with tempfile.TemporaryDirectory() as d:
        head = _init_repo(d)
        assert dp.git_head_sha(d) == head


def test_worktree_clean_true_then_dirty():
    with tempfile.TemporaryDirectory() as d:
        _init_repo(d)
        assert dp.git_worktree_clean(d) is True
        with open(os.path.join(d, "untracked.txt"), "w", encoding="utf-8") as fh:
            fh.write("y\n")
        assert dp.git_worktree_clean(d) is False


def test_non_git_dir_fails_closed():
    with tempfile.TemporaryDirectory() as d:
        assert dp.git_head_sha(d) is None
        assert dp.git_worktree_clean(d) is False


ALL = [
    ("head_sha_returns_commit", test_head_sha_returns_commit),
    ("worktree_clean_true_then_dirty", test_worktree_clean_true_then_dirty),
    ("non_git_dir_fails_closed", test_non_git_dir_fails_closed),
]

if __name__ == "__main__":
    ok = True
    for name, fn in ALL:
        try:
            fn()
            print(f"PASS {name}")
        except Exception as exc:  # noqa: BLE001
            ok = False
            print(f"FAIL {name}: {type(exc).__name__}: {exc}")
    sys.exit(0 if ok else 1)

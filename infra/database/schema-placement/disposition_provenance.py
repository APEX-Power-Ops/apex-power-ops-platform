"""Git checkout-provenance checks shared by the disposition tooling (SP026). Pure git-subprocess
helpers with NO crypto and NO policy. The collector, the census-acceptance gate, and the preapply
checker all bind their evidence/trust to a reviewed commit through these functions. Kept here (not in
collect_disposition) so the destructive checker never imports the collector."""

from __future__ import annotations


def git_head_sha(repo_dir):
    """Return the HEAD sha of repo_dir, or None if it cannot be determined (fail-closed)."""
    import subprocess  # noqa: PLC0415 -- keeps subprocess off the offline import path
    try:
        out = subprocess.run(["git", "-C", repo_dir, "rev-parse", "HEAD"],
                             capture_output=True, text=True, check=True, timeout=10)
        return out.stdout.strip() or None
    except Exception:  # noqa: BLE001
        return None


def git_worktree_clean(repo_dir):
    """True only if the git worktree has NO tracked-modified AND NO untracked changes. Fail-closed:
    any error => treated as dirty. A repo_sha only identifies the merged commit if the tree is clean."""
    import subprocess  # noqa: PLC0415
    try:
        out = subprocess.run(["git", "-C", repo_dir, "status", "--porcelain"],
                             capture_output=True, text=True, check=True, timeout=10)
        return out.stdout.strip() == ""
    except Exception:  # noqa: BLE001
        return False

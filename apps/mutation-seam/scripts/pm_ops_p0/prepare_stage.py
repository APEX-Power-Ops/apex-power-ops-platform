"""Stage 1 of P0-A evidence capture: build a verified, frozen, secret-free STAGE.

RI2-3 finding 1 (the self-verifying-worktree bypass). The evidence tool cannot authenticate
ITSELF while running from the mutable worktree: a repo-controlled clean filter
(`.git/info/attributes`), `remote.origin.uploadpack`, `git update-index --assume-unchanged`,
an ignored timestamp-valid `.pyc`, or simply a modified verifier hidden by an index flag can
make the old in-process preflight report "pristine" while attacker code runs in the
secret-bearing process. This module replaces that model with a two-stage design:

* **prepare (here, SECRET-FREE):** never reads a DSN. It pins a commit, then extracts the
  P0-A tooling package's `.py` blobs DIRECTLY FROM THE PINNED COMMIT OBJECT via
  ``git cat-file`` (which applies no working-tree filters, honours no index flags, and reads
  no `.pyc`), hash-verifies each against ``git ls-tree``, stages the hash-pinned dependency
  bundle, computes a STAGE DIGEST over the staged package, and freezes the stage read-only.
* **capture (`preserve_evidence.py capture`, SECRET-BEARING):** runs ``python -I -S``
  EXCLUSIVELY from the stage, imports nothing from the worktree, runs NO git, and refuses
  unless the stage matches the operator's out-of-band ``--expect-stage-digest``.

Because prepare is secret-free and the bytes come from the content-addressed commit object,
a compromised worktree/config cannot exfiltrate a secret here and cannot substitute the
staged bytes without changing their hashes (and thus the digest the operator verifies
out-of-band before injecting any secret). Stdlib only; no DSN, no database, no app import.
"""

from __future__ import annotations

import os
import sys

# Even secret-free, refuse a shadowable interpreter so a worktree `.pth`/PYTHONPATH cannot run
# during THIS process either (RI2 finding 1). Restrict sys.path to interpreter-prefix entries
# before any shadowable import, using only the builtin sys+os.
_TRUSTED_SYS_PREFIXES = tuple(
    os.path.realpath(getattr(sys, _attr))
    for _attr in ("prefix", "base_prefix", "exec_prefix", "base_exec_prefix")
    if getattr(sys, _attr, "")
)
sys.path[:] = [
    _p
    for _p in sys.path
    if _p
    and any(
        os.path.realpath(_p) == _b or os.path.realpath(_p).startswith(_b + os.sep)
        for _b in _TRUSTED_SYS_PREFIXES
    )
]

import argparse  # noqa: E402
import hashlib  # noqa: E402
import json  # noqa: E402
import logging  # noqa: E402
import subprocess  # noqa: E402
from datetime import datetime, timezone  # noqa: E402
from pathlib import Path  # noqa: E402

PROJECT_REF = "fxoyniqnrlkxfligbxmg"
# the package whose blobs the secret-bearing capture runs from; extracted from the pinned
# commit, NOT the worktree. Only these code files are staged (tests/README/requirements are
# not run by capture).
PACKAGE_REL = "apps/mutation-seam/scripts/pm_ops_p0"
STAGED_MODULES = (
    "__init__.py",
    "binding.py",
    "finalize_closeout.py",
    "preserve_evidence.py",
)
STAGE_DIGEST_NAME = "stage_digest.txt"
STAGE_PROVENANCE_NAME = "stage_provenance.json"

log = logging.getLogger("pm_ops_p0.prepare_stage")


class PrepareRefusal(Exception):
    """A fail-closed refusal carrying a stable, value-free code."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


# --- git preflight (secret-free; hardened against config-driven code execution) -------------

_GIT_HARDENING = (
    "-c",
    "core.fsmonitor=false",
    "-c",
    "core.hooksPath=/dev/null",
    "-c",
    "credential.helper=",
    "-c",
    "core.sshCommand=ssh",
    "-c",
    "protocol.ext.allow=never",
)
_GIT_ENV_ALLOW = (
    "PATH",
    "HOME",
    "USER",
    "LOGNAME",
    "LANG",
    "TERM",
    "TMPDIR",
    "SSH_AUTH_SOCK",
    "SSH_AGENT_PID",
)


def _git_env() -> dict[str, str]:
    env = {k: os.environ[k] for k in _GIT_ENV_ALLOW if k in os.environ}
    for key, value in os.environ.items():
        if key.startswith("LC_"):
            env[key] = value
    env["GIT_CONFIG_GLOBAL"] = "/dev/null"
    env["GIT_CONFIG_SYSTEM"] = "/dev/null"
    return env


def _repo_root() -> Path:
    start = Path(__file__).resolve()
    for parent in (start, *start.parents):
        if (parent / ".git").exists():
            return parent
    raise PrepareRefusal("repo_root_not_found")


def _make_git(repo_root: Path):
    def _git(*args: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["git", "-C", str(repo_root), *_GIT_HARDENING, *args],
            capture_output=True,
            text=True,
            check=False,
            env=_git_env(),
        )

    return _git


def _assert_governance(repo_root: Path, expect_repo_sha: str) -> str:
    """Refuse unless the tree is pristine and HEAD == origin/main == expect_repo_sha.

    Defence-in-depth only: the AUTHORITATIVE bytes come from ``git cat-file`` of the pinned
    commit (below), not the worktree, so even a hostile fetch/config here cannot taint the
    stage. Returns the confirmed HEAD sha.
    """
    git = _make_git(repo_root)
    head = git("rev-parse", "HEAD")
    if head.returncode != 0:
        raise PrepareRefusal("git_unavailable")
    head_sha = head.stdout.strip()
    if head_sha != expect_repo_sha:
        raise PrepareRefusal("repo_sha_mismatch")
    status = git(
        "-c",
        "status.showUntrackedFiles=normal",
        "status",
        "--porcelain",
        "--untracked-files=all",
    )
    if not (status.returncode == 0 and status.stdout.strip() == ""):
        raise PrepareRefusal("repo_dirty")
    origin_main: str | None = None
    if git("fetch", "--quiet", "origin", "refs/heads/main").returncode == 0:
        fh = git("rev-parse", "--verify", "--quiet", "FETCH_HEAD")
        if fh.returncode == 0 and fh.stdout.strip():
            origin_main = fh.stdout.strip()
    if origin_main is None:
        raise PrepareRefusal("origin_main_unresolvable")
    if origin_main != expect_repo_sha:
        raise PrepareRefusal("repo_head_not_origin_main")
    return head_sha


# --- extraction FROM THE PINNED COMMIT OBJECT (immune to worktree/index/filter/.pyc) --------


def _git_blob_sha(data: bytes) -> str:
    """git's own object id for a blob: sha1('blob <len>\\0' + content)."""
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def _extract_package(
    repo_root: Path, expect_repo_sha: str, stage_pkg: Path
) -> dict[str, str]:
    """Extract each STAGED_MODULES blob at ``expect_repo_sha`` into ``stage_pkg``.

    Uses ``git ls-tree`` (recorded blob ids) + ``git cat-file blob`` (raw object bytes). No
    working-tree read, so a clean filter / assume-unchanged / ignored .pyc / worktree edit is
    irrelevant. Each written file's git blob id is re-checked against ls-tree. Returns
    {module: sha256(content)}.
    """
    git = _make_git(repo_root)
    listing = git("ls-tree", "-r", "-z", expect_repo_sha, "--", PACKAGE_REL)
    if listing.returncode != 0:
        raise PrepareRefusal("pinned_tree_unreadable")
    # map basename -> blob id for the top-level package modules we stage
    blob_ids: dict[str, str] = {}
    for entry in listing.stdout.split("\0"):
        if not entry:
            continue
        meta, path = entry.split("\t", 1)
        _mode, otype, oid = meta.split(" ")
        if otype != "blob":
            continue
        rel = os.path.relpath(path, PACKAGE_REL).replace(os.sep, "/")
        if "/" in rel:  # only the package's top-level modules (skip tests/, etc.)
            continue
        blob_ids[rel] = oid
    stage_pkg.mkdir(parents=True)
    shas: dict[str, str] = {}
    for name in STAGED_MODULES:
        oid = blob_ids.get(name)
        if not oid:
            raise PrepareRefusal("staged_module_missing")
        blob = subprocess.run(
            ["git", "-C", str(repo_root), *_GIT_HARDENING, "cat-file", "blob", oid],
            capture_output=True,
            check=False,
            env=_git_env(),
        )
        if blob.returncode != 0:
            raise PrepareRefusal("pinned_blob_unreadable")
        data = blob.stdout
        if _git_blob_sha(data) != oid:  # belt: bytes match the recorded object id
            raise PrepareRefusal("pinned_blob_hash_mismatch")
        fd = os.open(stage_pkg / name, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o400)
        try:
            os.write(fd, data)
        finally:
            os.close(fd)
        shas[name] = hashlib.sha256(data).hexdigest()
    return shas


# --- dependency bundle staging (hash-pinned; manifest hash attested out-of-band) ------------


def _read_pinned_manifest(
    manifest_path: Path, expect_manifest_sha: str
) -> dict[str, str]:
    try:
        raw = manifest_path.read_bytes()
    except OSError:
        raise PrepareRefusal("bundle_manifest_unreadable") from None
    if hashlib.sha256(raw).hexdigest() != expect_manifest_sha.strip().lower():
        raise PrepareRefusal("bundle_manifest_untrusted")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        raise PrepareRefusal("bundle_manifest_malformed") from None
    entries: dict[str, str] = {}
    for line in text.splitlines():
        if not line.strip():
            continue
        parts = line.split(None, 1)
        if len(parts) != 2:
            raise PrepareRefusal("bundle_manifest_malformed")
        sha, rel = parts[0].strip().lower(), parts[1].strip()
        if (
            not rel
            or Path(rel).is_absolute()
            or ".." in Path(rel).parts
            or len(sha) != 64
        ):
            raise PrepareRefusal("bundle_manifest_malformed")
        entries[rel] = sha
    if not entries:
        raise PrepareRefusal("bundle_manifest_empty")
    return entries


def _stage_bundle(
    bundle_dir_arg: str, manifest_path: str, expect_manifest_sha: str, dest: Path
) -> None:
    """Verify + hash-while-copy the pinned dependency bundle into ``dest`` (no import here)."""
    manifest = _read_pinned_manifest(Path(manifest_path), expect_manifest_sha)
    root = Path(bundle_dir_arg)
    if root.is_symlink() or not root.is_dir():
        raise PrepareRefusal("bundle_dir_invalid")
    base = os.path.realpath(root)

    def _walk_err(_exc: OSError) -> None:
        raise PrepareRefusal("bundle_dir_unreadable")

    for dirpath, dirnames, filenames in os.walk(
        base, followlinks=False, onerror=_walk_err
    ):
        for nm in dirnames:
            if os.path.islink(os.path.join(dirpath, nm)):
                raise PrepareRefusal("bundle_unsafe_member")
        for nm in filenames:
            full = os.path.join(dirpath, nm)
            if os.path.islink(full):
                raise PrepareRefusal("bundle_unsafe_member")
            rel = os.path.relpath(full, base).replace(os.sep, "/")
            if rel not in manifest:
                raise PrepareRefusal("bundle_unlisted_file")
    dest.mkdir(parents=True)
    for rel, sha in manifest.items():
        src = os.path.join(base, rel)
        if os.path.islink(src) or not os.path.isfile(src):
            raise PrepareRefusal("bundle_member_missing")
        try:
            data = Path(src).read_bytes()
        except OSError:
            raise PrepareRefusal("bundle_member_unreadable") from None
        if hashlib.sha256(data).hexdigest() != sha:
            raise PrepareRefusal("bundle_hash_mismatch")
        out = dest / rel
        try:
            out.parent.mkdir(parents=True, exist_ok=True)
            fd = os.open(out, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o400)
            try:
                os.write(fd, data)
            finally:
                os.close(fd)
        except OSError:
            raise PrepareRefusal("bundle_stage_failed") from None


# --- stage digest + provenance + freeze -----------------------------------------------------


def compute_stage_digest(module_shas: dict[str, str]) -> str:
    """The out-of-band-attested identity of the staged package: a SHA-256 over the sorted
    ``<module>\\n<sha256hex>\\n`` lines. The operator computes the SAME value independently
    from the pinned commit and passes it to capture as ``--expect-stage-digest``."""
    body = "".join(f"{name}\n{module_shas[name]}\n" for name in sorted(module_shas))
    return hashlib.sha256(body.encode()).hexdigest()


def _freeze(stage: Path) -> None:
    for dirpath, dirnames, filenames in os.walk(stage):
        for nm in filenames:
            os.chmod(os.path.join(dirpath, nm), 0o400)
        for nm in dirnames:
            os.chmod(os.path.join(dirpath, nm), 0o500)
    os.chmod(stage, 0o500)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def prepare(
    *,
    expect_repo_sha: str,
    stage_dir: str,
    dependency_bundle: str,
    bundle_manifest: str,
    expect_bundle_manifest_sha256: str,
) -> str:
    """Build the frozen stage; return the stage digest. Value-free ``PrepareRefusal`` on failure."""
    stage = Path(stage_dir)
    if stage.exists():
        raise PrepareRefusal("stage_dir_exists")  # a fresh stage every run (no reuse)
    started = _utc_now_iso()
    root = _repo_root()
    head_sha = _assert_governance(root, expect_repo_sha)
    stage.mkdir(parents=True)  # 0700 by default (owner-only) until frozen
    module_shas = _extract_package(root, expect_repo_sha, stage / "pm_ops_p0")
    _stage_bundle(
        dependency_bundle,
        bundle_manifest,
        expect_bundle_manifest_sha256,
        stage / "deps",
    )
    digest = compute_stage_digest(module_shas)
    provenance = {
        "artifact": "pm_ops_p0.prepare_stage.provenance",
        "schema_version": 1,
        "expected_project_ref": PROJECT_REF,
        "repo_sha": head_sha,
        "expect_repo_sha": expect_repo_sha,
        "staged_module_sha256": module_shas,
        "stage_digest": digest,
        "dependency_bundle_manifest_sha256": expect_bundle_manifest_sha256.strip().lower(),
        "prepared_at_utc": started,
        "frozen_at_utc": _utc_now_iso(),
    }
    fd = os.open(
        stage / STAGE_PROVENANCE_NAME, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o400
    )
    try:
        os.write(fd, (json.dumps(provenance, indent=2, sort_keys=True) + "\n").encode())
    finally:
        os.close(fd)
    fd = os.open(stage / STAGE_DIGEST_NAME, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o400)
    try:
        os.write(fd, (digest + "\n").encode())
    finally:
        os.close(fd)
    _freeze(stage)
    return digest


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "P0-A stage 1 (SECRET-FREE): extract the tooling package from the pinned commit "
            "object into a frozen private stage + stage the hash-pinned dependency bundle. "
            "Run OUTSIDE Infisical injection; no DSN is read. Then verify the printed "
            "STAGE_DIGEST equals the GO's out-of-band value before running capture."
        )
    )
    parser.add_argument("--expect-repo-sha", required=True)
    parser.add_argument(
        "--stage-dir", required=True, help="fresh output dir (must not exist)"
    )
    parser.add_argument("--dependency-bundle", required=True)
    parser.add_argument("--bundle-manifest", required=True)
    parser.add_argument("--expect-bundle-manifest-sha256", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")
    args = build_parser().parse_args(argv)
    try:
        digest = prepare(
            expect_repo_sha=args.expect_repo_sha,
            stage_dir=args.stage_dir,
            dependency_bundle=args.dependency_bundle,
            bundle_manifest=args.bundle_manifest,
            expect_bundle_manifest_sha256=args.expect_bundle_manifest_sha256,
        )
    except PrepareRefusal as exc:
        print("RESULT FAIL")
        print(f"FAILURE {exc.code}")
        return 1
    except Exception as exc:  # noqa: BLE001
        log.warning("prepare failed: %s", type(exc).__name__)
        print("RESULT FAIL")
        print("FAILURE prepare_failed")
        return 1
    print("RESULT PASS")
    print(f"STAGE {args.stage_dir}")
    print(f"STAGE_DIGEST {digest}")
    return 0


def _isolation_gate(isolated: bool, no_site: bool) -> int | None:
    if not (isolated and no_site):
        print("RESULT FAIL")
        print("FAILURE interpreter_not_isolated_no_site")
        return 1
    return None


if __name__ == "__main__":
    _rc = _isolation_gate(sys.flags.isolated, sys.flags.no_site)
    sys.exit(_rc if _rc is not None else main())

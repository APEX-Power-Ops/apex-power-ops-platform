"""Fail-closed finalizer for the nine-category P0-A closeout (review round 3, finding 5).

``preserve_evidence.py`` captures only the DATABASE subset of P0-A. P0-A is complete only
when all nine design-§2 categories -- the script-captured DB evidence AND the operator/HTTP
captures (deployed OpenAPI, the ``/reset`` route + security, the backend classification, the
Render access logs) -- are present, hash-bound, and indexed. This finalizer verifies that,
fail-closed, and publishes a single ``closeout_index.json`` binding every artifact by
SHA-256, no-clobber.

It reads a closeout SPEC (JSON: each of categories 1..9 -> its artifact filenames under the
custody dir) and refuses on any of: a missing or duplicated category; an artifact path that
escapes the custody dir; a non-regular artifact (dir / symlink / device); a script artifact
absent from the evidence tool's ``manifest.sha256`` (unhashed) or whose bytes disagree with
it (hash mismatch); or an HTTP artifact that is not the expected valid JSON (a failed capture
that saved an error page). Every failure surfaces as a stable, value-free code.

Stdlib only -- no new dependency, no database, no network. Design-only until the operator's
separate ``P0-A READ-ONLY EVIDENCE`` GO.
"""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

MANIFEST_NAME = "manifest.sha256"
PROVENANCE_NAME = "00_provenance.json"
OUT_NAME = "closeout_index.json"
# the governed-run attestation the closeout leans on (must match preserve_evidence)
PROJECT_REF = "fxoyniqnrlkxfligbxmg"
EXPECTED_DB_ROLE = "postgres"
PROVENANCE_SCHEMA_VERSION = 2

# the nine design-§2 categories that a complete P0-A closeout must bind
REQUIRED_CATEGORIES = frozenset(range(1, 10))
# categories captured over HTTP; their artifacts must be the expected valid JSON, not an
# error page a failed `curl` saved (finding 5: "failed-HTTP ... categories fail")
HTTP_CATEGORIES = frozenset({1, 2})

# The REQUIRED source per category, per the runbook. The spec's declared source is
# VALIDATED against this (never trusted): categories 3/4/5/6/9 are script-captured DB
# evidence and MUST pass the manifest membership + hash binding; marking one "operator"
# would otherwise skip that binding entirely (Codex-xhigh P1).
CATEGORY_SOURCE = {
    1: "operator",  # deployed OpenAPI
    2: "operator",  # /reset route + security
    3: "script",  # effective privileges + membership closure
    4: "script",  # SECURITY DEFINER discovery + exact function ACL
    5: "script",  # counts
    6: "script",  # pg_default_acl
    7: "operator",  # backend classification
    8: "operator",  # Render /reset access logs
    9: "script",  # rollback inputs
}

# The EXACT tool-deterministic filenames each SCRIPT category must bind, per the runbook.
# Script evidence files have fixed names, so a spec cannot satisfy a category with the wrong
# (but manifest-present) artifact — e.g. listing 05_counts.txt for categories 3/4/6/9
# (Codex-xhigh-final P1b). Operator categories (1/2/7/8) keep operator-chosen filenames,
# validated instead by content (HTTP shape / JSON parse).
CATEGORY_SCRIPT_ARTIFACTS = {
    3: {"03_effective_privilege.txt", "04_role_membership_closure.txt"},
    4: {"07_secdef_discovery.txt", "08_secdef_function_acl.txt"},
    5: {"05_counts.txt"},
    6: {"06_default_acl.txt"},
    9: {"02_table_acl.txt", "06_default_acl.txt", "08_secdef_function_acl.txt"},
}

# Minimum artifact count for operator categories whose runbook definition names multiple
# captures. Category 1 is "deployed OpenAPI for BOTH hosts", so it must bind >= 2 (Codex-c7
# P1b). NOTE (operator-review scope, lens-B A4): the finalizer enforces STRUCTURE + integrity
# (present, hashed, valid-JSON shape, exact /reset route, both OpenAPI hosts). Deeper
# SEMANTICS of the operator captures — that each OpenAPI is a DIFFERENT host, the deployed
# version/commit SHA is recorded, the log export covers the right window — are confirmed by
# the operator at the closeout drift review (runbook Part C), not mechanized here.
CATEGORY_MIN_ARTIFACTS = {1: 2}

log = logging.getLogger("pm_ops_p0.finalize_closeout")


class CloseoutError(Exception):
    """A fail-closed closeout refusal carrying a stable, value-free code."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_spec(spec_path: Path) -> list[dict]:
    """Parse + shape-validate the closeout spec; raise value-free ``CloseoutError``.

    Shape: ``{"categories": [{"category": int in 1..9, "source": "script"|"operator",
    "artifacts": [non-empty str, ...]}, ...]}``.
    """
    try:
        doc = json.loads(spec_path.read_text())
    except (OSError, ValueError):
        raise CloseoutError("spec_unreadable") from None
    cats = doc.get("categories") if isinstance(doc, dict) else None
    if not isinstance(cats, list) or not cats:
        raise CloseoutError("spec_invalid")
    out: list[dict] = []
    for entry in cats:
        if not isinstance(entry, dict):
            raise CloseoutError("spec_invalid")
        cat = entry.get("category")
        source = entry.get("source")
        arts = entry.get("artifacts")
        if (
            not isinstance(cat, int)
            or isinstance(cat, bool)
            or cat not in REQUIRED_CATEGORIES
        ):
            raise CloseoutError("spec_invalid")
        if source not in ("script", "operator"):
            raise CloseoutError("spec_invalid")
        if (
            not isinstance(arts, list)
            or not arts
            or not all(isinstance(a, str) and a for a in arts)
        ):
            raise CloseoutError("spec_invalid")
        out.append({"category": cat, "source": source, "artifacts": list(arts)})
    return out


def _assert_categories_complete(spec: list[dict]) -> None:
    seen = [e["category"] for e in spec]
    if any(seen.count(c) > 1 for c in seen):
        raise CloseoutError("duplicate_category")
    if REQUIRED_CATEGORIES - set(seen):
        raise CloseoutError("missing_category")
    # source is not caller's free choice: each category's source MUST match the runbook,
    # so a DB category cannot be downgraded to "operator" to skip the manifest hash binding.
    for entry in spec:
        if entry["source"] != CATEGORY_SOURCE[entry["category"]]:
            raise CloseoutError("category_source_mismatch")
        # script categories must bind their EXACT tool-deterministic artifact set, so a
        # manifest-present but wrong-for-the-category file cannot satisfy them.
        expected = CATEGORY_SCRIPT_ARTIFACTS.get(entry["category"])
        if expected is not None and set(entry["artifacts"]) != expected:
            raise CloseoutError("category_artifacts_mismatch")
        # NOTE: the DISTINCT-artifact and per-category minimum checks are applied in
        # finalize() on RESOLVED custody-relative paths, not raw spec strings, so aliases
        # like `x.json` and `./x.json` cannot satisfy a multi-capture minimum (Codex-c12 P2).


def _read_manifest(custody_dir: Path) -> dict[str, str]:
    """Parse ``manifest.sha256`` (lines ``<sha256>  <name>``) -> {name: sha256}."""
    manifest = custody_dir / MANIFEST_NAME
    result: dict[str, str] = {}
    if manifest.is_file():
        for line in manifest.read_text().splitlines():
            if not line.strip():
                continue
            sha, name = line.split(None, 1)
            result[name.strip()] = sha.strip()
    return result


def _require_provenance(custody_dir: Path, manifest: dict[str, str]) -> str:
    """Provenance must exist, be manifest-listed, AND hash-match the manifest; return its sha.

    The provenance record carries the git-equality attestation the whole closeout
    leans on, so presence alone is insufficient: its bytes are verified against the
    evidence manifest (lens-B finding A2) — a post-capture edit is ``hash_mismatch``. The
    returned digest is bound into the published index so the attestation is recorded there
    too, not only cross-checked (Codex-final P2b).
    """
    prov = custody_dir / PROVENANCE_NAME
    # reject a SYMLINK provenance (is_file follows links): the attestation must be a real file
    # inside the custody bundle, not a link to JSON elsewhere (Codex-c12 P2).
    if prov.is_symlink() or not prov.is_file() or PROVENANCE_NAME not in manifest:
        raise CloseoutError("provenance_missing")
    digest = _sha256_file(prov)
    if digest != manifest[PROVENANCE_NAME]:
        raise CloseoutError("hash_mismatch")
    # the closeout LEANS on the governed-run attestation, so verify its CONTENT, not just the
    # hash: a stale/old-tool provenance (no schema_version 2, no origin_main_sha, missing the
    # equality/pristine/role attestation) must not close out P0-A (Codex-c11 P2).
    try:
        record = json.loads(prov.read_text())
    except (ValueError, UnicodeDecodeError):
        raise CloseoutError("provenance_attestation_invalid") from None
    sha = record.get("repo_sha") if isinstance(record, dict) else None
    attested = isinstance(record, dict) and all(
        (
            record.get("schema_version") == PROVENANCE_SCHEMA_VERSION,
            record.get("repo_tree_pristine") is True,
            record.get("repo_head_equals_origin_main") is True,
            record.get("expected_db_role") == EXPECTED_DB_ROLE,
            record.get("expected_project_ref") == PROJECT_REF,
            bool(sha),
            sha == record.get("origin_main_sha") == record.get("expect_repo_sha"),
        )
    )
    if not attested:
        raise CloseoutError("provenance_attestation_invalid")
    return digest


def _verify_manifest_bundle(
    custody: Path, base: Path, manifest: dict[str, str]
) -> None:
    """Every manifest-listed file must be a within-custody regular file with a matching hash.

    Covers script artifacts no category references (00_p0a_snapshot.sql, 01_markers.txt): a
    post-manifest edit to ANY manifest-bound byte must fail the closeout (Codex-c12 P2).
    """
    for name, sha in manifest.items():
        path = _resolve_within(custody, name)
        if path.is_symlink() or not path.is_file():
            raise CloseoutError("artifact_not_regular")
        if _sha256_file(path) != sha:
            raise CloseoutError("hash_mismatch")


def _resolve_within(custody_dir: Path, rel: str) -> Path:
    """Return ``custody_dir/rel`` iff it does not escape the custody dir.

    Rejects absolute paths, ``..`` traversal, and symlink escapes (``resolve`` follows
    links) with a value-free ``artifact_path_escape``. Returns the PRE-resolve path so the
    caller can lstat it (a symlink to a regular file inside the dir is still non-regular).
    """
    base = custody_dir.resolve()
    raw = base / rel
    try:
        raw.resolve().relative_to(base)
    except ValueError:
        raise CloseoutError("artifact_path_escape") from None
    return raw


# HTTP (JSON) captures must carry at least one key characteristic of the category, so a
# saved error body ({"error": ...}, {}, [], "Not Found") — not just an HTML error page — is
# rejected (lens-B A1: category 2 previously accepted ANY well-formed JSON).
_HTTP_REQUIRED_KEYS = {
    1: ("openapi", "paths"),  # deployed OpenAPI document
    2: ("security", "path"),  # POST /reset route + its security state
}


def _validate_http_artifact(category: int, path: Path) -> None:
    """Category 1/2 artifacts must be the FULL expected shape of JSON, not a saved error page.

    ALL of a category's markers must be present (Codex-xhigh-final P1a): a partial capture
    like ``{"path": "/reset", "error": "unauthorized"}`` — the ``/reset`` path but no
    ``security`` state — must fail, not pass on a single matching key.
    """
    try:
        doc = json.loads(path.read_text())
    except (ValueError, UnicodeDecodeError):
        raise CloseoutError("failed_http") from None
    required = _HTTP_REQUIRED_KEYS.get(category)
    if required is None:
        return
    if not isinstance(doc, dict) or not all(key in doc for key in required):
        raise CloseoutError("failed_http")
    if category == 2:
        # the evidence must be the EXACT POST /reset route (Codex-c7 P2) and must PROVE the
        # destructive POST method -- an explicit method == POST or an OpenAPI `post` member.
        # An unspecified method is insufficient for the /reset route state (Codex-c9 P2).
        if doc.get("path") != "/reset":
            raise CloseoutError("failed_http")
        if str(doc.get("method", "")).upper() != "POST" and "post" not in doc:
            raise CloseoutError("failed_http")


def _require_parseable_json(path: Path) -> None:
    """Any ``.json`` artifact must parse (lens-B A3: a JSON-named error page must fail)."""
    try:
        json.loads(path.read_text())
    except (ValueError, UnicodeDecodeError):
        raise CloseoutError("failed_json") from None


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_restricted_file(path: Path, data: bytes) -> None:
    """Write ``data`` to ``path`` at 0400, O_EXCL (no clobber), short-write-safe + fsync'd."""
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o400)
    try:
        view = memoryview(data)
        while view:
            written = os.write(fd, view)
            if written == 0:  # pragma: no cover - defensive against a stuck fd
                raise OSError("closeout write made no progress")
            view = view[written:]
        os.fsync(fd)
    finally:
        os.close(fd)


def _fsync_dir(path: Path) -> None:
    fd = os.open(path, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def _publish_no_clobber(out_path: Path, data: bytes) -> None:
    """Atomically publish ``data`` to ``out_path`` (0400), no-clobber + durable (lens-B A6).

    Writes a sibling ``.partial`` (O_EXCL, fsync'd), hard-links it onto the final name
    (``os.link`` is atomic and raises ``FileExistsError`` if the final exists -> no clobber),
    then removes the partial and fsyncs the directory. A crash mid-write leaves only the
    ``.partial`` file, never a truncated final index at the canonical name.
    """
    partial = out_path.parent / f"{out_path.name}.partial"
    _write_restricted_file(partial, data)
    try:
        os.link(partial, out_path)  # atomic no-clobber publish
    finally:
        with contextlib.suppress(FileNotFoundError):
            os.unlink(partial)
    _fsync_dir(out_path.parent)


def finalize(
    spec_path: str | Path,
    custody_dir: str | Path,
    out_path: str | Path,
    *,
    clock: str,
) -> Path:
    """Validate the nine-category closeout and publish ``closeout_index.json`` no-clobber.

    Raises ``CloseoutError`` (value-free) on any validation failure and ``FileExistsError``
    if the index already exists. Returns the written index path on success.
    """
    custody = Path(custody_dir)
    base = custody.resolve()
    spec = load_spec(Path(spec_path))
    _assert_categories_complete(spec)  # missing / duplicate -> before touching files
    manifest = _read_manifest(custody)
    prov_digest = _require_provenance(custody, manifest)

    index_categories: list[dict] = []
    for entry in sorted(spec, key=lambda e: e["category"]):
        category, source = entry["category"], entry["source"]
        artifacts: list[dict] = []
        for name in entry["artifacts"]:
            path = _resolve_within(custody, name)
            if path.is_symlink() or not path.is_file():
                raise CloseoutError("artifact_not_regular")
            # the path RELATIVE to custody (not the basename) keys the manifest AND is what
            # the index records, so a subdir artifact (captures/openapi.json) is identified
            # exactly and cannot alias a flat manifest entry or another basename (Codex-c5
            # P2 / lens-B A6). Flat script artifacts match; any nested name -> unhashed.
            rel = path.resolve().relative_to(base).as_posix()
            digest = _sha256_file(path)
            if source == "script":
                recorded = manifest.get(rel)
                if recorded is None:
                    raise CloseoutError(
                        "unhashed_artifact"
                    )  # not covered by the tool manifest
                if recorded != digest:
                    raise CloseoutError("hash_mismatch")
            elif rel in manifest:
                # an operator category (backend, /reset logs, ...) must be a NEW operator
                # capture, never a manifest-listed script DB artifact standing in for it
                # (Codex-c11 P2): that would pass a category with the wrong evidence entirely.
                raise CloseoutError("operator_artifact_is_db")
            if category in HTTP_CATEGORIES:
                _validate_http_artifact(category, path)
            elif path.name.endswith(".json"):
                _require_parseable_json(
                    path
                )  # a JSON-named operator error page must fail
            artifacts.append(
                {"name": rel, "sha256": digest, "bytes": path.stat().st_size}
            )
        # DISTINCT + minimum enforced on RESOLVED paths, so `x.json` and `./x.json` cannot
        # both count toward a multi-capture minimum (Codex-c12 P2).
        rels = [a["name"] for a in artifacts]
        if len(set(rels)) != len(rels):
            raise CloseoutError("duplicate_artifact")
        if len(rels) < CATEGORY_MIN_ARTIFACTS.get(category, 1):
            raise CloseoutError("category_incomplete")
        index_categories.append(
            {"category": category, "source": source, "artifacts": artifacts}
        )

    # every manifest-listed file (incl. ones no category references, e.g. 00_p0a_snapshot.sql
    # / 01_markers.txt) must currently be a within-custody regular file whose hash matches, so
    # a post-manifest edit to ANY bound byte fails the closeout before all_artifacts_hashed is
    # asserted (Codex-c12 P2).
    _verify_manifest_bundle(custody, base, manifest)

    prov_path = custody / PROVENANCE_NAME
    index = {
        "artifact": "pm_ops_p0.closeout_index",
        "schema_version": 1,
        "custody_dir": str(custody.resolve()),
        "generated_at_utc": clock,
        "provenance": {
            "name": PROVENANCE_NAME,
            "sha256": prov_digest,  # the git/role attestation is RECORDED here, not only cross-checked
            "bytes": prov_path.stat().st_size,
        },
        "manifest_sha256": _sha256_file(custody / MANIFEST_NAME),
        "categories": index_categories,
        "all_categories_present": True,
        "all_artifacts_hashed": True,
    }
    data = (json.dumps(index, indent=2, sort_keys=True) + "\n").encode()
    _publish_no_clobber(Path(out_path), data)
    return Path(out_path)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Fail-closed nine-category P0-A closeout finalizer. Verifies the closeout spec "
            "against the published custody dir + evidence manifest and writes a no-clobber "
            "closeout_index.json binding every artifact by SHA-256. Requires a per-action GO."
        )
    )
    parser.add_argument(
        "--spec",
        required=True,
        help="closeout spec JSON: categories 1..9 -> artifact filenames under the custody dir.",
    )
    parser.add_argument(
        "--custody-dir",
        required=True,
        help="the published P0-A custody run directory (holds the DB artifacts + manifest).",
    )
    parser.add_argument(
        "--out",
        default=None,
        help=f"closeout index output path (default: <custody-dir>/{OUT_NAME}).",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")
    args = build_parser().parse_args(argv)
    custody = Path(args.custody_dir)
    out = Path(args.out) if args.out else custody / OUT_NAME
    try:
        run = finalize(args.spec, custody, out, clock=_utc_now_iso())
    except CloseoutError as exc:
        print("RESULT FAIL")
        print(f"FAILURE {exc.code}")
        return 1
    except FileExistsError:
        print("RESULT FAIL")
        print("FAILURE closeout_exists")
        return 1
    except Exception as exc:  # noqa: BLE001
        log.warning("closeout finalize failed: %s", type(exc).__name__)  # class only
        print("RESULT FAIL")
        print("FAILURE finalize_failed")
        return 1
    print("RESULT PASS")
    print(f"CLOSEOUT {run}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

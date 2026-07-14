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

# the nine design-§2 categories that a complete P0-A closeout must bind
REQUIRED_CATEGORIES = frozenset(range(1, 10))
# categories captured over HTTP; their artifacts must be the expected valid JSON, not an
# error page a failed `curl` saved (finding 5: "failed-HTTP ... categories fail")
HTTP_CATEGORIES = frozenset({1, 2})

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


def _require_provenance(custody_dir: Path, manifest: dict[str, str]) -> None:
    prov = custody_dir / PROVENANCE_NAME
    if not (prov.is_file() and PROVENANCE_NAME in manifest):
        raise CloseoutError("provenance_missing")


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


def _validate_http_artifact(category: int, path: Path) -> None:
    """Category 1/2 artifacts must be the expected valid JSON, not a saved error page."""
    try:
        doc = json.loads(path.read_text())
    except (ValueError, UnicodeDecodeError):
        raise CloseoutError("failed_http") from None
    if category == 1 and not (
        isinstance(doc, dict) and ("openapi" in doc or "paths" in doc)
    ):
        # an OpenAPI capture must carry an openapi version or a paths object
        raise CloseoutError("failed_http")


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_no_clobber(path: Path, data: bytes) -> None:
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
    spec = load_spec(Path(spec_path))
    _assert_categories_complete(spec)  # missing / duplicate -> before touching files
    manifest = _read_manifest(custody)
    _require_provenance(custody, manifest)

    index_categories: list[dict] = []
    for entry in sorted(spec, key=lambda e: e["category"]):
        category, source = entry["category"], entry["source"]
        artifacts: list[dict] = []
        for name in entry["artifacts"]:
            path = _resolve_within(custody, name)
            if path.is_symlink() or not path.is_file():
                raise CloseoutError("artifact_not_regular")
            digest = _sha256_file(path)
            if source == "script":
                recorded = manifest.get(path.name)
                if recorded is None:
                    raise CloseoutError(
                        "unhashed_artifact"
                    )  # not covered by the tool manifest
                if recorded != digest:
                    raise CloseoutError("hash_mismatch")
            if category in HTTP_CATEGORIES:
                _validate_http_artifact(category, path)
            artifacts.append(
                {"name": path.name, "sha256": digest, "bytes": path.stat().st_size}
            )
        index_categories.append(
            {"category": category, "source": source, "artifacts": artifacts}
        )

    index = {
        "artifact": "pm_ops_p0.closeout_index",
        "schema_version": 1,
        "custody_dir": str(custody.resolve()),
        "generated_at_utc": clock,
        "categories": index_categories,
        "all_categories_present": True,
        "all_artifacts_hashed": True,
    }
    data = (json.dumps(index, indent=2, sort_keys=True) + "\n").encode()
    _write_no_clobber(Path(out_path), data)
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

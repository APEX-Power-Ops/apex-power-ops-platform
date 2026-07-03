"""Schema/consistency check for reference/records/SERVING_CONTRACT.yaml.

Gate 5 Task 6: this contract is reference-only (nothing in Gate 5 reads it at
runtime), so this test does not touch any database. It only parses the YAML
and cross-checks it against the invariants the .md companion documents, plus
confirms infra/secret-audit.sh Check 3 (RECORDS_SERVING_GLOBS) is still
dormant - no default value has been introduced that would make Check 3 always
run.

No pyyaml dependency: the file's structure (flat block mappings + simple
flow-style lists, no anchors/multi-doc/nested-flow-mappings) is parsed with a
small hand-rolled indentation parser so this test does not require adding a
new dependency to the venv for a docs-only task.
"""
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
YAML_PATH = os.path.join(HERE, "SERVING_CONTRACT.yaml")
REPO_ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
SECRET_AUDIT_PATH = os.path.join(REPO_ROOT, "infra", "secret-audit.sh")


def _strip_comment(line):
    # No quoted strings contain '#' in this file, so a plain split is safe.
    return line.split("#", 1)[0]


def _parse_scalar(raw):
    raw = raw.strip()
    if raw == "":
        return None
    if raw.startswith("[") and raw.endswith("]"):
        inner = raw[1:-1].strip()
        if inner == "":
            return []
        return [item.strip() for item in inner.split(",")]
    if raw == "true":
        return True
    if raw == "false":
        return False
    if raw.startswith('"') and raw.endswith('"') and len(raw) >= 2:
        return raw[1:-1]
    return raw


def load_simple_yaml(path):
    """Parse a flat, indentation-based YAML subset into nested dict/list.

    Supports: '#' comments, block mappings, 2-space indentation, inline
    flow-style lists ('[a, b, c]'), and scalars (bare words / true / false).
    Does not support: anchors, multi-document files, block sequences ('- x'),
    or nested flow mappings. Sufficient for SERVING_CONTRACT.yaml only.
    """
    with open(path, "r", encoding="ascii") as fh:
        raw_lines = fh.readlines()

    lines = []
    for raw in raw_lines:
        stripped = _strip_comment(raw).rstrip("\n")
        if stripped.strip() == "":
            continue
        indent = len(stripped) - len(stripped.lstrip(" "))
        lines.append((indent, stripped.strip()))

    root = {}
    # stack of (indent, container)
    stack = [(-1, root)]
    for indent, content in lines:
        while stack and indent <= stack[-1][0]:
            stack.pop()
        parent = stack[-1][1]
        if ":" not in content:
            raise AssertionError("unparseable line (no ':'): %r" % content)
        key, _, rest = content.partition(":")
        key = key.strip()
        rest = rest.strip()
        if rest == "":
            child = {}
            parent[key] = child
            stack.append((indent, child))
        else:
            parent[key] = _parse_scalar(rest)
    return root


def test_yaml_parses_and_has_top_level_shape():
    doc = load_simple_yaml(YAML_PATH)
    assert doc.get("version") == "1" or doc.get("version") == 1
    assert "roles" in doc and isinstance(doc["roles"], dict)
    assert "drm_boundary" in doc and isinstance(doc["drm_boundary"], dict)
    assert "dsn_form_inventory" in doc


def test_every_connecting_role_has_supabase_target():
    doc = load_simple_yaml(YAML_PATH)
    roles = doc["roles"]
    assert roles, "roles map must not be empty"
    for name, spec in roles.items():
        if spec.get("connects") is True:
            target = spec.get("supabase_target")
            assert target not in (None, ""), (
                "role %s has connects: true but no supabase_target" % name
            )


def test_every_non_connecting_role_is_owner_only_with_no_dsn():
    doc = load_simple_yaml(YAML_PATH)
    roles = doc["roles"]
    for name, spec in roles.items():
        if spec.get("connects") is False:
            assert spec.get("owner_only") is True, (
                "role %s has connects: false but is not owner_only" % name
            )
            assert spec.get("dsn") == "none", (
                "role %s has connects: false but dsn is not 'none' (%r)"
                % (name, spec.get("dsn"))
            )
            assert "supabase_target" not in spec, (
                "role %s is owner_only but declares a supabase_target" % name
            )


def test_known_roles_present_with_expected_connect_posture():
    doc = load_simple_yaml(YAML_PATH)
    roles = doc["roles"]
    expected_connects = {
        "records_api": True,
        "records_intake_writer": True,
        "records_auditor": True,
        "records_owner": False,
        "records_fn_owner": False,
    }
    for name, expected in expected_connects.items():
        assert name in roles, "expected role %s missing from contract" % name
        assert roles[name].get("connects") is expected, (
            "role %s connects posture mismatch: expected %r, got %r"
            % (name, expected, roles[name].get("connects"))
        )


def test_drm_boundary_keys_exist():
    doc = load_simple_yaml(YAML_PATH)
    drm = doc["drm_boundary"]
    assert "source_links_protects" in drm
    assert "tolerance_values" in drm
    assert drm["source_links_protects"] == "lineage_provenance"
    assert drm["tolerance_values"] == "first_class_record_content"


def test_dsn_form_inventory_has_expected_shapes():
    doc = load_simple_yaml(YAML_PATH)
    inventory = doc["dsn_form_inventory"]
    assert isinstance(inventory, list) and len(inventory) > 0
    expected = {
        "keyword_user",
        "url_userinfo",
        "url_driver_qualified",
        "pg_env_vars",
    }
    assert expected.issubset(set(inventory)), (
        "dsn_form_inventory missing expected shapes: %s"
        % (expected - set(inventory))
    )


def test_yaml_is_ascii_only():
    with open(YAML_PATH, "rb") as fh:
        data = fh.read()
    try:
        data.decode("ascii")
    except UnicodeDecodeError as exc:
        raise AssertionError("SERVING_CONTRACT.yaml has non-ASCII bytes: %s" % exc)


def test_md_companion_is_ascii_only():
    md_path = os.path.join(HERE, "SERVING_CONTRACT.md")
    assert os.path.isfile(md_path), "SERVING_CONTRACT.md companion is missing"
    with open(md_path, "rb") as fh:
        data = fh.read()
    try:
        data.decode("ascii")
    except UnicodeDecodeError as exc:
        raise AssertionError("SERVING_CONTRACT.md has non-ASCII bytes: %s" % exc)


def test_secret_audit_check3_stays_dormant():
    """Check 3 (RECORDS_SERVING_GLOBS) must remain SKIP-by-default.

    This test does not touch a database; it only greps the checked-in
    infra/secret-audit.sh text to prove no default value has been assigned to
    RECORDS_SERVING_GLOBS (e.g. via ':=' / '=' default-assignment forms or a
    hardcoded non-empty literal), which would make Check 3 always execute
    instead of SKIP until a real serving config exists.
    """
    assert os.path.isfile(SECRET_AUDIT_PATH), "infra/secret-audit.sh not found"
    with open(SECRET_AUDIT_PATH, "r", encoding="ascii") as fh:
        text = fh.read()

    assert "RECORDS_SERVING_GLOBS" in text, (
        "secret-audit.sh no longer references RECORDS_SERVING_GLOBS at all"
    )

    # The only sanctioned live reference is the "is it set" test used to gate
    # Check 3 (":-" default-if-unset inside a test, never assigned). Reject
    # any line that assigns RECORDS_SERVING_GLOBS a literal default value,
    # e.g. `RECORDS_SERVING_GLOBS:=...`, `RECORDS_SERVING_GLOBS=...`, or
    # `: "${RECORDS_SERVING_GLOBS:=...}"`.
    assignment_pat = re.compile(
        r"RECORDS_SERVING_GLOBS\s*(:?=)\s*[^}\s]"
    )
    for lineno, line in enumerate(text.splitlines(), start=1):
        if "RECORDS_SERVING_GLOBS" not in line:
            continue
        # Allow the read-only default-if-unset test form: ${VAR:-...}
        if re.search(r"\$\{RECORDS_SERVING_GLOBS:-[^}]*\}", line):
            continue
        # Allow plain expansion/use forms: ${RECORDS_SERVING_GLOBS}, and the
        # SKIP/say/comment lines that just mention the name.
        if re.search(r"\$\{RECORDS_SERVING_GLOBS\}", line):
            continue
        if re.match(r"\s*#", line):
            continue
        if re.search(r"RECORDS_SERVING_GLOBS\s+set", line):
            continue
        # Anything else that assigns the variable a default is a live wire.
        assert not assignment_pat.search(line), (
            "secret-audit.sh line %d appears to assign a default to "
            "RECORDS_SERVING_GLOBS, which would make Check 3 non-dormant: %r"
            % (lineno, line)
        )

    # Positive confirmation: the SKIP branch text is still present.
    assert "no RECORDS_SERVING_GLOBS set" in text, (
        "secret-audit.sh SKIP message for an unset RECORDS_SERVING_GLOBS "
        "is missing - Check 3 dormancy path may have been altered"
    )

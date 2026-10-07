"""Representative false-green tests for the Records admission validator."""

from __future__ import annotations

import contextlib
import copy
import hashlib
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[3]
sys.path.insert(0, str(HERE))

import validate_records_admission as validator  # noqa: E402


MANIFEST = HERE / "records-admission-manifest.json"
EXPECTED_BASE = "bdec885a5cd2862da7907054646c9c0fb5df5ef2"
EXPECTED_TREE = "b3f91a2392e0afd7b545bab2b6441c7ed6e27432"
EXPECTED_AUDIT = "5db6a3a0582eac515c55f1c66496ae46e64541b65325e66430346adf20cbeb43"


def synthetic_authority(label: str) -> dict[str, str]:
    digest = hashlib.sha256(label.encode("utf-8")).hexdigest()
    return {
        "identity": "Synthetic fixture test authority",
        "immutable_locator": f"urn:sha256:{digest}",
        "digest_algorithm": "sha256",
        "digest": digest,
        "timestamp": "2030-01-01T00:00:00+00:00",
        "supersession_rule": "A later synthetic fixture must bind and supersede this exact test vector.",
    }


class RecordsAdmissionValidatorTest(unittest.TestCase):
    def setUp(self) -> None:
        self.real = validator.load_manifest(MANIFEST)

    def validate(self, document: dict) -> dict:
        return validator.validate_manifest(
            document,
            REPO_ROOT,
            expected_base=EXPECTED_BASE,
            expected_tree=EXPECTED_TREE,
            expected_audit_sha256=EXPECTED_AUDIT,
            verify_git_diff=False,
            external_audit_binding_only=True,
        )

    def diagnostic_codes(self, result: dict) -> set[str]:
        return {item["code"] for item in result["diagnostics"]}

    def run_git(self, root: Path, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", "-C", str(root), *args],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

    def clone_candidate(self, directory: str) -> Path:
        clone = Path(directory) / "candidate"
        head = self.run_git(REPO_ROOT, "rev-parse", "HEAD").stdout.strip()
        subprocess.run(
            [
                "git",
                "clone",
                "--quiet",
                "--no-hardlinks",
                "--no-checkout",
                str(REPO_ROOT),
                str(clone),
            ],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        self.run_git(clone, "checkout", "--quiet", "--detach", head)
        return clone

    def validate_clone(self, clone: Path) -> dict:
        document = validator.load_manifest(
            clone / MANIFEST.relative_to(REPO_ROOT)
        )
        return validator.validate_manifest(
            document,
            clone,
            expected_base=EXPECTED_BASE,
            expected_tree=EXPECTED_TREE,
            expected_audit_sha256=EXPECTED_AUDIT,
            verify_git_diff=True,
            external_audit_binding_only=True,
        )

    def assert_invalid_with(self, document: dict, code: str) -> dict:
        result = self.validate(document)
        self.assertEqual(result["admission_result"], "INVALID", result)
        self.assertFalse(result["execution_authorized"])
        self.assertIn(code, self.diagnostic_codes(result), result)
        return result

    def synthetic_fixture(self) -> dict:
        document = copy.deepcopy(self.real)
        document["fixture_kind"] = "synthetic"
        document["candidate"] = {
            "id": "RECORDS-FIRST-SLICE-2026-07",
            "decision_status": "accepted",
            "implementation_readiness": "ready",
            "execution_authorized": False,
        }

        for item in document["open_human_decisions"]:
            item["state"] = "resolved"
            item["authority"] = synthetic_authority(f"decision:{item['code']}")

        for item in document["technical_invariants"]:
            item["state"] = "satisfied"
            item["evidence"] = synthetic_authority(f"evidence:{item['code']}")

        document["serving_guardrails"]["runtime_identities"] = [
            {
                "name": "records_api",
                "owner": False,
                "superuser": False,
                "bypassrls": False,
            },
            {
                "name": "records_intake_writer",
                "owner": False,
                "superuser": False,
                "bypassrls": False,
            },
            {
                "name": "records_auditor",
                "owner": False,
                "superuser": False,
                "bypassrls": False,
            },
        ]

        for item in document["first_slice_candidates"]:
            if item["code"] == "RFS-GROUNDING":
                item["decision_status"] = "accepted"
                item["selected"] = True
            else:
                item["decision_status"] = "proposed"
                item["selected"] = False

        document["recommendation"] = {
            "candidate_code": "RFS-GROUNDING",
            "decision_status": "accepted",
            "ratified": True,
            "selected": True,
            "execution_authorized": False,
        }
        return document

    def test_real_manifest_is_held_and_reports_sorted_unresolved_codes(self) -> None:
        result = self.validate(self.real)
        self.assertEqual(result["admission_result"], "HELD", result)
        self.assertFalse(result["execution_authorized"])
        self.assertEqual(result["diagnostics"], [])
        self.assertEqual(
            result["unresolved_decision_codes"],
            [f"REC-D{number:03d}" for number in range(1, 12)],
        )

    def test_synthetic_accepted_fixture_is_satisfiable_but_unauthorized(self) -> None:
        result = self.validate(self.synthetic_fixture())
        self.assertEqual(result["admission_result"], "SATISFIABLE_FIXTURE", result)
        self.assertFalse(result["execution_authorized"])
        self.assertEqual(result["unresolved_decision_codes"], [])
        self.assertEqual(result["diagnostics"], [])

    def test_publication_cli_requires_exactly_held_and_preserves_general_fixture_mode(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            manifest = Path(directory) / "synthetic.json"
            manifest.write_text(
                json.dumps(self.synthetic_fixture()),
                encoding="utf-8",
            )
            common = [
                "--repo-root",
                str(REPO_ROOT),
                "--manifest",
                str(manifest),
                "--expect-base",
                EXPECTED_BASE,
                "--expect-tree",
                EXPECTED_TREE,
                "--expect-audit-sha256",
                EXPECTED_AUDIT,
                "--external-audit-binding-only",
            ]

            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                general_exit = validator.main(common)
            self.assertEqual(general_exit, 0)
            self.assertEqual(
                json.loads(output.getvalue())["admission_result"],
                "SATISFIABLE_FIXTURE",
            )

            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                publication_exit = validator.main(
                    [*common, "--expect-admission-result", "HELD"]
                )
            result = json.loads(output.getvalue())
            self.assertEqual(publication_exit, 1)
            self.assertEqual(result["admission_result"], "SATISFIABLE_FIXTURE")
            self.assertFalse(result["audit_artifact_verified"])
            self.assertFalse(result["execution_authorized"])

        workflow = (
            REPO_ROOT / ".github/workflows/records-authority-admission-ci.yml"
        ).read_text(encoding="utf-8")
        self.assertIn("--expect-admission-result HELD", workflow)
        self.assertIn("--external-audit-binding-only", workflow)

    def test_ready_state_with_unresolved_decisions_is_rejected(self) -> None:
        document = copy.deepcopy(self.real)
        document["fixture_kind"] = "synthetic"
        document["candidate"]["decision_status"] = "accepted"
        document["candidate"]["implementation_readiness"] = "ready"
        result = self.assert_invalid_with(document, "REC-A006")
        messages = " ".join(item["message"] for item in result["diagnostics"])
        self.assertIn("implementation-ready state", messages)

    def test_unknown_states_and_duplicate_json_keys_are_rejected(self) -> None:
        mutations = (
            ("decision status", ("candidate", "decision_status"), "approved", "REC-A002"),
            ("readiness", ("candidate", "implementation_readiness"), "pending", "REC-A002"),
            ("decision state", ("open_human_decisions", 0, "state"), "pending", "REC-A006"),
        )
        for name, path, value, expected_code in mutations:
            with self.subTest(name=name):
                document = copy.deepcopy(self.real)
                target = document
                for part in path[:-1]:
                    target = target[part]
                target[path[-1]] = value
                self.assert_invalid_with(document, expected_code)

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "duplicate.json"
            path.write_text('{"schema_version":"1","schema_version":"2"}', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "duplicate JSON key"):
                validator.load_manifest(path)

    def test_candidate_id_is_frozen(self) -> None:
        document = copy.deepcopy(self.real)
        document["candidate"]["id"] = "RECORDS-FIRST-SLICE-2026-08"
        result = self.assert_invalid_with(document, "REC-A002")
        self.assertIn(
            "candidate ID differs from frozen packet",
            {item["message"] for item in result["diagnostics"]},
        )

    def test_placeholder_and_ai_inferred_authority_are_rejected(self) -> None:
        mutations = (
            ("identity", "Codex AI-inferred approval"),
            ("supersession_rule", "TBD"),
        )
        for field, value in mutations:
            with self.subTest(field=field):
                document = copy.deepcopy(self.real)
                document["ratified_precedents"][0]["authority"][field] = value
                self.assert_invalid_with(document, "REC-A003")

    def test_plausible_supersession_rule_drift_is_rejected(self) -> None:
        for index, precedent in enumerate(self.real["ratified_precedents"]):
            with self.subTest(code=precedent["code"]):
                document = copy.deepcopy(self.real)
                document["ratified_precedents"][index]["authority"][
                    "supersession_rule"
                ] = "A later repository edit may silently supersede this precedent."
                result = self.assert_invalid_with(document, "REC-A003")
                self.assertIn(
                    "ratified authority differs from immutable precedent",
                    {item["message"] for item in result["diagnostics"]},
                )

    def test_every_authority_field_and_immutable_shape_is_required(self) -> None:
        required = (
            "identity",
            "immutable_locator",
            "digest_algorithm",
            "digest",
            "timestamp",
            "supersession_rule",
        )
        for field in required:
            with self.subTest(missing=field):
                document = copy.deepcopy(self.real)
                del document["ratified_precedents"][0]["authority"][field]
                self.assert_invalid_with(document, "REC-A003")

        malformed = (
            ("immutable_locator", "refs/heads/main"),
            ("digest_algorithm", "sha512"),
            ("digest", "ABC"),
            ("timestamp", "2026-06-12"),
        )
        for field, value in malformed:
            with self.subTest(malformed=field):
                document = copy.deepcopy(self.real)
                document["ratified_precedents"][0]["authority"][field] = value
                self.assert_invalid_with(document, "REC-A003")

    def test_data_api_and_privileged_runtime_identities_are_rejected(self) -> None:
        document = copy.deepcopy(self.real)
        document["serving_guardrails"]["data_api_exposed"] = True
        self.assert_invalid_with(document, "REC-A008")

        for identity in ("records_owner", "postgres", "service_role", "records_bypass"):
            with self.subTest(identity=identity):
                document = self.synthetic_fixture()
                document["serving_guardrails"]["runtime_identities"][0]["name"] = identity
                self.assert_invalid_with(document, "REC-A008")

        document = self.synthetic_fixture()
        document["serving_guardrails"]["runtime_identities"][0]["owner"] = True
        self.assert_invalid_with(document, "REC-A008")

        document = self.synthetic_fixture()
        document["serving_guardrails"]["runtime_identities"][0]["bypassrls"] = True
        self.assert_invalid_with(document, "REC-A008")

    def test_stale_base_tree_and_audit_bindings_are_rejected(self) -> None:
        mutations = (
            ("base_commit", "0" * 40),
            ("base_tree", "0" * 40),
        )
        for field, value in mutations:
            with self.subTest(field=field):
                document = copy.deepcopy(self.real)
                document["bindings"][field] = value
                self.assert_invalid_with(document, "REC-A004")

        document = copy.deepcopy(self.real)
        document["bindings"]["audit"]["digest"] = "0" * 64
        self.assert_invalid_with(document, "REC-A004")

        document = copy.deepcopy(self.real)
        document["bindings"]["audit"]["path"] = "some-other-audit.md"
        self.assert_invalid_with(document, "REC-A004")

    def test_audit_artifact_bytes_are_recomputed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            audit = Path(directory) / "authorized-audit.md"
            payload = b"authorized synthetic audit fixture\n"
            audit.write_bytes(payload)
            digest = hashlib.sha256(payload).hexdigest()
            document = copy.deepcopy(self.real)
            document["bindings"]["audit"]["path"] = str(audit)
            document["bindings"]["audit"]["digest"] = digest
            with mock.patch.object(validator, "AUDIT_PATH", str(audit)):
                verified = validator.validate_manifest(
                    document,
                    REPO_ROOT,
                    expected_base=EXPECTED_BASE,
                    expected_tree=EXPECTED_TREE,
                    expected_audit_sha256=digest,
                    audit_artifact=audit,
                )
                self.assertEqual(verified["admission_result"], "HELD", verified)
                self.assertTrue(verified["audit_artifact_verified"])

                audit.write_text("altered audit bytes\n", encoding="utf-8")
                actual_mismatch = validator.validate_manifest(
                    document,
                    REPO_ROOT,
                    expected_base=EXPECTED_BASE,
                    expected_tree=EXPECTED_TREE,
                    expected_audit_sha256=digest,
                    audit_artifact=audit,
                )

                audit.write_bytes(payload)
                expected_mismatch = validator.validate_manifest(
                    document,
                    REPO_ROOT,
                    expected_base=EXPECTED_BASE,
                    expected_tree=EXPECTED_TREE,
                    expected_audit_sha256="0" * 64,
                    audit_artifact=audit,
                )

                alternate = Path(directory) / "different-audit.md"
                alternate.write_bytes(payload)
                wrong_path = validator.validate_manifest(
                    document,
                    REPO_ROOT,
                    expected_base=EXPECTED_BASE,
                    expected_tree=EXPECTED_TREE,
                    expected_audit_sha256=digest,
                    audit_artifact=alternate,
                )

                manifest_mismatch_document = copy.deepcopy(document)
                manifest_mismatch_document["bindings"]["audit"]["digest"] = "1" * 64
                manifest_mismatch = validator.validate_manifest(
                    manifest_mismatch_document,
                    REPO_ROOT,
                    expected_base=EXPECTED_BASE,
                    expected_tree=EXPECTED_TREE,
                    expected_audit_sha256=digest,
                    audit_artifact=audit,
                )

                missing = validator.validate_manifest(
                    document,
                    REPO_ROOT,
                    expected_base=EXPECTED_BASE,
                    expected_tree=EXPECTED_TREE,
                    expected_audit_sha256=digest,
                    audit_artifact=Path(directory) / "missing-audit.md",
                )

        for name, result in (
            ("actual", actual_mismatch),
            ("expected", expected_mismatch),
            ("path", wrong_path),
            ("manifest", manifest_mismatch),
            ("missing", missing),
        ):
            with self.subTest(name=name):
                self.assertEqual(result["admission_result"], "INVALID", result)
                self.assertFalse(result["audit_artifact_verified"])
                self.assertFalse(result["execution_authorized"])
                self.assertIn("REC-A004", self.diagnostic_codes(result))
        self.assertIn(
            "audit artifact digest differs from manifest binding",
            {item["message"] for item in actual_mismatch["diagnostics"]},
        )
    def test_unsafe_missing_duplicate_and_hash_mismatched_artifacts_are_rejected(self) -> None:
        mutations = (
            ("traversal", "../escape.md", None),
            ("missing", "docs/no-such-records-artifact.md", None),
            (
                "hash mismatch",
                None,
                "0" * 64,
            ),
        )
        for name, path_value, digest_value in mutations:
            with self.subTest(name=name):
                document = copy.deepcopy(self.real)
                artifact = document["bindings"]["artifacts"][0]
                if path_value is not None:
                    artifact["path"] = path_value
                if digest_value is not None:
                    artifact["digest"] = digest_value
                self.assert_invalid_with(document, "REC-A005")

        document = copy.deepcopy(self.real)
        document["bindings"]["artifacts"][1]["path"] = (
            document["bindings"]["artifacts"][0]["path"]
        )
        self.assert_invalid_with(document, "REC-A005")

        document = copy.deepcopy(self.real)
        document["bindings"]["artifacts"] = document["bindings"]["artifacts"][2:]
        self.assert_invalid_with(document, "REC-A005")

        document = copy.deepcopy(self.real)
        document["first_slice_candidates"][0]["source_binding"]["git_blob"] = (
            "0" * 40
        )
        self.assert_invalid_with(document, "REC-A011")

    def test_real_acceptance_execution_and_authority_emissions_are_rejected(self) -> None:
        document = copy.deepcopy(self.real)
        document["candidate"]["decision_status"] = "accepted"
        self.assert_invalid_with(document, "REC-A002")

        for value in (True, 0, 1):
            with self.subTest(execution_authorized=value):
                document = copy.deepcopy(self.real)
                document["candidate"]["execution_authorized"] = value
                self.assert_invalid_with(document, "REC-A009")

        for field in validator.EMISSION_KEYS:
            with self.subTest(emission=field):
                document = copy.deepcopy(self.real)
                document["authority_emissions"][field] = True
                self.assert_invalid_with(document, "REC-A009")

    def test_inventory_slice_recommendation_and_acceptance_drift_are_rejected(self) -> None:
        document = copy.deepcopy(self.real)
        document["open_human_decisions"].pop()
        self.assert_invalid_with(document, "REC-A006")

        document = copy.deepcopy(self.real)
        document["open_human_decisions"][1]["code"] = "REC-D001"
        self.assert_invalid_with(document, "REC-A006")

        document = copy.deepcopy(self.real)
        fourth = copy.deepcopy(document["first_slice_candidates"][0])
        fourth["code"] = "RFS-FOURTH"
        document["first_slice_candidates"].append(fourth)
        self.assert_invalid_with(document, "REC-A011")

        semantic_mutations = (
            (
                "precedent choice",
                ("ratified_precedents", 0, "choice"),
                "online_only_native_app",
                "REC-A003",
            ),
            (
                "decision title",
                ("open_human_decisions", 0, "title"),
                "No human decision required",
                "REC-A006",
            ),
            (
                "invariant title",
                ("technical_invariants", 0, "title"),
                "Authentication need not be verified",
                "REC-A007",
            ),
            (
                "slice apparatus",
                ("first_slice_candidates", 0, "apparatus_key"),
                "anything",
                "REC-A011",
            ),
        )
        for name, path, value, code in semantic_mutations:
            with self.subTest(name=name):
                document = copy.deepcopy(self.real)
                document[path[0]][path[1]][path[2]] = value
                self.assert_invalid_with(document, code)

        document = copy.deepcopy(self.real)
        document["recommendation"]["selected"] = True
        self.assert_invalid_with(document, "REC-A011")

        document = copy.deepcopy(self.real)
        document["acceptance_contract"]["elements"][0:2] = reversed(
            document["acceptance_contract"]["elements"][0:2]
        )
        self.assert_invalid_with(document, "REC-A010")

        document = copy.deepcopy(self.real)
        document["acceptance_contract"]["ptm_office_import_is_field_proof"] = True
        self.assert_invalid_with(document, "REC-A010")

    def test_verify_git_diff_accepts_the_exact_candidate_history(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            result = self.validate_clone(self.clone_candidate(directory))
        self.assertEqual(result["admission_result"], "HELD", result)
        self.assertEqual(result["diagnostics"], [])
        self.assertFalse(result["audit_artifact_verified"])
        self.assertFalse(result["execution_authorized"])
        self.assertEqual(
            result["unresolved_decision_codes"],
            [f"REC-D{number:03d}" for number in range(1, 12)],
        )

    def test_verify_git_diff_rejects_transient_unauthorized_history(self) -> None:
        transient = (
            "docs/superpowers/specs/records-p0/TRANSIENT-UNAUTHORIZED.md"
        )
        with tempfile.TemporaryDirectory() as directory:
            clone = self.clone_candidate(directory)
            self.run_git(clone, "config", "user.name", "Synthetic test author")
            self.run_git(clone, "config", "user.email", "synthetic@example.invalid")
            path = clone / transient
            path.write_text("synthetic transient fixture\n", encoding="utf-8")
            self.run_git(clone, "add", "--", transient)
            self.run_git(clone, "commit", "--quiet", "-m", "add transient path")
            self.run_git(clone, "rm", "--quiet", "--", transient)
            self.run_git(clone, "commit", "--quiet", "-m", "remove transient path")
            result = self.validate_clone(clone)

        self.assertEqual(result["admission_result"], "INVALID", result)
        self.assertFalse(result["execution_authorized"])
        self.assertIn("REC-A012", self.diagnostic_codes(result))
        messages = {item["message"] for item in result["diagnostics"]}
        self.assertTrue(
            any(
                message.startswith(f"transient forbidden path {transient}")
                for message in messages
            ),
            messages,
        )
        self.assertTrue(
            any(message.startswith("transient status D") for message in messages),
            messages,
        )


if __name__ == "__main__":
    unittest.main()

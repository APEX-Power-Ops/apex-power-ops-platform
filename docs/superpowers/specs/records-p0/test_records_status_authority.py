"""DB-free guard for the canonical Records migration/status surfaces."""

from __future__ import annotations

import re
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[4]
MIGRATIONS = REPO_ROOT / "infra/database/migrations/records"


def read(path: str) -> str:
    return (REPO_ROOT / path).read_text(encoding="utf-8")


class RecordsStatusAuthorityTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.up_migrations = sorted(
            int(match.group(1))
            for path in MIGRATIONS.glob("[0-9][0-9][0-9]_*.sql")
            if not path.stem.endswith("_down")
            if (match := re.match(r"^(\d{3})_", path.name))
        )

    def test_migration_chain_is_contiguous_through_049(self) -> None:
        self.assertEqual(self.up_migrations, list(range(1, 50)))

    def test_lane_charter_tracks_the_derived_ceiling_and_completed_security(self) -> None:
        lane = read("docs/lanes/README.md")
        self.assertIn("migrations `001`-`049`", lane)
        self.assertNotIn("migrations through `044`", lane)
        self.assertNotIn("next = security/RLS", lane)

    def test_current_state_is_post_049_and_dormant(self) -> None:
        state = read("reference/records/CURRENT-STATE.md")
        self.assertIn("migrations `001` through `049`", state)
        self.assertIn("production-applied but deliberately dormant", state)
        self.assertNotIn("Consolidated platform records migrations: `001` through `044`", state)
        self.assertNotIn("Security/RLS - design, implement, and test", state)

    def test_manifest_describes_the_full_runner_and_removes_obsolete_quick_path(self) -> None:
        manifest = read("infra/database/migrations/records/MANIFEST.md")
        self.assertIn("applies `001`-`049` forward-incrementally", manifest)
        self.assertNotIn("apex_neta_stage", manifest)
        self.assertNotIn("Not yet applied to the governed Supabase project", manifest)

    def test_punchlist_treats_security_and_audit_as_completed_substrate(self) -> None:
        punchlist = read("reference/records/PUNCHLIST.md")
        self.assertIn("migrations `001`-`049`", punchlist)
        self.assertIn("Gate 3/5 security, ownership, and audit substrate", punchlist)
        self.assertNotIn("contains records migrations through `044`", punchlist)


if __name__ == "__main__":
    unittest.main()

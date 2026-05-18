"""
In-memory data store for the mutation seam.
Used during prototype phase before connecting to Supabase.
"""
from datetime import datetime, timezone
from typing import Any, Dict, List
from uuid import uuid4

from app.pm_lane_seed import build_pm_lane_seed


class MemoryStore:
    """Thread-safe in-memory store for all entities."""

    def __init__(self):
        """Initialize the store with empty collections."""
        self.apparatus: Dict[str, Dict[str, Any]] = {}
        self.checklist_items: Dict[str, Dict[str, Any]] = {}
        self.hours: Dict[str, Dict[str, Any]] = {}
        self.issues: Dict[str, Dict[str, Any]] = {}
        self.assignments: Dict[str, Dict[str, Any]] = {}
        self.durable_field_records: Dict[str, Dict[str, Any]] = {}
        self.production_tracking_records: Dict[str, Dict[str, Any]] = {}
        self.customer_completion_records: Dict[str, Dict[str, Any]] = {}
        self.financial_handoff_records: Dict[str, Dict[str, Any]] = {}
        self.temp_power_actuals_capture_reviews: Dict[str, Dict[str, Any]] = {}
        self.temp_power_customer_preview_reviews: Dict[str, Dict[str, Any]] = {}
        self.temp_power_customer_delivery_proof_reviews: Dict[str, Dict[str, Any]] = {}
        self.tasks: Dict[str, Dict[str, Any]] = {}
        self.workpackages: Dict[str, Dict[str, Any]] = {}
        self.snapshots: Dict[str, Dict[str, Any]] = {}
        self.idempotency_keys: Dict[str, Dict[str, Any]] = {}
        self.pm_import_candidate_approvals: Dict[str, Dict[str, Any]] = {}
        self.audit_log: List[Dict[str, Any]] = []
        self.projects: Dict[str, Dict[str, Any]] = {}

    def seed_demo_data(self):
        """Populate the store with demo data."""
        now = datetime.now(timezone.utc).isoformat()
        seed = build_pm_lane_seed(now)

        self.projects[seed["project"]["id"]] = seed["project"]
        for row in seed["workpackages"]:
            self.workpackages[row["id"]] = row
        for row in seed["tasks"]:
            self.tasks[row["id"]] = row
        for row in seed["apparatus"]:
            self.apparatus[row["id"]] = row
        for row in seed["checklist_items"]:
            self.checklist_items[row["id"]] = row
        for row in seed["assignments"]:
            self.assignments[row["id"]] = row
        for row in seed["hours"]:
            self.hours[row["id"]] = row
        for row in seed["snapshots"]:
            self.snapshots[row["id"]] = row
        for row in seed["issues"]:
            self.issues[row["id"]] = row

    def reset(self):
        """Clear all data and reseed."""
        self.__init__()
        self.seed_demo_data()


# Singleton instance
store = MemoryStore()
store.seed_demo_data()

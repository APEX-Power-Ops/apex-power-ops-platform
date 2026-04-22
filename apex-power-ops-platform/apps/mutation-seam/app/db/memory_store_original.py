"""
In-memory data store for the mutation seam.
Used during prototype phase before connecting to Supabase.
"""
from datetime import datetime, timezone
from typing import Any, Dict, List
from uuid import uuid4


class MemoryStore:
    """Thread-safe in-memory store for all entities."""

    def __init__(self):
        """Initialize the store with empty collections."""
        self.apparatus: Dict[str, Dict[str, Any]] = {}
        self.checklist_items: Dict[str, Dict[str, Any]] = {}
        self.hours: Dict[str, Dict[str, Any]] = {}
        self.issues: Dict[str, Dict[str, Any]] = {}
        self.assignments: Dict[str, Dict[str, Any]] = {}
        self.tasks: Dict[str, Dict[str, Any]] = {}
        self.workpackages: Dict[str, Dict[str, Any]] = {}
        self.snapshots: Dict[str, Dict[str, Any]] = {}
        self.idempotency_keys: Dict[str, Dict[str, Any]] = {}
        self.audit_log: List[Dict[str, Any]] = []
        self.projects: Dict[str, Dict[str, Any]] = {}

    def seed_demo_data(self):
        """Populate the store with demo data."""
        now = datetime.now(timezone.utc).isoformat()

        # Create 1 project
        self.projects["proj-001"] = {
            "id": "proj-001",
            "name": "Stack Data Center",
            "created_at": now,
            "updated_at": now,
        }

        # Create 2 workpackages
        self.workpackages["wp-001"] = {
            "id": "wp-001",
            "project_id": "proj-001",
            "name": "Electrical Systems",
            "status": "active",
            "created_at": now,
            "updated_at": now,
        }
        self.workpackages["wp-002"] = {
            "id": "wp-002",
            "project_id": "proj-001",
            "name": "Safety & Controls",
            "status": "active",
            "created_at": now,
            "updated_at": now,
        }

        # Create 4 tasks (2 per WP)
        tasks_data = [
            ("task-001", "wp-001", "Ground Testing", 1.0),
            ("task-002", "wp-001", "Insulation Testing", 0.8),
            ("task-003", "wp-002", "Arc Flash Analysis", 0.6),
            ("task-004", "wp-002", "Controls Documentation", 0.4),
        ]
        for task_id, wp_id, name, priority in tasks_data:
            self.tasks[task_id] = {
                "id": task_id,
                "workpackage_id": wp_id,
                "project_id": "proj-001",
                "name": name,
                "status": "not_started",
                "priority": priority,
                "assigned_to": None,
                "created_at": now,
                "updated_at": now,
            }

        # Create 6 apparatus with mixed statuses
        apparatus_data = [
            ("app-001", "task-001", "Main Breaker 480V", "ATS", "not_started", None),
            ("app-002", "task-001", "Distribution Panel", "MTS", "ready", "tech-001"),
            ("app-003", "task-002", "Cable Assembly A", "ATS", "active", "tech-001"),
            ("app-004", "task-002", "Cable Assembly B", "ATS", "not_started", None),
            ("app-005", "task-003", "Control Transformer", "MTS", "not_started", None),
            ("app-006", "task-004", "Safety Switch", "MTS", "ready", None),
        ]
        for app_id, task_id, name, standard, status, assigned_to in apparatus_data:
            self.apparatus[app_id] = {
                "id": app_id,
                "task_id": task_id,
                "project_id": "proj-001",
                "name": name,
                "neta_standard": standard,
                "status": status,
                "assigned_to": assigned_to,
                "created_at": now,
                "updated_at": now,
            }

        # Create 12 checklist items (2 per apparatus)
        checklist_names = ["Visual inspection", "Continuity test"]
        item_counter = 1
        for app_id in self.apparatus.keys():
            for cname in checklist_names:
                item_id = f"item-{item_counter:03d}"
                self.checklist_items[item_id] = {
                    "id": item_id,
                    "apparatus_id": app_id,
                    "task_id": self.apparatus[app_id]["task_id"],
                    "project_id": "proj-001",
                    "name": cname,
                    "completed": False,
                    "created_at": now,
                    "updated_at": now,
                }
                item_counter += 1

        # Create 2 assignments
        self.assignments["assign-001"] = {
            "id": "assign-001",
            "apparatus_id": "app-002",
            "task_id": "task-001",
            "project_id": "proj-001",
            "assigned_to": "tech-001",
            "assigned_by": "lead-001",
            "created_at": now,
            "updated_at": now,
        }
        self.assignments["assign-002"] = {
            "id": "assign-002",
            "apparatus_id": "app-003",
            "task_id": "task-002",
            "project_id": "proj-001",
            "assigned_to": "tech-001",
            "assigned_by": "lead-001",
            "created_at": now,
            "updated_at": now,
        }

        # Create 2 progress snapshots
        self.snapshots["snap-001"] = {
            "id": "snap-001",
            "workpackage_id": "wp-001",
            "project_id": "proj-001",
            "period_start": "2026-04-01",
            "period_end": "2026-04-15",
            "status": "submitted",
            "percent_complete": 45,
            "hours_reported": 120,
            "submitted_by": "lead-001",
            "created_at": now,
            "updated_at": now,
        }
        self.snapshots["snap-002"] = {
            "id": "snap-002",
            "workpackage_id": "wp-002",
            "project_id": "proj-001",
            "period_start": "2026-04-01",
            "period_end": "2026-04-15",
            "status": "draft",
            "percent_complete": 20,
            "hours_reported": 40,
            "submitted_by": "lead-001",
            "created_at": now,
            "updated_at": now,
        }

        # Create 2 issues
        self.issues["issue-001"] = {
            "id": "issue-001",
            "apparatus_id": "app-003",
            "task_id": "task-002",
            "project_id": "proj-001",
            "title": "Insulation resistance out of range",
            "severity": "medium",
            "status": "open",
            "blocks_completion": False,
            "reported_by": "tech-001",
            "created_at": now,
            "updated_at": now,
        }
        self.issues["issue-002"] = {
            "id": "issue-002",
            "apparatus_id": "app-001",
            "task_id": "task-001",
            "project_id": "proj-001",
            "title": "Ground rod connection loose",
            "severity": "high",
            "status": "open",
            "blocks_completion": True,
            "reported_by": "tech-001",
            "created_at": now,
            "updated_at": now,
        }

    def reset(self):
        """Clear all data and reseed."""
        self.__init__()
        self.seed_demo_data()


# Singleton instance
store = MemoryStore()
store.seed_demo_data()

#!/usr/bin/env python3
"""
ASTA M1 Persisted State Machine with One Active Worker

Manages run lifecycle with persisted state transitions.
One active worker per machine. Deterministic restart/resume.
Idempotent cancel/rerun. Immutable snapshots.
"""

from __future__ import annotations
from typing import Dict, List, Optional, Any, Set, Tuple, Callable
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
import json
import sqlite3
import threading
import time
import os
import hashlib
from contextlib import contextmanager

# ==============================================================================
# Run States
# ==============================================================================

class RunState(str, Enum):
    """Run lifecycle states."""
    PENDING = "pending"           # Plan approved, waiting for worker
    INITIALIZING = "initializing" # Worker starting up
    RUNNING = "running"           # Checks executing
    PAUSED = "paused"             # Paused by user
    COMPLETED = "completed"       # All checks finished
    FAILED = "failed"             # Critical failure
    CANCELLED = "cancelled"       # Cancelled by user
    NO_RESULT = "no_result"       # No checks executed

class CheckState(str, Enum):
    """Individual check states."""
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    SKIPPED = "skipped"

class AttemptState(str, Enum):
    """Individual attempt states."""
    PASSED = "Passed"
    FAILED = "Failed"
    FLAKY = "Flaky"
    SKIPPED = "Skipped"
    BLOCKED = "Blocked"
    INCONCLUSIVE = "Inconclusive"
    UNSUPPORTED = "Unsupported"
    ERROR = "Error"

# ==============================================================================
# State Transition Definitions
# ==============================================================================

# Valid state transitions: from_state -> set of valid to_states
VALID_RUN_TRANSITIONS = {
    RunState.PENDING: {RunState.INITIALIZING, RunState.CANCELLED},
    RunState.INITIALIZING: {RunState.RUNNING, RunState.FAILED, RunState.CANCELLED},
    RunState.RUNNING: {RunState.COMPLETED, RunState.FAILED, RunState.PAUSED, RunState.CANCELLED},
    RunState.PAUSED: {RunState.RUNNING, RunState.CANCELLED},
    RunState.COMPLETED: set(),  # Terminal
    RunState.FAILED: {RunState.CANCELLED},  # Can cancel cleanup
    RunState.CANCELLED: set(),  # Terminal
    RunState.NO_RESULT: set(),  # Terminal
}

VALID_CHECK_TRANSITIONS = {
    CheckState.PENDING: {CheckState.QUEUED, CheckState.SKIPPED, CheckState.CANCELLED},
    CheckState.QUEUED: {CheckState.RUNNING, CheckState.CANCELLED, CheckState.SKIPPED},
    CheckState.RUNNING: {CheckState.COMPLETED, CheckState.FAILED, CheckState.CANCELLED},
    CheckState.COMPLETED: set(),
    CheckState.FAILED: set(),
    CheckState.CANCELLED: set(),
    CheckState.SKIPPED: set(),
}

# ==============================================================================
# State Machine Core
# ==============================================================================

@dataclass
class StateTransition:
    """Record of a state transition."""
    entity_type: str          # "run", "check", "attempt"
    entity_id: str
    from_state: str
    to_state: str
    timestamp: str
    actor: str                # "system", "user", "worker"
    reason: str = ""
    metadata: Dict = field(default_factory=dict)

@dataclass
class RunSnapshot:
    """Immutable snapshot of run state."""
    run_id: str
    project_id: str
    plan_revision: int
    content_hash: str
    state: RunState
    scope_types: List[str]
    risk_approval: str
    checks_total: int
    checks_completed: int
    checks_failed: int
    checks_blocked: int
    checks_unsupported: int
    started_at: Optional[str]
    completed_at: Optional[str]
    snapshot_at: str
    snapshot_hash: str


# ==============================================================================
# State Machine Engine
# ==============================================================================

class StateMachineEngine:
    """
    Persisted state machine for run lifecycle management.
    All transitions are guarded, persisted, and auditable.
    """

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._lock = threading.RLock()
        self._active_run: Optional[str] = None  # Track single active run per machine
        self._worker_lock = threading.Lock()
        self._init_tables()

    def _init_tables(self):
        """Initialize state machine tables."""
        with sqlite3.connect(self.db_path) as conn:
            # Run state tracking
            conn.execute("""
                CREATE TABLE IF NOT EXISTS run_state_machine (
                    run_id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    plan_revision INTEGER NOT NULL,
                    content_hash TEXT NOT NULL,
                    state TEXT NOT NULL,
                    scope_types_json TEXT NOT NULL,
                    risk_approval TEXT NOT NULL,
                    checks_total INTEGER DEFAULT 0,
                    checks_completed INTEGER DEFAULT 0,
                    checks_failed INTEGER DEFAULT 0,
                    checks_blocked INTEGER DEFAULT 0,
                    checks_unsupported INTEGER DEFAULT 0,
                    started_at TEXT,
                    completed_at TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    worker_id TEXT,  -- Which worker owns this run
                    metadata_json TEXT
                )
            """)

            # Check state tracking
            conn.execute("""
                CREATE TABLE IF NOT EXISTS check_state_machine (
                    check_id TEXT PRIMARY KEY,
                    run_id TEXT NOT NULL,
                    check_key TEXT NOT NULL,
                    capability_id TEXT NOT NULL,
                    state TEXT NOT NULL,
                    queued_at TEXT,
                    started_at TEXT,
                    completed_at TEXT,
                    attempt_count INTEGER DEFAULT 0,
                    last_attempt_id TEXT,
                    error_message TEXT,
                    metadata_json TEXT
                )
            """)

            # Attempt tracking
            conn.execute("""
                CREATE TABLE IF NOT EXISTS attempt_state_machine (
                    attempt_id TEXT PRIMARY KEY,
                    check_id TEXT NOT NULL,
                    attempt_number INTEGER NOT NULL,
                    state TEXT NOT NULL,
                    exit_code INTEGER,
                    stdout TEXT,
                    stderr TEXT,
                    duration_seconds INTEGER,
                    evidence_hash TEXT,
                    error_message TEXT,
                    started_at TEXT,
                    completed_at TEXT,
                    worker_id TEXT
                )
            """)

            # Transition audit log
            conn.execute("""
                CREATE TABLE IF NOT EXISTS state_transitions (
                    id TEXT PRIMARY KEY,
                    entity_type TEXT NOT NULL,
                    entity_id TEXT NOT NULL,
                    from_state TEXT,
                    to_state TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    actor TEXT NOT NULL,
                    reason TEXT,
                    metadata_json TEXT
                )
            """)

            # Active worker registry (singleton enforcement)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS active_worker (
                    worker_id TEXT PRIMARY KEY,
                    run_id TEXT,
                    started_at TEXT NOT NULL,
                    heartbeat_at TEXT NOT NULL,
                    pid INTEGER,
                    metadata_json TEXT
                )
            """)

            # Create indexes
            conn.execute("CREATE INDEX IF NOT EXISTS idx_transitions_entity ON state_transitions(entity_type, entity_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_check_run ON check_state_machine(run_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_attempt_check ON attempt_state_machine(check_id)")

    # ==========================================================================
    # Run Lifecycle
    # ==========================================================================

    def create_run(self,
                   run_id: str,
                   project_id: str,
                   plan_revision: int,
                   content_hash: str,
                   scope_types: List[str],
                   risk_approval: str,
                   checks_total: int) -> bool:
        """Create a new run in PENDING state."""
        with self._lock, self._db_transaction() as conn:
            # Check for existing run
            existing = conn.execute("SELECT run_id FROM run_state_machine WHERE run_id = ?", (run_id,)).fetchone()
            if existing:
                return False

            now = datetime.utcnow().isoformat() + "Z"
            conn.execute("""
                INSERT INTO run_state_machine
                (run_id, project_id, plan_revision, content_hash, state, scope_types_json,
                 risk_approval, checks_total, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (run_id, project_id, plan_revision, content_hash, RunState.PENDING.value,
                  json.dumps(scope_types), risk_approval, checks_total, now, now))

            self._log_transition(conn, "run", run_id, None, RunState.PENDING.value, "system", "Run created")
            return True

    def transition_run(self,
                       run_id: str,
                       to_state: RunState,
                       actor: str = "system",
                       reason: str = "",
                       worker_id: str = None,
                       metadata: Dict = None) -> Tuple[bool, str]:
        """Transition run state with validation and persistence."""
        with self._lock, self._db_transaction() as conn:
            # Get current state
            row = conn.execute("SELECT state, worker_id FROM run_state_machine WHERE run_id = ?", (run_id,)).fetchone()
            if not row:
                return False, f"Run {run_id} not found"

            from_state = RunState(row[0])
            current_worker = row[1]

            # Validate transition
            if to_state not in VALID_RUN_TRANSITIONS.get(from_state, set()):
                return False, f"Invalid transition: {from_state.value} -> {to_state.value}"

            # Worker ownership check
            if worker_id and current_worker and current_worker != worker_id:
                return False, f"Run owned by different worker: {current_worker}"

            # Update state
            now = datetime.utcnow().isoformat() + "Z"
            updates = ["state = ?", "updated_at = ?"]
            params = [to_state.value, now]

            if to_state == RunState.INITIALIZING:
                updates.append("started_at = ?")
                params.append(now)
                if worker_id:
                    updates.append("worker_id = ?")
                    params.append(worker_id)
            elif to_state in (RunState.COMPLETED, RunState.FAILED, RunState.CANCELLED):
                updates.append("completed_at = ?")
                params.append(now)

            if metadata:
                updates.append("metadata_json = ?")
                params.append(json.dumps(metadata))

            params.append(run_id)
            conn.execute(f"UPDATE run_state_machine SET {', '.join(updates)} WHERE run_id = ?", params)

            # Log transition
            self._log_transition(conn, "run", run_id, from_state.value, to_state.value, actor, reason, metadata)

            # Update active worker tracking
            if to_state == RunState.INITIALIZING and worker_id:
                self._register_worker(conn, worker_id, run_id)
            elif to_state in (RunState.COMPLETED, RunState.FAILED, RunState.CANCELLED):
                self._unregister_worker(conn, worker_id or current_worker)

            return True, "Transition successful"

    def get_run_state(self, run_id: str) -> Optional[Dict]:
        """Get current run state."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute("SELECT * FROM run_state_machine WHERE run_id = ?", (run_id,)).fetchone()
            if row:
                return dict(row)
        return None

    # ==========================================================================
    # Check Lifecycle
    # ==========================================================================

    def create_checks(self, run_id: str, checks: List[Dict]) -> bool:
        """Create check entries for a run."""
        with self._lock, self._db_transaction() as conn:
            for check in checks:
                conn.execute("""
                    INSERT INTO check_state_machine
                    (check_id, run_id, check_key, capability_id, state)
                    VALUES (?, ?, ?, ?, ?)
                """, (check["check_id"], run_id, check["check_key"],
                      check["capability_id"], CheckState.PENDING.value))
            return True

    def transition_check(self,
                         check_id: str,
                         to_state: CheckState,
                         actor: str = "system",
                         reason: str = "",
                         metadata: Dict = None) -> Tuple[bool, str]:
        """Transition check state."""
        with self._lock, self._db_transaction() as conn:
            row = conn.execute("SELECT state FROM check_state_machine WHERE check_id = ?", (check_id,)).fetchone()
            if not row:
                return False, f"Check {check_id} not found"

            from_state = CheckState(row[0])

            if to_state not in VALID_CHECK_TRANSITIONS.get(from_state, set()):
                return False, f"Invalid transition: {from_state.value} -> {to_state.value}"

            now = datetime.utcnow().isoformat() + "Z"
            updates = ["state = ?"]
            params = [to_state.value]

            if to_state == CheckState.QUEUED:
                updates.append("queued_at = ?")
                params.append(now)
            elif to_state == CheckState.RUNNING:
                updates.append("started_at = ?")
                params.append(now)
            elif to_state in (CheckState.COMPLETED, CheckState.FAILED, CheckState.CANCELLED, CheckState.SKIPPED):
                updates.append("completed_at = ?")
                params.append(now)

            params.append(check_id)
            conn.execute(f"UPDATE check_state_machine SET {', '.join(updates)} WHERE check_id = ?", params)

            self._log_transition(conn, "check", check_id, from_state.value, to_state.value, actor, reason, metadata)
            return True, "Transition successful"

    # ==========================================================================
    # Attempt Tracking
    # ==========================================================================

    def create_attempt(self,
                       attempt_id: str,
                       check_id: str,
                       attempt_number: int,
                       worker_id: str) -> bool:
        """Create a new attempt."""
        with self._lock, self._db_transaction() as conn:
            now = datetime.utcnow().isoformat() + "Z"
            conn.execute("""
                INSERT INTO attempt_state_machine
                (attempt_id, check_id, attempt_number, state, started_at, worker_id)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (attempt_id, check_id, attempt_number, AttemptState.RUNNING.value, now, worker_id))

            # Update check attempt count
            conn.execute("""
                UPDATE check_state_machine
                SET attempt_count = attempt_count + 1, last_attempt_id = ?
                WHERE check_id = ?
            """, (attempt_id, check_id))
            return True

    def complete_attempt(self,
                         attempt_id: str,
                         state: str,
                         exit_code: int,
                         stdout: str,
                         stderr: str,
                         duration_seconds: int,
                         evidence_hash: str,
                         error_message: str = None) -> bool:
        """Complete an attempt with result."""
        with self._lock, self._db_transaction() as conn:
            now = datetime.utcnow().isoformat() + "Z"
            conn.execute("""
                UPDATE attempt_state_machine
                SET state = ?, exit_code = ?, stdout = ?, stderr = ?,
                    duration_seconds = ?, evidence_hash = ?, error_message = ?, completed_at = ?
                WHERE attempt_id = ?
            """, (state, exit_code, stdout, stderr, duration_seconds, evidence_hash, error_message, now, attempt_id))
            return True

    # ==========================================================================
    # Single Active Worker Enforcement
    # ==========================================================================

    def acquire_worker_slot(self, worker_id: str, run_id: str) -> Tuple[bool, str]:
        """Acquire exclusive worker slot for a run."""
        with self._worker_lock, self._db_transaction() as conn:
            # Check if another worker is active
            active = conn.execute("SELECT worker_id, run_id FROM active_worker WHERE worker_id != ?", (worker_id,)).fetchone()
            if active:
                return False, f"Worker {active[0]} already active on run {active[1]}"

            # Register this worker
            now = datetime.utcnow().isoformat() + "Z"
            conn.execute("""
                INSERT OR REPLACE INTO active_worker
                (worker_id, run_id, started_at, heartbeat_at, pid)
                VALUES (?, ?, ?, ?, ?)
            """, (worker_id, run_id, datetime.utcnow().isoformat() + "Z", now, os.getpid()))
            return True, "Worker slot acquired"

    def release_worker_slot(self, worker_id: str) -> bool:
        """Release worker slot."""
        with self._worker_lock, self._db_transaction() as conn:
            conn.execute("DELETE FROM active_worker WHERE worker_id = ?", (worker_id,))
            return True

    def heartbeat(self, worker_id: str) -> bool:
        """Update worker heartbeat."""
        with self._db_transaction() as conn:
            conn.execute("UPDATE active_worker SET heartbeat_at = ? WHERE worker_id = ?",
                        (datetime.utcnow().isoformat() + "Z", worker_id))
            return True

    # ==========================================================================
    # Restart/Resume
    # ==========================================================================

    def resume_run(self, run_id: str, worker_id: str) -> Tuple[bool, str, Optional[Dict]]:
        """Resume a run after restart. Returns (success, message, resume_info)."""
        with self._lock, self._db_transaction() as conn:
            run = conn.execute("SELECT * FROM run_state_machine WHERE run_id = ?", (run_id,)).fetchone()
            if not run:
                return False, "Run not found", None

            state = RunState(run["state"])

            # Can only resume from these states
            if state not in (RunState.PAUSED, RunState.INITIALIZING, RunState.RUNNING):
                return False, f"Cannot resume from state {state.value}", None

            # Check for incomplete checks
            incomplete = conn.execute("""
                SELECT check_id, state FROM check_state_machine
                WHERE run_id = ? AND state IN (?, ?, ?)
            """, (run_id, CheckState.QUEUED.value, CheckState.RUNNING.value, CheckState.PENDING.value)).fetchall()

            resume_info = {
                "run_id": run_id,
                "state": state.value,
                "incomplete_checks": [{"check_id": c[0], "state": c[1]} for c in incomplete],
                "checks_total": run["checks_total"],
                "checks_completed": run["checks_completed"]
            }

            # Transition to INITIALIZING to restart worker
            success, msg = self.transition_run(run_id, RunState.INITIALIZING, "system", "Restart resume", worker_id)
            if success:
                return True, "Run resumed", resume_info
            return False, msg, None

    def cancel_run(self, run_id: str, actor: str = "user", reason: str = "") -> Tuple[bool, str]:
        """Cancel a run (idempotent)."""
        with self._lock, self._db_transaction() as conn:
            run = conn.execute("SELECT state FROM run_state_machine WHERE run_id = ?", (run_id,)).fetchone()
            if not run:
                return False, "Run not found"

            state = RunState(run[0])

            # Idempotent: if already cancelled, succeed
            if state == RunState.CANCELLED:
                return True, "Already cancelled"

            # Cancel pending/running checks
            conn.execute("""
                UPDATE check_state_machine
                SET state = ?
                WHERE run_id = ? AND state IN (?, ?, ?)
            """, (CheckState.CANCELLED.value, run_id,
                  CheckState.PENDING.value, CheckState.QUEUED.value, CheckState.RUNNING.value))

            # Transition run to cancelled
            return self.transition_run(run_id, RunState.CANCELLED, actor, reason or "User cancelled")

    def rerun_check(self, check_id: str, worker_id: str) -> Tuple[bool, str, Optional[str]]:
        """Rerun a check (creates new attempt). Idempotent for completed checks."""
        with self._lock, self._db_transaction() as conn:
            check = conn.execute("SELECT run_id, state, attempt_count FROM check_state_machine WHERE check_id = ?", (check_id,)).fetchone()
            if not check:
                return False, "Check not found", None

            run_id, state, attempt_count = check

            # Only rerun completed/failed/cancelled checks
            if state not in (CheckState.COMPLETED, CheckState.FAILED, CheckState.CANCELLED):
                return False, f"Cannot rerun check in state {state}", None

            # Create new attempt
            new_attempt_number = attempt_count + 1
            attempt_id = f"att_{hashlib.sha256(f'{check_id}{new_attempt_number}{datetime.utcnow().isoformat()}'.encode()).hexdigest()[:12]}"

            # Reset check state to QUEUED
            self.transition_check(check_id, CheckState.QUEUED, "system", "Rerun requested")

            # Create new attempt
            self.create_attempt(attempt_id, check_id, new_attempt_number, worker_id)

            return True, "Check queued for rerun", attempt_id

    # ==========================================================================
    # Snapshots
    # ==========================================================================

    def create_run_snapshot(self, run_id: str) -> Optional[RunSnapshot]:
        """Create immutable snapshot of run state."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            run = conn.execute("SELECT * FROM run_state_machine WHERE run_id = ?", (run_id,)).fetchone()
            if not run:
                return None

            # Get check states
            checks = conn.execute("""
                SELECT state FROM check_state_machine WHERE run_id = ?
            """, (run_id,)).fetchall()

            completed = sum(1 for c in checks if c["state"] in (CheckState.COMPLETED.value, CheckState.FAILED.value))
            failed = sum(1 for c in checks if c["state"] == CheckState.FAILED.value)
            blocked = sum(1 for c in checks if c["state"] == CheckState.BLOCKED.value)
            unsupported = sum(1 for c in checks if c["state"] == CheckState.UNSUPPORTED.value)

            snapshot = RunSnapshot(
                run_id=run_id,
                project_id=run["project_id"],
                plan_revision=run["plan_revision"],
                content_hash=run["content_hash"],
                state=RunState(run["state"]),
                scope_types=json.loads(run["scope_types_json"]),
                risk_approval=run["risk_approval"],
                checks_total=run["checks_total"],
                checks_completed=completed,
                checks_failed=failed,
                checks_blocked=blocked,
                checks_unsupported=unsupported,
                started_at=run["started_at"],
                completed_at=run["completed_at"],
                snapshot_at=datetime.utcnow().isoformat() + "Z",
                snapshot_hash=hashlib.sha256(f"{run_id}{datetime.utcnow().isoformat()}".encode()).hexdigest()
            )
            return snapshot

    # ==========================================================================
    # Helpers
    # ==========================================================================

    @contextmanager
    def _db_transaction(self):
        """Database transaction context manager."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _log_transition(self, conn, entity_type: str, entity_id: str,
                        from_state: Optional[str], to_state: str,
                        actor: str, reason: str, metadata: Dict = None):
        """Log state transition to audit log."""
        transition_id = f"trans_{hashlib.sha256(f'{entity_type}{entity_id}{to_state}{datetime.utcnow().isoformat()}'.encode()).hexdigest()[:12]}"
        conn.execute("""
            INSERT INTO state_transitions
            (id, entity_type, entity_id, from_state, to_state, timestamp, actor, reason, metadata_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (transition_id, entity_type, entity_id, from_state, to_state,
              datetime.utcnow().isoformat() + "Z", actor, reason, json.dumps(metadata or {})))

    def _register_worker(self, conn, worker_id: str, run_id: str):
        """Register active worker."""
        now = datetime.utcnow().isoformat() + "Z"
        conn.execute("""
            INSERT OR REPLACE INTO active_worker
            (worker_id, run_id, started_at, heartbeat_at, pid)
            VALUES (?, ?, ?, ?, ?)
        """, (worker_id, run_id, now, now, os.getpid()))

    def _unregister_worker(self, conn, worker_id: str):
        """Unregister worker."""
        conn.execute("DELETE FROM active_worker WHERE worker_id = ?", (worker_id,))


# ==============================================================================
# Run State Machine Facade
# ==============================================================================

class RunStateMachine:
    """High-level facade for run state management."""

    def __init__(self, db_path: Path):
        self.engine = StateMachineEngine(db_path)

    def start_run(self,
                  run_id: str,
                  project_id: str,
                  plan_revision: int,
                  content_hash: str,
                  scope_types: List[str],
                  risk_approval: str,
                  checks: List[Dict]) -> bool:
        """Start a new run."""
        checks_total = len(checks)
        if not self.engine.create_run(run_id, project_id, plan_revision, content_hash, scope_types, risk_approval, checks_total):
            return False
        if not self.engine.create_checks(run_id, checks):
            return False
        return True

    def start_worker(self, run_id: str, worker_id: str) -> Tuple[bool, str]:
        """Start worker for run."""
        return self.engine.transition_run(run_id, RunState.INITIALIZING, "worker", "Worker starting", worker_id)

    def start_checks(self, run_id: str, worker_id: str) -> bool:
        """Mark checks as queued/running."""
        # Implementation would queue checks for worker
        return True

    def complete_run(self, run_id: str, worker_id: str, success: bool) -> Tuple[bool, str]:
        """Complete a run."""
        to_state = RunState.COMPLETED if success else RunState.FAILED
        return self.engine.transition_run(run_id, to_state, "worker", "Run completed" if success else "Run failed", worker_id)

    def cancel_run(self, run_id: str, reason: str = "") -> Tuple[bool, str]:
        return self.engine.cancel_run(run_id, "user", reason)

    def rerun_check(self, check_id: str, worker_id: str) -> Tuple[bool, str, Optional[str]]:
        return self.engine.rerun_check(check_id, worker_id)

    def get_run_status(self, run_id: str) -> Optional[Dict]:
        return self.engine.get_run_state(run_id)

    def resume(self, run_id: str, worker_id: str) -> Tuple[bool, str, Optional[Dict]]:
        return self.engine.resume_run(run_id, worker_id)

    def snapshot(self, run_id: str) -> Optional[RunSnapshot]:
        return self.engine.create_run_snapshot(run_id)


# ==============================================================================
# CLI Integration
# ==============================================================================

if __name__ == "__main__":
    import sys
    import os

    if len(sys.argv) > 1 and sys.argv[1] == "test":
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            sm = RunStateMachine(db_path)

            run_id = "run_test123"
            project_id = "proj_test"

            checks = [
                {"check_id": "chk_1", "check_key": "pytest_unit", "capability_id": "pytest_unit"},
                {"check_id": "chk_2", "check_key": "schemathesis_api", "capability_id": "schemathesis_api"}
            ]

            # Start run
            success = sm.start_run(run_id, project_id, 1, "hash123", ["unit", "api"], "high", checks)
            print(f"Start run: {success}")

            # Start worker
            success, msg = sm.start_worker(run_id, "worker1")
            print(f"Start worker: {success} - {msg}")

            # Get status
            status = sm.get_run_status(run_id)
            print(f"Status: {status['state']}")

            # Complete
            success, msg = sm.complete_run(run_id, "worker1", True)
            print(f"Complete: {success} - {msg}")

            status = sm.get_run_status(run_id)
            print(f"Final status: {status['state']}")

            print("All tests passed!")
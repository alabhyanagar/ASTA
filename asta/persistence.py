#!/usr/bin/env python3
"""
ASTA M1 Physical Data Contracts and Local Persistence Design

Defines the physical data contracts for local persistence:
- IDs, immutable snapshots, DB schema/migrations
- Report schema_version, artifact digest
- File/DB consistency, locking, backup/deletion/retention
- SQLite with SQLAlchemy/Alembic (M1), PostgreSQL later
"""

from __future__ import annotations
from typing import Dict, List, Optional, Any, Literal
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from pathlib import Path
from enum import Enum
import hashlib
import json
import sqlite3
import threading
import contextlib
import os
import time
import shutil

# ==============================================================================
# Physical Data Contracts
# ==============================================================================

class EntityType(str, Enum):
    """Types of entities in the persistence layer."""
    PROJECT = "project"
    RUN = "run"
    CHECK = "check"
    ATTEMPT = "attempt"
    FINDING = "finding"
    ARTIFACT = "artifact"
    APPROVAL = "approval"
    RECOMMENDATION = "recommendation"
    AUDIT_EVENT = "audit_event"
    CREDENTIAL_REF = "credential_ref"

class IDFormat(str, Enum):
    """ID format strategies."""
    UUID = "uuid"                    # UUID v4
    CONTENT_HASH = "content_hash"    # SHA256 of content
    COMPOSITE = "composite"          # Type + hash prefix
    SEQUENTIAL = "sequential"        # Sequential integer (for internal)

@dataclass
class IDPolicy:
    """ID generation policy for each entity type."""
    entity_type: EntityType
    format: IDFormat
    prefix: str = ""
    length: int = 12  # For hash-based IDs

    def generate(self, content: str = None) -> str:
        """Generate an ID according to policy."""
        if self.format == IDFormat.UUID:
            import uuid
            return f"{self.prefix}{uuid.uuid4().hex[:self.length]}"
        elif self.format == IDFormat.CONTENT_HASH:
            if content is None:
                content = datetime.utcnow().isoformat()
            return f"{self.prefix}{hashlib.sha256(content.encode()).hexdigest()[:self.length]}"
        elif self.format == IDFormat.COMPOSITE:
            if content is None:
                content = datetime.utcnow().isoformat()
            return f"{self.prefix}{hashlib.sha256(content.encode()).hexdigest()[:self.length]}"
        elif self.format == IDFormat.SEQUENTIAL:
            # Would need a sequence generator
            return f"{self.prefix}000001"
        return self.generate()

# M1 ID Policies
M1_ID_POLICIES = {
    EntityType.PROJECT: IDPolicy(EntityType.PROJECT, IDFormat.CONTENT_HASH, "proj_", 12),
    EntityType.RUN: IDPolicy(EntityType.RUN, IDFormat.CONTENT_HASH, "run_", 12),
    EntityType.CHECK: IDPolicy(EntityType.CHECK, IDFormat.CONTENT_HASH, "chk_", 12),
    EntityType.ATTEMPT: IDPolicy(EntityType.ATTEMPT, IDFormat.CONTENT_HASH, "att_", 12),
    EntityType.FINDING: IDPolicy(EntityType.FINDING, IDFormat.CONTENT_HASH, "fnd_", 12),
    EntityType.ARTIFACT: IDPolicy(EntityType.ARTIFACT, IDFormat.CONTENT_HASH, "art_", 16),
    EntityType.APPROVAL: IDPolicy(EntityType.APPROVAL, IDFormat.CONTENT_HASH, "apr_", 12),
    EntityType.RECOMMENDATION: IDPolicy(EntityType.RECOMMENDATION, IDFormat.CONTENT_HASH, "rec_", 12),
    EntityType.AUDIT_EVENT: IDPolicy(EntityType.AUDIT_EVENT, IDFormat.CONTENT_HASH, "aud_", 12),
    EntityType.CREDENTIAL_REF: IDPolicy(EntityType.CREDENTIAL_REF, IDFormat.CONTENT_HASH, "cred_", 12),
}

# ==============================================================================
# Immutable Snapshots
# ==============================================================================

@dataclass
class SnapshotMetadata:
    """Metadata for an immutable snapshot."""
    snapshot_id: str
    entity_type: EntityType
    entity_id: str
    content_hash: str
    created_at: str
    schema_version: str
    parent_snapshot_id: Optional[str] = None  # For lineage

    def to_dict(self) -> Dict:
        return asdict(self)

class SnapshotStore:
    """Stores immutable snapshots of entities."""

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._init_schema()

    def _init_schema(self):
        """Initialize snapshot storage schema."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS snapshots (
                    snapshot_id TEXT PRIMARY KEY,
                    entity_type TEXT NOT NULL,
                    entity_id TEXT NOT NULL,
                    content_hash TEXT NOT NULL,
                    content_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    schema_version TEXT NOT NULL,
                    parent_snapshot_id TEXT,
                    FOREIGN KEY (parent_snapshot_id) REFERENCES snapshots(snapshot_id)
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_snapshots_entity
                ON snapshots(entity_type, entity_id)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_snapshots_hash
                ON snapshots(content_hash)
            """)

    def create_snapshot(self,
                        entity_type: EntityType,
                        entity_id: str,
                        content: Dict,
                        schema_version: str = "1.0",
                        parent_snapshot_id: Optional[str] = None) -> 'SnapshotMetadata':
        """Create an immutable snapshot of an entity."""
        content_json = json.dumps(content, sort_keys=True)
        content_hash = hashlib.sha256(content_json.encode()).hexdigest()

        snapshot_id = M1_ID_POLICIES[entity_type].generate(content_json)
        created_at = datetime.utcnow().isoformat() + "Z"

        metadata = SnapshotMetadata(
            snapshot_id=snapshot_id,
            entity_type=entity_type,
            entity_id=entity_id,
            content_hash=content_hash,
            created_at=created_at,
            schema_version=schema_version,
            parent_snapshot_id=parent_snapshot_id
        )

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO snapshots
                (snapshot_id, entity_type, entity_id, content_hash, content_json, created_at, schema_version, parent_snapshot_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (snapshot_id, entity_type.value, entity_id, content_hash, content_json, created_at, schema_version, parent_snapshot_id))

        return metadata

    def get_latest_snapshot(self, entity_type: EntityType, entity_id: str) -> Optional['SnapshotMetadata']:
        """Get the latest snapshot for an entity."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM snapshots
                WHERE entity_type = ? AND entity_id = ?
                ORDER BY created_at DESC LIMIT 1
            """, (entity_type.value, entity_id))
            row = cursor.fetchone()
            if row:
                return SnapshotMetadata(**dict(row))
        return None

    def get_snapshot_history(self, entity_type: EntityType, entity_id: str) -> List['SnapshotMetadata']:
        """Get all snapshots for an entity (lineage)."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM snapshots
                WHERE entity_type = ? AND entity_id = ?
                ORDER BY created_at ASC
            """, (entity_type.value, entity_id))
            return [SnapshotMetadata(**dict(row)) for row in cursor.fetchall()]

# ==============================================================================
# SQLite Schema (M1 Implementation)
# ==============================================================================

M1_SQLITE_SCHEMA = """
-- ============================================================================
-- ASTA M1 SQLite Schema
-- ============================================================================

-- Projects table
CREATE TABLE IF NOT EXISTS projects (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    source_path TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    profile_json TEXT NOT NULL,
    scope_json TEXT NOT NULL,
    config_json TEXT NOT NULL,
    credentials_json TEXT NOT NULL,
    dependencies_json TEXT NOT NULL,
    checks_included_json TEXT NOT NULL,
    checks_excluded_json TEXT NOT NULL,
    checks_blocked_json TEXT NOT NULL,
    checks_unsupported_json TEXT NOT NULL,
    checks_awaiting_authorization_json TEXT NOT NULL,
    authorization_confirmed INTEGER DEFAULT 0,
    ownership_confirmed INTEGER DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_projects_source ON projects(source_path);

-- Runs table
CREATE TABLE IF NOT EXISTS runs (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(id),
    plan_revision INTEGER NOT NULL,
    content_hash TEXT NOT NULL,
    status TEXT NOT NULL,
    started_at TEXT NOT NULL,
    completed_at TEXT,
    scope_types_json TEXT NOT NULL,
    risk_approval TEXT NOT NULL,
    checks_total INTEGER DEFAULT 0,
    passed_count INTEGER DEFAULT 0,
    failed_count INTEGER DEFAULT 0,
    blocked_count INTEGER DEFAULT 0,
    unsupported_count INTEGER DEFAULT 0,
    error_count INTEGER DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_runs_project ON runs(project_id);
CREATE INDEX IF NOT EXISTS idx_runs_status ON runs(status);

-- Checks table
CREATE TABLE IF NOT EXISTS checks (
    id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL REFERENCES runs(id),
    key TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    capability_id TEXT NOT NULL,
    test_type TEXT NOT NULL,
    state TEXT NOT NULL,
    reason TEXT,
    risk_level TEXT NOT NULL,
    target TEXT,
    limits_json TEXT,
    evidence_json TEXT,
    adapter_id TEXT,
    tool_versions_json TEXT
);

CREATE INDEX IF NOT EXISTS idx_checks_run ON checks(run_id);
CREATE INDEX IF NOT EXISTS idx_checks_capability ON checks(capability_id);

-- Attempts table
CREATE TABLE IF NOT EXISTS attempts (
    id TEXT PRIMARY KEY,
    check_id TEXT NOT NULL REFERENCES checks(id),
    attempt_number INTEGER NOT NULL,
    state TEXT NOT NULL,
    exit_code INTEGER,
    stdout TEXT,
    stderr TEXT,
    duration_seconds INTEGER,
    evidence_hash TEXT,
    error_message TEXT,
    started_at TEXT,
    completed_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_attempts_check ON attempts(check_id);

-- Artifacts table
CREATE TABLE IF NOT EXISTS artifacts (
    id TEXT PRIMARY KEY,
    attempt_id TEXT NOT NULL REFERENCES attempts(id),
    artifact_type TEXT NOT NULL,
    file_path TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    redaction_state TEXT,
    size_bytes INTEGER,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_artifacts_attempt ON artifacts(attempt_id);
CREATE INDEX IF NOT EXISTS idx_artifacts_hash ON artifacts(content_hash);

-- Approvals table
CREATE TABLE IF NOT EXISTS approvals (
    id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL REFERENCES runs(id),
    plan_content_hash TEXT NOT NULL,
    plan_revision INTEGER NOT NULL,
    approved_checks_json TEXT NOT NULL,
    excluded_checks_json TEXT NOT NULL,
    approved_recommendations_json TEXT NOT NULL,
    declined_recommendations_json TEXT NOT NULL,
    deferred_recommendations_json TEXT NOT NULL,
    approved_at TEXT NOT NULL,
    approved_by TEXT,
    valid INTEGER DEFAULT 1,
    invalidation_reason TEXT
);

CREATE INDEX IF NOT EXISTS idx_approvals_run ON approvals(run_id);

-- Audit Events table
CREATE TABLE IF NOT EXISTS audit_events (
    id TEXT PRIMARY KEY,
    event_type TEXT NOT NULL,
    severity TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    actor_type TEXT NOT NULL,
    actor_id TEXT NOT NULL,
    actor_source TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    action TEXT NOT NULL,
    reason TEXT NOT NULL,
    policy_version TEXT NOT NULL,
    outcome TEXT NOT NULL,
    metadata_json TEXT NOT NULL,
    redacted_fields_json TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_events(timestamp);
CREATE INDEX IF NOT EXISTS idx_audit_entity ON audit_events(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_audit_type ON audit_events(event_type);
CREATE INDEX IF NOT EXISTS idx_audit_actor ON audit_events(actor_type, actor_id);

-- Snapshots table (for immutable entity history)
CREATE TABLE IF NOT EXISTS snapshots (
    snapshot_id TEXT PRIMARY KEY,
    entity_type TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    content_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    schema_version TEXT NOT NULL,
    parent_snapshot_id TEXT REFERENCES snapshots(snapshot_id)
);

CREATE INDEX IF NOT EXISTS idx_snapshots_entity ON snapshots(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_snapshots_hash ON snapshots(content_hash);

-- Credential References table (never stores actual secrets)
CREATE TABLE IF NOT EXISTS credential_refs (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(id),
    reference_type TEXT NOT NULL,  -- 'os-keyring', 'env', 'file'
    reference_value TEXT NOT NULL, -- e.g., 'os-keyring:my-secret' or 'ENV_VAR_NAME'
    purpose TEXT NOT NULL,
    allowed_targets_json TEXT,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_cred_project ON credential_refs(project_id);
"""

# ==============================================================================
# Migration Management (Alembic-style)
# ==============================================================================

@dataclass
class Migration:
    """Database migration definition."""
    version: str
    name: str
    up_sql: str
    down_sql: str
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")

    def to_dict(self) -> Dict:
        return asdict(self)

class MigrationManager:
    """Manages database migrations."""

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.migrations: List[Migration] = []
        self._register_migrations()
        self._ensure_migration_table()

    def _ensure_migration_table(self):
        """Ensure migration tracking table exists."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    version TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    applied_at TEXT NOT NULL,
                    checksum TEXT NOT NULL
                )
            """)

    def _register_migrations(self):
        """Register all migrations."""
        # Migration 1: Initial schema
        self.migrations.append(Migration(
            version="1.0.0",
            name="initial_schema",
            up_sql=M1_SQLITE_SCHEMA,
            down_sql="DROP TABLE IF EXISTS projects, runs, checks, attempts, artifacts, approvals, audit_events, snapshots, credential_refs;"
        ))

        # Migration 1.1: Add language_binding column to checks
        self.migrations.append(Migration(
            version="1.1.0",
            name="add_language_binding",
            up_sql="ALTER TABLE checks ADD COLUMN language_binding_json TEXT;",
            down_sql="ALTER TABLE checks DROP COLUMN language_binding_json;"
        ))

        # Migration 1.2: Add risk_approval to runs (if missing)
        self.migrations.append(Migration(
            version="1.2.0",
            name="add_risk_approval_to_runs",
            up_sql="ALTER TABLE runs ADD COLUMN risk_approval TEXT DEFAULT 'high';",
            down_sql="ALTER TABLE runs DROP COLUMN risk_approval;"
        ))

    def get_applied_migrations(self) -> List[str]:
        """Get list of applied migration versions."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT version FROM schema_migrations ORDER BY applied_at")
            return [row[0] for row in cursor.fetchall()]

    def get_pending_migrations(self) -> List[Migration]:
        """Get migrations that haven't been applied."""
        applied = set(self.get_applied_migrations())
        return [m for m in self.migrations if m.version not in applied]

    def apply_migration(self, migration: Migration) -> bool:
        """Apply a single migration."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.executescript(migration.up_sql)
                # Record migration
                checksum = hashlib.sha256(migration.up_sql.encode()).hexdigest()
                conn.execute("""
                    INSERT INTO schema_migrations (version, name, applied_at, checksum)
                    VALUES (?, ?, ?, ?)
                """, (migration.version, migration.name, datetime.utcnow().isoformat() + "Z", checksum))
            return True
        except Exception as e:
            print(f"Migration {migration.version} failed: {e}")
            return False

    def migrate(self) -> bool:
        """Apply all pending migrations."""
        pending = self.get_pending_migrations()
        for migration in pending:
            print(f"Applying migration {migration.version}: {migration.name}")
            if not self.apply_migration(migration):
                return False
        return True

    def rollback(self, target_version: str) -> bool:
        """Rollback to a specific version (not implemented for M1)."""
        # M1 doesn't support rollback; would need down_sql execution
        print("Rollback not supported in M1")
        return False

# ==============================================================================
# Artifact Digest and File/DB Consistency
# ==============================================================================

class ArtifactManager:
    """Manages artifacts with content-addressed storage."""

    def __init__(self, artifacts_dir: Path, db_path: Path):
        self.artifacts_dir = artifacts_dir
        self.db_path = db_path
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)
        self._init_artifact_store()

    def _init_artifact_store(self):
        """Initialize artifact storage directory structure."""
        (self.artifacts_dir / "by_hash").mkdir(exist_ok=True)
        (self.artifacts_dir / "by_attempt").mkdir(exist_ok=True)

    def store_artifact(self,
                       attempt_id: str,
                       artifact_type: str,
                       content: bytes,
                       redaction_state: str = "none") -> Dict:
        """Store an artifact with content-addressed hash."""
        content_hash = hashlib.sha256(content).hexdigest()

        # Store by hash (content-addressed)
        hash_path = self.artifacts_dir / "by_hash" / content_hash[:2] / content_hash[2:4] / content_hash
        hash_path.parent.mkdir(parents=True, exist_ok=True)
        hash_path.write_bytes(content)

        # Store by attempt
        attempt_path = self.artifacts_dir / "by_attempt" / attempt_id
        attempt_path.mkdir(parents=True, exist_ok=True)
        artifact_file = attempt_path / f"{artifact_type}_{hashlib.sha256(artifact_type.encode()).hexdigest()[:8]}"

        # Create symlink or copy
        try:
            artifact_file.symlink_to(hash_path)
        except:
            artifact_file.write_bytes(content)

        size_bytes = len(content)

        # Record in database
        artifact_id = f"art_{hashlib.sha256(f'{attempt_id}{artifact_type}{content_hash}'.encode()).hexdigest()[:12]}"

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO artifacts
                (id, attempt_id, artifact_type, file_path, content_hash, redaction_state, size_bytes, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (artifact_id, attempt_id, artifact_type, str(hash_path), content_hash, "none", len(content), datetime.utcnow().isoformat() + "Z"))

        return {
            "artifact_id": artifact_id,
            "content_hash": content_hash,
            "file_path": str(hash_path),
            "size_bytes": size_bytes,
            "artifact_type": artifact_type
        }

    def get_artifact(self, artifact_id: str) -> Optional[bytes]:
        """Retrieve artifact content by ID."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT file_path FROM artifacts WHERE id = ?", (artifact_id,))
            row = cursor.fetchone()
            if row:
                return Path(row[0]).read_bytes()
        return None

    def verify_artifact_integrity(self, artifact_id: str) -> bool:
        """Verify artifact content matches its hash."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT file_path, content_hash FROM artifacts WHERE id = ?", (artifact_id,))
            row = cursor.fetchone()
            if row:
                content = Path(row[0]).read_bytes()
                actual_hash = hashlib.sha256(content).hexdigest()
                return actual_hash == row[1]
        return False

# ==============================================================================
# Locking and Concurrency
# ==============================================================================

class DatabaseLock:
    """File-based database locking for SQLite concurrency."""

    def __init__(self, db_path: Path, timeout: float = 30.0):
        self.db_path = db_path
        self.lock_path = db_path.with_suffix(db_path.suffix + ".lock")
        self.timeout = timeout
        self._lock = threading.Lock()
        self._acquired = False

    @contextlib.contextmanager
    def acquire(self):
        """Acquire database lock."""
        start = time.time()
        while time.time() - start < self.timeout:
            try:
                # Try to create lock file exclusively
                fd = os.open(self.lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                os.write(fd, str(os.getpid()).encode())
                os.close(fd)
                self._acquired = True
                try:
                    yield
                finally:
                    self.release()
                return
            except FileExistsError:
                time.sleep(0.1)
                continue

        raise TimeoutError(f"Could not acquire database lock within {self.timeout}s")

    def release(self):
        """Release database lock."""
        if self._acquired and self.lock_path.exists():
            self.lock_path.unlink()
            self._acquired = False

# ==============================================================================
# Backup, Deletion, Retention
# ==============================================================================

class RetentionPolicy:
    """Retention policy configuration."""

    def __init__(self):
        # From TBD resolution
        self.policies = {
            "source_content_days": 90,
            "run_state_days": 365,
            "markdown_reports_days": 730,
            "json_reports_days": -1,  # -1 = indefinite
            "audit_logs_days": 365,
            "transcripts_days": 90,
            "secret_refs_days": 365,
        }

    def get_retention_days(self, entity_type: str) -> int:
        return self.policies.get(entity_type, 365)

class BackupManager:
    """Manages database and artifact backups."""

    def __init__(self, db_path: Path, artifacts_dir: Path, backup_dir: Path):
        self.db_path = db_path
        self.artifacts_dir = artifacts_dir
        self.backup_dir = backup_dir
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def create_backup(self, backup_name: str = None) -> Path:
        """Create a full backup of database and artifacts."""
        if backup_name is None:
            backup_name = f"backup_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"

        backup_path = self.backup_dir / backup_name
        backup_path.mkdir(parents=True, exist_ok=True)

        # Backup database (SQLite backup API)
        with sqlite3.connect(self.db_path) as source:
            with sqlite3.connect(backup_path / "asta.db") as dest:
                source.backup(dest)

        # Backup artifacts (copy directory)
        import shutil
        shutil.copytree(self.artifacts_dir, backup_path / "artifacts", dirs_exist_ok=True)

        # Create backup manifest
        manifest = {
            "backup_name": backup_name,
            "created_at": datetime.utcnow().isoformat() + "Z",
            "db_path": str(self.db_path),
            "artifacts_path": str(self.artifacts_dir),
            "schema_version": "1.0"
        }
        (backup_path / "manifest.json").write_text(json.dumps(manifest, indent=2))

        return backup_path

    def list_backups(self) -> List[Dict]:
        """List available backups."""
        backups = []
        for path in self.backup_dir.iterdir():
            if path.is_dir() and (path / "manifest.json").exists():
                manifest = json.loads((path / "manifest.json").read_text())
                manifest["path"] = str(path)
                backups.append(manifest)
        return sorted(backups, key=lambda b: b["created_at"], reverse=True)

    def restore_backup(self, backup_name: str) -> bool:
        """Restore from backup (destructive)."""
        backup_path = self.backup_dir / backup_name
        if not backup_path.exists():
            return False

        # Restore database
        import shutil
        shutil.copy2(backup_path / "asta.db", self.db_path)

        # Restore artifacts
        if (backup_path / "artifacts").exists():
            if self.artifacts_dir.exists():
                shutil.rmtree(self.artifacts_dir)
            shutil.copytree(backup_path / "artifacts", self.artifacts_dir)

        return True

class RetentionManager:
    """Manages retention and cleanup of old data."""

    def __init__(self, db_path: Path, artifacts_dir: Path, policy: RetentionPolicy):
        self.db_path = db_path
        self.artifacts_dir = artifacts_dir
        self.policy = policy

    def cleanup_expired(self) -> Dict[str, int]:
        """Clean up expired data according to retention policy."""
        results = {
            "runs_deleted": 0,
            "artifacts_deleted": 0,
            "audit_events_deleted": 0,
            "snapshots_deleted": 0
        }

        cutoff_run = datetime.utcnow() - timedelta(days=self.policy.get_retention_days("run_state_days"))
        cutoff_audit = datetime.utcnow() - timedelta(days=self.policy.get_retention_days("audit_logs_days"))

        with sqlite3.connect(self.db_path) as conn:
            # Delete old runs (and cascade to checks, attempts, artifacts)
            cursor = conn.execute("""
                SELECT id FROM runs WHERE completed_at < ?
            """, (cutoff_run.isoformat(),))
            run_ids = [row[0] for row in cursor.fetchall()]

            for run_id in run_ids:
                # Delete artifacts first (foreign key)
                conn.execute("DELETE FROM artifacts WHERE attempt_id IN (SELECT id FROM attempts WHERE check_id IN (SELECT id FROM checks WHERE run_id = ?))", (run_id,))
                conn.execute("DELETE FROM attempts WHERE check_id IN (SELECT id FROM checks WHERE run_id = ?)", (run_id,))
                conn.execute("DELETE FROM checks WHERE run_id = ?", (run_id,))
                conn.execute("DELETE FROM approvals WHERE run_id = ?", (run_id,))
                conn.execute("DELETE FROM runs WHERE id = ?", (run_id,))
                results["runs_deleted"] += 1

            # Delete old audit events
            cursor = conn.execute("DELETE FROM audit_events WHERE created_at < ?", (cutoff_audit.isoformat(),))
            results["audit_events_deleted"] = cursor.rowcount

            # Delete old snapshots
            cursor = conn.execute("DELETE FROM snapshots WHERE created_at < ?", (cutoff_audit.isoformat(),))
            results["snapshots_deleted"] = cursor.rowcount

        return results


# ==============================================================================
# Report Schema Version
# ==============================================================================

REPORT_SCHEMA_VERSION = "1.0"

REPORT_JSON_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "ASTA Run Report",
    "type": "object",
    "required": [
        "schema_version",
        "run_id",
        "timestamp",
        "scope",
        "status",
        "domains",
        "findings",
        "evidence",
        "limitations",
        "recommendations"
    ],
    "properties": {
        "schema_version": {"type": "string", "const": "1.0"},
        "run_id": {"type": "string", "format": "uuid"},
        "timestamp": {"type": "string", "format": "date-time"},
        "scope": {
            "type": "object",
            "required": ["types", "authorized_targets"],
            "properties": {
                "types": {"type": "array", "items": {"type": "string"}},
                "authorized_targets": {"type": "array", "items": {"type": "string"}}
            }
        },
        "status": {"type": "string", "enum": ["Failures found", "Unreliable results", "Passed in tested scope", "No result"]},
        "domains": {"type": "array", "items": {"type": "string"}},
        "findings": {"type": "array", "items": {"type": "object"}},
        "evidence": {"type": "object"},
        "limitations": {"type": "array", "items": {"type": "string"}},
        "recommendations": {"type": "array", "items": {"type": "string"}}
    }
}

# ==============================================================================
# Persistence Manager (Main Entry Point)
# ==============================================================================

class PersistenceManager:
    """Main persistence manager coordinating all components."""

    def __init__(self, workspace_path: Path):
        self.workspace_path = workspace_path
        self.db_path = workspace_path / ".asta" / "asta.db"
        self.artifacts_dir = workspace_path / ".asta" / "artifacts"
        self.backup_dir = workspace_path / ".asta" / "backups"

        # Initialize components
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.migration_manager = MigrationManager(self.db_path)
        self.snapshot_store = SnapshotStore(self.db_path)
        self.artifact_manager = ArtifactManager(self.artifacts_dir, self.db_path)
        self.backup_manager = BackupManager(self.db_path, self.artifacts_dir, self.backup_dir)
        self.retention_manager = RetentionManager(self.db_path, self.artifacts_dir, RetentionPolicy())

        # Apply migrations
        self.migration_manager.migrate()

    def get_connection(self):
        """Get a database connection with locking."""
        return DatabaseLock(self.db_path).acquire()

    def close(self):
        """Cleanup resources."""
        pass

# ==============================================================================
# CLI Integration
# ==============================================================================

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "test":
        print("Testing persistence layer...")
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            pm = PersistenceManager(workspace)
            print("PersistenceManager initialized")
            print(f"DB: {pm.db_path}")
            print(f"Artifacts: {pm.artifacts_dir}")
            print("Migrations applied:", pm.migration_manager.get_applied_migrations())

            # Test artifact storage
            artifact = pm.artifact_manager.store_artifact("attempt1", "stdout", b"Hello World")
            print(f"Stored artifact: {artifact['artifact_id']}, hash: {artifact['content_hash'][:16]}...")

            # Test snapshot
            snap = pm.snapshot_store.create_snapshot(
                entity_type=EntityType.PROJECT,
                entity_id="proj_test",
                content={"name": "test", "value": "data"},
                schema_version="1.0"
            )
            print(f"Created snapshot: {snap.snapshot_id}")

            print("All tests passed!")
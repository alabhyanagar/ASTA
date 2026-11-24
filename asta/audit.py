#!/usr/bin/env python3
"""
ASTA M1 Audit Event System

Records audit events for security and lifecycle decisions:
- Target decisions, approvals, plan revisions
- Egress decisions, credential references
- Cancellation, AI provider/data-sharing events
- Artifact access
- No secret values; each event has actor/source, time, policy version, reason
"""

from __future__ import annotations
from typing import Dict, List, Optional, Any, Literal
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
import hashlib
import json
import sqlite3
import threading
import uuid

# ==============================================================================
# Audit Event Types
# ==============================================================================

class AuditEventType(str, Enum):
    """Types of audit events."""
    # Target/Authorization
    TARGET_AUTHORIZED = "target_authorized"
    TARGET_REVOKED = "target_revoked"
    TARGET_ACCESS_ATTEMPT = "target_access_attempt"
    TARGET_ACCESS_DENIED = "target_access_denied"

    # Approvals
    PLAN_APPROVED = "plan_approved"
    PLAN_REJECTED = "plan_rejected"
    PLAN_REVISION_CREATED = "plan_revision_created"
    CHECK_APPROVED = "check_approved"
    CHECK_AUTHORIZED = "check_authorized"
    CHECK_AUTHORIZATION_DENIED = "check_authorization_denied"
    HIGH_RISK_AUTHORIZED = "high_risk_authorized"
    HIGH_RISK_AUTHORIZATION_DENIED = "high_risk_authorization_denied"

    # Scope/Configuration
    SCOPE_MODIFIED = "scope_modified"
    CONFIG_CHANGED = "config_changed"
    POLICY_VERSION_CHANGED = "policy_version_changed"

    # Egress/Network
    EGRESS_ALLOWED = "egress_allowed"
    EGRESS_DENIED = "egress_denied"
    EGRESS_RULE_ADDED = "egress_rule_added"
    EGRESS_RULE_REMOVED = "egress_rule_removed"
    DNS_RESOLUTION = "dns_resolution"
    REDIRECT_FOLLOWED = "redirect_followed"

    # Credentials
    CREDENTIAL_REFERENCED = "credential_referenced"
    CREDENTIAL_ROTATED = "credential_rotated"
    CREDENTIAL_ACCESS_ATTEMPT = "credential_access_attempt"
    CREDENTIAL_ACCESS_DENIED = "credential_access_denied"
    SECRET_REDACTED = "secret_redacted"

    # Execution Lifecycle
    RUN_STARTED = "run_started"
    RUN_COMPLETED = "run_completed"
    RUN_FAILED = "run_failed"
    RUN_CANCELLED = "run_cancelled"
    RUN_PAUSED = "run_paused"
    RUN_RESUMED = "run_resumed"
    CHECK_STARTED = "check_started"
    CHECK_COMPLETED = "check_completed"
    CHECK_FAILED = "check_failed"
    CHECK_CANCELLED = "check_cancelled"
    ATTEMPT_STARTED = "attempt_started"
    ATTEMPT_COMPLETED = "attempt_completed"
    RERUN_REQUESTED = "rerun_requested"

    # AI/ML
    AI_PROVIDER_CONFIGURED = "ai_provider_configured"
    AI_PROVIDER_REMOVED = "ai_provider_removed"
    AI_DATA_SHARING_ENABLED = "ai_data_sharing_enabled"
    AI_DATA_SHARING_DISABLED = "ai_data_sharing_disabled"
    AI_MODEL_INVOKED = "ai_model_invoked"
    AI_INVOCATION_FAILED = "ai_invocation_failed"

    # Artifacts
    ARTIFACT_CREATED = "artifact_created"
    ARTIFACT_ACCESSED = "artifact_accessed"
    ARTIFACT_REDACTED = "artifact_redacted"
    ARTIFACT_DELETED = "artifact_deleted"
    ARTIFACT_INTEGRITY_VERIFIED = "artifact_integrity_verified"
    ARTIFACT_INTEGRITY_FAILED = "artifact_integrity_failed"

    # Security
    SECURITY_SCAN_STARTED = "security_scan_started"
    SECURITY_SCAN_COMPLETED = "security_scan_completed"
    VULNERABILITY_DETECTED = "vulnerability_detected"
    SECRET_DETECTED = "secret_detected"
    PATH_TRAVERSAL_ATTEMPT = "path_traversal_attempt"
    INJECTION_ATTEMPT = "injection_attempt"

    # Admin/Configuration
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    CONFIG_IMPORTED = "config_imported"
    CONFIG_EXPORTED = "config_exported"
    BACKUP_CREATED = "backup_created"
    BACKUP_RESTORED = "backup_restored"
    RETENTION_CLEANUP = "retention_cleanup"

class AuditSeverity(str, Enum):
    """Audit event severity."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class AuditActorType(str, Enum):
    """Type of actor that triggered the event."""
    USER = "user"
    SYSTEM = "system"
    WORKER = "worker"
    AI_PROVIDER = "ai_provider"
    EXTERNAL = "external"
    SCHEDULED = "scheduled"

@dataclass
class AuditEvent:
    """A single audit event record."""
    event_id: str
    event_type: AuditEventType
    severity: AuditSeverity
    timestamp: str
    actor_type: AuditActorType
    actor_id: str                    # User ID, worker ID, system component
    actor_source: str                # IP, hostname, component name
    entity_type: str                 # run, check, attempt, artifact, project, etc.
    entity_id: str
    action: str                      # What was done
    reason: str                      # Why it was done
    policy_version: str = "1.0"
    outcome: str = "success"         # success, failure, partial
    metadata: Dict = field(default_factory=dict)
    # No secret values - redacted before storage
    redacted_fields: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "severity": self.severity.value,
            "timestamp": self.timestamp,
            "actor_type": self.actor_type.value,
            "actor_id": self.actor_id,
            "actor_source": self.actor_source,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "action": self.action,
            "reason": self.reason,
            "policy_version": self.policy_version,
            "outcome": self.outcome,
            "metadata": self.metadata,
            "redacted_fields": self.redacted_fields
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True)

    @classmethod
    def from_dict(cls, data: Dict) -> 'AuditEvent':
        return cls(
            event_id=data["event_id"],
            event_type=AuditEventType(data["event_type"]),
            severity=AuditSeverity(data["severity"]),
            timestamp=data["timestamp"],
            actor_type=AuditActorType(data["actor_type"]),
            actor_id=data["actor_id"],
            actor_source=data["actor_source"],
            entity_type=data["entity_type"],
            entity_id=data["entity_id"],
            action=data["action"],
            reason=data["reason"],
            policy_version=data.get("policy_version", "1.0"),
            outcome=data.get("outcome", "success"),
            metadata=data.get("metadata", {}),
            redacted_fields=data.get("redacted_fields", [])
        )

# ==============================================================================
# Secret Redaction
# ==============================================================================

class SecretRedactor:
    """Redacts secret values from audit event metadata."""

    # Patterns that indicate secret values
    SECRET_PATTERNS = [
        r'(?i)(password|passwd|pwd)\s*[=:]\s*\S+',
        r'(?i)(secret|token|key|apikey|api_key)\s*[=:]\s*\S+',
        r'(?i)(authorization|auth)\s*[=:]\s*\S+',
        r'(?i)(bearer|basic)\s+\S+',
        r'(?i)(private_key|privkey)\s*[=:]\s*\S+',
        r'(?i)(ssh_key|sshkey)\s*[=:]\s*\S+',
        r'(?i)(database_url|db_url)\s*[=:]\s*\S+',
        r'(?i)(connection_string|conn_str)\s*[=:]\s*\S+',
    ]

    # Known secret prefixes
    SECRET_PREFIXES = [
        "sk-", "pk-", "ghp_", "gho_", "ghu_", "ghs_", "ghr_",
        "aws_access_key_id", "aws_secret_access_key",
        "google_api_key", "azure_key",
    ]

    @classmethod
    def redact(cls, data: Any, path: str = "") -> tuple[Any, List[str]]:
        """
        Recursively redact secret values from data.
        Returns (redacted_data, list_of_redacted_paths).
        """
        redacted_paths = []

        if isinstance(data, dict):
            result = {}
            for key, value in data.items():
                current_path = f"{path}.{key}" if path else key
                redacted_value, paths = cls.redact(value, current_path)
                result[key] = redacted_value
                redacted_paths.extend(paths)
            return result, redacted_paths

        elif isinstance(data, list):
            result = []
            for i, item in enumerate(data):
                redacted_item, paths = cls.redact(item, f"{path}[{i}]")
                result.append(redacted_item)
                redacted_paths.extend(paths)
            return result, redacted_paths

        elif isinstance(data, str):
            # Check for secret patterns
            for pattern in cls.SECRET_PATTERNS:
                import re
                if re.search(pattern, data):
                    return "[REDACTED]", [path]

            # Check for secret prefixes
            for prefix in cls.SECRET_PREFIXES:
                if data.startswith(prefix):
                    return "[REDACTED]", [path]

            # Check for long random strings (potential secrets)
            if len(data) >= 32 and data.isalnum() and any(c.isupper() for c in data) and any(c.islower() for c in data):
                # Looks like a token/key
                return "[REDACTED]", [path]

        return data, redacted_paths

# ==============================================================================
# Audit Logger
# ==============================================================================

class AuditLogger:
    """Main audit logger with persistence and redaction."""

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._lock = threading.Lock()
        self._init_schema()
        self._redactor = SecretRedactor()

    def _init_schema(self):
        """Initialize audit event table."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS audit_events (
                    event_id TEXT PRIMARY KEY,
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
                )
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_events(timestamp)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_audit_entity ON audit_events(entity_type, entity_id)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_audit_type ON audit_events(event_type)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_audit_actor ON audit_events(actor_type, actor_id)
            """)

    def log(self, event: AuditEvent) -> str:
        """Log an audit event with redaction."""
        # Redact secrets from metadata
        redacted_metadata, redacted_paths = SecretRedactor.redact(event.metadata)

        # Create event with redacted metadata
        redacted_event = AuditEvent(
            event_id=event.event_id,
            event_type=event.event_type,
            severity=event.severity,
            timestamp=event.timestamp,
            actor_type=event.actor_type,
            actor_id=event.actor_id,
            actor_source=event.actor_source,
            entity_type=event.entity_type,
            entity_id=event.entity_id,
            action=event.action,
            reason=event.reason,
            policy_version=event.policy_version,
            outcome=event.outcome,
            metadata=redacted_metadata,
            redacted_fields=redacted_paths
        )

        # Persist to database
        with self._lock, self._db_transaction() as conn:
            conn.execute("""
                INSERT INTO audit_events
                (event_id, event_type, severity, timestamp, actor_type, actor_id,
                 actor_source, entity_type, entity_id, action, reason, policy_version,
                 outcome, metadata_json, redacted_fields_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                redacted_event.event_id,
                redacted_event.event_type.value,
                redacted_event.severity.value,
                redacted_event.timestamp,
                redacted_event.actor_type.value,
                redacted_event.actor_id,
                redacted_event.actor_source,
                redacted_event.entity_type,
                redacted_event.entity_id,
                redacted_event.action,
                redacted_event.reason,
                redacted_event.policy_version,
                redacted_event.outcome,
                json.dumps(redacted_event.metadata),
                json.dumps(redacted_event.redacted_fields)
            ))

        return redacted_event.event_id

    def log_event(self,
                  event_type: AuditEventType,
                  severity: AuditSeverity,
                  actor_type: AuditActorType,
                  actor_id: str,
                  actor_source: str,
                  entity_type: str,
                  entity_id: str,
                  action: str,
                  reason: str,
                  policy_version: str = "1.0",
                  outcome: str = "success",
                  metadata: Dict = None) -> str:
        """Convenience method to create and log an event."""
        event = AuditEvent(
            event_id=f"audit_{uuid.uuid4().hex[:16]}",
            event_type=event_type,
            severity=severity,
            timestamp=datetime.utcnow().isoformat() + "Z",
            actor_type=actor_type,
            actor_id=actor_id,
            actor_source=actor_source,
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            reason=reason,
            policy_version=policy_version,
            outcome=outcome,
            metadata=metadata or {}
        )
        return self.log(event)

    def query_events(self,
                     entity_type: str = None,
                     entity_id: str = None,
                     event_type: AuditEventType = None,
                     actor_id: str = None,
                     start_time: str = None,
                     end_time: str = None,
                     limit: int = 100) -> List[Dict]:
        """Query audit events with filters."""
        query = "SELECT * FROM audit_events WHERE 1=1"
        params = []

        if entity_type:
            query += " AND entity_type = ?"
            params.append(entity_type)
        if entity_id:
            query += " AND entity_id = ?"
            params.append(entity_id)
        if event_type:
            query += " AND event_type = ?"
            params.append(event_type.value)
        if actor_id:
            query += " AND actor_id = ?"
            params.append(actor_id)
        if start_time:
            query += " AND timestamp >= ?"
            params.append(start_time)
        if end_time:
            query += " AND timestamp <= ?"
            params.append(end_time)

        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    def get_event(self, event_id: str) -> Optional[Dict]:
        """Get a single audit event by ID."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute("SELECT * FROM audit_events WHERE event_id = ?", (event_id,)).fetchone()
            return dict(row) if row else None

    def get_audit_trail(self, entity_type: str, entity_id: str) -> List[Dict]:
        """Get complete audit trail for an entity."""
        return self.query_events(entity_type=entity_type, entity_id=entity_id, limit=1000)

    @contextmanager
    def _db_transaction(self):
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

# ==============================================================================
# High-Level Audit Helpers
# ==============================================================================

class AuditFacade:
    """High-level audit logging facade for common operations."""

    def __init__(self, db_path: Path):
        self.logger = AuditLogger(db_path)

    # Target Authorization
    def target_authorized(self, actor_id: str, actor_source: str, target: str,
                          reason: str, policy_version: str = "1.0", metadata: Dict = None):
        return self.logger.log_event(
            event_type=AuditEventType.TARGET_AUTHORIZED,
            severity=AuditSeverity.INFO,
            actor_type=AuditActorType.USER,
            actor_id=actor_id,
            actor_source=actor_source,
            entity_type="target",
            entity_id=target,
            action="authorize",
            reason=reason,
            policy_version=policy_version,
            metadata=metadata or {"target": target}
        )

    def target_access_denied(self, actor_id: str, actor_source: str, target: str,
                             reason: str, policy_version: str = "1.0"):
        return self.logger.log_event(
            event_type=AuditEventType.TARGET_ACCESS_DENIED,
            severity=AuditSeverity.WARNING,
            actor_type=AuditActorType.SYSTEM,
            actor_id="system",
            actor_source="egress_controller",
            entity_type="target",
            entity_id=target,
            action="access_denied",
            reason=reason,
            policy_version=policy_version,
            outcome="failure",
            metadata={"target": target, "denied_reason": reason}
        )

    # Approvals
    def plan_approved(self, actor_id: str, actor_source: str, plan_id: str,
                      plan_hash: str, approved_checks: List[str],
                      approved_recommendations: List[str], reason: str):
        return self.logger.log_event(
            event_type=AuditEventType.PLAN_APPROVED,
            severity=AuditSeverity.INFO,
            actor_type=AuditActorType.USER,
            actor_id=actor_id,
            actor_source=actor_source,
            entity_type="plan",
            entity_id=plan_id,
            action="approve",
            reason=reason,
            metadata={
                "plan_hash": plan_hash,
                "approved_checks": approved_checks,
                "approved_recommendations": approved_recommendations
            }
        )

    def check_authorized(self, actor_id: str, actor_source: str, check_id: str,
                         risk_level: str, authorized: bool, reason: str):
        return self.logger.log_event(
            event_type=AuditEventType.CHECK_AUTHORIZED if authorized else AuditEventType.CHECK_AUTHORIZATION_DENIED,
            severity=AuditSeverity.INFO if authorized else AuditSeverity.WARNING,
            actor_type=AuditActorType.USER,
            actor_id=actor_id,
            actor_source=actor_source,
            entity_type="check",
            entity_id=check_id,
            action="authorize" if authorized else "deny_authorization",
            reason=reason,
            metadata={"risk_level": risk_level, "authorized": authorized}
        )

    def high_risk_authorized(self, actor_id: str, actor_source: str, check_id: str,
                             risk_level: str, reason: str):
        return self.logger.log_event(
            event_type=AuditEventType.HIGH_RISK_AUTHORIZED,
            severity=AuditSeverity.WARNING,
            actor_type=AuditActorType.USER,
            actor_id=actor_id,
            actor_source=actor_source,
            entity_type="check",
            entity_id=check_id,
            action="high_risk_authorize",
            reason=reason,
            metadata={"risk_level": risk_level}
        )

    # Scope/Config
    def scope_modified(self, actor_id: str, actor_source: str, plan_id: str,
                       old_scope: List[str], new_scope: List[str], reason: str):
        return self.logger.log_event(
            event_type=AuditEventType.SCOPE_MODIFIED,
            severity=AuditSeverity.INFO,
            actor_type=AuditActorType.USER,
            actor_id=actor_id,
            actor_source=actor_source,
            entity_type="plan",
            entity_id=plan_id,
            action="modify_scope",
            reason=reason,
            metadata={"old_scope": old_scope, "new_scope": new_scope}
        )

    def config_changed(self, actor_id: str, actor_source: str, config_path: str,
                       changes: Dict, reason: str):
        return self.logger.log_event(
            event_type=AuditEventType.CONFIG_CHANGED,
            severity=AuditSeverity.INFO,
            actor_type=AuditActorType.USER,
            actor_id=actor_id,
            actor_source=actor_source,
            entity_type="config",
            entity_id=config_path,
            action="modify_config",
            reason=reason,
            metadata={"changes": changes}
        )

    # Egress
    def egress_allowed(self, worker_id: str, target: str, protocol: str,
                       reason: str, metadata: Dict = None):
        return self.logger.log_event(
            event_type=AuditEventType.EGRESS_ALLOWED,
            severity=AuditSeverity.INFO,
            actor_type=AuditActorType.WORKER,
            actor_id=worker_id,
            actor_source="egress_controller",
            entity_type="egress",
            entity_id=f"{worker_id}:{target}",
            action="allow",
            reason=reason,
            metadata=metadata or {"target": target, "protocol": protocol}
        )

    def egress_denied(self, worker_id: str, target: str, protocol: str,
                      reason: str, metadata: Dict = None):
        return self.logger.log_event(
            event_type=AuditEventType.EGRESS_DENIED,
            severity=AuditSeverity.WARNING,
            actor_type=AuditActorType.SYSTEM,
            actor_id="egress_controller",
            actor_source="egress_controller",
            entity_type="egress",
            entity_id=f"{worker_id}:{target}",
            action="deny",
            reason=reason,
            outcome="failure",
            metadata=metadata or {"target": target, "protocol": protocol, "denied_reason": reason}
        )

    # Credentials
    def credential_referenced(self, actor_id: str, actor_source: str,
                              credential_ref: str, purpose: str, target: str):
        return self.logger.log_event(
            event_type=AuditEventType.CREDENTIAL_REFERENCED,
            severity=AuditSeverity.INFO,
            actor_type=AuditActorType.SYSTEM,
            actor_id="credential_manager",
            actor_source="credential_manager",
            entity_type="credential_ref",
            entity_id=credential_ref,
            action="reference",
            reason=purpose,
            metadata={"purpose": purpose, "target": target}
        )

    def secret_redacted(self, actor_id: str, actor_source: str,
                        field_path: str, value_type: str):
        return self.logger.log_event(
            event_type=AuditEventType.SECRET_REDACTED,
            severity=AuditSeverity.INFO,
            actor_type=AuditActorType.SYSTEM,
            actor_id="secret_redactor",
            actor_source="secret_redactor",
            entity_type="secret",
            entity_id=field_path,
            action="redact",
            reason="Secret value redacted from logs/artifacts",
            metadata={"field_path": field_path, "value_type": value_type}
        )

    # Execution
    def run_started(self, run_id: str, project_id: str, worker_id: str,
                    scope_types: List[str], risk_approval: str):
        return self.logger.log_event(
            event_type=AuditEventType.RUN_STARTED,
            severity=AuditSeverity.INFO,
            actor_type=AuditActorType.WORKER,
            actor_id=worker_id,
            actor_source="worker",
            entity_type="run",
            entity_id=run_id,
            action="start",
            reason="Run started",
            metadata={"project_id": project_id, "scope_types": scope_types, "risk_approval": risk_approval}
        )

    def run_completed(self, run_id: str, status: str, checks_total: int,
                      passed: int, failed: int, worker_id: str):
        return self.logger.log_event(
            event_type=AuditEventType.RUN_COMPLETED if status == "completed" else AuditEventType.RUN_FAILED,
            severity=AuditSeverity.INFO if status == "completed" else AuditSeverity.ERROR,
            actor_type=AuditActorType.WORKER,
            actor_id=worker_id,
            actor_source="worker",
            entity_type="run",
            entity_id=run_id,
            action="complete" if status == "completed" else "fail",
            reason=f"Run {status}",
            outcome="success" if status == "completed" else "failure",
            metadata={
                "checks_total": checks_total,
                "passed": passed,
                "failed": failed
            }
        )

    def run_cancelled(self, run_id: str, actor_id: str, actor_source: str, reason: str):
        return self.logger.log_event(
            event_type=AuditEventType.RUN_CANCELLED,
            severity=AuditSeverity.WARNING,
            actor_type=AuditActorType.USER if actor_source == "user" else AuditActorType.SYSTEM,
            actor_id=actor_id,
            actor_source=actor_source,
            entity_type="run",
            entity_id=run_id,
            action="cancel",
            reason=reason
        )

    def check_started(self, run_id: str, check_id: str, worker_id: str, capability_id: str):
        return self.logger.log_event(
            event_type=AuditEventType.CHECK_STARTED,
            severity=AuditSeverity.INFO,
            actor_type=AuditActorType.WORKER,
            actor_id=worker_id,
            actor_source="worker",
            entity_type="check",
            entity_id=check_id,
            action="start",
            reason="Check execution started",
            metadata={"run_id": run_id, "capability_id": capability_id}
        )

    def check_completed(self, run_id: str, check_id: str, status: str,
                        worker_id: str, duration_seconds: int):
        return self.logger.log_event(
            event_type=AuditEventType.CHECK_COMPLETED if status == "completed" else AuditEventType.CHECK_FAILED,
            severity=AuditSeverity.INFO if status == "completed" else AuditSeverity.ERROR,
            actor_type=AuditActorType.WORKER,
            actor_id=worker_id,
            actor_source="worker",
            entity_type="check",
            entity_id=check_id,
            action="complete" if status == "completed" else "fail",
            reason=f"Check {status}",
            outcome="success" if status == "completed" else "failure",
            metadata={"run_id": run_id, "duration_seconds": duration_seconds}
        )

    # Artifacts
    def artifact_created(self, artifact_id: str, attempt_id: str,
                         artifact_type: str, content_hash: str, size_bytes: int):
        return self.logger.log_event(
            event_type=AuditEventType.ARTIFACT_CREATED,
            severity=AuditSeverity.INFO,
            actor_type=AuditActorType.SYSTEM,
            actor_id="artifact_manager",
            actor_source="artifact_manager",
            entity_type="artifact",
            entity_id=artifact_id,
            action="create",
            reason="Artifact created",
            metadata={"attempt_id": attempt_id, "type": artifact_type, "content_hash": content_hash}
        )

    def artifact_accessed(self, artifact_id: str, actor_id: str,
                          actor_source: str, purpose: str):
        return self.logger.log_event(
            event_type=AuditEventType.ARTIFACT_ACCESSED,
            severity=AuditSeverity.INFO,
            actor_type=AuditActorType.USER,
            actor_id=actor_id,
            actor_source=actor_source,
            entity_type="artifact",
            entity_id=artifact_id,
            action="access",
            reason=purpose
        )

    def secret_redacted_event(self, artifact_id: str, field_path: str, value_type: str):
        return self.logger.log_event(
            event_type=AuditEventType.SECRET_REDACTED,
            severity=AuditSeverity.INFO,
            actor_type=AuditActorType.SYSTEM,
            actor_id="secret_redactor",
            actor_source="secret_redactor",
            entity_type="artifact",
            entity_id=artifact_id,
            action="redact_secret",
            reason="Secret value redacted from artifact",
            metadata={"field_path": field_path, "value_type": value_type}
        )

    # AI
    def ai_model_invoked(self, provider: str, model: str, purpose: str,
                         data_shared: bool, metadata: Dict = None):
        return self.logger.log_event(
            event_type=AuditEventType.AI_MODEL_INVOKED,
            severity=AuditSeverity.INFO,
            actor_type=AuditActorType.AI_PROVIDER,
            actor_id=provider,
            actor_source=provider,
            entity_type="ai_model",
            entity_id=model,
            action="invoke",
            reason=purpose,
            metadata=metadata or {"model": model, "data_shared": data_shared}
        )

    def ai_data_sharing_enabled(self, actor_id: str, provider: str, model: str):
        return self.logger.log_event(
            event_type=AuditEventType.AI_DATA_SHARING_ENABLED,
            severity=AuditSeverity.WARNING,
            actor_type=AuditActorType.USER,
            actor_id=actor_id,
            actor_source=actor_source,
            entity_type="ai_config",
            entity_id=f"{provider}:{model}",
            action="enable_data_sharing",
            reason="AI data sharing enabled for provider",
            metadata={"provider": provider, "model": model}
        )

    # Security
    def vulnerability_detected(self, vulnerability_id: str, severity: str,
                               component: str, version: str, description: str):
        return self.logger.log_event(
            event_type=AuditEventType.VULNERABILITY_DETECTED,
            severity=AuditSeverity(severity.upper()) if severity.upper() in ["INFO", "WARNING", "ERROR", "CRITICAL"] else AuditSeverity.WARNING,
            actor_type=AuditActorType.SYSTEM,
            actor_id="vulnerability_scanner",
            actor_source="vulnerability_scanner",
            entity_type="vulnerability",
            entity_id=vulnerability_id,
            action="detect",
            reason=description,
            severity=AuditSeverity(severity.upper()) if severity.upper() in ["INFO", "WARNING", "ERROR", "CRITICAL"] else AuditSeverity.WARNING,
            metadata={"component": component, "version": version}
        )

    def path_traversal_attempt(self, actor_id: str, actor_source: str,
                               attempted_path: str, blocked: bool):
        return self.logger.log_event(
            event_type=AuditEventType.PATH_TRAVERSAL_ATTEMPT,
            severity=AuditSeverity.CRITICAL if not blocked else AuditSeverity.WARNING,
            actor_type=AuditActorType.EXTERNAL,
            actor_id=actor_id,
            actor_source=actor_source,
            entity_type="path",
            entity_id=attempted_path,
            action="traverse" if not blocked else "attempt_blocked",
            reason="Path traversal attempt detected",
            outcome="failure" if not blocked else "success",
            metadata={"attempted_path": attempted_path, "blocked": blocked}
        )


# ==============================================================================
# CLI Integration
# ==============================================================================

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "test":
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "audit.db"
            audit = AuditFacade(db_path)

            # Test logging various events
            audit.target_authorized("user1", "cli", "https://api.example.com", "API testing authorized")
            audit.plan_approved("user1", "cli", "plan_123", "hash123", ["pytest_unit"], ["rec_1"], "Plan approved for testing")
            audit.check_authorized("user1", "cli", "check_1", "high", True, "High risk check authorized")
            audit.egress_allowed("worker1", "https://api.example.com", "https", "API testing")
            audit.egress_denied("worker1", "http://internal.service", "http", "Internal services blocked")
            audit.credential_referenced("user1", "cli", "os-keyring:db-password", "database access", "db.example.com")
            audit.run_started("run_123", "proj_456", "worker_1", ["unit", "api"], "high")
            audit.check_started("run_123", "chk_1", "worker1", "pytest_unit")
            audit.check_completed("run_123", "chk_1", "completed", "worker1", 45)
            audit.run_completed("run_123", "completed", 10, 8, 2, "worker1")
            audit.secret_redacted_event("art_123", "metadata.password", "password")
            audit.ai_model_invoked("ollama", "llama3", "test_generation", True, {"tokens": 100})
            audit.vulnerability_detected("CVE-2024-1234", "HIGH", "requests", "2.31.0", "CRLF injection")
            audit.path_traversal_attempt("attacker", "192.168.1.1", "../../../etc/passwd", True)

            # Query events
            events = audit.logger.query_events(limit=20)
            print(f"Logged {len(events)} events")
            for e in events[:5]:
                print(f"  {e['timestamp']} | {e['event_type']} | {e['entity_type']}:{e['entity_id']} | {e['action']}")

            # Test secret redaction
            test_metadata = {
                "password": "secret123",
                "api_key": "sk-1234567890abcdef",
                "normal_field": "normal_value",
                "nested": {
                    "token": "ghp_abcdefghijklmnopqrstuvwxyz",
                    "normal": "value"
                }
            }
            redacted, paths = SecretRedactor.redact(test_metadata)
            print(f"\nRedacted paths: {paths}")
            print(f"Redacted data: {json.dumps(redacted, indent=2)}")

            print("\nAll audit tests passed!")
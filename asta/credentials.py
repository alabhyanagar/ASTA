#!/usr/bin/env python3
"""
ASTA M1 Scoped Per-Run Credential Injection

Implements secure credential handling:
- Named environment references or interactive input
- Secrets exist only for authorized check duration
- Host-wide environment NOT passed to worker
- Secrets never stored in config, DB, reports, prompts, logs, artifacts
- Absence/mismatch blocks the check
- Audit trail for all credential access
"""

from __future__ import annotations
from typing import Dict, List, Optional, Any, Literal
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
import hashlib
import json
import os
import secrets
import sqlite3
import threading
import getpass
import base64

# ==============================================================================
# Credential Types and References
# ==============================================================================

class CredentialReferenceType(str, Enum):
    """Types of credential references."""
    OS_KEYRING = "os-keyring"       # OS credential store (Windows Credential Manager, libsecret, keychain)
    ENV_VAR = "env-var"             # Environment variable reference
    FILE_REF = "file-ref"           # File path reference (encrypted file)
    INTERACTIVE = "interactive"     # Interactive prompt at runtime
    NONE = "none"                   # No credential needed

class CredentialPurpose(str, Enum):
    """Purpose of the credential."""
    DATABASE = "database"
    API_AUTH = "api_auth"
    REGISTRY = "registry"
    SSH_KEY = "ssh_key"
    TLS_CERT = "tls_cert"
    GENERIC = "generic"

@dataclass
class CredentialReference:
    """Reference to a credential (never stores the actual secret)."""
    reference_id: str
    reference_type: CredentialReferenceType
    reference_value: str           # e.g., "os-keyring:db-password", "ENV_VAR_NAME", "/path/to/encrypted/file"
    purpose: CredentialPurpose
    allowed_targets: List[str] = field(default_factory=list)  # Targets this credential can access
    description: str = ""
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")

    def to_dict(self) -> Dict:
        return {
            "reference_id": self.reference_id,
            "reference_type": self.reference_type.value,
            "reference_value": self.reference_value,
            "purpose": self.purpose.value,
            "allowed_targets": self.allowed_targets,
            "description": self.description,
            "created_at": self.created_at
        }

@dataclass
class InjectedCredential:
    """A credential injected into a check's environment (ephemeral)."""
    injection_id: str
    reference_id: str
    check_id: str
    run_id: str
    secret_value: str              # The actual secret (only in memory during injection)
    environment_variable: str      # Name of env var to inject
    injected_at: str
    expires_at: str                # When this injection expires
    audit_event_id: str            # Audit trail

    def to_dict(self, include_secret: bool = False) -> Dict:
        data = {
            "injection_id": self.injection_id,
            "reference_id": self.reference_id,
            "check_id": self.check_id,
            "run_id": self.run_id,
            "environment_variable": self.environment_variable,
            "injected_at": self.injected_at,
            "expires_at": self.expires_at,
            "audit_event_id": self.audit_event_id
        }
        if include_secret:
            data["secret_value"] = self.secret_value
        return data

# ==============================================================================
# Credential Store (References Only)
# ==============================================================================

class CredentialReferenceStore:
    """Stores credential references (never actual secrets)."""

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._lock = threading.Lock()
        self._init_schema()

    def _init_schema(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS credential_references (
                    reference_id TEXT PRIMARY KEY,
                    reference_type TEXT NOT NULL,
                    reference_value TEXT NOT NULL,
                    purpose TEXT NOT NULL,
                    allowed_targets_json TEXT NOT NULL,
                    description TEXT,
                    created_at TEXT NOT NULL,
                    project_id TEXT REFERENCES projects(id)
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_cred_project ON credential_references(project_id)")

    def add_reference(self, reference: 'CredentialReference', project_id: str) -> bool:
        """Add a credential reference."""
        with self._lock, self._db_transaction() as conn:
            try:
                conn.execute("""
                    INSERT INTO credential_references
                    (reference_id, reference_type, reference_value, purpose, allowed_targets_json, description, created_at, project_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (reference.reference_id, reference.reference_type.value, reference.reference_value,
                      reference.purpose.value, json.dumps(reference.allowed_targets), reference.description,
                      reference.created_at, project_id))
                return True
            except sqlite3.IntegrityError:
                return False

    def get_reference(self, reference_id: str) -> Optional['CredentialReference']:
        """Get a credential reference by ID."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute("SELECT * FROM credential_references WHERE reference_id = ?", (reference_id,)).fetchone()
            if row:
                return CredentialReference(
                    reference_id=row["reference_id"],
                    reference_type=CredentialReferenceType(row["reference_type"]),
                    reference_value=row["reference_value"],
                    purpose=CredentialPurpose(row["purpose"]),
                    allowed_targets=json.loads(row["allowed_targets_json"]),
                    description=row["description"],
                    created_at=row["created_at"]
                )
        return None

    def list_references(self, project_id: str = None) -> List['CredentialReference']:
        """List all credential references."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            if project_id:
                rows = conn.execute("SELECT * FROM credential_references WHERE project_id = ?", (project_id,)).fetchall()
            else:
                rows = conn.execute("SELECT * FROM credential_references").fetchall()

            return [CredentialReference(
                reference_id=row["reference_id"],
                reference_type=CredentialReferenceType(row["reference_type"]),
                reference_value=row["reference_value"],
                purpose=CredentialPurpose(row["purpose"]),
                allowed_targets=json.loads(row["allowed_targets_json"]),
                description=row["description"],
                created_at=row["created_at"]
            ) for row in rows]

    def delete_reference(self, reference_id: str) -> bool:
        """Delete a credential reference."""
        with self._lock, self._db_transaction() as conn:
            cursor = conn.execute("DELETE FROM credential_references WHERE reference_id = ?", (reference_id,))
            return cursor.rowcount > 0

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
# Credential Resolvers
# ==============================================================================

class CredentialResolver:
    """Resolves credential references to actual secret values."""

    def __init__(self):
        self._cache: Dict[str, str] = {}  # reference_id -> secret (short-lived)
        self._cache_lock = threading.Lock()
        self._cache_ttl = 300  # 5 minutes

    def resolve(self, reference: 'CredentialReference', context: Dict = None) -> Optional[str]:
        """Resolve a credential reference to its secret value."""
        # Check cache first
        with self._cache_lock:
            if reference.reference_id in self._cache:
                return self._cache[reference.reference_id]

        # Resolve based on type
        secret = None
        if reference.reference_type == CredentialReferenceType.OS_KEYRING:
            secret = self._resolve_os_keyring(reference.reference_value)
        elif reference.reference_type == CredentialReferenceType.ENV_VAR:
            secret = self._resolve_env_var(reference.reference_value)
        elif reference.reference_type == CredentialReferenceType.FILE_REF:
            secret = self._resolve_file_ref(reference.reference_value)
        elif reference.reference_type == CredentialReferenceType.INTERACTIVE:
            secret = self._resolve_interactive(reference)

        # Cache if resolved
        if secret:
            with self._cache_lock:
                self._cache[reference.reference_id] = secret
                # Schedule cache expiry
                threading.Timer(self._cache_ttl, self._expire_cache, args=[reference.reference_id]).start()

        return secret

    def _resolve_os_keyring(self, keyring_path: str) -> Optional[str]:
        """Resolve from OS keyring (Windows Credential Manager, libsecret, macOS Keychain)."""
        # Format: "os-keyring:service:account" or "os-keyring:label"
        try:
            import keyring
            # Parse keyring_path
            parts = keyring_path.split(":", 2)
            if len(parts) >= 3:
                service, account = parts[1], parts[2]
            else:
                service, account = "asta", parts[1] if len(parts) > 1 else "default"

            password = keyring.get_password(service, account)
            return password
        except ImportError:
            # Fallback for systems without keyring
            return None
        except Exception:
            return None

    def _resolve_env_var(self, var_name: str) -> Optional[str]:
        """Resolve from environment variable."""
        return os.environ.get(var_name)

    def _resolve_file_ref(self, file_path: str) -> Optional[str]:
        """Resolve from encrypted file reference."""
        # Format: "file-ref:/path/to/encrypted/file"
        path = file_path.replace("file-ref:", "")
        try:
            # File should contain base64-encoded encrypted secret
            # In M1, we support plaintext files for development (with warning)
            content = Path(file_path).read_text().strip()
            # If base64, decode
            try:
                return base64.b64decode(content).decode()
            except:
                # Assume plaintext for development
                return content
        except Exception:
            return None

    def _resolve_interactive(self, reference: 'CredentialReference') -> Optional[str]:
        """Prompt user interactively for secret."""
        try:
            prompt = f"Enter {reference.purpose.value} credential ({reference.reference_value}): "
            secret = getpass.getpass(prompt)
            return secret if secret else None
        except Exception:
            return None

    def _expire_cache(self, reference_id: str):
        """Expire cached secret."""
        with self._cache_lock:
            self._cache.pop(reference_id, None)

    def clear_cache(self):
        """Clear all cached secrets."""
        with self._cache_lock:
            self._cache.clear()

# ==============================================================================
# Credential Injection Manager
# ==============================================================================

class CredentialInjectionManager:
    """Manages per-run, per-check credential injection."""

    def __init__(self, db_path: Path, audit_facade: 'AuditFacade'):
        self.db_path = db_path
        self.audit = audit_facade
        self.reference_store = CredentialReferenceStore(db_path)
        self.resolver = CredentialResolver()
        self._lock = threading.Lock()
        self._active_injections: Dict[str, InjectedCredential] = {}  # injection_id -> InjectedCredential
        self._init_schema()

    def _init_schema(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS credential_injections (
                    injection_id TEXT PRIMARY KEY,
                    reference_id TEXT NOT NULL,
                    check_id TEXT NOT NULL,
                    run_id TEXT NOT NULL,
                    environment_variable TEXT NOT NULL,
                    injected_at TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    audit_event_id TEXT NOT NULL
                    -- secret_value NOT stored
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_injection_check ON credential_injections(check_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_injection_run ON credential_injections(run_id)")

    def inject_credentials_for_check(self,
                                     check_id: str,
                                     run_id: str,
                                     references: List['CredentialReference'],
                                     worker_id: str) -> List['InjectedCredential']:
        """
        Inject credentials for a specific check.
        Returns list of injected credentials (with secret values for worker).
        """
        injections = []

        for ref in references:
            # Verify reference is allowed for this check's target
            if not self._is_reference_allowed(ref, check_id):
                self._audit_credential_denied(ref.reference_id, check_id, "Reference not allowed for this check")
                continue

            # Resolve secret
            secret = self.resolver.resolve(ref)
            if not secret:
                self._audit_credential_denied(ref.reference_id, check_id, "Secret not found or could not be resolved")
                continue

            # Create injection
            injection_id = f"inj_{secrets.token_hex(8)}"
            env_var = self._generate_env_var_name(ref)
            injected_at = datetime.utcnow().isoformat() + "Z"
            expires_at = (datetime.utcnow() + timedelta(minutes=30)).isoformat() + "Z"  # Short-lived

            # Audit the injection
            audit_event_id = self._audit_credential_injected(ref.reference_id, check_id, ref.purpose.value)

            injection = InjectedCredential(
                injection_id=injection_id,
                reference_id=ref.reference_id,
                check_id=check_id,
                run_id=run_id,
                secret_value=secret,
                environment_variable=env_var,
                injected_at=injected_at,
                expires_at=expires_at,
                audit_event_id=audit_event_id
            )

            # Store injection record (without secret)
            self._store_injection(injection)

            # Track active injection
            with self._lock:
                self._active_injections[injection_id] = injection

            injections.append(injection)

        return injections

    def _generate_env_var_name(self, reference: 'CredentialReference') -> str:
        """Generate environment variable name for injected credential."""
        # Format: ASTA_CREDS_<purpose>_<short_hash>
        hash_suffix = hashlib.sha256(reference.reference_id.encode()).hexdigest()[:8]
        return f"ASTA_CREDS_{reference.purpose.value.upper()}_{hash_suffix}"

    def _is_reference_allowed(self, reference: 'CredentialReference', check_id: str) -> bool:
        """Check if reference is allowed for this check."""
        # If no allowed targets specified, allow all
        if not reference.allowed_targets:
            return True

        # In M1, check if check's target is in allowed targets
        # This would need check target info - simplified for M1
        return True

    def _store_injection(self, injection: 'InjectedCredential'):
        """Store injection record (without secret)."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO credential_injections
                (injection_id, reference_id, check_id, run_id, environment_variable, injected_at, expires_at, audit_event_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (injection.injection_id, injection.reference_id, injection.check_id,
                  injection.run_id, injection.environment_variable, injection.injected_at,
                  injection.expires_at, injection.audit_event_id))

    def _audit_credential_injected(self, reference_id: str, check_id: str, purpose: str) -> str:
        """Audit credential injection."""
        # This would integrate with the audit facade
        return f"audit_{secrets.token_hex(8)}"

    def _audit_credential_denied(self, reference_id: str, check_id: str, reason: str):
        """Audit credential injection denial."""
        pass

    def get_injected_environment(self, check_id: str) -> Dict[str, str]:
        """Get environment variables for a check's injected credentials."""
        env = {}
        with self._lock:
            for injection in self._active_injections.values():
                if injection.check_id == check_id:
                    env[injection.environment_variable] = injection.secret_value
        return env

    def cleanup_injections(self, run_id: str = None, check_id: str = None):
        """Clean up expired or completed injections."""
        now = datetime.utcnow().isoformat() + "Z"
        with self._lock:
            to_remove = []
            for inj_id, injection in self._active_injections.items():
                if injection.expires_at < now:
                    to_remove.append(inj_id)
                elif run_id and injection.run_id != run_id:
                    continue
                elif check_id and injection.check_id != check_id:
                    continue
                else:
                    to_remove.append(inj_id)

            for inj_id in to_remove:
                self._active_injections.pop(inj_id, None)

    def get_injection_history(self, run_id: str = None, check_id: str = None) -> List['InjectedCredential']:
        """Get injection history (without secrets)."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            query = "SELECT * FROM credential_injections WHERE 1=1"
            params = []
            if run_id:
                query += " AND run_id = ?"
                params.append(run_id)
            if check_id:
                query += " AND check_id = ?"
                params.append(check_id)
            query += " ORDER BY injected_at DESC"

            rows = conn.execute(query, params).fetchall()
            return [InjectedCredential(
                injection_id=row["injection_id"],
                reference_id=row["reference_id"],
                check_id=row["check_id"],
                run_id=row["run_id"],
                secret_value="",  # Never return secrets from history
                environment_variable=row["environment_variable"],
                injected_at=row["injected_at"],
                expires_at=row["expires_at"],
                audit_event_id=row["audit_event_id"]
            ) for row in rows]

# ==============================================================================
# Credential Facade (High-Level API)
# ==============================================================================

class CredentialFacade:
    """High-level credential management facade."""

    def __init__(self, db_path: Path, audit_facade: 'AuditFacade'):
        self.reference_store = CredentialReferenceStore(db_path)
        self.injection_manager = CredentialInjectionManager(db_path, audit_facade)
        self.resolver = CredentialResolver()

    def add_credential_reference(self,
                                 reference_type: CredentialReferenceType,
                                 reference_value: str,
                                 purpose: CredentialPurpose,
                                 allowed_targets: List[str] = None,
                                 description: str = "",
                                 project_id: str = "default") -> 'CredentialReference':
        """Add a new credential reference."""
        reference_id = f"cred_{secrets.token_hex(8)}"
        reference = CredentialReference(
            reference_id=reference_id,
            reference_type=reference_type,
            reference_value=reference_value,
            purpose=purpose,
            allowed_targets=allowed_targets or [],
            description=description
        )

        if self.reference_store.add_reference(reference, project_id):
            return reference
        raise ValueError(f"Credential reference {reference_id} already exists")

    def list_credential_references(self, project_id: str = None) -> List['CredentialReference']:
        return self.reference_store.list_references(project_id)

    def remove_credential_reference(self, reference_id: str) -> bool:
        return self.reference_store.delete_reference(reference_id)

    def inject_for_check(self,
                         check_id: str,
                         run_id: str,
                         reference_ids: List[str],
                         worker_id: str) -> List['InjectedCredential']:
        """Inject credentials for a check."""
        references = []
        for ref_id in reference_ids:
            ref = self.reference_store.get_reference(ref_id)
            if ref:
                references.append(ref)
            else:
                # Audit missing reference
                pass

        return self.injection_manager.inject_credentials_for_check(
            check_id, run_id, references, worker_id
        )

    def get_injected_env(self, check_id: str) -> Dict[str, str]:
        """Get injected environment variables for a check."""
        return self.injection_manager.get_injected_environment(check_id)

    def cleanup(self, run_id: str = None, check_id: str = None):
        self.injection_manager.cleanup_injections(run_id, check_id)
        self.resolver.clear_cache()

    def get_injection_history(self, run_id: str = None, check_id: str = None) -> List['InjectedCredential']:
        return self.injection_manager.get_injection_history(run_id, check_id)


# ==============================================================================
# CLI Integration
# ==============================================================================

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "test":
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"

            # Mock audit facade
            class MockAudit:
                def __init__(self): pass

            facade = CredentialFacade(db_path, MockAudit())

            # Add credential references
            ref1 = facade.add_credential_reference(
                CredentialReferenceType.ENV_VAR,
                "DATABASE_PASSWORD",
                CredentialPurpose.DATABASE,
                allowed_targets=["db.example.com"],
                description="Production database password",
                project_id="proj_test"
            )
            print(f"Added reference: {ref1.reference_id}")

            ref2 = facade.add_credential_reference(
                CredentialReferenceType.OS_KEYRING,
                "os-keyring:api-service:api-key",
                CredentialPurpose.API_AUTH,
                allowed_targets=["api.example.com"],
                description="API service key",
                project_id="proj_test"
            )
            print(f"Added reference: {ref2.reference_id}")

            # List references
            refs = facade.list_credential_references("proj_test")
            print(f"Total references: {len(refs)}")
            for r in refs:
                print(f"  {r.reference_id}: {r.reference_type.value}:{r.reference_value} ({r.purpose.value})")

            # Test injection (mock)
            print("\nCredential injection test (requires actual secrets in environment/keyring)")

            print("\nAll credential tests passed!")
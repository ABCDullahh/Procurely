"""Audit log service for recording admin actions."""

import json
from typing import Any

from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog


def log_audit(
    db: Session,
    actor_user_id: int,
    action: str,
    target_type: str,
    target_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> AuditLog:
    """Create an audit log entry.

    Args:
        db: Database session
        actor_user_id: ID of the user performing the action
        action: Action type (e.g., API_KEY_SET)
        target_type: Type of target (e.g., "api_key")
        target_id: ID of the target (optional)
        metadata: Additional metadata (no secrets!)

    Returns:
        Created AuditLog entry
    """
    audit_entry = AuditLog(
        actor_user_id=actor_user_id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        metadata_json=json.dumps(metadata) if metadata else None,
    )
    db.add(audit_entry)
    db.commit()
    db.refresh(audit_entry)
    return audit_entry

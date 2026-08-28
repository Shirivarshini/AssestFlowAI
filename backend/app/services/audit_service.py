from sqlalchemy.orm import Session

from app.models import AuditLog


def record(db: Session, action: str, asset_id: str | None = None, actor: str = "SYSTEM", details: dict | None = None, before_state: dict | None = None, after_state: dict | None = None, reason: str | None = None, source_refs: list[str] | None = None, related_event_id: str | None = None, related_decision_id: str | None = None) -> AuditLog:
    """SOURCE: 03_ARCHITECTURE.md rule 6 — every material financing
    decision must be auditable. Append-only; rows are never updated."""
    log = AuditLog(asset_id=asset_id, actor=actor, actor_type=actor, action=action, details=details or {}, before_state=before_state, after_state=after_state, reason=reason, source_refs=source_refs, related_event_id=related_event_id, related_decision_id=related_decision_id)
    db.add(log)
    db.commit()
    db.refresh(log)
    return log

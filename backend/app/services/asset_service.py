from datetime import datetime

from sqlalchemy.orm import Session

from app.core.enums import LifecycleStage, LIFECYCLE_ORDER
from app.core.errors import NotFoundError, InvalidTransitionError, ValidationError
from app.models import Asset, AssetLifecycleEvent, FinancingExposure
from app.schemas import AssetCreate, LifecycleEventCreate
from app.services import audit_service


def get_asset(db: Session, asset_id: str) -> Asset:
    asset = db.get(Asset, asset_id)
    if not asset:
        raise NotFoundError(f"Asset {asset_id} not found.", {"asset_id": asset_id})
    return asset


def list_assets(db: Session) -> list[Asset]:
    return db.query(Asset).order_by(Asset.created_at.desc()).all()


def create_asset(db: Session, payload: AssetCreate) -> Asset:
    if payload.current_lifecycle_stage not in LifecycleStage.__members__:
        raise ValidationError(
            f"Unknown lifecycle stage '{payload.current_lifecycle_stage}'.",
            {"allowed": [s.value for s in LifecycleStage]},
        )
    asset = Asset(**payload.model_dump())
    db.add(asset)
    db.flush()

    # SOURCE: 05_DATABASE_SCHEMA.md financing_exposure tracks exposure
    # independently of individual financing products — initialize at zero.
    db.add(FinancingExposure(asset_id=asset.id, total_outstanding=0.0, currency=asset.currency))
    db.commit()
    db.refresh(asset)

    audit_service.record(db, "ASSET_CREATED", asset.id, details={"product_name": asset.product_name})
    return asset


def is_valid_transition(from_stage: str, to_stage: str) -> bool:
    """SOURCE: 06_ASSET_LIFECYCLE.md — engine should reject impossible
    transitions unless a demo scenario explicitly models a
    correction/reversal. ASSUMPTION: forward-only along the canonical
    order is "valid"; a move to the immediately preceding stage is
    treated as an explicit correction/reversal and allowed; any larger
    jump backward or skip forward beyond +1 is rejected."""
    try:
        from_idx = LIFECYCLE_ORDER.index(LifecycleStage(from_stage))
        to_idx = LIFECYCLE_ORDER.index(LifecycleStage(to_stage))
    except ValueError:
        return False
    if to_idx == from_idx + 1:
        return True
    if to_idx == from_idx - 1:  # explicit correction/reversal
        return True
    return False


def apply_lifecycle_event(db: Session, asset_id: str, payload: LifecycleEventCreate) -> AssetLifecycleEvent:
    asset = get_asset(db, asset_id)
    from_stage = asset.current_lifecycle_stage
    to_stage = payload.to_stage

    if to_stage is not None:
        if to_stage not in LifecycleStage.__members__:
            raise ValidationError(
                f"Unknown lifecycle stage '{to_stage}'.",
                {"allowed": [s.value for s in LifecycleStage]},
            )
        if not is_valid_transition(from_stage, to_stage):
            raise InvalidTransitionError(
                f"Cannot transition asset {asset_id} from {from_stage} to {to_stage}.",
                {"from_stage": from_stage, "to_stage": to_stage},
            )
        asset.current_lifecycle_stage = to_stage
        asset.updated_at = datetime.utcnow()

    event = AssetLifecycleEvent(
        asset_id=asset_id,
        event_type=payload.event_type,
        from_stage=from_stage,
        to_stage=to_stage,
        source_id=payload.source_id,
        severity=payload.severity,
        payload=payload.payload,
    )
    db.add(event)
    db.commit()
    db.refresh(event)

    audit_service.record(
        db, "LIFECYCLE_EVENT", asset_id,
        details={"event_type": payload.event_type, "from_stage": from_stage, "to_stage": to_stage},
    )
    return event


def get_timeline(db: Session, asset_id: str) -> list[AssetLifecycleEvent]:
    get_asset(db, asset_id)  # 404 if missing
    return (
        db.query(AssetLifecycleEvent)
        .filter(AssetLifecycleEvent.asset_id == asset_id)
        .order_by(AssetLifecycleEvent.event_time.asc())
        .all()
    )

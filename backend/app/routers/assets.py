from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import AssetLifecycleEvent
from app.schemas import AssetCreate, AssetOut, LifecycleEventCreate, LifecycleEventOut, TimelineOut
from app.services import asset_service, event_service

router = APIRouter(tags=["assets"])


@router.get("/events", response_model=list[LifecycleEventOut])
def list_events(limit: int = 20, db: Session = Depends(get_db)):
    """Return the newest lifecycle events across all assets."""
    safe_limit = max(1, min(limit, 100))
    return db.query(AssetLifecycleEvent).order_by(AssetLifecycleEvent.event_time.desc()).limit(safe_limit).all()


@router.get("/assets", response_model=list[AssetOut])
def list_assets(db: Session = Depends(get_db)):
    return asset_service.list_assets(db)


@router.get("/assets/{asset_id}", response_model=AssetOut)
def get_asset(asset_id: str, db: Session = Depends(get_db)):
    return asset_service.get_asset(db, asset_id)


@router.post("/assets", response_model=AssetOut, status_code=201)
def create_asset(payload: AssetCreate, db: Session = Depends(get_db)):
    return asset_service.create_asset(db, payload)


@router.get("/assets/{asset_id}/timeline", response_model=TimelineOut)
def get_timeline(asset_id: str, db: Session = Depends(get_db)):
    asset = asset_service.get_asset(db, asset_id)
    events = asset_service.get_timeline(db, asset_id)
    return TimelineOut(asset_id=asset_id, current_lifecycle_stage=asset.current_lifecycle_stage, events=events)


@router.post("/assets/{asset_id}/events", response_model=LifecycleEventOut, status_code=201)
def post_event(asset_id: str, payload: LifecycleEventCreate, db: Session = Depends(get_db)):
    """SOURCE: 04_API_CONTRACT.md POST /assets/{asset_id}/events.
    Runs the full 12_EVENT_SYSTEM.md event flow (state update, reassessment,
    financing decision, alerting, audit) and returns the stored event."""
    result = event_service.process_event(db, asset_id, payload)
    return result["event"]

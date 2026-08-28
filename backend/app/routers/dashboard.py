from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Asset, AssetLifecycleEvent, FinancingExposure, Alert, FinancingTransaction, AIDecision
from app.schemas import DashboardOut, LifecycleEventOut, FinancingTransactionOut, DecisionOut

router = APIRouter(tags=["dashboard"])


@router.get("/dashboard", response_model=DashboardOut)
def get_dashboard(db: Session = Depends(get_db)):
    """SOURCE: 04_API_CONTRACT.md GET /dashboard field list: asset counts,
    total exposure, financing opportunities, risk alerts, recent events,
    financing transitions."""
    assets = db.query(Asset).all()
    asset_counts: dict[str, int] = {}
    for a in assets:
        asset_counts[a.current_lifecycle_stage] = asset_counts.get(a.current_lifecycle_stage, 0) + 1

    total_exposure = sum(e.total_outstanding for e in db.query(FinancingExposure).all())

    open_alerts = db.query(Alert).filter(Alert.status == "OPEN").all()
    risk_alerts = len(open_alerts)

    # ASSUMPTION: "financing opportunities" = assets with no active financing yet.
    active_asset_ids = {
        t.asset_id for t in db.query(FinancingTransaction).filter(FinancingTransaction.status == "ACTIVE").all()
    }
    financing_opportunities = len([a for a in assets if a.id not in active_asset_ids])

    recent_events = (
        db.query(AssetLifecycleEvent).order_by(AssetLifecycleEvent.event_time.desc()).limit(10).all()
    )
    financing_transitions = (
        db.query(FinancingTransaction)
        .filter(FinancingTransaction.status == "TRANSITIONED")
        .order_by(FinancingTransaction.start_date.desc())
        .limit(10)
        .all()
    )
    recent_decisions = db.query(AIDecision).order_by(AIDecision.created_at.desc()).limit(10).all()

    return DashboardOut(
        asset_counts=asset_counts,
        total_exposure=total_exposure,
        financing_opportunities=financing_opportunities,
        risk_alerts=risk_alerts,
        recent_events=[LifecycleEventOut.model_validate(e) for e in recent_events],
        financing_transitions=[FinancingTransactionOut.model_validate(t) for t in financing_transitions],
        recent_decisions=[DecisionOut.model_validate(d) for d in recent_decisions],
        duplicate_financing_warnings=len([a for a in open_alerts if a.alert_type == "DUPLICATE_FINANCING"]),
        over_leverage_warnings=len([a for a in open_alerts if a.alert_type == "OVER_LEVERAGE"]),
        pending_alerts=len(open_alerts),
    )

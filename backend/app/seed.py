"""
Demo seed script.

Sets up one asset plus simulated multi-source records so the team can
run 15_DEMO_SCENARIOS.md scenarios end-to-end against the real API
instead of only unit tests. Run with: python -m app.seed
"""
from app.database import Base, engine, SessionLocal
from app.models import Asset, SourceRecord
from app.schemas import AssetCreate
from app.services import asset_service, valuation_service, risk_service, financing_service, decision_service
from app.core.enums import DecisionType

Base.metadata.create_all(bind=engine)


def run():
    db = SessionLocal()
    try:
        asset = asset_service.create_asset(
            db,
            AssetCreate(
                external_reference="PO-2026-0091",
                product_name="Cotton Yarn - Grade A",
                quantity=5000,
                unit="KG",
                owner_id="SUPPLIER-DEMO-1",
                current_lifecycle_stage="SHIPMENT",
                current_location="Port of Chennai",
                current_estimated_value=2_500_000,
                currency="INR",
            ),
        )

        # SOURCE: 15_DEMO_SCENARIOS.md Scenario 4 — conflicting sources.
        db.add_all([
            SourceRecord(asset_id=asset.id, source_name="ERP", field="physical_state", value="COMPLETE"),
            SourceRecord(asset_id=asset.id, source_name="TELEMETRY", field="physical_state", value="IN_TRANSIT_92_PCT"),
            SourceRecord(asset_id=asset.id, source_name="WAREHOUSE", field="physical_state", value="COMPLETE"),
        ])
        db.commit()

        valuation_service.estimate_value(db, asset)
        risk = risk_service.assess_risk(db, asset)
        evaluation = financing_service.evaluate_financing(
            db, asset, risk_score=risk.overall_score, risk_level=risk.risk_level, confidence=risk.confidence,
        )
        decision_service.record_decision(db, asset, DecisionType.FINANCING_EVALUATION.value, evaluation)

        if evaluation["recommended_instrument"] and evaluation["recommended_amount"] > 0:
            financing_service.open_or_update_financing(
                db, asset, evaluation["recommended_instrument"], evaluation["recommended_amount"],
            )

        print(f"Seeded demo asset: {asset.id}")
        print(f"Financing evaluation: {evaluation}")
    finally:
        db.close()


if __name__ == "__main__":
    run()

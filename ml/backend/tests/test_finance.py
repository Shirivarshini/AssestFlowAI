"""Tests for Features 5-8."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from finance.decision_engine import evaluate_financing
from finance.financing_amount import calculate_dynamic_financing
from finance.financing_need import calculate_financing_need
from finance.instrument_selector import select_financing_instrument
from finance.risk_engine import calculate_risk
from finance.schemas import (
    AssetState,
    Condition,
    ProductionStatus,
    ShipmentStatus,
    Stage,
)
from finance.value_engine import calculate_asset_value


def make_asset(**overrides) -> AssetState:
    base = dict(
        asset_id="AST-TEST",
        stage=Stage.SHIPMENT,
        purchase_value=10_000_000,
        quantity=900,
        condition=Condition.GOOD,
        location="Chennai Port",
        shipment_status=ShipmentStatus.ON_TIME,
        production_status=ProductionStatus.COMPLETED,
        buyer_risk=20,
        production_risk=20,
        shipment_risk=20,
        asset_risk=20,
        data_confidence=0.95,
        required_capital=5_000_000,
        existing_financing=3_000_000,
    )
    base.update(overrides)
    return AssetState(**base)


def test_value_calculation():
    result = calculate_asset_value(make_asset())
    assert result["asset_value"] == 9_000_000


def test_shipment_delay_increases_risk():
    normal = calculate_risk(make_asset())
    delayed = calculate_risk(
        make_asset(
            shipment_status=ShipmentStatus.DELAYED,
            shipment_risk=20,
        )
    )
    assert delayed["risk_score"] > normal["risk_score"]
    assert "Shipment delay detected" in delayed["risk_factors"]


def test_financing_need():
    result = calculate_financing_need(
        make_asset(required_capital=5_000_000, existing_financing=3_000_000)
    )
    assert result["financing_need"] == 2_000_000
    assert result["financing_needed"] is True


def test_financing_need_never_negative():
    result = calculate_financing_need(
        make_asset(required_capital=1_000_000, existing_financing=3_000_000)
    )
    assert result["financing_need"] == 0
    assert result["financing_needed"] is False


def test_instrument_selection():
    assert (
        select_financing_instrument(Stage.SHIPMENT, "LOW")
        == "IN_TRANSIT_FINANCING"
    )
    assert select_financing_instrument(Stage.PAYMENT, "LOW") == "NONE"


def test_high_risk_instrument_review():
    assert (
        select_financing_instrument(Stage.SHIPMENT, "HIGH")
        == "INSTRUMENT_REVIEW_REQUIRED"
    )


def test_dynamic_financing():
    result = calculate_dynamic_financing(
        asset_value=9_000_000,
        risk_level="MEDIUM",
        data_confidence=0.72,
        existing_financing=3_000_000,
        financing_need=2_000_000,
    )
    assert result["maximum_safe_financing"] > 0
    assert result["recommended_amount"] <= result["available_financing"]
    assert result["recommended_amount"] <= 2_000_000


def test_over_leverage_protection():
    result = calculate_dynamic_financing(
        asset_value=9_000_000,
        risk_level="MEDIUM",
        data_confidence=0.72,
        existing_financing=50_000_000,
        financing_need=2_000_000,
    )
    assert result["available_financing"] == 0
    assert result["recommended_amount"] == 0
    assert result["over_leveraged"] is True


def test_high_risk_pauses():
    decision = evaluate_financing(
        make_asset(
            buyer_risk=90,
            production_risk=90,
            shipment_risk=90,
            asset_risk=90,
            data_confidence=0.95,
        )
    )
    assert decision["risk_level"] == "HIGH"
    assert decision["action"] == "PAUSE"


def test_low_data_confidence_does_not_allow_financing():
    decision = evaluate_financing(make_asset(data_confidence=0.40))
    assert decision["action"] == "DO_NOT_FINANCE"


def test_payment_stage():
    decision = evaluate_financing(
        make_asset(
            stage=Stage.PAYMENT,
            required_capital=0,
            existing_financing=0,
        )
    )
    assert decision["instrument"] == "NONE"
    assert decision["asset_value"] == 0


def test_pipeline_invariants():
    decision = evaluate_financing(make_asset())
    assert decision["recommended_amount"] <= decision["available_financing"]
    assert decision["recommended_amount"] <= decision["financing_need"]
    assert decision["recommended_amount"] <= decision["maximum_safe_financing"]
    assert decision["recommended_amount"] >= 0

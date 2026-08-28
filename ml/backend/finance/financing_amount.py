"""Feature 8 — dynamic financing and exposure protection."""

from .schemas import RiskLevel

# Hackathon prototype policy constants — not a production lending model.
ADVANCE_RATE = 0.70

RISK_FACTOR_MAP = {
    RiskLevel.LOW: 1.00,
    RiskLevel.MEDIUM: 0.80,
    RiskLevel.HIGH: 0.70,
}


def calculate_dynamic_financing(
    asset_value: int,
    risk_level: RiskLevel,
    data_confidence: float,
    existing_financing: int,
    financing_need: int,
) -> dict:
    """Calculate the safe exposure and recommended additional financing."""

    risk_factor = RISK_FACTOR_MAP[risk_level]

    maximum_safe_financing = int(
        round(
            asset_value
            * ADVANCE_RATE
            * risk_factor
            * data_confidence
        )
    )

    if existing_financing >= maximum_safe_financing:
        return {
            "maximum_safe_financing": maximum_safe_financing,
            "available_financing": 0,
            "recommended_amount": 0,
            "over_leveraged": True,
        }

    available_financing = max(
        maximum_safe_financing - existing_financing,
        0,
    )

    recommended_amount = max(
        0,
        min(
            financing_need,
            available_financing,
            maximum_safe_financing,
        ),
    )

    return {
        "maximum_safe_financing": maximum_safe_financing,
        "available_financing": available_financing,
        "recommended_amount": recommended_amount,
        "over_leveraged": False,
    }

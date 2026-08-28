"""Feature 6 — financing need calculator."""

from .schemas import AssetState


def calculate_financing_need(asset: AssetState) -> dict:
    financing_need = max(
        asset.required_capital - asset.existing_financing,
        0,
    )

    return {
        "required_capital": asset.required_capital,
        "existing_financing": asset.existing_financing,
        "financing_need": financing_need,
        "financing_needed": financing_need > 0,
    }

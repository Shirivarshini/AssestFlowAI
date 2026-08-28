"""Optional AI explanation layer.

The deterministic finance engine remains the source of truth for all
financial numbers. The LLM only turns the result into plain business
language. If no API key/package is available, a local fallback is used.
"""

import json
import os

try:
    import anthropic
except ImportError:  # pragma: no cover
    anthropic = None

# Override this with ANTHROPIC_MODEL if needed.
DEFAULT_MODEL = "claude-sonnet-4-6"

SYSTEM_PROMPT = """You are an AI supply-chain financing explanation assistant.

A deterministic financial engine has already calculated the financing
decision. Your only job is to explain that decision clearly to a business
user.

Rules:
- Never invent numbers.
- Never change the action.
- Never change the financing instrument.
- Never change the recommended amount.
- Never propose an amount different from the supplied amount.
- Do not provide legal, investment, or lending guarantees.
- Mention the main risk factors when present.
- Keep the answer to 2-4 short sentences.
"""


def generate_explanation(decision: dict) -> str:
    api_key = os.getenv("ANTHROPIC_API_KEY")

    if anthropic is None or not api_key:
        return _fallback_explanation(decision)

    try:
        client = anthropic.Anthropic(api_key=api_key)
        model = os.getenv("ANTHROPIC_MODEL", DEFAULT_MODEL)

        message = client.messages.create(
            model=model,
            max_tokens=250,
            system=SYSTEM_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": (
                        "Explain this already-calculated financing decision "
                        "in simple business language. Do not recalculate it.\n\n"
                        + json.dumps(decision, default=str)
                    ),
                }
            ],
        )

        text = " ".join(
            block.text
            for block in message.content
            if getattr(block, "type", None) == "text"
        ).strip()

        return text or _fallback_explanation(decision)

    except Exception:
        return _fallback_explanation(decision)


def _fallback_explanation(decision: dict) -> str:
    action = decision.get("action", "UNKNOWN")
    instrument = decision.get("instrument", "UNKNOWN")
    amount = int(decision.get("recommended_amount", 0))
    factors = decision.get("risk_factors") or []

    if factors:
        factor_text = " Key factors: " + ", ".join(factors) + "."
    else:
        factor_text = ""

    return (
        f"Recommended action is {action} using {instrument}, with "
        f"additional financing of ₹{amount:,}.{factor_text}"
    )

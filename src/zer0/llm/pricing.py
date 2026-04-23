"""Gemini model pricing table (USD per 1M tokens).

Prices sourced from Google AI pricing page. Update when prices change.
Unknown models fall back to zero cost with a warning log — no crash.
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

# (input_per_1m_usd, output_per_1m_usd)
_PRICES: dict[str, tuple[float, float]] = {
    "gemini-2.5-flash": (0.15, 0.60),
    "gemini-2.5-flash-preview-04-17": (0.15, 0.60),
    "gemini-2.0-flash": (0.10, 0.40),
    "gemini-2.0-flash-lite": (0.075, 0.30),
    "gemini-1.5-flash": (0.075, 0.30),
    "gemini-1.5-flash-8b": (0.0375, 0.15),
    "gemini-1.5-pro": (1.25, 5.00),
    "gemini-1.0-pro": (0.50, 1.50),
}


def estimate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    """Return estimated USD cost for the given token counts and model."""
    prices = _PRICES.get(model)
    if prices is None:
        logger.warning("No pricing data for model %r — cost defaulting to 0", model)
        return 0.0
    input_price, output_price = prices
    return (input_tokens * input_price + output_tokens * output_price) / 1_000_000

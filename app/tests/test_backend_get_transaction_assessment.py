"""Real-LLM tests for `app.backend.is_diversion_risk`.

These hit the configured endpoint (config.openai_base_url / config.model) with the real
`diversion_agent` and the real flagged-entity list from `app.data`. Nothing is mocked:
the agent's only job is to decide whether the counterparty appears on that list.

Run with:  uv run pytest tests/test_backend_get_transaction_assessment.py -s
"""

from __future__ import annotations

import asyncio

from app.backend import is_diversion_risk


def _run(description: str) -> bool:
    return asyncio.run(is_diversion_risk(description))


def test_flagged_company_is_detected() -> None:
    """Counterparty is on the internal flagged list (INT-0101)."""
    description = (
        "Outbound shipment of two fibre-optic sensor units to Meridian Freight Solutions FZE, "
        "Warehouse 7, Jebel Ali Free Zone, Dubai."
    )

    risk = _run(description)
    print(f"\nis_diversion_risk: {risk}")

    assert risk is True


def test_unknown_company_is_not_flagged() -> None:
    """Counterparty appears nowhere on the internal flagged list."""
    description = (
        "Outbound shipment of two fibre-optic sensor units to Nordvik Kontorvarsler AB, "
        "Vasagatan 14, Stockholm."
    )

    risk = _run(description)
    print(f"\nis_diversion_risk: {risk}")

    assert risk is False

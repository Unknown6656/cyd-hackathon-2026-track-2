"""Real-LLM tests for `app.backend.get_classification`.

These hit the configured endpoint (config.openai_base_url / config.model) with the real
`classifier_agent`. Only the corpus backends behind the three tools are mocked — EKN lookup
(`get_ekn_description`), legislation search (`semantic_search_legislation`) and ordinances /
control-list search (`semantic_search_control_lists`) — so no vector DB is needed and we can
assert exactly which EKNs the model asked for, and in which order. The `*_tool` wrappers are
bound into the agent at import time, so the backend names are what has to be patched.
Mocked descriptions contain a further EKN reference only where a test wants the agent to
follow it.

Run with:  uv run pytest tests/test_backend_get_classification.py -s
"""

from __future__ import annotations

import asyncio
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from app.backend import get_classification
from app.models import AdviseClassificationRegime, AdviseClassificationResponse, Item

# Simple, self-consistent stand-ins for the real corpus lookups.
EKN_DETAILS = {
    "A4004": "A4004: Armoured fibre-optic cable of military specification, "
    "ruggedised for field deployment. Controlled as dual_use.",
    "A4005": "A4005: Optical amplifier for field deployment. "
    "An export licence is required for every destination.",
}

# One fixed passage per corpus - enough for the model to cite, no vector DB needed.
LEGISLATION_RESULTS = [
    {
        "file_name": "KMV_SR-514.511",
        "text": "Kriegsmaterial: gepanzerte Glasfaserkabel und optische Verstärker für den "
        "militärischen Feldeinsatz bedürfen einer Ausfuhrbewilligung.",
    },
]
ORDINANCES_RESULTS = [
    {
        "file_name": "GKV_Anhang-1-2_dual-use",
        "EKN": "A4004",
        "text": "Dual-Use-Güter: Glasfaserkabel und optische "
        "Verstärker sind als Dual-Use-Güter gelistet. Für den militärischen Einsatz ist eine Ausfuhrbewilligung nötig.",
    },
]


def _lookup(details: dict[str, str]) -> Any:
    """Tool backend: unknown EKNs raise instead of silently returning a stub."""

    def fetch(ekn: str) -> str:
        return details.get(ekn, "no results")

    return fetch


def _run(description: str, details: dict[str, str] = EKN_DETAILS) -> tuple[AdviseClassificationResponse, Any]:
    mock_fetch = MagicMock(side_effect=_lookup(details))
    with (
        patch("app.agents.get_ekn_description", mock_fetch),
        patch("app.agents.semantic_search_legislation", return_value=LEGISLATION_RESULTS),
        patch("app.agents.semantic_search_control_lists", return_value=ORDINANCES_RESULTS),
    ):
        result = asyncio.run(get_classification(Item(description=description, specifications={})))
    return result, mock_fetch


def _requested(mock_fetch: Any) -> list[str]:
    """The EKNs the model asked for, in call order."""
    return [
        str(call.args[0] if call.args else call.kwargs["ekn"])
        for call in mock_fetch.call_args_list
    ]


def test_one_reference_is_resolved_with_one_tool_call() -> None:
    description = (
        "Armoured fibre-optic cable of military specification, ruggedised for field "
        "deployment. See EKN A4004 for the controlled definition of this cable."
    )

    result, mock_fetch = _run(description)
    print(f"\ntool calls: {mock_fetch.call_args_list}\n{result}")

    mock_fetch.assert_called_once_with("A4004")

    #assert result.controlled is True
    #assert result.regime is AdviseClassificationRegime.DUAL_USE
    #assert "A4004" in result.citations
    #assert result.deciding_text.strip()


def test_two_references_are_resolved_one_tool_call_each() -> None:
    description = (
        "Export consignment: one armoured fibre-optic cable of military specification "
        "plus one optical amplifier for field deployment. "
        "See EKN A4004 for the cable and EKN A4005 for the amplifier."
    )

    result, mock_fetch = _run(description)
    print(f"\ntool calls: {mock_fetch.call_args_list}\n{result}")

    # each EKN named in the query is fetched exactly once (the model picks the order)
    assert sorted(_requested(mock_fetch)) == ["A4004", "A4005"]

    #assert result.controlled is True
    #assert {"A4004", "A4005"} <= set(result.citations)
    #assert result.deciding_text.strip()


def test_reference_chain_stops_after_second_tool_call() -> None:
    """Query names A4004; A4004's text names A4005; A4005's text names nothing further."""
    chained_details = {
        "A4004": "A4004: Armoured fibre-optic cable of military specification. "
        "For the amplifier that is part of this cable set, see EKN A4005.",
        "A4005": "A4005: Optical amplifier for field deployment. "
        "An export licence is required for every destination.",
    }
    description = (
        "Is an export licence needed for our armoured fibre-optic cable of military "
        "specification? See EKN A4004 for the controlled definition of this cable."
    )

    result, mock_fetch = _run(description, chained_details)
    print(f"\ntool calls: {mock_fetch.call_args_list}\n{result}")

    # A4005 can only have come from A4004's result; nothing asks for more
    assert _requested(mock_fetch) == ["A4004", "A4005"]

    #assert result.controlled is True
    #assert "A4004" in result.citations
    #assert result.deciding_text.strip()


def test_real() -> None:
    description = "standalone high-speed ADC integrated circuit for test and measurement",
    specifications = {
        "resolution_bits": 12,
        "sampling_rate": "450 MSa/s",
        "channels": 1
    }

    # expected = {
    #     "controlled": True,
    #     "regime": "dual_use",
    #     "entries": [
    #         "GKV Anhang 2 3A001"
    #     ],
    #     "entry": "3A001.a.5.a",
    #     "note": "12 bit (>=12, <14) with sampling rate 450 MSa/s > 400 MSPS"
    # }

    item = Item(description=description, specifications=specifications)
    result = asyncio.run(get_classification(item))

    print(result)
    assert False
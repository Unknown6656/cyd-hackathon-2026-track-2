"""Smoke tests for `app.subagents.run_subagents`.

These hit the configured endpoint with the real orchestrator + the three regime
subagents (war materiel / specific military / dual use) and their real corpus
tools - nothing is mocked, so a running Qdrant / corpus is required.

The parametrized cases come from `app/selected_item_requests_responses.json`,
which holds the /advise request payloads extracted from `data/test_items_*.json`
and `data/test_advice_200.json` for the item IDs C-16, C-14, N-20, S-05, S-08,
S-17. The expected regime is the ground truth shipped with those files.

Run with:  uv run pytest tests/test_subagents_smoke.py -s
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from app.subagents import run_subagents

DATA_FILE = Path(__file__).resolve().parents[1] / "selected_item_requests_responses.json"

# `regime: "none"` in the item files maps to the `not_controlled` output literal.
REGIME_NOT_CONTROLLED = "not_controlled"
REGIME_SPECIFIC_MILITARY = "specific_military"


def _prompt(item: dict[str, Any]) -> str:
    """Rebuild the classifier prompt from an extracted /advise item block."""
    description = item.get("description") or ""
    specifications = item.get("specifications")
    if not specifications:
        return description
    return (
        f"{description}\n\n"
        "specifications:\n"
        f"{json.dumps(specifications, ensure_ascii=False, indent=2)}"
    )


def _regime(regime: str | None) -> str:
    """Map a ground-truth regime onto the orchestrator's output literal."""
    return regime if regime and regime != "none" else REGIME_NOT_CONTROLLED


def _entries() -> list[tuple[str, str, str]]:
    """One (prompt, expected regime, id) per extracted entry: item entries plus advice cases."""
    cases: list[tuple[str, str, str]] = []
    for entry in json.loads(DATA_FILE.read_text())["items"]:
        item_id = entry["id"]
        for item_entry in entry["item_entries"]:
            cases.append(
                (
                    _prompt(item_entry["request"]["item"]),
                    _regime(item_entry["expected_classification"]["regime"]),
                    f"{item_id}-items",
                )
            )
        for case in entry["advice_cases"]:
            classification = case["response"].get("classification") or {}
            cases.append(
                (
                    _prompt(case["request"]["item"]),
                    _regime(classification.get("regime")),
                    f"{item_id}-{case['case_id']}",
                )
            )
    return cases


ENTRIES = _entries()
CASES = [pytest.param(prompt, regime, id=id) for prompt, regime, id in ENTRIES]
MILITARY_CASES = [
    pytest.param(prompt, regime, id=id)
    for prompt, regime, id in ENTRIES
    if regime == REGIME_SPECIFIC_MILITARY
]


@pytest.mark.parametrize("prompt,expected_regime", CASES)
def test_subagents_classify_selected_items(prompt: str, expected_regime: str) -> None:
    """The orchestrator must reach the ground-truth regime for every selected item."""
    result = run_subagents(prompt)
    got = str(getattr(result.output, "classification", result.output))

    print(f"\nprompt:\n{prompt}\n")
    print(f"expected: {expected_regime}\nRESULT: {result.output}")

    assert got == expected_regime, f"expected {expected_regime}, got {got}: {result.output.reason}"
    assert str(getattr(result.output, "reason", "")).strip()


@pytest.mark.parametrize("prompt,expected_regime", MILITARY_CASES)
def test_subagents_classify_selected_military_items(prompt: str, expected_regime: str) -> None:
    """The orchestrator must reach the ground-truth regime for every selected item."""
    result = run_subagents(prompt)
    got = str(getattr(result.output, "classification", result.output))

    print(f"\nprompt:\n{prompt}\n")
    print(f"expected: {expected_regime}\nRESULT: {result.output}")

    assert got == expected_regime, f"expected {expected_regime}, got {got}: {result.output.reason}"
    assert str(getattr(result.output, "reason", "")).strip()


def test_subagents() -> None:
    #result = run_subagents("biological weapons")
    prompt = """standalone high-speed ADC integrated circuit for test and measurement.

       {
         "specifications": {
            "resolution_bits": 12,
            "sampling_rate": "450 MSa/s",
            "channels": 1
        }"""
    #prompt = "strain of a biological agent selected and modified to increase its effectiveness for combat use"
    result = run_subagents(prompt)

    print("RESULT: ", result.output)

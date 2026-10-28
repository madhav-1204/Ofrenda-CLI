"""
Tests for the interview loop.

We mock llm.chat so nothing touches the network.
"""
from unittest.mock import patch, call

import pytest

from ofrenda.config import Config
from ofrenda import interview


# ── helpers ──────────────────────────────────────────────────────────────────

def _run_with_inputs(model_replies: list[str], user_inputs: list[str]) -> list[tuple]:
    """
    Run run_interview with mocked LLM replies and mocked user input.
    Returns the list of (question, answer) pairs.
    """
    cfg = Config()
    with (
        patch("ofrenda.interview.llm.chat", side_effect=model_replies),
        patch("ofrenda.interview.Prompt.ask", side_effect=user_inputs),
        patch("ofrenda.interview.console"),  # suppress output during tests
    ):
        return interview.run_interview("Rosa", "grandmother", cfg)


# ── basic flow ───────────────────────────────────────────────────────────────

def test_normal_answer_captured():
    replies = ["What did she love to cook?", "[INTERVIEW COMPLETE]"]
    inputs = ["She made tamales every Sunday."]
    pairs = _run_with_inputs(replies, inputs)
    assert len(pairs) == 1
    assert pairs[0][1] == "She made tamales every Sunday."


def test_skip_recorded_correctly():
    replies = ["What did she love to cook?", "Was there a song?", "[INTERVIEW COMPLETE]"]
    inputs = ["skip", "La Llorona."]
    pairs = _run_with_inputs(replies, inputs)
    assert pairs[0][1] == "[skipped]"
    assert pairs[1][1] == "La Llorona."


def test_done_stops_loop():
    replies = ["What did she love to cook?", "Was there music?"]
    inputs = ["done"]
    pairs = _run_with_inputs(replies, inputs)
    # Loop stops after "done"; only the first question pair is recorded
    assert len(pairs) == 1
    assert pairs[0][1] == "[done]"


def test_multiple_answers():
    replies = [
        "What did she love to eat?",
        "Any songs?",
        "A phrase she used?",
        "[INTERVIEW COMPLETE]",
    ]
    inputs = ["Tamales.", "La Paloma.", "Mija, come here."]
    pairs = _run_with_inputs(replies, inputs)
    assert len(pairs) == 3
    assert pairs[2][1] == "Mija, come here."


def test_empty_pairs_when_immediately_done():
    """If the user types 'done' on the very first question."""
    replies = ["What did she love to cook?"]
    inputs = ["done"]
    pairs = _run_with_inputs(replies, inputs)
    assert len(pairs) == 1
    assert pairs[0][1] == "[done]"

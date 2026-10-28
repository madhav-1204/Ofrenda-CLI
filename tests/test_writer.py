"""Tests for writer.py — slug, transcript building, file output."""
import json
from pathlib import Path
from unittest.mock import patch

import pytest

from ofrenda.config import Config
from ofrenda.writer import _slug, _build_transcript, save


# ── slug ────────────────────────────────────────────────────────────────────

def test_slug_simple():
    assert _slug("Rosa") == "rosa"

def test_slug_spaces():
    assert _slug("María José") == "maría-josé"

def test_slug_leading_trailing():
    assert _slug("  Grandpa Joe  ") == "grandpa-joe"

def test_slug_multiple_spaces():
    # Multiple spaces collapse to a single dash — cleaner slug
    assert _slug("John  Paul") == "john-paul"


# ── transcript ───────────────────────────────────────────────────────────────

def test_transcript_includes_answers():
    pairs = [
        ("What did they love to eat?", "She made the best tamales."),
        ("Was there a song?", "La Llorona, always."),
    ]
    t = _build_transcript("Rosa", "grandmother", pairs)
    assert "Rosa" in t
    assert "grandmother" in t
    assert "tamales" in t
    assert "La Llorona" in t

def test_transcript_skips_excluded():
    pairs = [
        ("What did they love to eat?", "[skipped]"),
        ("Was there a song?", "La Paloma."),
    ]
    t = _build_transcript("Rosa", "grandmother", pairs)
    assert "[skipped]" not in t
    assert "La Paloma" in t

def test_transcript_done_excluded():
    pairs = [
        ("Any last thing?", "[done]"),
    ]
    t = _build_transcript("Rosa", "grandmother", pairs)
    assert "[done]" not in t


# ── save (integration, LLM mocked) ───────────────────────────────────────────

FAKE_REMEMBRANCE = "She made the best tamales on Sunday mornings."
FAKE_CHECKLIST = "## Foods & drinks\n- [ ] Tamales"


def test_save_creates_files(tmp_path):
    cfg = Config(data_dir=tmp_path)
    pairs = [("What did they love to eat?", "Tamales, every Sunday.")]

    with patch("ofrenda.writer.llm.chat", side_effect=[FAKE_REMEMBRANCE, FAKE_CHECKLIST]):
        out_dir = save("Rosa", "grandmother", pairs, cfg)

    assert (out_dir / "remembrance.md").exists()
    assert (out_dir / "ofrenda.md").exists()
    assert (out_dir / "session.json").exists()


def test_save_remembrance_content(tmp_path):
    cfg = Config(data_dir=tmp_path)
    pairs = [("What did they love to eat?", "Tamales, every Sunday.")]

    with patch("ofrenda.writer.llm.chat", side_effect=[FAKE_REMEMBRANCE, FAKE_CHECKLIST]):
        out_dir = save("Rosa", "grandmother", pairs, cfg)

    text = (out_dir / "remembrance.md").read_text(encoding="utf-8")
    assert "Rosa" in text
    assert FAKE_REMEMBRANCE in text


def test_save_session_json(tmp_path):
    cfg = Config(data_dir=tmp_path)
    pairs = [("A question?", "An answer.")]

    with patch("ofrenda.writer.llm.chat", side_effect=[FAKE_REMEMBRANCE, FAKE_CHECKLIST]):
        out_dir = save("Rosa", "grandmother", pairs, cfg)

    session = json.loads((out_dir / "session.json").read_text(encoding="utf-8"))
    assert session["name"] == "Rosa"
    assert session["pairs"][0]["a"] == "An answer."


def test_save_uses_slug_as_dirname(tmp_path):
    cfg = Config(data_dir=tmp_path)
    pairs = [("Q?", "A.")]

    with patch("ofrenda.writer.llm.chat", side_effect=[FAKE_REMEMBRANCE, FAKE_CHECKLIST]):
        out_dir = save("María José", "mother", pairs, cfg)

    assert out_dir.name == "maría-josé"

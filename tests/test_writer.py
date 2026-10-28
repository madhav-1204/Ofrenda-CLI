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

def test_transcript_excludes_interviewer_text():
    pairs = [
        ("That sounds wonderful. What did they love to eat?", "She made tamales."),
        ("A lovely memory. What song did she sing?", "La Llorona."),
    ]
    t = _build_transcript("Rosa", "grandmother", pairs)
    assert "That sounds wonderful" not in t
    assert "What did they love to eat?" not in t
    assert "A lovely memory" not in t
    assert "What song did she sing?" not in t
    assert "She made tamales." in t
    assert "La Llorona." in t


def test_remembrance_prompt_only_contains_user_answers_mocked(tmp_path):
    cfg = Config(data_dir=tmp_path)
    interviewer_commentary = "Oh how sweet! Tell me about their favourite food."
    interviewer_q2 = "Did they sing any particular song while cooking?"
    interviewer_skipped_q = "What was their favourite colour?"

    pairs = [
        (interviewer_commentary, "He loved eating mirchi bajji outside school."),
        (interviewer_skipped_q, "[skipped]"),
        (interviewer_q2, "He hummed Kal Ho Naa Ho badly on purpose."),
    ]

    with patch("ofrenda.writer.llm.chat", side_effect=["Remembrance text", "Checklist text"]) as mock_chat:
        save("Karthik", "childhood friend", pairs, cfg)

    # First call to llm.chat is for remembrance
    remembrance_call = mock_chat.call_args_list[0]
    messages = remembrance_call[0][0]
    user_prompt_content = messages[1]["content"]

    # (a) prompt contains the user's answers
    assert "He loved eating mirchi bajji outside school." in user_prompt_content
    assert "He hummed Kal Ho Naa Ho badly on purpose." in user_prompt_content

    # (b) prompt contains none of the interviewer's text
    assert interviewer_commentary not in user_prompt_content
    assert interviewer_q2 not in user_prompt_content
    assert interviewer_skipped_q not in user_prompt_content

    # (c) skipped questions do not appear
    assert "[skipped]" not in user_prompt_content


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

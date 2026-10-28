"""
Generates remembrance.md and ofrenda.md from interview pairs,
then saves everything to disk.

Also writes session.json so the interview can be inspected later.
"""
from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

from rich.console import Console

from ofrenda import llm
from ofrenda.interview import _load_prompt

if TYPE_CHECKING:
    from ofrenda.config import Config

console = Console()


def _slug(name: str) -> str:
    """'María José' → 'maria-jose'"""
    s = name.lower().strip()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"[\s_]+", "-", s)
    return s


def _build_transcript(
    name: str, relationship: str, pairs: list[tuple[str, str]]
) -> str:
    lines = [f"Name: {name}", f"Relationship: {relationship}", "---"]
    for question, answer in pairs:
        if answer in ("[skipped]", "[done]"):
            continue
        lines.append(f"Q: {question}")
        lines.append(f"A: {answer}")
        lines.append("")
    return "\n".join(lines)


def _generate_remembrance(
    name: str, relationship: str, pairs: list[tuple[str, str]], cfg: "Config"
) -> str:
    system = _load_prompt("remembrance.txt")
    transcript = _build_transcript(name, relationship, pairs)
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": transcript},
    ]
    console.print("Writing remembrance...", style="dim")
    return llm.chat(messages, cfg)


def _generate_checklist(
    name: str, relationship: str, pairs: list[tuple[str, str]], cfg: "Config"
) -> str:
    system = _load_prompt("ofrenda_checklist.txt")
    transcript = _build_transcript(name, relationship, pairs)
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": transcript},
    ]
    console.print("Building ofrenda checklist...", style="dim")
    return llm.chat(messages, cfg)


def save(
    name: str,
    relationship: str,
    pairs: list[tuple[str, str]],
    cfg: "Config",
) -> Path:
    """
    Generate both files and save them. Returns the directory path.
    """
    slug = _slug(name)
    out_dir: Path = cfg.ofrenda_dir(slug)
    out_dir.mkdir(parents=True, exist_ok=True)

    remembrance_text = _generate_remembrance(name, relationship, pairs, cfg)
    checklist_text = _generate_checklist(name, relationship, pairs, cfg)

    # remembrance.md
    remembrance_path = out_dir / "remembrance.md"
    remembrance_path.write_text(
        f"# {name}\n\n{remembrance_text}\n",
        encoding="utf-8",
    )

    # ofrenda.md
    ofrenda_path = out_dir / "ofrenda.md"
    ofrenda_path.write_text(
        f"# Ofrenda for {name}\n\n{checklist_text}\n",
        encoding="utf-8",
    )

    # session.json — raw interview data, useful for debugging or re-running
    session = {
        "name": name,
        "relationship": relationship,
        "created": datetime.now().isoformat(timespec="seconds"),
        "model": cfg.model,
        "pairs": [{"q": q, "a": a} for q, a in pairs],
    }
    (out_dir / "session.json").write_text(
        json.dumps(session, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    return out_dir

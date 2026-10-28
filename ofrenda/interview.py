"""
The interview loop.

Sends the full conversation history to the model on each turn so that
each question can react to the previous answer. Handles skip/done.
Returns a plain list of (question, answer) pairs for the writer to use.
"""
from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from rich.console import Console
from rich.prompt import Prompt
from rich.text import Text

from ofrenda import llm

if TYPE_CHECKING:
    from ofrenda.config import Config

_PROMPTS_DIR = Path(__file__).parent.parent / "prompts"

console = Console()


def _load_prompt(filename: str) -> str:
    path = _PROMPTS_DIR / filename
    return path.read_text(encoding="utf-8").strip()


def _print_model(text: str) -> None:
    console.print(Text(text, style="italic"))
    console.print()


def run_interview(name: str, relationship: str, cfg: "Config") -> list[tuple[str, str]]:
    """
    Run the interview and return a list of (question, answer) pairs.
    Skipped questions are included with answer="[skipped]".
    """
    system_prompt = _load_prompt("interviewer.txt")

    # Seed the conversation with context so the first question is personal.
    seed = (
        f"The person sharing memories is remembering someone named {name}, "
        f"their {relationship}. Please begin with your first question."
    )

    messages: list[dict] = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": seed},
    ]

    pairs: list[tuple[str, str]] = []

    console.print()
    console.rule(style="dim")
    console.print(
        f"  Remembering [bold]{name}[/bold] — {relationship}",
        style="dim",
    )
    console.print(
        "  Type [bold]skip[/bold] to skip a question, "
        "[bold]done[/bold] to finish early.",
        style="dim",
    )
    console.rule(style="dim")
    console.print()

    while True:
        # Ask the model for the next question
        reply = llm.chat(messages, cfg)

        if "[INTERVIEW COMPLETE]" in reply:
            break

        _print_model(reply)

        # Get user's answer
        answer = Prompt.ask("[dim]>[/dim]").strip()

        if answer.lower() == "done":
            pairs.append((reply, "[done]"))
            console.print()
            console.print("Thank you for sharing this.", style="dim italic")
            break

        if answer.lower() == "skip":
            pairs.append((reply, "[skipped]"))
            messages.append({"role": "assistant", "content": reply})
            messages.append({"role": "user", "content": "skip"})
            continue

        pairs.append((reply, answer))
        messages.append({"role": "assistant", "content": reply})
        messages.append({"role": "user", "content": answer})

    console.print()
    return pairs

"""
ofrenda CLI — three commands: new, list, show.
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.markdown import Markdown
from rich.prompt import Prompt

from ofrenda import interview, writer
from ofrenda.config import load_config
from ofrenda.llm import OllamaError

app = typer.Typer(
    name="ofrenda",
    help="Remember someone, quietly.",
    add_completion=False,
    no_args_is_help=True,
)
console = Console()
err_console = Console(stderr=True, style="bold red")


def _handle_ollama_error(e: OllamaError) -> None:
    err_console.print(f"\n{e}\n")
    raise typer.Exit(code=1)


@app.command()
def new(
    model: Optional[str] = typer.Option(
        None, "--model", "-m", help="Override the Ollama model (e.g. gemma3:1b)."
    ),
) -> None:
    """Start a new remembrance interview."""
    cfg = load_config(model_override=model)

    console.print()
    console.print("[bold]ofrenda[/bold]", style="dim")
    console.print("A quiet place to remember someone.", style="dim")
    console.print()

    name = Prompt.ask("Who are you remembering").strip()
    if not name:
        err_console.print("A name is required.")
        raise typer.Exit(code=1)

    relationship = Prompt.ask("How did you know them").strip()
    if not relationship:
        err_console.print("A relationship is required.")
        raise typer.Exit(code=1)

    try:
        pairs = interview.run_interview(name, relationship, cfg)
    except OllamaError as e:
        _handle_ollama_error(e)
        return

    if not pairs:
        console.print("No answers recorded. Nothing was saved.", style="dim")
        raise typer.Exit()

    try:
        out_dir = writer.save(name, relationship, pairs, cfg)
    except OllamaError as e:
        _handle_ollama_error(e)
        return

    console.print()
    console.print(f"Saved to [bold]{out_dir}[/bold]", style="green")
    console.print(f"  {out_dir / 'remembrance.md'}", style="dim")
    console.print(f"  {out_dir / 'ofrenda.md'}", style="dim")
    console.print()


@app.command("list")
def list_remembrances(
    data_dir: Optional[str] = typer.Option(None, "--data-dir", help="Path to ofrendas folder.")
) -> None:
    """List all saved remembrances."""
    cfg = load_config()
    if data_dir:
        cfg.data_dir = Path(data_dir)

    base = cfg.data_dir
    if not base.exists():
        console.print("No remembrances saved yet.", style="dim")
        raise typer.Exit()

    entries = sorted(
        d for d in base.iterdir()
        if d.is_dir() and (d / "remembrance.md").exists()
    )

    if not entries:
        console.print("No remembrances saved yet.", style="dim")
        raise typer.Exit()

    console.print()
    for entry in entries:
        # Read the first non-empty, non-header line as a preview
        text = (entry / "remembrance.md").read_text(encoding="utf-8")
        lines = [l for l in text.splitlines() if l.strip() and not l.startswith("#")]
        preview = lines[0][:72] + "…" if lines else ""
        console.print(f"[bold]{entry.name}[/bold]")
        console.print(f"  {preview}", style="dim")
    console.print()


@app.command()
def show(
    name: str = typer.Argument(..., help="The slug or name of the person."),
    data_dir: Optional[str] = typer.Option(None, "--data-dir"),
) -> None:
    """Print a saved remembrance."""
    cfg = load_config()
    if data_dir:
        cfg.data_dir = Path(data_dir)

    from ofrenda.writer import _slug
    slug = _slug(name)
    person_dir = cfg.data_dir / slug

    if not person_dir.exists():
        # Try treating the argument as a literal folder name
        person_dir = cfg.data_dir / name

    remembrance = person_dir / "remembrance.md"
    ofrenda_file = person_dir / "ofrenda.md"

    if not remembrance.exists():
        err_console.print(
            f"No remembrance found for '{name}'.\n"
            f"Run `ofrenda list` to see what's saved."
        )
        raise typer.Exit(code=1)

    console.print()
    console.print(Markdown(remembrance.read_text(encoding="utf-8")))

    if ofrenda_file.exists():
        console.print()
        console.print(Markdown(ofrenda_file.read_text(encoding="utf-8")))

    console.print()


if __name__ == "__main__":
    app()

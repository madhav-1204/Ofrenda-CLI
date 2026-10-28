"""
Configuration: model name, data folder, and optional ~/.ofrenda.toml overrides.
"""
from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

_CONFIG_FILE = Path.home() / ".ofrenda.toml"
_DEFAULT_MODEL = "gemma3:4b"
_DEFAULT_DATA_DIR = Path("ofrendas")
_DEFAULT_OLLAMA_URL = "http://localhost:11434"


@dataclass
class Config:
    model: str = _DEFAULT_MODEL
    data_dir: Path = field(default_factory=lambda: _DEFAULT_DATA_DIR)
    ollama_url: str = _DEFAULT_OLLAMA_URL

    def ofrenda_dir(self, person_slug: str) -> Path:
        return self.data_dir / person_slug


def load_config(model_override: str | None = None) -> Config:
    """
    Load config from ~/.ofrenda.toml (if it exists), then apply any
    CLI-level overrides. Missing keys fall back to defaults silently.
    """
    cfg = Config()

    if _CONFIG_FILE.exists():
        with open(_CONFIG_FILE, "rb") as fh:
            data = tomllib.load(fh)
        cfg.model = data.get("model", cfg.model)
        cfg.ollama_url = data.get("ollama_url", cfg.ollama_url)
        if "data_dir" in data:
            cfg.data_dir = Path(data["data_dir"])

    # Env var is a convenience escape hatch (lower priority than CLI flag)
    if not model_override:
        if env_model := os.environ.get("OFRENDA_MODEL"):
            cfg.model = env_model

    # CLI flag wins over everything
    if model_override:
        cfg.model = model_override

    return cfg

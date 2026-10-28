"""Tests for config loading."""
import os
import textwrap
from pathlib import Path

import pytest

from ofrenda.config import Config, load_config, _DEFAULT_MODEL, _DEFAULT_DATA_DIR


def test_defaults():
    cfg = Config()
    assert cfg.model == _DEFAULT_MODEL
    assert cfg.data_dir == _DEFAULT_DATA_DIR
    assert "11434" in cfg.ollama_url


def test_model_override():
    cfg = load_config(model_override="gemma3:1b")
    assert cfg.model == "gemma3:1b"


def test_env_var_override(monkeypatch):
    monkeypatch.setenv("OFRENDA_MODEL", "llama3.2:3b")
    cfg = load_config()
    assert cfg.model == "llama3.2:3b"


def test_cli_flag_beats_env(monkeypatch):
    monkeypatch.setenv("OFRENDA_MODEL", "llama3.2:3b")
    cfg = load_config(model_override="gemma3:4b")
    assert cfg.model == "gemma3:4b"


def test_toml_file(tmp_path, monkeypatch):
    toml = tmp_path / ".ofrenda.toml"
    toml.write_text(
        textwrap.dedent("""\
        model = "phi4:latest"
        data_dir = "/tmp/my-ofrendas"
        """),
        encoding="utf-8",
    )
    # Patch the config file path
    import ofrenda.config as cfg_module
    monkeypatch.setattr(cfg_module, "_CONFIG_FILE", toml)
    cfg = load_config()
    assert cfg.model == "phi4:latest"
    assert cfg.data_dir == Path("/tmp/my-ofrendas")


def test_ofrenda_dir():
    cfg = Config()
    d = cfg.ofrenda_dir("abuela-rosa")
    assert d == Path("ofrendas") / "abuela-rosa"

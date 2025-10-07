from __future__ import annotations

import json
from pathlib import Path

import pytest

from src import load_config


def test_load_config_reads_yaml(tmp_path: Path) -> None:
    config = tmp_path / "config.yaml"
    config.write_text("version: dev\nmode: paper", encoding="utf-8")

    data = load_config(config)

    assert data["mode"] == "paper"
    assert data["version"] == "dev"


def test_load_config_reads_json(tmp_path: Path) -> None:
    config = tmp_path / "config.json"
    payload = {"version": "dev", "mode": "paper"}
    config.write_text(json.dumps(payload), encoding="utf-8")

    data = load_config(config)

    assert data == payload


def test_load_config_missing_file(tmp_path: Path) -> None:
    missing = tmp_path / "missing.yaml"

    with pytest.raises(FileNotFoundError):
        load_config(missing)


def test_load_config_invalid_extension(tmp_path: Path) -> None:
    config = tmp_path / "config.txt"
    config.write_text("unsupported", encoding="utf-8")

    with pytest.raises(ValueError):
        load_config(config)

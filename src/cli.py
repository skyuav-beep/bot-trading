"""Command-line entry point for local bot-trading workflows."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict

import yaml


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="bot-trading",
        description="Run local helpers for the bot-trading project.",
    )
    parser.add_argument(
        "--config",
        default="configs/dev.yaml",
        help="Path to the runtime configuration file (default: configs/dev.yaml).",
    )
    return parser


def load_config(path: str | Path) -> Dict[str, Any]:
    """Load configuration data from YAML or JSON files."""
    config_path = Path(path)
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    text = config_path.read_text(encoding="utf-8")
    if config_path.suffix in {".yaml", ".yml"}:
        return yaml.safe_load(text) or {}
    if config_path.suffix == ".json":
        return json.loads(text)

    raise ValueError(f"Unsupported config format: {config_path.suffix}")


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    config = load_config(args.config)
    print(f"Loaded config from {args.config}: {config}")
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI execution only
    raise SystemExit(main())

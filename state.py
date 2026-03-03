"""State file for tracking processed episode slugs. Single source of truth (no Drive check)."""

from __future__ import annotations

import json
from pathlib import Path

def _load_state(path: Path) -> list[str]:
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text())
        return data.get("processed", [])
    except (json.JSONDecodeError, OSError):
        return []


def _save_state(path: Path, processed: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"processed": processed}, indent=2) + "\n")


def is_processed(slug: str, state_path: Path | None = None) -> bool:
    """Return True if the episode slug has already been processed."""
    path = state_path
    processed = _load_state(path)
    return slug in processed


def mark_processed(slug: str, state_path: Path | None = None) -> None:
    """Append slug to processed list and persist. Idempotent: same slug not duplicated."""
    path = state_path
    processed = _load_state(path)
    if slug not in processed:
        processed.append(slug)
        _save_state(path, processed)

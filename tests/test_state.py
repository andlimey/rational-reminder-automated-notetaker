"""Tests for state module. Use tmp_path; no Drive checks."""

import json
import pytest
from pathlib import Path

from state import is_processed, mark_processed


def test_is_processed_returns_false_when_file_missing(tmp_path):
    state_file = tmp_path / "processed.json"
    assert is_processed("397", state_path=state_file) is False


def test_is_processed_returns_false_when_file_empty(tmp_path):
    state_file = tmp_path / "processed.json"
    state_file.write_text("{}")
    assert is_processed("397", state_path=state_file) is False


def test_is_processed_returns_true_when_slug_in_state(tmp_path):
    state_file = tmp_path / "processed.json"
    state_file.parent.mkdir(parents=True, exist_ok=True)
    state_file.write_text(json.dumps({"processed": ["397", "396"]}))
    assert is_processed("397", state_path=state_file) is True
    assert is_processed("396", state_path=state_file) is True
    assert is_processed("395", state_path=state_file) is False


def test_mark_processed_persists(tmp_path):
    state_file = tmp_path / "processed.json"
    mark_processed("397", state_path=state_file)
    assert state_file.exists()
    data = json.loads(state_file.read_text())
    assert data["processed"] == ["397"]


def test_mark_processed_idempotent(tmp_path):
    state_file = tmp_path / "processed.json"
    mark_processed("397", state_path=state_file)
    mark_processed("397", state_path=state_file)
    data = json.loads(state_file.read_text())
    assert data["processed"] == ["397"]


def test_mark_processed_appends(tmp_path):
    state_file = tmp_path / "processed.json"
    mark_processed("397", state_path=state_file)
    mark_processed("396", state_path=state_file)
    data = json.loads(state_file.read_text())
    assert data["processed"] == ["397", "396"]

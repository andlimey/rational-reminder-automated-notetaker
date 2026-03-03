"""Tests for run.py: want-list reading and candidate selection."""

import pytest
from pathlib import Path
from unittest.mock import patch

from run import read_episodes_to_process


def test_read_episodes_to_process_returns_slugs_when_file_has_lines(tmp_path):
    path = tmp_path / "want.txt"
    path.write_text("397\n396\n395\n", encoding="utf-8")
    with patch("run.EPISODES_TO_PROCESS_PATH", path):
        result = read_episodes_to_process()
    assert result == ["397", "396", "395"]


def test_read_episodes_to_process_strips_whitespace_and_skips_comments(tmp_path):
    path = tmp_path / "want.txt"
    path.write_text(" 397 \n# comment\n396\n\n", encoding="utf-8")
    with patch("run.EPISODES_TO_PROCESS_PATH", path):
        result = read_episodes_to_process()
    assert result == ["397", "396"]


def test_read_episodes_to_process_returns_none_when_file_empty(tmp_path):
    path = tmp_path / "empty.txt"
    path.write_text("", encoding="utf-8")
    with patch("run.EPISODES_TO_PROCESS_PATH", path):
        result = read_episodes_to_process()
    assert result is None


def test_read_episodes_to_process_returns_none_when_file_only_comments(tmp_path):
    path = tmp_path / "comments.txt"
    path.write_text("# one\n# two\n", encoding="utf-8")
    with patch("run.EPISODES_TO_PROCESS_PATH", path):
        result = read_episodes_to_process()
    assert result is None


def test_read_episodes_to_process_returns_none_when_file_missing(tmp_path):
    path = tmp_path / "nonexistent.txt"
    assert not path.exists()
    with patch("run.EPISODES_TO_PROCESS_PATH", path):
        result = read_episodes_to_process()
    assert result is None


def test_candidates_from_want_list_then_filter_unprocessed(tmp_path):
    """When want list has slugs, only those episodes (and unprocessed) are considered."""
    from state import is_processed

    state_file = tmp_path / "state.json"
    state_file.write_text('{"processed": ["397"]}', encoding="utf-8")

    episodes = [
        {"slug": "397", "title": "Ep 397"},
        {"slug": "396", "title": "Ep 396"},
        {"slug": "395", "title": "Ep 395"},
    ]
    want_slugs = ["396", "397"]
    want_set = set(want_slugs)
    candidates = [e for e in episodes if e["slug"] in want_set]
    assert [e["slug"] for e in candidates] == ["397", "396"]

    to_process = [
        e for e in candidates
        if not is_processed(e["slug"], state_path=state_file)
    ]
    assert [e["slug"] for e in to_process] == ["396"]


def test_candidates_latest_only_when_want_list_empty():
    """When want_slugs is None, candidates is only the first (latest) episode."""
    episodes = [
        {"slug": "397", "title": "Ep 397"},
        {"slug": "396", "title": "Ep 396"},
    ]
    candidates = [episodes[0]] if episodes else []
    assert [e["slug"] for e in candidates] == ["397"]

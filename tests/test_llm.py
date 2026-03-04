"""Tests for LLM notetaker. Mock Gemini client; no real API calls."""

import pytest
from unittest.mock import patch, MagicMock

from llm.notetaker import generate_notes, _build_prompt


def test_build_prompt_includes_title_date_transcript():
    prompt = _build_prompt("Episode 397: Title", "2026-02-19", "Ben Felix: Hello world.", None)
    assert "Episode 397: Title" in prompt
    assert "2026-02-19" in prompt
    assert "Ben Felix: Hello world." in prompt


def test_build_prompt_includes_key_points_when_provided():
    prompt = _build_prompt("Title", "2026-01-01", "Transcript.", ["Point one", "Point two"])
    assert "Point one" in prompt
    assert "Point two" in prompt


def test_build_prompt_includes_episode_url_when_provided():
    url = "https://rationalreminder.ca/podcast/397"
    prompt = _build_prompt("Title", "2026-01-01", "Transcript.", None, episode_url=url)
    assert url in prompt
    assert "Episode URL" in prompt


@patch("llm.notetaker._get_client")
@patch.dict("os.environ", {"RETURN_TEST_NOTES": ""}, clear=False)
def test_generate_notes_returns_mock_response(mock_get_client):
    mock_model = MagicMock()
    mock_model.generate_content.return_value = MagicMock(text="## Summary\n\nGreat episode.")
    mock_get_client.return_value = mock_model

    result = generate_notes(
        title="Test Episode",
        date_ymd="2026-02-19",
        transcript="Host: Hello.",
        api_key="fake-key",
    )
    assert "## Summary" in result
    assert "Great episode" in result
    mock_model.generate_content.assert_called_once()
    call_args = mock_model.generate_content.call_args[0][0]
    assert "Test Episode" in call_args
    assert "2026-02-19" in call_args
    assert "Hello" in call_args


@patch("llm.notetaker._get_client")
@patch.dict("os.environ", {"RETURN_TEST_NOTES": ""}, clear=False)
def test_generate_notes_passes_episode_url_into_prompt(mock_get_client):
    mock_model = MagicMock()
    mock_model.generate_content.return_value = MagicMock(text="## Summary\n\nDone.")
    mock_get_client.return_value = mock_model
    episode_url = "https://rationalreminder.ca/podcast/397"
    generate_notes(
        title="Ep 397",
        date_ymd="2026-02-19",
        transcript="Content here.",
        episode_url=episode_url,
        api_key="fake",
    )
    call_args = mock_model.generate_content.call_args[0][0]
    assert episode_url in call_args


@patch.dict("os.environ", {"RETURN_TEST_NOTES": ""}, clear=False)
def test_generate_notes_empty_transcript_returns_placeholder():
    with patch("llm.notetaker._get_client"):
        result = generate_notes("Title", "2026-01-01", "", api_key="fake")
    assert "No transcript" in result


@patch("llm.notetaker._get_client")
def test_generate_notes_retries_on_rate_limit_then_succeeds(mock_get_client):
    mock_model = MagicMock()
    mock_get_client.return_value = mock_model
    mock_model.generate_content.side_effect = [
        Exception("429 Resource Exhausted"),
        Exception("429 Resource Exhausted"),
        MagicMock(text="## Summary\n\nRetry success."),
    ]
    with patch.dict("os.environ", {"RETURN_TEST_NOTES": ""}, clear=False):
        result = generate_notes("Title", "2026-01-01", "Transcript.", api_key="fake")
    assert "Retry success" in result
    assert mock_model.generate_content.call_count == 3

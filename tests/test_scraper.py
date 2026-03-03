"""Tests for scraper module. Run against fixtures (no live HTTP)."""

import pytest
from pathlib import Path

from scraper.date_utils import parse_date
from scraper.episode import parse_episode_html
from scraper.directory import parse_directory_html, _slug_from_href


FIXTURES_DIR = Path(__file__).parent / "fixtures"


class TestDateUtils:
    """Date parsing and normalization to YYYY-MM-DD."""

    def test_feb_19_2026(self):
        assert parse_date("Feb 19, 2026") == "2026-02-19"

    def test_february_19_2026(self):
        assert parse_date("February 19, 2026") == "2026-02-19"

    def test_jan_1_2026(self):
        assert parse_date("Jan 1, 2026") == "2026-01-01"

    def test_empty_returns_none(self):
        assert parse_date("") is None
        assert parse_date("   ") is None

    def test_invalid_returns_none(self):
        assert parse_date("not a date") is None


class TestEpisodeParser:
    """Episode HTML parsing using fixture episode_397.html."""

    @pytest.fixture
    def episode_html(self):
        path = FIXTURES_DIR / "episode_397.html"
        if not path.exists():
            pytest.skip("Fixture episode_397.html not found")
        return path.read_text(encoding="utf-8")

    def test_parse_from_html_string(self, episode_html):
        data = parse_episode_html(html=episode_html)
        assert "Hendrik Bessembinder" in data["title"]
        assert "Rational Reminder" not in data["title"]
        assert data["date_ymd"] == "2026-02-19"
        assert "Ben Felix:" in data["transcript"]
        assert "Disclaimer" not in data["transcript"]
        assert len(data["key_points"]) >= 1

    def test_parse_from_html_path(self, episode_html):
        path = FIXTURES_DIR / "episode_397.html"
        if not path.exists():
            pytest.skip("Fixture not found")
        data = parse_episode_html(html_path=path)
        assert data["date_ymd"] == "2026-02-19"
        assert data["transcript"].strip()

    def test_no_transcript_returns_empty(self):
        html = """
        <html><head><title>No Transcript Episode</title></head>
        <body><p>January 1, 2025</p>
        <h2>Key Points</h2><p>Nothing.</p>
        <h2>Disclaimer</h2></body></html>
        """
        data = parse_episode_html(html=html)
        assert data["transcript"] == ""
        assert data["title"] == "No Transcript Episode"

    def test_read_the_transcript_lowercase_t(self):
        html = """
        <html><head><title>Old Episode</title></head>
        <body><p>Jan 5, 2019</p>
        <h2>Read the Transcript:</h2>
        <p>Host: Hello world.</p>
        <h2>Disclaimer</h2></body></html>
        """
        data = parse_episode_html(html=html)
        assert "Hello world" in data["transcript"]
        assert data["date_ymd"] == "2019-01-05"


class TestDirectoryParser:
    """Directory parsing (unit tests with inline HTML)."""

    def test_slug_from_href(self):
        assert _slug_from_href("/podcast/397") == "397"
        assert _slug_from_href("https://rationalreminder.ca/podcast/388-x63ds") == "388-x63ds"
        assert _slug_from_href("/podcast/crypto1") == "crypto1"
        assert _slug_from_href("/blog/123") is None

    def test_parse_directory_snippet(self):
        html = """
        <html><body>
        <a href="/podcast/397">Episode 397: Some Title</a>
        <a href="https://rationalreminder.ca/podcast/396">Episode 396: Other</a>
        <a href="/podcast/2024">2024</a>
        </body></html>
        """
        episodes = parse_directory_html(html=html)
        slugs = [e["slug"] for e in episodes]
        assert "397" in slugs
        assert "396" in slugs
        assert "2024" not in slugs  # year-only link text may be excluded by title check

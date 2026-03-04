"""Tests for markdown and filename builder."""

import pytest
from markdown_builder import (
    build_frontmatter,
    build_markdown,
    sanitize_filename,
    markdown_filename,
)


class TestFrontmatter:
    def test_format(self):
        out = build_frontmatter("2026-02-19")
        assert out.startswith("---")
        assert "date: 2026-02-19" in out
        assert "tags:" in out
        assert "- rational_reminder" in out
        assert out.endswith("\n\n")

    def test_build_markdown_includes_frontmatter_and_body(self):
        out = build_markdown("2025-03-05", "## Summary\n\nGood episode.")
        assert "date: 2025-03-05" in out
        assert "tags:" in out
        assert "- rational_reminder" in out
        assert "## Summary" in out

    def test_build_markdown_appends_episode_url_when_provided(self):
        out = build_markdown("2025-03-05", "## Summary\n\nGood.", episode_url="https://rationalreminder.ca/podcast/397")
        assert out.endswith("\n\n---\n\nhttps://rationalreminder.ca/podcast/397")
        assert "## Summary" in out


class TestFilenameSanitization:
    def test_episode_number_prefixed(self):
        name = markdown_filename("397", "Hendrik Bessembinder - Constant Leverage")
        assert name.startswith("397 - ")
        assert name.endswith(".md")

    def test_invalid_chars_replaced(self):
        name = sanitize_filename("Test: Episode * and / or \\", "1", max_length=80)
        assert ":" not in name
        assert "*" not in name
        assert "/" not in name
        assert "\\" not in name

    def test_length_capped(self):
        name = sanitize_filename("A" * 200, "1", max_length=20)
        assert len(name) <= 20 + 5  # 1 -  + ... possible

    def test_markdown_filename_has_md_suffix(self):
        name = markdown_filename("397", "Some Title")
        assert name.endswith(".md")

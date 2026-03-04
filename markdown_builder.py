"""Build markdown with YAML frontmatter and sanitize filenames for Drive/filesystem."""

from __future__ import annotations

import re
from pathlib import Path

# Characters invalid in filenames (Windows/Drive): / \ : * ? " < > |
INVALID_FILENAME_CHARS = re.compile(r'[/\\:*?"<>|]')
DEFAULT_MAX_FILENAME_LEN = 100


def build_frontmatter(date_ymd: str) -> str:
    """Return YAML frontmatter block with date and tags. date_ymd must be YYYY-MM-DD."""
    return f"---\ndate: {date_ymd}\ntags:\n  - rational_reminder\n---\n\n"


def sanitize_filename(title: str, episode_slug: str, max_length: int = DEFAULT_MAX_FILENAME_LEN) -> str:
    """Sanitize title for use as filename; prefix with episode slug. Returns name without .md."""
    # Remove invalid chars, collapse spaces
    cleaned = INVALID_FILENAME_CHARS.sub(" ", title)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    if not cleaned:
        cleaned = f"Episode {episode_slug}"
    else:
        cleaned = f"{episode_slug} - {cleaned}"
    if len(cleaned) > max_length:
        cleaned = cleaned[: max_length - 3].rstrip() + "..."
    return cleaned


def build_markdown(date_ymd: str, body: str, episode_url: str | None = None) -> str:
    """Full markdown content: frontmatter + body; optionally append --- and episode URL."""
    out = build_frontmatter(date_ymd) + body
    if episode_url:
        out += "\n\n---\n\n" + episode_url
    return out


def markdown_filename(episode_slug: str, title: str, max_length: int = DEFAULT_MAX_FILENAME_LEN) -> str:
    """Return the final filename including .md extension."""
    base = sanitize_filename(title, episode_slug, max_length)
    return f"{base}.md" if not base.endswith(".md") else base

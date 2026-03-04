"""Parse Rational Reminder episode page: title, date, key points, transcript."""

from __future__ import annotations

import re
import time

import requests
from bs4 import BeautifulSoup

from scraper.date_utils import parse_date

USER_AGENT = "RationalReminderNotetaker/1.0 (personal automation)"


def _extract_title(soup: BeautifulSoup) -> str:
    """Title from <title> or first h1, strip ' — Rational Reminder' suffix."""
    title_tag = soup.find("title")
    if title_tag and title_tag.get_text(strip=True):
        title = title_tag.get_text(strip=True)
    else:
        h1 = soup.find("h1")
        title = h1.get_text(strip=True) if h1 else ""
    # Strip suffix
    for suffix in (" — Rational Reminder", " - Rational Reminder"):
        if title.endswith(suffix):
            title = title[: -len(suffix)].strip()
            break
    return title


def _extract_date(soup: BeautifulSoup) -> str | None:
    """Find date on page (e.g. February 19, 2026) and return YYYY-MM-DD."""
    # Common pattern: date in paragraph or near top
    text = soup.get_text()
    # Look for "Month DD, YYYY" or "Month DD YYYY"
    patterns = [
        r"(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}",
        r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4}",
    ]
    for pat in patterns:
        m = re.search(pat, text, re.I)
        if m:
            parsed = parse_date(m.group(0))
            if parsed:
                return parsed
    return None


# "Read the Transcript" with optional colon, flexible whitespace, case-insensitive
TRANSCRIPT_MARKER_RE = re.compile(
    r"Read\s+the\s+Transcript\s*:?\s*",
    re.IGNORECASE,
)

def _extract_transcript(soup: BeautifulSoup) -> str:
    """
    Extract transcript: content after "Read the Transcript" (with optional colon)
    until next ## or disclaimer. Handles casing and whitespace variations.
    """
    text = soup.get_text(separator="\n")
    match = TRANSCRIPT_MARKER_RE.search(text)
    if not match:
        return ""
    chunk = text[match.end() :].lstrip()
    stop_markers = ("\n## ", "\nDisclaimer", "\nIs there an error", "Participate in our Community")
    end = len(chunk)
    for stop in stop_markers:
        pos = chunk.find(stop)
        if pos != -1 and pos < end:
            end = pos
    return chunk[:end].strip()


def _extract_key_points(soup: BeautifulSoup) -> list[str]:
    """Extract key points list if present (Key Points From This Episode)."""
    points = []
    text = soup.get_text(separator="\n")
    for marker in ("Key Points From This Episode:", "Key Points From This Episode"):
        idx = text.find(marker)
        if idx != -1:
            start = idx + len(marker)
            chunk = text[start:].strip()
            # Until "Read The Transcript" or "Read the Transcript"
            for end_marker in ("Read The Transcript:", "Read the Transcript:"):
                pos = chunk.find(end_marker)
                if pos != -1:
                    chunk = chunk[:pos]
            # Parse lines like "(0:01:03) Welcome back..."
            for line in chunk.splitlines():
                line = line.strip()
                if line and (line.startswith("(") or line[0].isdigit() or ":" in line[:20]):
                    points.append(line)
            break
    return points


def parse_episode_html(url: str) -> dict:
    """
    Fetch the given episode page URL and parse.
    Returns dict with keys: title, date_ymd, transcript, key_points.
    transcript and key_points may be empty; date_ymd may be None.
    """
    resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    date_ymd = _extract_date(soup)
    return {
        "title": _extract_title(soup),
        "date_ymd": date_ymd,
        "transcript": _extract_transcript(soup),
        "key_points": _extract_key_points(soup),
    }


def fetch_episode(url: str, delay_seconds: float = 1.0) -> dict:
    """Fetch episode page by URL and parse. Adds a small delay to be polite."""
    time.sleep(delay_seconds)
    return parse_episode_html(url)

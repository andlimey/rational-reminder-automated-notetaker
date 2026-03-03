"""Scrape Rational Reminder podcast directory for episode list."""

from __future__ import annotations

import re
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup

from scraper.date_utils import parse_date

USER_AGENT = "RationalReminderNotetaker/1.0 (personal automation)"

def _get_html(html: str | None, html_path: Path | None, url: str) -> str:
    if html is not None:
        return html
    if html_path is not None and html_path.exists():
        return html_path.read_text(encoding="utf-8", errors="replace")
    resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=30)
    resp.raise_for_status()
    return resp.text


def _slug_from_href(href: str) -> str | None:
    """Extract slug from href like /podcast/397 or /podcast/388-x63ds."""
    if not href or "/podcast/" not in href:
        return None
    href = href.split("?")[0].rstrip("/")
    parts = href.split("/podcast/")
    if len(parts) < 2:
        return None
    return parts[-1].strip() or None


def parse_directory_html(
    html: str | None = None,
    html_path: Path | None = None,
    url: str = "",
) -> list[dict]:
    """
    Parse directory page. Returns list of dicts with keys: slug, title, date_ymd, url.
    Provide one of: html, html_path, or url.
    """
    raw = _get_html(html, html_path, url)
    soup = BeautifulSoup(raw, "html.parser")
    episodes = []
    seen_slugs = set()

    # Find all links to /podcast/...
    for a in soup.find_all("a", href=True):
        href = a.get("href", "")
        slug = _slug_from_href(href)
        if not slug or slug in seen_slugs:
            continue
        title = a.get_text(strip=True)
        # Skip non-episode links (e.g. year anchors)
        if not title or re.match(r"^\d{4}$", title.strip()):
            continue
        # Try to get date from parent list item or nearby text
        date_ymd = None
        parent = a.parent
        if parent:
            parent_text = parent.get_text(separator=" ")
            # e.g. "Feb 19, 2026 Episode 397: ..." or "Jan 1, 2026 ..."
            for part in parent_text.split():
                if re.match(r"^(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)", part, re.I):
                    # Find full date in parent
                    m = re.search(
                        r"(\w+\s+\d{1,2},?\s+\d{4})",
                        parent_text,
                        re.I,
                    )
                    if m:
                        date_ymd = parse_date(m.group(1))
                    break
        full_url = href if href.startswith("http") else f"https://rationalreminder.ca{href}"
        episodes.append({
            "slug": slug,
            "title": title,
            "date_ymd": date_ymd,
            "url": full_url,
        })
        seen_slugs.add(slug)

    # Sort by date descending (newest first) when date available, else keep order
    with_date = [(e, e["date_ymd"] or "") for e in episodes]
    with_date.sort(key=lambda x: x[1], reverse=True)
    return [e for e, _ in with_date]


def fetch_directory_episodes(
    url: str,
    delay_seconds: float = 1.0,
) -> list[dict]:
    """Fetch directory page and return parsed episode list."""
    time.sleep(delay_seconds)
    return parse_directory_html(url=url)

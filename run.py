#!/usr/bin/env python3
"""
Orchestrate: scrape directory -> filter by want list (or latest only) -> filter unprocessed ->
for each: scrape episode -> Gemini notes -> build markdown -> send email -> mark processed.

Want list: data/episodes_to_process.txt (one slug per line). Empty or missing => process latest only.
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

from email_send import send_notes_email
from llm import generate_notes
from markdown_builder import build_markdown, markdown_filename
from scraper import fetch_directory_episodes, fetch_episode
from state import is_processed, mark_processed

load_dotenv()

DIRECTORY_URL = "https://rationalreminder.ca/podcast-directory"
PODCAST_BASE_URL = "https://rationalreminder.ca"
PROCESSED_EPISODES_PATH = Path("data/processed_episodes.json")
EPISODES_TO_PROCESS_PATH = Path("data/episodes_to_process.txt")
DELAY_BETWEEN_EPISODES = 1.5

def read_episodes_to_process() -> list[str] | None:
    """
    Read want-list file: one slug per line (e.g. 1, 2, 3 on separate lines).
    Empty lines and lines starting with # are skipped. Returns list of slugs if file
    exists and has at least one slug; else None (latest-only fallback).
    """
    p = EPISODES_TO_PROCESS_PATH
    if not p.exists():
        return None
    slugs = []
    for line in p.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if s and not s.startswith("#"):
            for part in s.split(","):
                slug = part.strip()
                if slug:
                    slugs.append(slug)
    return slugs if slugs else None

def main() -> None:
    episodes = fetch_directory_episodes(url=DIRECTORY_URL, delay_seconds=1.0)

    want_slugs = read_episodes_to_process()
    if want_slugs is not None and len(want_slugs) > 0:
        want_set = set(want_slugs)
        candidates = [e for e in episodes if e["slug"] in want_set]
    else:
        candidates = [episodes[0]] if episodes else [] # fetches the latest episode only

    to_process = [
        e for e in candidates
        if not is_processed(e["slug"], state_path=PROCESSED_EPISODES_PATH)
    ]
    if not to_process:
        print("No new episodes to process.")
        return

    for ep in to_process:
        slug = ep["slug"]
        episode_url = f"{PODCAST_BASE_URL}/podcast/{slug}"
        print(f"Processing episode {slug}...")
        try:
            data = fetch_episode(episode_url, delay_seconds=DELAY_BETWEEN_EPISODES)
        except Exception as e:
            print(f"  Failed to fetch: {e}")
            continue

        title = data["title"]
        date_ymd = data["date_ymd"]
        transcript = data["transcript"]
        key_points = data.get("key_points") or []

        if not transcript or not transcript.strip():
            print("  No transcript, marking as processed without notes.")
            mark_processed(slug, state_path=PROCESSED_EPISODES_PATH)
            continue

        try:
            notes_body = generate_notes(
                title=title,
                date_ymd=date_ymd,
                transcript=transcript,
                key_points=key_points,
                episode_url=episode_url,
            )
        except Exception as e:
            print(f"  Failed to generate notes: {e}")
            continue

        date_for_frontmatter = date_ymd or "0000-01-01"
        full_md = build_markdown(date_for_frontmatter, notes_body, episode_url=episode_url)
        filename = markdown_filename(slug, title)

        try:
            email_address = os.environ.get("NOTES_EMAIL_TO")
            send_notes_email(content=full_md, filename=filename, receiver_email=email_address)
        except Exception as e:
            print(f"  Failed to send email: {e}")
            continue

        mark_processed(slug, state_path=PROCESSED_EPISODES_PATH)
        print(f"  Sent {filename}")

    print("Done.")


if __name__ == "__main__":
    main()

"""Generate structured notes and key takeaways from episode transcript using Gemini."""

from __future__ import annotations

import os
import time

import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

DEFAULT_MODEL = "gemini-2.5-flash"


def _get_client(api_key: str | None = None):
    api_key = api_key or os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not set in environment or .env")
    genai.configure(api_key=api_key)
    return genai.GenerativeModel(DEFAULT_MODEL)


def _build_prompt(title: str, date_ymd: str | None, transcript: str, key_points: list[str] | None = None) -> str:
    key_points_block = ""
    if key_points:
        key_points_block = "\n\n**Key points from the episode (for reference):**\n" + "\n".join(f"- {p}" for p in key_points[:20])
    return f"""You are helping create concise notes for a podcast listener. Below is the title, date, and full transcript of a Rational Reminder podcast episode.

**Title:** {title}
**Date:** {date_ymd or 'Unknown'}{key_points_block}

**Transcript:**
{transcript[:1000000]}

---

Please write structured notes in markdown with these sections (use ## for section headers):
1. **Summary** - 2-4 sentence summary of the episode.
2. **Key Takeaways** - Bullet list of the main takeaways (5-10 items).
3. **Detailed Notes** - Detailed notes of the episode. You may section it into subtopics.
4. **Topics** - Main topics or themes covered.

Output only the markdown content (no preamble). Use clear, scannable formatting.

After each section header, output a new line."""


def generate_notes(
    title: str,
    date_ymd: str | None,
    transcript: str,
    key_points: list[str] | None = None,
    api_key: str | None = None,
) -> str:
    """
    Call Gemini to generate notes and key takeaways from the transcript.
    Returns markdown string (body only, no frontmatter).
    """
    if os.environ.get("RETURN_TEST_NOTES"):
        return "## Summary\n\nTest"
    if not transcript or not transcript.strip():
        return "*No transcript available for this episode.*"
    prompt = _build_prompt(title, date_ymd, transcript, key_points)
    model = _get_client(api_key)

    max_retries = 5
    last_error = None
    for attempt in range(max_retries):
        try:
            response = model.generate_content(prompt)
            if not response or not response.text:
                return "*Failed to generate notes.*"
            return response.text.strip()
        except Exception as e:
            last_error = e
            msg = str(e).lower()
            if "429" in msg or "resource" in msg or "exhausted" in msg:
                if attempt < max_retries - 1:
                    delay = min(2 ** attempt, 60)
                    time.sleep(delay)
                    continue
            raise
    raise last_error

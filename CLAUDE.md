# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Setup
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Run the pipeline
python run.py

# Run tests
pip install pytest pytest-cov
pytest

# Run a single test file
pytest tests/test_scraper.py

# Run a single test
pytest tests/test_scraper.py::test_function_name
```

## Environment Variables

Copy `.env.example` to `.env`. Required variables:
- `GEMINI_API_KEY` — Google AI Studio key
- `NOTES_EMAIL_TO` — Recipient email address
- `RESEND_API_KEY` — Resend email service key

Optional:
- `RESEND_FROM` — Sender address (defaults to Resend onboarding address)
- `RETURN_TEST_NOTES` — Any value enables test mode (skips real Gemini calls)

## Architecture

The pipeline in `run.py` is the entry point and orchestrates everything:

1. **Scrape** episode list from `rationalreminder.ca/podcast-directory` (`scraper/directory.py`)
2. **Filter** by want-list (`data/episodes_to_process.txt`) or default to latest episode only
3. **Skip** already-processed episodes (`state.py` → `data/processed_episodes.json`)
4. For each episode:
   - **Scrape** episode page for title, date, transcript, key points (`scraper/episode.py`)
   - **Generate** markdown notes via Gemini (`llm/notetaker.py`) — includes retry with exponential backoff on 429s
   - **Format** with YAML frontmatter + source URL footer (`markdown_builder.py`)
   - **Email** as styled HTML body + `.md` attachment via Resend (`email_send.py`)
   - **Mark** episode as processed in state file

## GitHub Actions

Two workflows in `.github/workflows/`:
- **`notetaker-scheduler.yml`** — runs every Monday 09:00 UTC; commits updated `processed_episodes.json`
- **`on-demand-notetaker.yml`** — triggers when `data/episodes_to_process.txt` changes on main; clears the want-list after run

To queue specific episodes for processing, add their slugs to `data/episodes_to_process.txt` and push to main.

## Testing Notes

Tests use HTML fixtures in `tests/fixtures/` and mock all external APIs — no real HTTP or API calls are made during tests.

# Rational Reminder Automated Notetaker

Automatically generates notes from [Rational Reminder](https://rationalreminder.ca/) podcast episodes and emails them to you as markdown attachments.

**Credits.** Podcast content, transcripts, and the Rational Reminder brand are © [Rational Reminder](https://rationalreminder.ca/). This project is an independent tool for personal note-taking and is not affiliated with or endorsed by Rational Reminder or its hosts.

## What it does

1. **Scrapes** the podcast directory and episode pages from rationalreminder.ca
2. **Generates notes** from episode transcripts using Google Gemini
3. **Builds markdown** with YAML frontmatter (date, `rational_reminder` tag)
4. **Sends email** via [Resend](https://resend.com) with the notes attached as a `.md` file
5. **Tracks processed episodes** in `data/processed_episodes.json` so runs only handle new or requested episodes

You can process a **want-list** of episode slugs, or leave the list empty to process only the **latest** episode each run.

## Requirements

- Python 3.9+
- [Gemini API key](https://aistudio.google.com/apikey)
- [Resend](https://resend.com) account and API key (for sending email)

## Setup

1. **Clone and create a virtual environment**

   ```bash
   cd rational-reminder-automated-notetaker
   python3 -m venv .venv
   source .venv/bin/activate   # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Configure environment**

   Copy `.env.example` to `.env` and set:

   | Variable | Required | Description |
   |----------|----------|-------------|
   | `GEMINI_API_KEY` | Yes | From [Google AI Studio](https://aistudio.google.com/apikey) |
   | `NOTES_EMAIL_TO` | Yes | Email address that receives the notes |
   | `RESEND_API_KEY` | Yes | From [Resend API Keys](https://resend.com/api-keys) |
   | `RESEND_FROM` | No | Sender address (default: `onboarding@resend.dev` for testing; use a [verified domain](https://resend.com/domains) in production) |
   | `RETURN_TEST_NOTES` | No | Set to `true` to skip Gemini and return placeholder notes (for development) |

3. **Optional: episode want-list**

   - File: `data/episodes_to_process.txt`
   - One episode slug per line (e.g. `397`, `398`). Lines starting with `#` and empty lines are ignored.
   - If the file is missing or has no slugs, the pipeline processes **only the latest** episode.

## Usage

**Run locally**

```bash
python run.py
```

**Run on a schedule or manually (GitHub Actions)**

The workflow `.github/workflows/weekly-notetaker.yml` runs every **Monday at 09:00 UTC** and can be triggered manually from the Actions tab. Add these repository secrets:

- `GEMINI_API_KEY`
- `NOTES_EMAIL_TO`
- `RESEND_API_KEY`

The workflow commits `data/processed_episodes.json` after a run so the next run skips already-processed episodes.

## Tests

```bash
pip install pytest pytest-cov
pytest
```

## Project layout

- `run.py` — Main pipeline: scrape → filter → notes → email → state
- `email_send.py` — Sends markdown via Resend
- `markdown_builder.py` — Frontmatter and markdown formatting
- `state.py` — Read/write `data/processed_episodes.json`
- `llm/notetaker.py` — Gemini-based note generation (with retries for rate limits)
- `scraper/` — Directory and episode scraping from rationalreminder.ca
- `data/episodes_to_process.txt` — Optional want-list of episode slugs
- `data/processed_episodes.json` — State of processed episodes (created/updated by runs)

## License

This project is licensed under the [MIT License](LICENSE).

"""Send episode notes as email with markdown attached via Resend."""

from __future__ import annotations

import base64
import os
import re

import resend
from dotenv import load_dotenv
from markdown_it import MarkdownIt

load_dotenv()


def _strip_frontmatter(content: str) -> str:
    """Remove leading YAML frontmatter block (---...---) if present."""
    return re.sub(r"^---\n.*?\n---\n+", "", content, count=1, flags=re.DOTALL)


def _build_html_email(content: str, filename: str) -> str:
    """Convert markdown content to a styled HTML email body."""
    body_md = _strip_frontmatter(content)
    md = MarkdownIt(options_update={"linkify": True}).enable("linkify")
    body_html = md.render(body_md)

    return f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
           font-size: 16px; line-height: 1.6; color: #1a1a1a;
           background-color: #f5f5f5; margin: 0; padding: 20px; }}
    .container {{ max-width: 680px; margin: 0 auto; background: #fff;
                  border-radius: 8px; padding: 32px 40px; border: 1px solid #e0e0e0; }}
    .subtitle {{ font-size: 13px; color: #888; margin-bottom: 24px;
                 padding-bottom: 16px; border-bottom: 1px solid #e8e8e8; }}
    h2 {{ font-size: 20px; color: #111; border-bottom: 2px solid #e8e8e8;
          padding-bottom: 6px; margin-top: 28px; margin-bottom: 8px; }}
    ul, ol {{ padding-left: 24px; margin: 0 0 12px 0; }}
    li {{ margin-bottom: 4px; }}
    p {{ margin: 0 0 12px 0; }}
    a {{ color: #2563eb; }}
    hr {{ border: none; border-top: 1px solid #e8e8e8; margin: 24px 0; }}
    code {{ background: #f3f4f6; padding: 2px 5px; border-radius: 3px;
            font-size: 14px; font-family: monospace; }}
  </style>
</head>
<body>
  <div class="container">
    <p class="subtitle">{filename}</p>
    {body_html}
  </div>
</body>
</html>"""


def send_notes_email(
    content: str,
    filename: str,
    receiver_email: str,
) -> None:
    """
    Send an email with the markdown content attached as a file using Resend.
    receiver_email is required.
    """
    if not receiver_email.strip():
        raise ValueError("receiver_email is required")

    api_key = os.environ.get("RESEND_API_KEY")
    if not api_key:
        raise ValueError("RESEND_API_KEY not set")

    from_addr = os.environ.get("RESEND_FROM", "onboarding@resend.dev")
    resend.api_key = api_key

    attachment_content = base64.b64encode(content.encode("utf-8")).decode("ascii")
    params = {
        "from": from_addr,
        "to": [receiver_email],
        "subject": f"Rational Reminder Automated Notetaker: {filename}",
        "text": f"Notes for episode: {filename}",
        "html": _build_html_email(content, filename),
        "attachments": [
            {"content": attachment_content, "filename": filename},
        ],
    }
    resend.Emails.send(params)

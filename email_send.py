"""Send episode notes as email with markdown attached via Resend."""

from __future__ import annotations

import base64
import os

import resend
from dotenv import load_dotenv

load_dotenv()


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
        "attachments": [
            {"content": attachment_content, "filename": filename},
        ],
    }
    resend.Emails.send(params)

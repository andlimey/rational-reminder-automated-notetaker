"""Tests for email send. Mock Resend; no real emails."""

import base64
import os
from unittest.mock import patch

import pytest

from email_send import send_notes_email


@patch("email_send.resend.Emails.send")
def test_send_notes_email_attaches_markdown(mock_send):
    with patch.dict(
        "os.environ",
        {
            "RESEND_API_KEY": "re_test",
            "NOTES_EMAIL_TO": "to@example.com",
        },
        clear=False,
    ):
        content = "---\ndate: 2026-02-19\n---\n\n## Summary\n\nGood."
        filename = "397 - Episode Title.md"
        send_notes_email(content=content, filename=filename, receiver_email="to@example.com")

    mock_send.assert_called_once()
    params = mock_send.call_args[0][0]
    assert params["to"] == ["to@example.com"]
    assert params["subject"] == f"Rational Reminder Automated Notetaker: {filename}"
    assert params["text"] == f"Notes for episode: {filename}"
    assert params["from"] == "onboarding@resend.dev"
    assert len(params["attachments"]) == 1
    att = params["attachments"][0]
    assert att["filename"] == filename
    decoded = base64.b64decode(att["content"]).decode("utf-8")
    assert decoded == content


def test_send_notes_email_raises_without_api_key():
    with patch.dict("os.environ", {"NOTES_EMAIL_TO": "a@b.com", "RESEND_API_KEY": ""}, clear=False):
        with pytest.raises(ValueError, match="RESEND_API_KEY"):
            send_notes_email(content="x", filename="a.md", receiver_email="to@example.com")


def test_send_notes_email_raises_without_recipient():
    with patch.dict("os.environ", {"RESEND_API_KEY": "re_x", "NOTES_EMAIL_TO": ""}, clear=False):
        with pytest.raises(ValueError, match="receiver_email is required"):
            send_notes_email(content="x", filename="a.md", receiver_email="")

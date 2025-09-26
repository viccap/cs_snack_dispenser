from __future__ import annotations

import logging
import mimetypes
import os
import smtplib
from datetime import datetime, timezone
from email.message import EmailMessage
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

from . import selfie_llm, storage

logger = logging.getLogger(__name__)
load_dotenv()

SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
SMTP_FROM = os.getenv("SMTP_FROM")
SMTP_USE_TLS = os.getenv("SMTP_USE_TLS", "true").lower() in {"1", "true", "yes"}
EMAIL_SUBJECT = os.getenv("EMAIL_SUBJECT", "Dein Creative Space Snack-Update")


class EmailConfigurationError(RuntimeError):
    """Raised when SMTP configuration is incomplete."""


def _require(value: Optional[str], name: str) -> str:
    if not value:
        raise EmailConfigurationError(f"Environment variable '{name}' must be set to send emails")
    return value


def _build_email(to_address: str, body: str, attachment: Optional[Path], description: Optional[str]) -> EmailMessage:
    msg = EmailMessage()
    msg["Subject"] = EMAIL_SUBJECT
    msg["From"] = _require(SMTP_FROM, "SMTP_FROM")
    msg["To"] = to_address

    footnote = "\n\n--\nAutomatisch gesendet vom Creative Space Snackbot"
    if description:
        footnote = f"\n\nBeschreibung: {description}{footnote}"

    msg.set_content(body + footnote)

    if attachment and attachment.exists():
        mime_type, _ = mimetypes.guess_type(attachment.name)
        maintype = "application"
        subtype = "octet-stream"
        if mime_type and "/" in mime_type:
            maintype, subtype = mime_type.split("/", 1)
        with open(attachment, "rb") as f:
            msg.add_attachment(
                f.read(),
                maintype=maintype,
                subtype=subtype,
                filename=attachment.name,
            )
    return msg


def _send_email_message(message: EmailMessage) -> None:
    host = _require(SMTP_HOST, "SMTP_HOST")
    username = _require(SMTP_USERNAME, "SMTP_USERNAME")
    password = _require(SMTP_PASSWORD, "SMTP_PASSWORD")

    if SMTP_USE_TLS:
        with smtplib.SMTP(host, SMTP_PORT) as server:
            server.starttls()
            server.login(username, password)
            server.send_message(message)
    else:
        with smtplib.SMTP_SSL(host, SMTP_PORT) as server:
            server.login(username, password)
            server.send_message(message)


def schedule_privacy_email(
    email: str,
    selfie_path: Optional[Path],
    description: Optional[str],
    *,
    send_immediately: bool = True,
) -> str:
    storage.ensure_storage()
    record = storage.queue_email(email=email, selfie_path=selfie_path, description=description)
    logger.info(
        "Queued privacy reminder email",
        extra={
            "record_id": record["id"],
            "email": email,
            "selfie_path": record.get("selfie_path"),
            "send_at": record.get("send_at"),
        },
    )

    if send_immediately:
        success = _dispatch_record(record)
        if not success:
            raise RuntimeError("Instant email dispatch failed; see logs for details")

    return record["send_at"]


def process_due_emails(current_time: Optional[datetime] = None) -> None:
    current_time = current_time or datetime.now(timezone.utc)
    due_records = storage.get_due_emails(current_time)
    if not due_records:
        return

    for record in due_records:
        _dispatch_record(record)


def _dispatch_record(record: dict) -> bool:
    record_id = record.get("id")
    email = record.get("email")
    selfie_path_str = record.get("selfie_path")
    selfie_path = Path(selfie_path_str) if selfie_path_str else None

    try:
        description_text = None
        email_body = "Hallo!"  # fallback minimal message
        if selfie_path and selfie_path.exists():
            description_text, email_body = selfie_llm.llm_email_main(str(selfie_path))

        message = _build_email(email, email_body, selfie_path, description_text)
        _send_email_message(message)
        storage.mark_email_sent(record_id, email_body=email_body, description=description_text)
        logger.info("Sent privacy reminder email", extra={"record_id": record_id, "email": email})
        return True
    except Exception as exc:  # pragma: no cover - defensive
        logger.exception("Failed to send privacy email", extra={"record_id": record_id})
        storage.mark_email_failed(record_id, reason=str(exc))
        return False

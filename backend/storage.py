from __future__ import annotations

import base64
import json
import os
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Optional

SELFIE_DIR = Path(__file__).resolve().parent / "storage" / "selfies"
SELFIE_DIR.mkdir(parents=True, exist_ok=True)

EMAIL_QUEUE_FILE = Path(__file__).resolve().parent / "storage" / "email_queue.json"


def _selfie_filename(extension: str) -> Path:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f")
    return SELFIE_DIR / f"selfie_{timestamp}.{extension}"


def save_selfie_from_data_url(data_url: str) -> Path:
    """Persist the selfie from a base64 data URL, return the file path."""
    header, _, encoded = data_url.partition(",")
    if not encoded:
        raise ValueError("Invalid data URL provided for selfie")

    extension = "png" if "png" in header else "jpeg"
    target_path = _selfie_filename(extension)

    with open(target_path, "wb") as f:
        f.write(base64.b64decode(encoded))

    return target_path


def save_selfie_bytes(data: bytes, mime_type: Optional[str] = None) -> Path:
    """Persist a selfie provided as raw bytes (e.g., from Streamlit camera input)."""
    if not data:
        raise ValueError("No selfie data provided")

    extension = "png"
    if mime_type and "/" in mime_type:
        candidate = mime_type.split("/")[-1].lower()
        if candidate in {"png", "jpg", "jpeg"}:
            extension = "jpg" if candidate == "jpeg" else candidate

    target_path = _selfie_filename(extension)
    with open(target_path, "wb") as f:
        f.write(data)
    return target_path


def ensure_storage() -> None:
    """Guarantee that storage directories exist."""
    os.makedirs(SELFIE_DIR, exist_ok=True)
    EMAIL_QUEUE_FILE.parent.mkdir(parents=True, exist_ok=True)


def _load_email_queue_raw() -> List[Dict]:
    if not EMAIL_QUEUE_FILE.exists():
        return []
    try:
        data = json.loads(EMAIL_QUEUE_FILE.read_text())
    except json.JSONDecodeError:
        return []
    if isinstance(data, list):
        return data
    return []


def _normalize_iso(value: Optional[str], *, default: Optional[datetime] = None) -> str:
    if not value:
        dt = default or datetime.now(timezone.utc)
    else:
        try:
            dt = datetime.fromisoformat(value)
        except ValueError:
            dt = default or datetime.now(timezone.utc)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat()


def _normalize_record(record: Dict) -> Dict:
    record.setdefault("id", str(uuid.uuid4()))
    record.setdefault("status", "pending")
    record.setdefault("sent_at", None)
    record.setdefault("email_body", None)
    record.setdefault("llm_description", record.get("llm_description"))
    # Backward compatibility: ensure datetime fields exist
    now = datetime.now(timezone.utc)
    record["queued_at"] = _normalize_iso(record.get("queued_at"), default=now)
    record["send_at"] = _normalize_iso(record.get("send_at"), default=now)
    sent_at = record.get("sent_at")
    if sent_at:
        record["sent_at"] = _normalize_iso(sent_at)
    failed_at = record.get("failed_at")
    if failed_at:
        record["failed_at"] = _normalize_iso(failed_at)
    return record


def load_email_queue() -> List[Dict]:
    return [_normalize_record(rec) for rec in _load_email_queue_raw()]


def save_email_queue(records: List[Dict]) -> None:
    EMAIL_QUEUE_FILE.write_text(json.dumps(records, indent=2))


def queue_email(email: str, selfie_path: Optional[Path], description: Optional[str]) -> Dict:
    ensure_storage()
    now = datetime.now(timezone.utc)
    send_at = now

    queue_record = _normalize_record(
        {
            "id": str(uuid.uuid4()),
            "email": email,
            "selfie_path": str(selfie_path) if selfie_path else None,
            "llm_description": description,
            "email_body": None,
            "queued_at": now.isoformat(),
            "send_at": send_at.isoformat(),
            "status": "pending",
            "sent_at": None,
        }
    )

    records = load_email_queue()
    records.append(queue_record)
    save_email_queue(records)

    return queue_record


def get_due_emails(current_time: Optional[datetime] = None) -> List[Dict]:
    current_time = current_time or datetime.now(timezone.utc)
    records = load_email_queue()
    due: List[Dict] = []
    for record in records:
        send_at = None
        send_at_iso = record.get("send_at")
        if send_at_iso:
            try:
                send_at = datetime.fromisoformat(send_at_iso)
            except ValueError:
                send_at = None
            if send_at and send_at.tzinfo is None:
                send_at = send_at.replace(tzinfo=timezone.utc)
        if record.get("status") == "pending" and send_at and send_at <= current_time:
            due.append(record)
    return due


def mark_email_sent(record_id: str, email_body: Optional[str], description: Optional[str]) -> None:
    records = load_email_queue()
    updated = False
    for record in records:
        if record.get("id") == record_id:
            record["status"] = "sent"
            record["sent_at"] = datetime.now(timezone.utc).isoformat()
            if email_body:
                record["email_body"] = email_body
            if description:
                record["llm_description"] = description
            updated = True
            break
    if updated:
        save_email_queue(records)


def mark_email_failed(record_id: str, reason: str) -> None:
    records = load_email_queue()
    updated = False
    for record in records:
        if record.get("id") == record_id:
            record["status"] = "failed"
            record["error"] = reason
            record["failed_at"] = datetime.now(timezone.utc).isoformat()
            updated = True
            break
    if updated:
        save_email_queue(records)

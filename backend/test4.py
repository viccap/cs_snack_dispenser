"""Igloohome OTP helper used by the cs_lock_app backend.

This module fetches an OAuth access token with the provided client credentials
and requests a one-time PIN for the configured device. It exposes the
``generate_one_time_pin`` function which the FastAPI endpoint invokes when the
user completes the consent/selfie flow in the UI.
"""
from __future__ import annotations

import base64
import json
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

import requests
from dotenv import load_dotenv

AUTH_URL = "https://auth.igloohome.co/oauth2/token"
API_BASE_URL = "https://api.igloodeveloper.co"
DEFAULT_ACCESS_NAME = "Maintenance guy"
DEFAULT_VARIANCE = 1
DEFAULT_TZ_OFFSET = 0

load_dotenv()


class IglooConfigError(RuntimeError):
    """Raised when required configuration is missing."""


class IglooRequestError(RuntimeError):
    """Raised when the Igloohome API returns an unexpected response."""


def _next_top_of_hour(tz_offset_hours: int) -> str:
    """Return startDate string formatted as required by the Igloohome API."""
    if not (-12 <= tz_offset_hours <= 14):
        raise ValueError("tz_offset_hours must be between -12 and 14 hours inclusive")

    now_utc = datetime.now(timezone.utc)
    next_hour_utc = (
        now_utc.replace(minute=0, second=0, microsecond=0)
        + timedelta(hours=1)
        if now_utc.minute or now_utc.second or now_utc.microsecond
        else now_utc
    )

    tz = timezone(timedelta(hours=tz_offset_hours))
    start_local = next_hour_utc.astimezone(tz)

    offset_total_minutes = tz_offset_hours * 60
    sign = "+" if offset_total_minutes >= 0 else "-"
    hh = abs(offset_total_minutes) // 60
    mm = abs(offset_total_minutes) % 60
    offset_str = f"{sign}{hh:02d}:{mm:02d}"

    return f"{start_local.strftime('%Y-%m-%dT%H')}:00:00{offset_str}"


def _get_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise IglooConfigError(f"Environment variable '{name}' is required")
    return value


def _fetch_access_token(client_id: str, client_secret: str) -> Dict[str, Any]:
    credentials = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    response = requests.post(
        AUTH_URL,
        headers={
            "Authorization": f"Basic {credentials}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        data={
            "grant_type": "client_credentials",
        },
        timeout=15,
    )
    try:
        response.raise_for_status()
    except requests.HTTPError as exc:  # pragma: no cover - defensive
        raise IglooRequestError(f"Failed to obtain access token: {exc}") from exc

    payload = response.json()
    if "access_token" not in payload:
        raise IglooRequestError("Igloohome token response missing 'access_token'")
    return payload


def _request_one_time_pin(
    access_token: str,
    device_id: str,
    variance: int,
    start_date: str,
    access_name: str,
) -> Dict[str, Any]:
    if len(access_name) > 60:
        raise ValueError("accessName can contain up to 60 characters.")
    if not (1 <= variance <= 5):
        raise ValueError("For One-Time (OTP), 'variance' must be between 1 and 5 inclusive.")

    response = requests.post(
        f"{API_BASE_URL}/igloohome/devices/{device_id}/algopin/onetime",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        json={
            "variance": variance,
            "startDate": start_date,
            "accessName": access_name,
        },
        timeout=30,
    )
    try:
        response.raise_for_status()
    except requests.HTTPError as exc:  # pragma: no cover - defensive
        raise IglooRequestError(f"Failed to generate OTP: {exc}") from exc

    return response.json()


def generate_one_time_pin(
    *,
    access_name: Optional[str] = None,
    variance: int = DEFAULT_VARIANCE,
    tz_offset_hours: int = DEFAULT_TZ_OFFSET,
) -> Dict[str, Any]:
    print("generating one time pin...")
    """Generate a one-time pin and return the API payload.

    Returns a dictionary with the following keys:
    - ``code``: the OTP provided by Igloohome (if any)
    - ``token``: metadata from the OAuth token request
    - ``raw``: raw response payload from the OTP endpoint
    """

    client_id = _get_env("IGLOO_CLIENT_ID")
    client_secret = _get_env("IGLOO_CLIENT_SECRET")
    device_id = _get_env("IGLOO_DEVICE_ID")

    token_payload = _fetch_access_token(client_id, client_secret)
    print("fetched access token... ", token_payload)
    access_token = token_payload["access_token"]

    start_date = _next_top_of_hour(tz_offset_hours)
    response_payload = _request_one_time_pin(
        access_token=access_token,
        device_id=device_id,
        variance=variance,
        start_date=start_date,
        access_name=access_name or DEFAULT_ACCESS_NAME,
    )
    print("requested one time pin... ", response_payload)
    code = response_payload.get("pin")
    if not code:
        raise IglooRequestError("Igloohome response did not include an OTP code")

    return code


def main() -> None:
    result = generate_one_time_pin()
    print(result)


if __name__ == "__main__":
    main()

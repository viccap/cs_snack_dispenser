from __future__ import annotations

import base64
import os
from typing import Tuple

import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("LLM_API_KEY")
BASE_URL = os.getenv("LLM_BASE_URL", "https://chat-ai.academiccloud.de/v1")
MODEL_WITH_IMAGE = os.getenv("LLM_IMAGE_MODEL", "internvl2.5-8b")
MODEL_EMAIL = os.getenv("LLM_EMAIL_MODEL", "openai-gpt-oss-120b")



class LLMConfigurationError(RuntimeError):
    """Raised when required environment variables are missing."""


def _require_api_key() -> str:
    if not API_KEY:
        raise LLMConfigurationError("LLM_API_KEY must be set in the environment to send emails")
    return API_KEY


def encode_image_to_data_uri(image_path: str) -> str:
    """Reads an image file, encodes to base64, returns a data URI string."""
    with open(image_path, "rb") as f:
        img_bytes = f.read()
    b64 = base64.b64encode(img_bytes).decode("utf-8")
    return f"data:image/jpeg;base64,{b64}"


def _post_completion(payload: dict) -> dict:
    headers = {
        "Authorization": f"Bearer {_require_api_key()}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    response = requests.post(f"{BASE_URL}/chat/completions", json=payload, headers=headers, timeout=60)
    response.raise_for_status()
    return response.json()


def describe_person_from_selfie(image_path: str) -> dict:
    image_data_uri = encode_image_to_data_uri(image_path)
    messages = [
        {
            "role": "system",
            "content": (
                "You always write from a you perspective. You are a sentient snack assistant "
                "that describes people in images in a friendly, non-sensitive way after they tried "
                "one of your snacks and adds a friendly compliment."
            ),
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": (
                        "Please describe the person in this image: hair color, approximate age, clothing, "
                        "visible accessories, expression. Add a friendly compliment and say at the end I "
                        "hope you liked the snack from the creative space."
                    ),
                },
                {"type": "image_url", "image_url": {"url": image_data_uri}},
            ],
        },
    ]

    payload = {
        "model": MODEL_WITH_IMAGE,
        "messages": messages,
        "temperature": 0.8,
        "top_p": 0.8,
    }

    return _post_completion(payload)


def formulate_email(description: str) -> dict:
    messages = [
        {
            "role": "system",
            "content": (
                "You are a helpful snack machine that writes short, friendly emails in German to users "
                "who have just used a snack from the 'Creative Space'. You are provided a description of a "
                "person. The email should include elements of the description like their clothing for "
                "example. The email should be polite. Make sure to include a friendly compliment based on "
                "the description. End the email by saying that you know a lot about them from the form they "
                "filled out but that their image and secrets are safe with the snack machine. The output "
                "should only include the email, nothing else. Use 'DU' form, start with 'Hallo!', and keep "
                "it under 150 words."
            ),
        },
        {
            "role": "user",
            "content": [{"type": "text", "text": description}],
        },
    ]

    payload = {
        "model": MODEL_EMAIL,
        "messages": messages,
        "temperature": 0.8,
        "top_p": 0.8,
    }

    return _post_completion(payload)


def _extract_message_content(response: dict) -> str:
    try:
        return response["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError, TypeError) as exc:  # pragma: no cover - defensive
        raise RuntimeError(f"Unexpected LLM response format: {response}") from exc


def llm_email_main(img_path: str) -> Tuple[str, str]:
    """Return (description_text, email_text) generated from the selfie image."""
    description_result = describe_person_from_selfie(img_path)
    description_text = _extract_message_content(description_result)

    email_result = formulate_email(description_text)
    email_text = _extract_message_content(email_result)

    return description_text, email_text

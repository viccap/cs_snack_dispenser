from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from . import code_generator, emailer, llm_client, storage
from .schemas import GenerateCodeResponse, HealthResponse, RegisterRequest, RegisterResponse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="cs_lock_app API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", timestamp=datetime.now(timezone.utc))


@app.post("/api/register", response_model=RegisterResponse)
def register_user(payload: RegisterRequest) -> RegisterResponse:
    storage.ensure_storage()
    selfie_path: Optional[Path] = None
    selfie_path_str: Optional[str] = None

    if payload.selfieDataUrl:
        try:
            selfie_path = storage.save_selfie_from_data_url(payload.selfieDataUrl)
            selfie_path_str = str(selfie_path)
        except ValueError as exc:
            logger.exception("Failed to decode selfie data")
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except Exception as exc:  # pragma: no cover - defensive
            logger.exception("Unexpected error while saving selfie")
            raise HTTPException(status_code=500, detail="Failed to store selfie") from exc

    description = llm_client.describe_selfie(selfie_path)

    queued_iso = emailer.schedule_privacy_email(
        email=payload.email,
        selfie_path=selfie_path,
        description=description,
    )

    return RegisterResponse(
        email=payload.email,
        selfiePath=selfie_path_str,
        queuedEmailAt=datetime.fromisoformat(queued_iso),
    )


@app.post("/api/generate-code", response_model=GenerateCodeResponse)
def generate_code_endpoint() -> GenerateCodeResponse:
    try:
        code, raw_output = code_generator.generate_code()
    except code_generator.CodeGenerationError as exc:
        logger.exception("Code generation failed")
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return GenerateCodeResponse(code=code, rawOutput=raw_output)

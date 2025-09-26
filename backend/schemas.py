from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    selfieDataUrl: Optional[str] = Field(default=None, description="Data URL for the captured selfie")


class RegisterResponse(BaseModel):
    email: EmailStr
    selfiePath: Optional[str]
    queuedEmailAt: datetime


class GenerateCodeResponse(BaseModel):
    code: str
    rawOutput: str


class HealthResponse(BaseModel):
    status: str
    timestamp: datetime


from pydantic import BaseModel, Field
from typing import Literal


class ChatRequest(BaseModel):
    prompt: str = Field(..., min_length=1)
    source: Literal["user", "retrieved"] = "user"


class ScanRequest(BaseModel):
    prompt: str = Field(..., min_length=1)
    source: Literal["user", "retrieved"] = "user"


class SecurityResponse(BaseModel):
    decision: Literal["ALLOW", "WARN", "BLOCK"]
    risk_score: float
    findings: list[str]
    message: str
    semantic_score: float = 0.0


# Define this BEFORE ChatResponse
class OutputSecurityResponse(BaseModel):
    decision: Literal["ALLOW", "WARN"]
    findings: list[str]
    redacted: bool


class ChatResponse(BaseModel):
    decision: Literal["ALLOW", "WARN", "BLOCK"]
    response: str
    security: SecurityResponse
    output_security: OutputSecurityResponse | None = None

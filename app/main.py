from app.security.output_inspector import inspect_output
from fastapi import FastAPI, HTTPException

from app.schemas import (
    ChatRequest,
    ScanRequest,
    ChatResponse,
    SecurityResponse
)

from app.security.pipeline import inspect_prompt
from app.llm.ollama_client import (
    generate_response,
    OllamaError
)


app = FastAPI(
    title="AI Middleware for LLM Security",
    description="Security gateway for protecting LLM applications",
    version="1.0.0"
)


@app.get("/")
def home():
    return {
        "project": "AI Middleware for LLM Security",
        "status": "running",
        "message": "Welcome to the AI Security Middleware API",
        "documentation": "/docs",
        "available_endpoints": [
            "/health",
            "/scan",
            "/chat"
        ]
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "AI Middleware",
        "version": "1.0.0",
        "llm": "Ollama - Qwen2.5 1.5B"
    }


@app.post("/scan", response_model=SecurityResponse)
def scan_prompt(request: ScanRequest):

    result = inspect_prompt(
        request.prompt,
        request.source
    )

    return result


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):

    # STEP 1: Inspect the incoming prompt
    security_result = inspect_prompt(
        request.prompt,
        request.source
    )

    # STEP 2: Block high-risk prompts
    if security_result.decision == "BLOCK":
        return ChatResponse(
            decision="BLOCK",
            response="Request blocked by security middleware.",
            security=security_result
        )

    # STEP 3: Stop suspicious prompts
    if security_result.decision == "WARN":
        return ChatResponse(
            decision="WARN",
            response=(
                "Request requires security review. "
                "It was not forwarded to the language model."
            ),
            security=security_result
        )

    # STEP 4: Generate a response using local Ollama
    try:
        llm_response = await generate_response(
            request.prompt
        )

    except OllamaError as error:
        raise HTTPException(
            status_code=503,
            detail=str(error)
        )

    # STEP 5: Inspect the generated response
    output_result = inspect_output(llm_response)

    # STEP 6: Return only the sanitized response
    return ChatResponse(
        decision=output_result["decision"],
        response=output_result["response"],
        security=security_result,
        output_security={
            "decision": output_result["decision"],
            "findings": output_result["findings"],
            "redacted": output_result["redacted"]
        }
    )

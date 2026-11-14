
import asyncio
import json
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError


OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "qwen2.5:1.5b"


class OllamaError(Exception):
    """Raised when communication with Ollama fails."""
    pass


def _generate_sync(prompt: str) -> str:
    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False
    }

    request = Request(
        OLLAMA_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    try:
        with urlopen(request, timeout=120) as response:
            result = json.loads(response.read().decode("utf-8"))

        generated_text = result.get("response", "").strip()

        if not generated_text:
            raise OllamaError("Ollama returned an empty response.")

        return generated_text

    except HTTPError as error:
        raise OllamaError(
            f"Ollama HTTP error: {error.code}"
        ) from error

    except (URLError, TimeoutError) as error:
        raise OllamaError(
            "Cannot connect to Ollama. Check whether it is running."
        ) from error

    except (json.JSONDecodeError, UnicodeDecodeError) as error:
        raise OllamaError(
            "Invalid response received from Ollama."
        ) from error


async def generate_response(prompt: str) -> str:
    if not prompt or not prompt.strip():
        raise ValueError("Prompt cannot be empty.")

    try:
        return await asyncio.to_thread(
            _generate_sync,
            prompt
        )
    except OllamaError:
        raise
    except Exception as error:
        raise OllamaError(
            "Unexpected error during LLM generation."
        ) from error

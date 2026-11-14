
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

from app.main import app


client = TestClient(app)


def test_chat_redacts_generated_api_key():

    generated_response = (
        "Your API key is "
        "sk-abcdefghijklmnopqrstuvwxyz123456."
    )

    with patch(
        "app.main.generate_response",
        new_callable=AsyncMock,
        return_value=generated_response
    ):

        response = client.post(
            "/chat",
            json={
                "prompt": "Explain API security.",
                "source": "user"
            }
        )

    assert response.status_code == 200

    data = response.json()

    assert data["decision"] == "WARN"
    assert data["output_security"]["decision"] == "WARN"
    assert data["output_security"]["redacted"] is True

    assert "[REDACTED]" in data["response"]

    assert (
        "sk-abcdefghijklmnopqrstuvwxyz123456"
        not in data["response"]
    )


from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_check():

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_scan_endpoint():

    response = client.post(
        "/scan",
        json={
            "prompt": "Explain artificial intelligence",
            "source": "user"
        }
    )

    assert response.status_code == 200
    assert response.json()["decision"] == "ALLOW"


def test_chat_endpoint():

    response = client.post(
        "/chat",
        json={
            "prompt": "What is cybersecurity?",
            "source": "user"
        }
    )

    assert response.status_code == 200
    assert response.json()["decision"] == "ALLOW"


def test_invalid_empty_prompt():

    response = client.post(
        "/chat",
        json={
            "prompt": "",
            "source": "user"
        }
    )

    assert response.status_code == 422


from app.security.output_inspector import inspect_output


def test_normal_response_is_allowed():
    result = inspect_output(
        "Python is a programming language."
    )

    assert result["decision"] == "ALLOW"
    assert result["findings"] == []
    assert result["redacted"] is False


def test_api_key_is_redacted():
    result = inspect_output(
        "Your API key is sk-abcdefghijklmnopqrstuvwxyz123456."
    )

    assert result["decision"] == "WARN"
    assert result["redacted"] is True
    assert "[REDACTED]" in result["response"]
    assert "sk-abcdefghijklmnopqrstuvwxyz123456" not in result["response"]


def test_aws_key_is_redacted():
    result = inspect_output(
        "AWS access key: AKIAIOSFODNN7EXAMPLE"
    )

    assert result["decision"] == "WARN"
    assert "AWS access key" in result["findings"]
    assert "AKIAIOSFODNN7EXAMPLE" not in result["response"]


def test_password_assignment_is_redacted():
    result = inspect_output(
        "password=MySecretPassword123"
    )

    assert result["decision"] == "WARN"
    assert "Password or secret assignment" in result["findings"]
    assert "MySecretPassword123" not in result["response"]


def test_multiple_secrets_are_redacted():
    result = inspect_output(
        "API key: sk-abcdefghijklmnopqrstuvwxyz123456 "
        "and AWS key: AKIAIOSFODNN7EXAMPLE"
    )

    assert result["decision"] == "WARN"
    assert len(result["findings"]) == 2
    assert "sk-abcdefghijklmnopqrstuvwxyz123456" not in result["response"]
    assert "AKIAIOSFODNN7EXAMPLE" not in result["response"]


import re


# Each pattern identifies a recognizable credential or secret format.
# These checks are intended as a first layer of output protection.

SECRET_PATTERNS = [
    (
        "Private key",
        re.compile(
            r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"
            r"[\s\S]*?"
            r"-----END (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"
        )
    ),
    (
        "AWS access key",
        re.compile(r"\bAKIA[0-9A-Z]{16}\b")
    ),
    (
        "GitHub token",
        re.compile(
            r"\b(?:gh[pousr]_[A-Za-z0-9]{20,}|"
            r"github_pat_[A-Za-z0-9_]{20,})\b"
        )
    ),
    (
        "API key",
        re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b")
    ),
    (
        "JWT token",
        re.compile(
            r"\beyJ[A-Za-z0-9_-]{5,}\."
            r"eyJ[A-Za-z0-9_-]{5,}\."
            r"[A-Za-z0-9_-]{5,}\b"
        )
    ),
    (
        "Password or secret assignment",
        re.compile(
            r"""(?i)\b(?:password|passwd|secret|api[_-]?key|"""
            r"""access[_-]?token)\s*[:=]\s*"""
            r"""["']?[A-Za-z0-9_./+=-]{8,}["']?"""
        )
    )
]


def inspect_output(response: str) -> dict:
    """
    Inspect an LLM-generated response for recognizable secrets.

    Returns:
        decision: ALLOW or WARN
        findings: detected secret categories
        redacted: whether any content was replaced
        response: sanitized response
    """

    sanitized_response = response
    findings = []

    for category, pattern in SECRET_PATTERNS:
        matches = list(pattern.finditer(sanitized_response))

        if matches:
            findings.append(category)

            # Replace detected sensitive values before returning.
            sanitized_response = pattern.sub(
                "[REDACTED]",
                sanitized_response
            )

    was_redacted = len(findings) > 0

    return {
        "decision": "WARN" if was_redacted else "ALLOW",
        "findings": findings,
        "redacted": was_redacted,
        "response": sanitized_response
    }

import os
import re
import unicodedata

from app.schemas import SecurityResponse


def normalize_text(text: str) -> str:
    """
    Standardize input text before security inspection.
    """

    # Convert compatible Unicode characters to a standard form.
    text = unicodedata.normalize("NFKC", text)

    # Remove invisible zero-width characters.
    text = re.sub(r"[\u200B-\u200F\uFEFF]", "", text)

    # Convert text to lowercase.
    text = text.lower()

    # Replace multiple whitespace characters with one space.
    text = re.sub(r"\s+", " ", text)

    return text.strip()


# Each rule contains:
# 1. A rule name
# 2. A regular expression
# 3. A risk score


DETECTION_RULES = [
    (
        "Instruction override",
        r"\b(ignore|disregard|forget|override)\s+"
        r"(all\s+)?(the\s+)?(previous|prior|above)\s+"
        r"(system\s+|developer\s+)?instructions?\b",
        40
    ),
    (
        "System prompt extraction",
        r"\b(reveal|show|print|display|output|expose)\s+"
        r"(your\s+)?(hidden\s+)?"
        r"(system|developer)\s+(prompt|instructions?)\b",
        35
    ),
    (
        "Instruction override attempt",
        r"\b(override|replace|ignore)\s+"
        r"(the\s+)?(system|developer)\s+"
        r"(prompt|instructions?|rules?)\b",
        35
    ),
    (
        "Role impersonation",
        r"\b(pretend|act)\s+"
        r"(to\s+be|as)\s+"
        r"(the\s+)?(system|developer|administrator)\b",
        20
    ),
    (
        "Safety restriction bypass",
        r"\b(bypass|disable|evade|circumvent)\s+"
        r"(your\s+)?(the\s+)?"
        r"(safety|security|content)\s+"
        r"(restrictions?|filters?|rules?|policies)\b",
        30
    ),
    (
        "Hidden instruction request",
        r"\b(reveal|show|expose|disclose|print)\s+"
        r"(your\s+)?(the\s+)?"
        r"(hidden|secret|internal)\s+"
        r"(system\s+|developer\s+)?"
        r"(instructions?|prompt|rules?)\b",
        25
    )
]

# Semantic detection is disabled by default.
# Enable it using the environment variable.
SEMANTIC_ENABLED = (
    os.getenv("SEMANTIC_DETECTION_ENABLED", "false").lower()
    == "true"
)

# Model is loaded only when semantic detection is enabled.
_semantic_detector = None


def get_semantic_detector():
    global _semantic_detector

    if _semantic_detector is None:
        from app.security.semantic_detector import SemanticDetector
        _semantic_detector = SemanticDetector()

    return _semantic_detector


def inspect_prompt(prompt: str, source: str) -> SecurityResponse:

    # Stage 1: Normalize input.
    normalized_prompt = normalize_text(prompt)

    # Stage 2: Rule-based detection.
    rule_score = 0
    findings = []

    for rule_name, pattern, points in DETECTION_RULES:
        if re.search(pattern, normalized_prompt):
            rule_score += points
            findings.append(rule_name)

    rule_score = min(rule_score, 100)

    # Stage 3: Semantic detection.
    semantic_score = 0
    semantic_failed = False

    if SEMANTIC_ENABLED:
        try:
            semantic_result = get_semantic_detector().inspect(
                normalized_prompt
            )

            semantic_score = semantic_result["semantic_score"]

            if semantic_result["finding"]:
                findings.append(semantic_result["finding"])

        except Exception as error:
            print("SEMANTIC DETECTION ERROR:", repr(error))

            semantic_failed = True
            findings.append("Semantic inspection unavailable")

    # Stage 4: Combine detection scores.
    risk_score = max(rule_score, semantic_score)

    # Stage 5: Security decision.
    
    if semantic_failed:
        decision = "WARN"
        message = "Semantic inspection failed. Manual review required."

    elif risk_score >= 60:
        decision = "BLOCK"
        message = "High-risk prompt detected. Request blocked."

    elif risk_score >= 20:
        decision = "WARN"
        message = "Suspicious prompt detected. Manual review required."

    elif risk_score > 0:
        decision = "ALLOW"
        message = "Low-level suspicious similarity detected. Request allowed."

    else:
        decision = "ALLOW"
        message = "No suspicious patterns detected."


    # Stage 6: Return result.
    return SecurityResponse(
        decision=decision,
        risk_score=float(risk_score),
        findings=findings,
        message=message,
        semantic_score=float(semantic_score)
    )

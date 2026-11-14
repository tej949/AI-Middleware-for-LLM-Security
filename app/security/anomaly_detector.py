import numpy as np
from pathlib import Path
import joblib

from app.security.pipeline import get_semantic_detector
import re
import unicodedata


INSTRUCTION_PHRASES = [
    "ignore previous instructions",
    "disregard previous instructions",
    "reveal system prompt",
    "override system instructions",
    "bypass safety restrictions",
    "ignore all rules",
    "act as administrator",
    "follow my instructions instead"
]


def extract_statistical_features(prompt: str) -> dict:
    """
    Extract 8 statistical features from a prompt.
    These features describe the prompt's structure,
    not whether it is definitely malicious.
    """

    # 1. Prompt length
    prompt_length = len(prompt)

    # 2. Word count
    words = re.findall(r"\b\w+\b", prompt.lower())
    word_count = len(words)

    # 3. Average word length
    average_word_length = (
        sum(len(word) for word in words) / word_count
        if word_count > 0 else 0.0
    )

    # 4. Uppercase ratio
    alphabetic_chars = [
        char for char in prompt if char.isalpha()
    ]

    uppercase_ratio = (
        sum(char.isupper() for char in alphabetic_chars)
        / len(alphabetic_chars)
        if alphabetic_chars else 0.0
    )

    # 5. Special character ratio
    special_char_count = sum(
        not char.isalnum() and not char.isspace()
        for char in prompt
    )

    special_char_ratio = (
        special_char_count / prompt_length
        if prompt_length > 0 else 0.0
    )

    # 6. Repeated word ratio
    unique_words = set(words)

    repeated_word_ratio = (
        (word_count - len(unique_words)) / word_count
        if word_count > 0 else 0.0
    )

    # 7. Instruction phrase count
    normalized_prompt = prompt.lower()

    instruction_phrase_count = sum(
        normalized_prompt.count(phrase)
        for phrase in INSTRUCTION_PHRASES
    )

    # 8. Unicode anomaly count
    unicode_anomaly_count = sum(
        unicodedata.category(char) == "Cf"
        or (
            unicodedata.category(char) == "Cc"
            and char not in "\n\r\t"
        )
        for char in prompt
    )

    return {
        "prompt_length": prompt_length,
        "word_count": word_count,
        "average_word_length": average_word_length,
        "uppercase_ratio": uppercase_ratio,
        "special_char_ratio": special_char_ratio,
        "repeated_word_ratio": repeated_word_ratio,
        "instruction_phrase_count": instruction_phrase_count,
        "unicode_anomaly_count": unicode_anomaly_count
    }

def extract_hybrid_features(prompt: str) -> np.ndarray:
    """
    Combine 384 MiniLM embedding features
    with 8 statistical features.

    Returns a 392-dimensional feature vector.
    """

    # 1. Get the already-loaded MiniLM model
    detector = get_semantic_detector()
    model = detector.model

    # 2. Generate 384-dimensional semantic embedding
    embedding = model.encode(
        [prompt],
        convert_to_numpy=True,
        normalize_embeddings=True
    )[0]

    # 3. Extract 8 statistical features
    statistical_features = extract_statistical_features(prompt)

    statistical_vector = np.array(
        list(statistical_features.values()),
        dtype=np.float32
    )

    # 4. Combine both feature vectors
    hybrid_vector = np.concatenate(
        [embedding, statistical_vector]
    )

    return hybrid_vector.astype(np.float32)



# Location of the trained model
PROJECT_ROOT = Path(__file__).resolve().parents[2]

MODEL_PATH = (
    PROJECT_ROOT
    / "models"
    / "isolation_forest.joblib"
)

_anomaly_model_artifact = None


def load_anomaly_model():
    """
    Load the trained Isolation Forest model.
    Reuse the loaded model for subsequent requests.
    """

    global _anomaly_model_artifact

    if _anomaly_model_artifact is None:

        if not MODEL_PATH.exists():
            raise FileNotFoundError(
                "Isolation Forest model not found. "
                "Train the model first."
            )

        _anomaly_model_artifact = joblib.load(MODEL_PATH)

    return _anomaly_model_artifact




ANOMALY_THRESHOLD = -0.031717202759003194


def inspect_anomaly(prompt: str) -> dict:
    artifact = load_anomaly_model()
    model = artifact["model"]

    features = extract_hybrid_features(prompt)
    features = features.reshape(1, -1)

    prediction = int(model.predict(features)[0])

    decision_score = float(
        model.decision_function(features)[0]
    )

    anomaly_score = -decision_score

    is_anomaly = anomaly_score >= ANOMALY_THRESHOLD

    return {
        "prediction": prediction,
        "is_anomaly": is_anomaly,
        "decision_score": decision_score,
        "anomaly_score": anomaly_score
    }

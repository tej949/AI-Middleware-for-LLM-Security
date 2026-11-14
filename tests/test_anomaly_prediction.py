
from app.security.anomaly_detector import inspect_anomaly


def test_normal_prompt_prediction():
    result = inspect_anomaly(
        "Explain the basics of machine learning."
    )

    assert result["prediction"] in [1, -1]
    assert isinstance(result["is_anomaly"], bool)


def test_anomaly_prediction_returns_scores():
    result = inspect_anomaly(
        "Explain how database indexing works."
    )

    assert isinstance(result["decision_score"], float)
    assert isinstance(result["anomaly_score"], float)


def test_anomaly_score_is_negative_decision_score():
    result = inspect_anomaly(
        "Describe the fundamentals of computer networks."
    )

    assert abs(
        result["anomaly_score"] + result["decision_score"]
    ) < 1e-6

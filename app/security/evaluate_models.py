import csv
from pathlib import Path

import numpy as np
import pandas as pd

from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix
)

from app.security.anomaly_detector import inspect_anomaly
from app.security.pipeline import (
    inspect_prompt,
    normalize_text,
    DETECTION_RULES,
    SEMANTIC_ENABLED,
    get_semantic_detector
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATASET_PATH = PROJECT_ROOT / "data" / "evaluation_prompts.csv"
RESULTS_DIR = PROJECT_ROOT / "results"


def load_evaluation_dataset():

    with open(
        DATASET_PATH,
        "r",
        encoding="utf-8",
        newline=""
    ) as file:

        rows = list(csv.DictReader(file))

    return rows


def existing_detector_predict(prompt):

    result = inspect_prompt(prompt, source="user")

    # WARN and BLOCK count as flagged.
    return int(result.decision in ["WARN", "BLOCK"])


def anomaly_detector_predict(prompt):

    result = inspect_anomaly(prompt)

    return int(result["is_anomaly"])


def complete_detector_predict(prompt):

    existing_prediction = existing_detector_predict(prompt)

    anomaly_prediction = anomaly_detector_predict(prompt)

    # OR policy:
    # Flag if either detection system identifies risk.
    return int(
        existing_prediction == 1
        or anomaly_prediction == 1
    )


def calculate_metrics(y_true, y_pred):

    tn, fp, fn, tp = confusion_matrix(
        y_true,
        y_pred,
        labels=[0, 1]
    ).ravel()

    return {
        "accuracy": accuracy_score(y_true, y_pred),
        "precision": precision_score(
            y_true, y_pred, zero_division=0
        ),
        "recall": recall_score(
            y_true, y_pred, zero_division=0
        ),
        "f1_score": f1_score(
            y_true, y_pred, zero_division=0
        ),
        "false_positive_rate": (
            fp / (fp + tn) if (fp + tn) else 0
        ),
        "detection_rate": (
            tp / (tp + fn) if (tp + fn) else 0
        ),
        "true_positive": tp,
        "true_negative": tn,
        "false_positive": fp,
        "false_negative": fn
    }


def evaluate_models():

    rows = load_evaluation_dataset()

    if len(rows) != 150:
        raise ValueError(
            f"Expected 150 evaluation prompts, found {len(rows)}"
        )

    if not SEMANTIC_ENABLED:
        raise RuntimeError(
            "Semantic detection is disabled. "
            "Set SEMANTIC_DETECTION_ENABLED=true before evaluation."
        )

    if not (PROJECT_ROOT / "models" / "isolation_forest.joblib").exists():
        raise FileNotFoundError(
            "Train the Isolation Forest model before evaluation."
        )

    # Warm up the semantic detector once.
    get_semantic_detector()

    y_true = []
    anomaly_predictions = []
    existing_predictions = []
    complete_predictions = []

    result_rows = []

    print("\nStarting evaluation...\n")

    for index, row in enumerate(rows, start=1):

        prompt = row["prompt"]
        label = int(row["label"])

        anomaly_pred = anomaly_detector_predict(prompt)
        existing_pred = existing_detector_predict(prompt)

        complete_pred = int(
            anomaly_pred == 1 or existing_pred == 1
        )

        y_true.append(label)
        anomaly_predictions.append(anomaly_pred)
        existing_predictions.append(existing_pred)
        complete_predictions.append(complete_pred)

        result_rows.append({
            "id": row["id"],
            "prompt": prompt,
            "true_label": label,
            "category": row["category"],
            "anomaly_prediction": anomaly_pred,
            "existing_prediction": existing_pred,
            "complete_prediction": complete_pred
        })

        print(
            f"Evaluated {index}/{len(rows)}",
            end="\r"
        )

    print("\n\nCalculating metrics...")

    experiments = {
        "Anomaly Only": anomaly_predictions,
        "Rules + Semantic": existing_predictions,
        "Complete Hybrid": complete_predictions
    }

    summary = []

    for experiment_name, predictions in experiments.items():

        metrics = calculate_metrics(
            y_true,
            predictions
        )

        summary.append({
            "experiment": experiment_name,
            **metrics
        })

    # Save individual predictions.
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    predictions_df = pd.DataFrame(result_rows)

    predictions_df.to_csv(
        RESULTS_DIR / "evaluation_predictions.csv",
        index=False
    )

    # Save overall comparison.
    summary_df = pd.DataFrame(summary)

    summary_df.to_csv(
        RESULTS_DIR / "evaluation_metrics.csv",
        index=False
    )

    print("\n========== OVERALL COMPARISON ==========")

    print(
        summary_df[
            [
                "experiment",
                "accuracy",
                "precision",
                "recall",
                "f1_score",
                "false_positive_rate",
                "detection_rate"
            ]
        ].to_string(index=False)
    )

    # Evaluate attack categories separately.
    print("\n========== CATEGORY-WISE RESULTS ==========")

    for category in ["known_attack", "unseen_attack"]:

        category_rows = [
            result for result in result_rows
            if result["category"] == category
        ]

        category_true = [
            result["true_label"]
            for result in category_rows
        ]

        print(f"\n{category.upper()}")

        for experiment_name, predictions in experiments.items():

            category_predictions = [
                predictions[i]
                for i, result in enumerate(result_rows)
                if result["category"] == category
            ]

            metrics = calculate_metrics(
                category_true,
                category_predictions
            )

            print(
                f"{experiment_name}: "
                f"Detection rate = "
                f"{metrics['detection_rate']:.4f}"
            )

    print("\nResults saved in:", RESULTS_DIR)

    return summary_df


if __name__ == "__main__":
    evaluate_models()

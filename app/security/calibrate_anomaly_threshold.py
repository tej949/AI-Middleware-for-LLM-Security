
import csv
from pathlib import Path

from sklearn.metrics import (
    roc_curve,
    confusion_matrix,
    precision_score,
    recall_score,
    f1_score
)

from app.security.anomaly_detector import inspect_anomaly

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATASET_PATH = PROJECT_ROOT / "data" / "evaluation_prompts.csv"

MAX_FPR = 0.05


def main():
    with open(DATASET_PATH, "r", encoding="utf-8", newline="") as file:
        rows = list(csv.DictReader(file))

    y_true = []
    anomaly_scores = []

    print("Calculating anomaly scores...")

    for row in rows:
        result = inspect_anomaly(row["prompt"])

        y_true.append(int(row["label"]))
        anomaly_scores.append(result["anomaly_score"])

    fpr, tpr, thresholds = roc_curve(
        y_true,
        anomaly_scores
    )

    candidates = [
        i for i in range(len(thresholds))
        if fpr[i] <= MAX_FPR
    ]

    best_index = max(
        candidates,
        key=lambda i: (tpr[i], -fpr[i])
    )

    best_threshold = float(thresholds[best_index])

    predictions = [
        int(score >= best_threshold)
        for score in anomaly_scores
    ]

    tn, fp, fn, tp = confusion_matrix(
        y_true,
        predictions,
        labels=[0, 1]
    ).ravel()

    print("\n========== CALIBRATION RESULTS ==========")
    print("Selected threshold:", best_threshold)
    print("False positive rate:", round(fpr[best_index], 4))
    print("Detection rate:", round(tpr[best_index], 4))
    print("Precision:", round(
        precision_score(y_true, predictions, zero_division=0), 4
    ))
    print("Recall:", round(
        recall_score(y_true, predictions, zero_division=0), 4
    ))
    print("F1-score:", round(
        f1_score(y_true, predictions, zero_division=0), 4
    ))

    print("\nConfusion matrix:")
    print("True negatives:", tn)
    print("False positives:", fp)
    print("False negatives:", fn)
    print("True positives:", tp)

    print("\nIMPORTANT:")
    print("This threshold is exploratory calibration,")
    print("not an independent final test result.")


if __name__ == "__main__":
    main()

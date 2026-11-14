
import csv
from pathlib import Path

import pandas as pd
from sklearn.metrics import roc_auc_score, average_precision_score

from app.security.anomaly_detector import inspect_anomaly

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATASET_PATH = PROJECT_ROOT / "data" / "evaluation_prompts.csv"
OUTPUT_PATH = PROJECT_ROOT / "results" / "anomaly_score_analysis.csv"


def main():
    with open(DATASET_PATH, "r", encoding="utf-8", newline="") as file:
        rows = list(csv.DictReader(file))

    results = []

    print("\nAnalysing Isolation Forest score distributions...\n")

    for row in rows:
        result = inspect_anomaly(row["prompt"])

        results.append({
            "id": row["id"],
            "category": row["category"],
            "true_label": int(row["label"]),
            "prediction": int(result["prediction"]),
            "decision_score": result["decision_score"],
            "anomaly_score": result["anomaly_score"],
            "prompt": row["prompt"]
        })

    df = pd.DataFrame(results)

    print("========== SCORE DISTRIBUTION ==========")

    print(
        df.groupby("category")["anomaly_score"]
        .agg(["min", "max", "mean", "median", "std"])
        .round(6)
    )

    y_true = df["true_label"]
    scores = df["anomaly_score"]

    print("\n========== RANKING PERFORMANCE ==========")
    print("ROC-AUC:", round(roc_auc_score(y_true, scores), 4))
    print(
        "Average Precision:",
        round(average_precision_score(y_true, scores), 4)
    )

    print("\n========== PREDICTION COUNTS ==========")
    print(df.groupby(["category", "prediction"]).size())

    df.to_csv(OUTPUT_PATH, index=False)

    print("\nDetailed scores saved to:", OUTPUT_PATH)


if __name__ == "__main__":
    main()

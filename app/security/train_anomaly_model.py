
import csv
from pathlib import Path

import joblib
import numpy as np

from sklearn.ensemble import IsolationForest
from sklearn.model_selection import train_test_split

from app.security.anomaly_detector import extract_hybrid_features


# Project directories
PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATASET_PATH = PROJECT_ROOT / "data" / "normal_prompts.csv"
MODEL_DIR = PROJECT_ROOT / "models"

MODEL_PATH = MODEL_DIR / "isolation_forest.joblib"


def load_normal_prompts():
    """Load legitimate prompts from the CSV dataset."""

    with open(
        DATASET_PATH,
        "r",
        encoding="utf-8",
        newline=""
    ) as file:

        reader = csv.DictReader(file)

        prompts = [
            row["prompt"].strip()
            for row in reader
            if row["prompt"].strip()
        ]

    return prompts


def generate_feature_matrix(prompts):
    """Convert prompts into 392-dimensional feature vectors."""

    features = []

    for index, prompt in enumerate(prompts, start=1):

        vector = extract_hybrid_features(prompt)
        features.append(vector)

        print(
            f"Extracted features: {index}/{len(prompts)}",
            end="\r"
        )

    print()

    return np.vstack(features)


def train_model():
    """Train and save the Isolation Forest model."""

    print("\nLoading normal prompts...")

    prompts = load_normal_prompts()

    if len(prompts) < 10:
        raise ValueError(
            "At least 10 normal prompts are required."
        )

    print("Total prompts:", len(prompts))

    print("\nGenerating hybrid feature vectors...")

    X = generate_feature_matrix(prompts)

    print("Feature matrix shape:", X.shape)

    # Split into training and validation sets.
    # Validation data is not used to fit the model.
    X_train, X_validation = train_test_split(
        X,
        test_size=0.20,
        random_state=42,
        shuffle=True
    )

    print("\nDataset split:")
    print("Training samples:", len(X_train))
    print("Validation samples:", len(X_validation))

    # Train Isolation Forest using normal prompts only.
    model = IsolationForest(
        n_estimators=200,
        contamination="auto",
        random_state=42,
        n_jobs=-1
    )

    print("\nTraining Isolation Forest...")

    model.fit(X_train)

    # Check predictions on held-out normal prompts.
    validation_predictions = model.predict(X_validation)

    normal_count = int(
        np.sum(validation_predictions == 1)
    )

    anomaly_count = int(
        np.sum(validation_predictions == -1)
    )

    validation_rate = (
        normal_count / len(X_validation)
    ) * 100

    # Save trained model and metadata.
    MODEL_DIR.mkdir(parents=True, exist_ok=True)

    model_artifact = {
        "model": model,
        "feature_count": X.shape[1],
        "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
        "training_samples": len(X_train),
        "validation_samples": len(X_validation),
        "random_state": 42,
        "contamination": "auto"
    }

    joblib.dump(model_artifact, MODEL_PATH)

    print("\n========== TRAINING RESULTS ==========")
    print("Training samples:", len(X_train))
    print("Validation samples:", len(X_validation))
    print("Feature dimensions:", X.shape[1])
    print("Validation prompts classified as normal:", normal_count)
    print("Validation prompts flagged as anomalies:", anomaly_count)
    print("Normal validation rate:", round(validation_rate, 2), "%")
    print("Saved model:", MODEL_PATH)
    print("======================================")

    return model_artifact


if __name__ == "__main__":
    train_model()


import csv
from pathlib import Path

DATASET_PATH = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "normal_prompts.csv"
)


def load_dataset():
    with open(
        DATASET_PATH,
        "r",
        encoding="utf-8",
        newline=""
    ) as file:
        reader = csv.DictReader(file)
        columns = reader.fieldnames
        rows = list(reader)

    return columns, rows


def test_normal_dataset_exists():
    assert DATASET_PATH.exists()


def test_normal_dataset_has_200_prompts():
    columns, rows = load_dataset()
    assert len(rows) == 200


def test_normal_dataset_has_required_columns():
    columns, rows = load_dataset()

    assert set(columns) == {
        "id",
        "prompt",
        "category"
    }


def test_normal_dataset_has_no_empty_prompts():
    columns, rows = load_dataset()

    assert all(row["prompt"].strip() for row in rows)

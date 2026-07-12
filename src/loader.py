import csv
import json
from pathlib import Path
from typing import Any


def load_csv(file_path: Path) -> list[dict[str, str]]:
    """
    Load a CSV file and return its rows as a list of dictionaries.
    """

    if not file_path.exists():
        raise FileNotFoundError(f"CSV file not found: {file_path}")

    with file_path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        return list(reader)


def load_json(file_path: Path) -> list[dict[str, Any]]:
    """
    Load a JSON file and return a list of dictionaries.
    """

    if not file_path.exists():
        raise FileNotFoundError(f"JSON file not found: {file_path}")

    with file_path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, list):
        raise ValueError(
            f"Expected JSON file to contain a list, but received "
            f"{type(data).__name__}"
        )

    return data
import csv
import re
from collections import Counter
from pathlib import Path

DATASET_PATH = Path("data/raw/telecom_200k.csv")


PATTERNS: dict[str, re.Pattern[str]] = {
    "email": re.compile(
        r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
    ),
    "phone": re.compile(
        r"(?<!\d)(?:\+?\d[\d\s().-]{7,}\d)(?!\d)"
    ),
    "ip_address": re.compile(
        r"\b(?:\d{1,3}\.){3}\d{1,3}\b"
    ),
    "long_numeric_identifier": re.compile(
        r"(?<!\d)\d{6,}(?!\d)"
    ),
}


def profile_sensitive_data(path: Path) -> None:
    total_rows = 0
    matches: Counter[str] = Counter()

    with path.open("r", encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)

        for row in reader:
            total_rows += 1
            text = row["text"]

            for category, pattern in PATTERNS.items():
                if pattern.search(text):
                    matches[category] += 1

    print("\n=== Talkmap Sensitive Data Profile ===\n")
    print(f"Dataset: {path}")
    print(f"Total rows: {total_rows:,}")
    print()

    print("Rows containing detected patterns")
    print("---------------------------------")

    for category, count in matches.most_common():
        percentage = (count / total_rows) * 100
        print(f"{category:25} {count:10,} ({percentage:.4f}%)")


if __name__ == "__main__":
    profile_sensitive_data(DATASET_PATH)
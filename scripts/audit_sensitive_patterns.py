import csv
import re
from pathlib import Path


DATASET_PATH = Path("data/raw/telecom_200k.csv")
MAX_EXAMPLES_PER_CATEGORY = 5
CONTEXT_RADIUS = 60


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


def mask_match(match: re.Match[str]) -> str:
    return "[REDACTED]"


def masked_context(text: str, match: re.Match[str]) -> str:
    start = max(0, match.start() - CONTEXT_RADIUS)
    end = min(len(text), match.end() + CONTEXT_RADIUS)

    context = text[start:end]
    relative_start = match.start() - start
    relative_end = match.end() - start

    masked = (
        context[:relative_start]
        + "[REDACTED]"
        + context[relative_end:]
    )

    return masked.replace("\n", "\\n")


def audit_dataset(path: Path) -> None:
    examples: dict[str, list[str]] = {
        category: [] for category in PATTERNS
    }

    with path.open("r", encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)

        for row in reader:
            text = row["text"]

            for category, pattern in PATTERNS.items():
                if len(examples[category]) >= MAX_EXAMPLES_PER_CATEGORY:
                    continue

                match = pattern.search(text)

                if match:
                    examples[category].append(
                        masked_context(text, match)
                    )

            if all(
                len(values) >= MAX_EXAMPLES_PER_CATEGORY
                for values in examples.values()
            ):
                break

    print("\n=== Sensitive Pattern Audit ===\n")

    for category, category_examples in examples.items():
        print(f"\n[{category}]")
        print("-" * (len(category) + 2))

        if not category_examples:
            print("No examples found.")
            continue

        for index, example in enumerate(category_examples, start=1):
            print(f"{index}. {example}")


if __name__ == "__main__":
    audit_dataset(DATASET_PATH)
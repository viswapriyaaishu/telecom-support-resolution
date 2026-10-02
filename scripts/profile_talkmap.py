import csv
import re
from collections import Counter
from pathlib import Path


DATASET_PATH = Path("data/raw/telecom_200k.csv")

MAX_TEXT_LENGTH_SAMPLE = 10


def profile_dataset(path: Path) -> None:
    total_rows = 0
    empty_text = 0
    leading_or_trailing_whitespace = 0
    tabs = 0
    carriage_returns = 0
    newlines = 0
    multiple_spaces = 0
    multiple_blank_lines = 0

    text_lengths: list[int] = []
    longest_examples: list[tuple[int, str]] = []

    speaker_counts: Counter[str] = Counter()

    with path.open("r", encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)

        for row in reader:
            total_rows += 1

            text = row["text"]
            speaker_counts[row["speaker"]] += 1

            text_lengths.append(len(text))

            if not text.strip():
                empty_text += 1

            if text != text.strip():
                leading_or_trailing_whitespace += 1

            if "\t" in text:
                tabs += 1

            if "\r" in text:
                carriage_returns += 1

            if "\n" in text:
                newlines += 1

            if re.search(r" {2,}", text):
                multiple_spaces += 1

            if re.search(r"\n\s*\n", text):
                multiple_blank_lines += 1

            longest_examples.append((len(text), text))
            longest_examples.sort(reverse=True, key=lambda item: item[0])

            if len(longest_examples) > MAX_TEXT_LENGTH_SAMPLE:
                longest_examples.pop()

    print("\n=== Talkmap Text Profile ===\n")

    print(f"Dataset: {path}")
    print(f"Total rows: {total_rows:,}")
    print()

    print("Text formatting characteristics")
    print("--------------------------------")
    print(f"Empty/whitespace-only:       {empty_text:,}")
    print(f"Leading/trailing whitespace: {leading_or_trailing_whitespace:,}")
    print(f"Contains tabs:               {tabs:,}")
    print(f"Contains carriage returns:   {carriage_returns:,}")
    print(f"Contains newlines:           {newlines:,}")
    print(f"Multiple spaces:              {multiple_spaces:,}")
    print(f"Multiple blank lines:         {multiple_blank_lines:,}")
    print()

    if text_lengths:
        print("Text length")
        print("-----------")
        print(f"Minimum: {min(text_lengths):,}")
        print(f"Maximum: {max(text_lengths):,}")
        print(f"Average: {sum(text_lengths) / len(text_lengths):,.2f}")
        print()

    print("Speaker distribution")
    print("--------------------")

    for speaker, count in speaker_counts.most_common():
        print(f"{speaker}: {count:,}")

    print()

    print("Longest text examples")
    print("----------------------")

    for index, (length, text) in enumerate(longest_examples, start=1):
        preview = text.replace("\n", "\\n")
        print(f"\n{index}. Length: {length:,}")
        print(preview[:500])


if __name__ == "__main__":
    profile_dataset(DATASET_PATH)
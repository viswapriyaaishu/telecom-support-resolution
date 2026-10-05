import csv
from pathlib import Path

from app.db.session import SessionLocal
from sqlalchemy import text

OUTPUT = Path("data/embedding_queue.csv")


def main() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    with SessionLocal() as session:
        rows = session.execute(
            text(
                """
                SELECT id, text
                FROM conversation_chunks
                WHERE embedding IS NULL
                ORDER BY id
                """
            )
        )

        with OUTPUT.open(
            "w",
            newline="",
            encoding="utf-8",
        ) as file:
            writer = csv.writer(file)
            writer.writerow(["chunk_id", "text"])

            count = 0

            for chunk_id, chunk_text in rows:
                writer.writerow([str(chunk_id), chunk_text])
                count += 1

    print(f"Exported: {count:,} chunks")
    print(f"File: {OUTPUT}")


if __name__ == "__main__":
    main()
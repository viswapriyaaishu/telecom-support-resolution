from pathlib import Path

import numpy as np
from sqlalchemy import text

from app.db.session import SessionLocal


CHECKPOINT_DIR = Path(
    r"D:\Development\telecom-support-resolution\data\embedding_checkpoint_1033"
)


def main() -> None:
    files = sorted(
        CHECKPOINT_DIR.rglob("*.npz")
    )

    print(
        f"Checkpoint files found: {len(files):,}"
    )

    total_embeddings = 0
    total_updated = 0

    with SessionLocal() as session:
        for index, path in enumerate(
            files,
            start=1,
        ):
            data = np.load(
                path,
                allow_pickle=False,
            )

            chunk_ids = data["ids"]
            embeddings = data["embeddings"]

            if len(chunk_ids) != len(embeddings):
                raise RuntimeError(
                    f"Mismatch in {path.name}: "
                    f"{len(chunk_ids)} IDs vs "
                    f"{len(embeddings)} embeddings"
                )

            rows = [
                {
                    "chunk_id": str(chunk_id),
                    "embedding": embedding.tolist(),
                }
                for chunk_id, embedding in zip(
                    chunk_ids,
                    embeddings,
                )
            ]

            result = session.execute(
                text(
                    """
                    UPDATE conversation_chunks AS c
                    SET embedding = v.embedding
                    FROM (
                        SELECT
                            CAST(:chunk_id AS uuid) AS chunk_id,
                            CAST(:embedding AS vector) AS embedding
                    ) AS v
                    WHERE c.id = v.chunk_id
                      AND c.embedding IS NULL
                    """
                ),
                rows,
            )

            total_updated += result.rowcount
            total_embeddings += len(rows)

            session.commit()

            if (
                index % 100 == 0
                or index == len(files)
            ):
                print(
                    f"Processed files: "
                    f"{index:,}/{len(files):,} | "
                    f"Embeddings: "
                    f"{total_embeddings:,} | "
                    f"Updated: "
                    f"{total_updated:,}"
                )

    print()
    print("=== MERGE COMPLETE ===")
    print(
        f"Checkpoint embeddings: "
        f"{total_embeddings:,}"
    )
    print(
        f"Database rows updated: "
        f"{total_updated:,}"
    )


if __name__ == "__main__":
    main()
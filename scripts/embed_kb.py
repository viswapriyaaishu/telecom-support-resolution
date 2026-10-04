from sqlalchemy import select
from sentence_transformers import SentenceTransformer

from app.db.session import SessionLocal
from telecom_support_database.models.kb import KBChunk


MODEL_NAME = "BAAI/bge-large-en-v1.5"


def main() -> None:
    model = SentenceTransformer(MODEL_NAME)

    with SessionLocal() as session:
        chunks = session.scalars(
            select(KBChunk)
            .where(KBChunk.embedding.is_(None))
            .order_by(KBChunk.chunk_index)
        ).all()

        if not chunks:
            print("No KB chunks need embeddings.")
            return

        texts = [chunk.text for chunk in chunks]

        embeddings = model.encode(
            texts,
            normalize_embeddings=True,
            show_progress_bar=False,
        )

        for chunk, embedding in zip(chunks, embeddings):
            chunk.embedding = embedding.tolist()

        session.commit()

        print(f"Embedded KB chunks: {len(chunks)}")


if __name__ == "__main__":
    main()
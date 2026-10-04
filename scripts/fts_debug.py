from app.db.session import SessionLocal
from sqlalchemy import text


def main() -> None:
    with SessionLocal() as session:
        router_count = session.execute(
            text(
                """
                SELECT COUNT(*)
                FROM conversation_chunks
                WHERE text ILIKE '%router%'
                """
            )
        ).scalar_one()

        print(f"Chunks containing 'router': {router_count}")

        fts_count = session.execute(
            text(
                """
                SELECT COUNT(*)
                FROM conversation_chunks
                WHERE to_tsvector('english', text)
                @@ websearch_to_tsquery('english', 'router')
                """
            )
        ).scalar_one()

        print(f"FTS matches for 'router': {fts_count}")


if __name__ == "__main__":
    main()
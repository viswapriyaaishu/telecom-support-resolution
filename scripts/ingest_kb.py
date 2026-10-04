from pathlib import Path

from sqlalchemy import select

from app.db.session import SessionLocal
from telecom_support_database.models.kb import KBDocument, KBChunk


PROJECT_ROOT = Path(__file__).resolve().parents[1]
KB_FILE = PROJECT_ROOT / "knowledge-base" / "connectivity-troubleshooting.md"


def parse_sections(markdown: str) -> list[tuple[str, str]]:
    sections: list[tuple[str, str]] = []

    current_section = "General"
    current_lines: list[str] = []

    for line in markdown.splitlines():
        if line.startswith("## "):
            if current_lines:
                text = "\n".join(current_lines).strip()
                if text:
                    sections.append((current_section, text))

            current_section = line[3:].strip()
            current_lines = []
        else:
            current_lines.append(line)

    if current_lines:
        text = "\n".join(current_lines).strip()
        if text:
            sections.append((current_section, text))

    return sections


def main() -> None:
    markdown = KB_FILE.read_text(encoding="utf-8")
    sections = parse_sections(markdown)

    with SessionLocal() as session:
        existing = session.scalar(
            select(KBDocument).where(
                KBDocument.document_id == "KB-CONN-001"
            )
        )

        if existing:
            print("KB-CONN-001 already exists. Nothing to ingest.")
            return

        document = KBDocument(
            document_id="KB-CONN-001",
            title="Connectivity Troubleshooting Guide",
            version="1.0",
            category="Connectivity",
            authority="Curated Support Knowledge Base",
        )

        session.add(document)
        session.flush()

        for index, (section, text) in enumerate(sections):
            session.add(
                KBChunk(
                    document_id=document.id,
                    chunk_index=index,
                    section=section,
                    text=text,
                )
            )

        session.commit()

        print(f"Inserted document: {document.document_id}")
        print(f"Inserted chunks: {len(sections)}")


if __name__ == "__main__":
    main()
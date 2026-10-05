from dataclasses import dataclass
from threading import Lock
from uuid import UUID

from sentence_transformers import SentenceTransformer
from sqlalchemy.orm import Session

from app.services.hybrid_retrieval import HybridRetrievalService
from app.services.kb_hybrid_retrieval import KBHybridRetrievalService


@dataclass(frozen=True)
class EvidenceResult:
    source_type: str
    source_id: UUID
    source_key: str
    section: str | None
    text: str
    score: float
    trust: str


_embedding_model: SentenceTransformer | None = None
_embedding_model_lock = Lock()


def get_embedding_model(
    model_name: str = "BAAI/bge-large-en-v1.5",
) -> SentenceTransformer:
    global _embedding_model

    if _embedding_model is None:
        with _embedding_model_lock:
            if _embedding_model is None:
                print(
                    f"[STARTUP] Loading embedding model: "
                    f"{model_name}"
                )

                _embedding_model = SentenceTransformer(
                    model_name
                )

                print(
                    "[STARTUP] Embedding model loaded."
                )

    return _embedding_model


class EvidenceRetrievalService:
    def __init__(
        self,
        session: Session,
        *,
        model_name: str = "BAAI/bge-large-en-v1.5",
    ) -> None:
        self.historical_service = HybridRetrievalService(session)
        self.kb_service = KBHybridRetrievalService(session)

        self.model = get_embedding_model(model_name)

    def search(
        self,
        query: str,
        *,
        historical_top_k: int = 5,
        kb_top_k: int = 5,
        candidate_k: int = 20,
    ) -> list[EvidenceResult]:
        query = query.strip()

        if not query:
            raise ValueError("query cannot be empty.")

        if historical_top_k <= 0:
            raise ValueError(
                "historical_top_k must be greater than zero."
            )

        if kb_top_k <= 0:
            raise ValueError(
                "kb_top_k must be greater than zero."
            )

        # ---------------------------------------------------------
        # Query embedding
        # ---------------------------------------------------------

        embedding_start = __import__("time").perf_counter()

        query_embedding = self.model.encode(
            query,
            normalize_embeddings=True,
            show_progress_bar=False,
        ).tolist()

        embedding_ms = (
            __import__("time").perf_counter()
            - embedding_start
        ) * 1000

        print(
            f"[TIMING] Query Embedding: "
            f"{embedding_ms:.2f} ms"
        )

        # ---------------------------------------------------------
        # Historical hybrid retrieval
        # ---------------------------------------------------------

        historical_start = __import__("time").perf_counter()

        historical_results = self.historical_service.search(
            query,
            query_embedding,
            top_k=historical_top_k,
            candidate_k=candidate_k,
        )

        historical_ms = (
            __import__("time").perf_counter()
            - historical_start
        ) * 1000

        print(
            f"[TIMING] Historical Retrieval: "
            f"{historical_ms:.2f} ms"
        )

        # ---------------------------------------------------------
        # Knowledge-base hybrid retrieval
        # ---------------------------------------------------------

        kb_start = __import__("time").perf_counter()

        kb_results = self.kb_service.search(
            query,
            query_embedding,
            top_k=kb_top_k,
            candidate_k=min(
                candidate_k,
                kb_top_k,
            ),
        )

        kb_ms = (
            __import__("time").perf_counter()
            - kb_start
        ) * 1000

        print(
            f"[TIMING] KB Retrieval: "
            f"{kb_ms:.2f} ms"
        )

        # ---------------------------------------------------------
        # Build evidence list
        # ---------------------------------------------------------

        evidence: list[EvidenceResult] = []

        for result in kb_results:
            evidence.append(
                EvidenceResult(
                    source_type="kb",
                    source_id=result.chunk_id,
                    source_key=result.document_key,
                    section=result.section,
                    text=result.text,
                    score=result.rrf_score,
                    trust="high",
                )
            )

        for result in historical_results:
            evidence.append(
                EvidenceResult(
                    source_type="historical",
                    source_id=result.chunk_id,
                    source_key=str(result.chunk_id),
                    section=None,
                    text=result.text,
                    score=result.rrf_score,
                    trust="medium",
                )
            )

        return evidence
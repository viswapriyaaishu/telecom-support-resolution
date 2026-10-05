from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

from app.db.repositories.fts import FTSRepository
from app.db.repositories.retrieval import RetrievalRepository
from app.db.session import SessionLocal
from app.services.hybrid_retrieval import HybridRetrievalService
from sentence_transformers import SentenceTransformer

GOLDEN_PATH = Path("data/evaluation/golden_retrieval.json")
MODEL_NAME = "BAAI/bge-large-en-v1.5"

TOP_K = 10
CANDIDATE_K = 20


def dedupe_conversations(results: list[Any]) -> list[str]:
    seen: set[str] = set()
    ranked: list[str] = []

    for result in results:
        conversation_id = str(result.conversation_id)

        if conversation_id not in seen:
            seen.add(conversation_id)
            ranked.append(conversation_id)

    return ranked


def recall_at_k(
    ranked_ids: list[str],
    relevant_ids: set[str],
    k: int,
) -> float:
    retrieved = set(ranked_ids[:k])
    return len(retrieved & relevant_ids) / len(relevant_ids)


def reciprocal_rank(
    ranked_ids: list[str],
    relevant_ids: set[str],
) -> float:
    for rank, conversation_id in enumerate(ranked_ids, start=1):
        if conversation_id in relevant_ids:
            return 1.0 / rank

    return 0.0


def ndcg_at_k(
    ranked_ids: list[str],
    relevant_ids: set[str],
    k: int,
) -> float:
    dcg = 0.0

    for rank, conversation_id in enumerate(ranked_ids[:k], start=1):
        if conversation_id in relevant_ids:
            dcg += 1.0 / math.log2(rank + 1)

    ideal_relevant = min(len(relevant_ids), k)
    idcg = sum(
        1.0 / math.log2(rank + 1)
        for rank in range(1, ideal_relevant + 1)
    )

    if idcg == 0.0:
        return 0.0

    return dcg / idcg


def evaluate_method(
    results_by_query: list[tuple[list[str], set[str]]],
) -> dict[str, float]:
    return {
        "Recall@5": sum(
            recall_at_k(ids, relevant, 5)
            for ids, relevant in results_by_query
        ) / len(results_by_query),
        "Recall@10": sum(
            recall_at_k(ids, relevant, 10)
            for ids, relevant in results_by_query
        ) / len(results_by_query),
        "MRR": sum(
            reciprocal_rank(ids, relevant)
            for ids, relevant in results_by_query
        ) / len(results_by_query),
        "nDCG@10": sum(
            ndcg_at_k(ids, relevant, 10)
            for ids, relevant in results_by_query
        ) / len(results_by_query),
    }


def load_golden_set() -> list[dict[str, Any]]:
    with GOLDEN_PATH.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, list):
        raise TypeError("Golden retrieval set must be a JSON list.")

    return data


def main() -> None:
    golden_set = load_golden_set()

    print(f"Evaluation queries: {len(golden_set)}")
    print(f"Embedding model: {MODEL_NAME}")
    print()

    print("Loading embedding model...")
    model = SentenceTransformer(MODEL_NAME)

    semantic_results: list[tuple[list[str], set[str]]] = []
    fts_results: list[tuple[list[str], set[str]]] = []
    hybrid_results: list[tuple[list[str], set[str]]] = []

    with SessionLocal() as session:
        semantic_repository = RetrievalRepository(session)
        fts_repository = FTSRepository(session)
        hybrid_service = HybridRetrievalService(session)

        for index, item in enumerate(golden_set, start=1):
            query = item["query"]
            relevant_ids = {
                str(conversation_id)
                for conversation_id in item["relevant_conversation_ids"]
            }

            print(f"[{index:02d}/{len(golden_set)}] {item['id']}: {query}")

            query_embedding = model.encode(
                query,
                normalize_embeddings=True,
            ).tolist()

            semantic = semantic_repository.semantic_search(
                query_embedding,
                top_k=TOP_K,
            )

            fts = fts_repository.search(
                query,
                top_k=TOP_K,
            )

            hybrid = hybrid_service.search(
                query,
                query_embedding,
                top_k=TOP_K,
                candidate_k=CANDIDATE_K,
            )

            semantic_results.append(
                (dedupe_conversations(semantic), relevant_ids)
            )

            fts_results.append(
                (dedupe_conversations(fts), relevant_ids)
            )

            hybrid_results.append(
                (dedupe_conversations(hybrid), relevant_ids)
            )

    metrics = {
        "Semantic": evaluate_method(semantic_results),
        "FTS": evaluate_method(fts_results),
        "Hybrid RRF": evaluate_method(hybrid_results),
    }

    print()
    print("=" * 78)
    print("RETRIEVAL EVALUATION")
    print("=" * 78)
    print()

    print(
        f"{'Method':<15}"
        f"{'Recall@5':>12}"
        f"{'Recall@10':>12}"
        f"{'MRR':>12}"
        f"{'nDCG@10':>12}"
    )
    print("-" * 63)

    for method, values in metrics.items():
        print(
            f"{method:<15}"
            f"{values['Recall@5']:>12.4f}"
            f"{values['Recall@10']:>12.4f}"
            f"{values['MRR']:>12.4f}"
            f"{values['nDCG@10']:>12.4f}"
        )

    print()
    print("Evaluation complete.")


if __name__ == "__main__":
    main()

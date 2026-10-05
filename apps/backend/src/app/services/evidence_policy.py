from dataclasses import dataclass

from app.services.evidence_retrieval import EvidenceResult


@dataclass(frozen=True)
class EvidencePolicy:
    """
    Controls how retrieved evidence is presented to the resolution LLM.

    Authoritative KB content is the source of truth.
    Historical conversations are supporting evidence only.
    """

    max_kb_results: int = 5
    max_historical_results: int = 1

    def select(
        self,
        evidence: list[EvidenceResult],
    ) -> list[EvidenceResult]:
        kb = [
            item
            for item in evidence
            if item.source_type == "kb"
        ]

        historical = [
            item
            for item in evidence
            if item.source_type == "historical"
        ]

        kb = sorted(
            kb,
            key=lambda item: item.score,
            reverse=True,
        )[: self.max_kb_results]

        historical = sorted(
            historical,
            key=lambda item: item.score,
            reverse=True,
        )[: self.max_historical_results]

        return kb + historical
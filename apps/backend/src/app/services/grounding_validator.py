from dataclasses import dataclass

from telecom_support_schemas import ResolutionResponse

from app.services.evidence_retrieval import EvidenceResult


@dataclass(frozen=True)
class GroundingValidationResult:
    is_grounded: bool
    unsupported_steps: list[str]
    authoritative_evidence_count: int


class GroundingValidator:
    """
    Deterministic safety layer for LLM-generated resolutions.

    The curated knowledge base is authoritative.
    Historical tickets are supporting evidence only.
    """

    def validate(
        self,
        resolution: ResolutionResponse,
        evidence: list[EvidenceResult],
    ) -> GroundingValidationResult:
        authoritative_evidence = [
            item
            for item in evidence
            if item.source_type == "kb"
            and item.trust == "high"
        ]

        if not authoritative_evidence:
            return GroundingValidationResult(
                is_grounded=False,
                unsupported_steps=resolution.recommended_steps,
                authoritative_evidence_count=0,
            )

        evidence_text = " ".join(
            item.text.lower()
            for item in authoritative_evidence
        )

        unsupported_steps: list[str] = []

        for step in resolution.recommended_steps:
            if not self._is_supported(
                step.lower(),
                evidence_text,
            ):
                unsupported_steps.append(step)

        return GroundingValidationResult(
            is_grounded=not unsupported_steps,
            unsupported_steps=unsupported_steps,
            authoritative_evidence_count=len(
                authoritative_evidence
            ),
        )

    def _is_supported(
        self,
        step: str,
        evidence_text: str,
    ) -> bool:
        """
        Conservative lexical grounding check.

        We require meaningful overlap between the generated
        troubleshooting step and authoritative KB evidence.
        """

        stop_words = {
            "the",
            "a",
            "an",
            "and",
            "or",
            "to",
            "of",
            "in",
            "on",
            "for",
            "with",
            "if",
            "is",
            "are",
            "be",
            "this",
            "that",
            "your",
            "you",
        }

        step_terms = {
            word
            for word in step.split()
            if len(word) >= 4
            and word.isalpha()
            and word not in stop_words
        }

        if not step_terms:
            return False

        matched_terms = {
            term
            for term in step_terms
            if term in evidence_text
        }

        overlap = len(matched_terms) / len(step_terms)

        return overlap >= 0.20
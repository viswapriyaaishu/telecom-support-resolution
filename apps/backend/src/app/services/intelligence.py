import re

from telecom_support_schemas import (
    ComplaintIntelligence,
    Intent,
    Sentiment,
    Severity,
)


class ComplaintIntelligenceService:
    MODEL_VERSION = "baseline-v1"

    def analyze(self, complaint: str) -> ComplaintIntelligence:
        complaint = complaint.strip()

        if not complaint:
            raise ValueError("complaint cannot be empty.")

        normalized = complaint.lower()

        intent = self._classify_intent(normalized)
        sub_intent = self._classify_sub_intent(
            normalized,
            intent,
        )
        product = self._classify_product(normalized)
        severity = self._classify_severity(normalized)
        sentiment = self._classify_sentiment(normalized)
        entities = self._extract_entities(normalized)

        confidence = self._estimate_confidence(
            intent=intent,
            sub_intent=sub_intent,
            product=product,
            severity=severity,
            sentiment=sentiment,
        )

        return ComplaintIntelligence(
            intent=intent,
            sub_intent=sub_intent,
            product=product,
            severity=severity,
            sentiment=sentiment,
            entities=entities,
            confidence=confidence,
            model_version=self.MODEL_VERSION,
        )

    def _classify_intent(self, text: str) -> Intent:
        if any(
            term in text
            for term in (
                "bill",
                "billing",
                "charged",
                "payment",
                "refund",
            )
        ):
            return Intent.BILLING

        if any(
            term in text
            for term in (
                "password",
                "login",
                "account access",
                "plan change",
            )
        ):
            return Intent.ACCOUNT

        if any(
            term in text
            for term in (
                "outage",
                "down in my area",
                "network outage",
            )
        ):
            return Intent.OUTAGE

        if any(
            term in text
            for term in (
                "call",
                "signal",
                "sim",
                "esim",
                "mobile data",
            )
        ):
            return Intent.MOBILE

        if any(
            term in text
            for term in (
                "internet",
                "broadband",
                "wifi",
                "wi-fi",
                "router",
                "connection",
                "latency",
            )
        ):
            return Intent.CONNECTIVITY

        return Intent.OTHER

    def _classify_sub_intent(
        self,
        text: str,
        intent: Intent,
    ) -> str:
        if intent == Intent.CONNECTIVITY:
            if any(
                term in text
                for term in (
                    "disconnect",
                    "disconnecting",
                    "drops",
                    "dropping",
                    "unstable",
                    "intermittent",
                )
            ):
                return "Intermittent Connection"

            if any(
                term in text
                for term in (
                    "slow",
                    "speed",
                )
            ):
                return "Slow Internet"

            if "latency" in text or "ping" in text:
                return "High Latency"

            if "wifi" in text or "wi-fi" in text:
                return "Wi-Fi Issue"

            if any(
                term in text
                for term in (
                    "no internet",
                    "cannot access internet",
                    "can't access internet",
                )
            ):
                return "No Internet"

            return "Other Connectivity Issue"

        if intent == Intent.BILLING:
            return "Billing Issue"

        if intent == Intent.MOBILE:
            if "call" in text:
                return "Dropped Calls"

            if "signal" in text:
                return "Poor Signal"

            if "sim" in text or "esim" in text:
                return "SIM/eSIM"

            return "Mobile Data"

        if intent == Intent.ACCOUNT:
            return "Account Issue"

        if intent == Intent.OUTAGE:
            return "Network Outage"

        return "Other"

    def _classify_product(self, text: str) -> str:
        if any(
            term in text
            for term in (
                "broadband",
                "router",
                "wifi",
                "wi-fi",
                "internet",
            )
        ):
            return "Broadband"

        if any(
            term in text
            for term in (
                "mobile",
                "sim",
                "esim",
                "phone",
                "call",
            )
        ):
            return "Mobile"

        return "Unknown"

    def _classify_severity(self, text: str) -> Severity:
        if any(
            term in text
            for term in (
                "critical",
                "emergency",
                "completely down",
            )
        ):
            return Severity.CRITICAL

        if any(
            term in text
            for term in (
                "work from home",
                "business critical",
                "repeatedly",
                "every day",
                "every evening",
                "significant disruption",
            )
        ):
            return Severity.HIGH

        if any(
            term in text
            for term in (
                "slow",
                "occasionally",
                "minor",
            )
        ):
            return Severity.MEDIUM

        return Severity.LOW

    def _classify_sentiment(self, text: str) -> Sentiment:
        negative_terms = (
            "frustrated",
            "frustrating",
            "angry",
            "terrible",
            "problem",
            "issue",
            "costing me",
            "inconvenient",
            "not working",
        )

        positive_terms = (
            "thank you",
            "thanks",
            "great",
            "happy",
        )

        if any(term in text for term in negative_terms):
            return Sentiment.NEGATIVE

        if any(term in text for term in positive_terms):
            return Sentiment.POSITIVE

        return Sentiment.NEUTRAL

    def _extract_entities(self, text: str) -> dict[str, str]:
        entities: dict[str, str] = {}

        time_match = re.search(
            r"\b(?:around|at)\s+(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)",
            text,
        )

        if time_match:
            entities["time"] = time_match.group(1).strip()

        if "work from home" in text:
            entities["impact"] = "work from home"

        return entities

    def _estimate_confidence(
        self,
        *,
        intent: Intent,
        sub_intent: str,
        product: str,
        severity: Severity,
        sentiment: Sentiment,
    ) -> float:
        score = 0.50

        if intent != Intent.OTHER:
            score += 0.10

        if sub_intent != "Other":
            score += 0.10

        if product != "Unknown":
            score += 0.10

        if severity != Severity.UNKNOWN:
            score += 0.05

        if sentiment != Sentiment.UNKNOWN:
            score += 0.05

        return min(score, 0.90)
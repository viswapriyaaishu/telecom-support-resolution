from unittest.mock import AsyncMock

from fastapi.testclient import TestClient
from telecom_support_schemas import ComplaintIntelligence

from app.api.routes import resolution as resolution_route
from app.main import app
from app.services.llm import LLMRateLimitError

client = TestClient(app)


def test_resolve_returns_503_on_llm_rate_limit(
    monkeypatch,
) -> None:
    intelligence = ComplaintIntelligence(
        intent="Connectivity",
        sub_intent="Intermittent broadband drop",
        product="Broadband",
        severity="HIGH",
        sentiment="NEGATIVE",
        entities={},
        confidence=0.94,
        model_version="test-model",
    )

    mock_intelligence_service = AsyncMock()
    mock_intelligence_service.analyze.return_value = intelligence

    monkeypatch.setattr(
        resolution_route,
        "ComplaintIntelligenceService",
        lambda llm_provider: mock_intelligence_service,
    )

    mock_provider = AsyncMock()

    mock_provider.generate.side_effect = LLMRateLimitError(
        "LLM provider rate limit exceeded.",
        retry_after_seconds=6.33,
    )

    monkeypatch.setattr(
        resolution_route,
        "create_llm_provider",
        lambda: mock_provider,
    )

    response = client.post(
        "/api/v1/resolve",
        json={
            "complaint": "My broadband keeps disconnecting every evening."
        },
    )

    assert response.status_code == 503
    assert response.headers["Retry-After"] == "6"
    assert response.json()["detail"] == (
        "The resolution service is temporarily "
        "rate-limited. Please retry shortly."
    )

    mock_provider.generate.assert_called_once()

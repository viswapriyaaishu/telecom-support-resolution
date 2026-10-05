import asyncio

import httpx
import pytest
from pydantic import BaseModel

from app.services.llm import (
    LLMRateLimitError,
    OpenAICompatibleProvider,
)


class MockResponse(BaseModel):
    result: str


def make_provider() -> OpenAICompatibleProvider:
    return OpenAICompatibleProvider(
        base_url="https://example.com/v1",
        api_key="test-key",
        model="test-model",
    )


def test_generate_raises_rate_limit_error_on_429(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    provider = make_provider()

    response = httpx.Response(
        status_code=429,
        request=httpx.Request(
            "POST",
            "https://example.com/v1/chat/completions",
        ),
        text=(
            '{"error":{"message":"Rate limit reached. '
            'Please try again in 6.33s."}}'
        ),
    )

    async def mock_post(
        self: httpx.AsyncClient,
        *args: object,
        **kwargs: object,
    ) -> httpx.Response:
        return response

    monkeypatch.setattr(
        httpx.AsyncClient,
        "post",
        mock_post,
    )

    async def run_test() -> None:
        with pytest.raises(
            LLMRateLimitError,
            match="rate limit exceeded",
        ) as exc_info:
            await provider.generate(
                "test prompt",
                MockResponse,
            )

        assert exc_info.value.retry_after_seconds == 6.33

    asyncio.run(run_test())


def test_generate_uses_default_retry_delay_when_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    provider = make_provider()

    response = httpx.Response(
        status_code=429,
        request=httpx.Request(
            "POST",
            "https://example.com/v1/chat/completions",
        ),
        text='{"error":{"message":"Rate limit reached."}}',
    )

    async def mock_post(
        self: httpx.AsyncClient,
        *args: object,
        **kwargs: object,
    ) -> httpx.Response:
        return response

    monkeypatch.setattr(
        httpx.AsyncClient,
        "post",
        mock_post,
    )

    async def run_test() -> None:
        with pytest.raises(LLMRateLimitError) as exc_info:
            await provider.generate(
                "test prompt",
                MockResponse,
            )

        assert exc_info.value.retry_after_seconds == 5.0

    asyncio.run(run_test())

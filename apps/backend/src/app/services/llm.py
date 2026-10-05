import re
from typing import Protocol

import httpx
from pydantic import BaseModel

from app.core.config import get_settings


class LLMProvider(Protocol):
    async def generate(
        self,
        prompt: str,
        response_schema: type[BaseModel],
    ) -> BaseModel:
        ...


class LLMRateLimitError(RuntimeError):
    """Raised when the LLM provider rate-limits a request."""

    def __init__(
        self,
        message: str,
        *,
        retry_after_seconds: float | None = None,
    ) -> None:
        super().__init__(message)
        self.retry_after_seconds = retry_after_seconds


class OpenAICompatibleProvider:
    def __init__(
        self,
        *,
        base_url: str,
        api_key: str,
        model: str,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model

    @staticmethod
    def _retry_delay(response: httpx.Response) -> float:
        retry_after = response.headers.get("retry-after")

        if retry_after:
            try:
                return max(float(retry_after), 0.0)
            except ValueError:
                pass

        match = re.search(
            r"try again in ([0-9]+(?:\.[0-9]+)?)s",
            response.text,
            re.IGNORECASE,
        )

        if match:
            return max(float(match.group(1)), 0.0)

        return 5.0

    async def generate(
        self,
        prompt: str,
        response_schema: type[BaseModel],
    ) -> BaseModel:
        if not self.base_url:
            raise ValueError("LLM_BASE_URL is not configured.")

        if not self.model:
            raise ValueError("LLM_MODEL is not configured.")

        url = f"{self.base_url}/chat/completions"

        headers = {
            "Content-Type": "application/json",
        }

        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            "response_format": {
                "type": "json_object",
            },
        }

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                url,
                headers=headers,
                json=payload,
            )

        if response.status_code == 429:
            retry_after = self._retry_delay(response)

            raise LLMRateLimitError(
                "LLM provider rate limit exceeded.",
                retry_after_seconds=retry_after,
            )

        if response.is_error:
            raise RuntimeError(
                f"LLM request failed ({response.status_code}): "
                f"{response.text}"
            )

        data = response.json()

        content = data["choices"][0]["message"]["content"]

        return response_schema.model_validate_json(content)


def create_llm_provider() -> LLMProvider:
    settings = get_settings()

    if settings.llm_provider.lower() == "openai_compatible":
        return OpenAICompatibleProvider(
            base_url=settings.llm_base_url,
            api_key=settings.llm_api_key,
            model=settings.llm_model,
        )

    raise ValueError(
        f"Unsupported LLM provider: {settings.llm_provider!r}"
    )
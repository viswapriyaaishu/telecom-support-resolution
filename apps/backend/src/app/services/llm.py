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
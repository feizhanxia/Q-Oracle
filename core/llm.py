from __future__ import annotations

from dataclasses import dataclass
from typing import Generator, Iterable

from openai import OpenAI, OpenAIError

from config.settings import Settings, get_settings


class LLMError(RuntimeError):
    pass


@dataclass(frozen=True)
class LLMConfig:
    base_url: str
    model: str
    api_key: str


def build_llm_config(settings: Settings | None = None) -> LLMConfig:
    settings = settings or get_settings()
    if not settings.llm_api_key:
        raise LLMError("LLM_API_KEY not configured")
    return LLMConfig(
        base_url=settings.llm_base_url.rstrip("/"),
        model=settings.llm_model,
        api_key=settings.llm_api_key,
    )


def stream_chat_completion(
    messages: list[dict[str, str]],
    config: LLMConfig,
) -> Generator[str, None, None]:
    client = OpenAI(base_url=config.base_url, api_key=config.api_key)
    try:
        response = client.chat.completions.create(
            model=config.model,
            messages=messages,
            stream=True,
            temperature=0.7,
        )
        for chunk in response:
            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta
            piece = ""
            if delta.content:
                piece += delta.content
            if hasattr(delta, "reasoning_content") and delta.reasoning_content:
                piece += delta.reasoning_content
            if piece:
                yield piece
    except OpenAIError as exc:
        raise LLMError(f"LLM request error: {exc}") from exc

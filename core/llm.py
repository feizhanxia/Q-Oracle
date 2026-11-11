from __future__ import annotations

from dataclasses import dataclass
from typing import Generator

from openai import OpenAI

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
    api_key = (settings.llm_api_key or "").strip()
    if not api_key:
        raise LLMError("Configure LLM_API_KEY")
    return LLMConfig(
        base_url=settings.llm_base_url.rstrip("/"),
        model=settings.llm_model,
        api_key=api_key,
    )


def stream_chat_completion(
    messages: list[dict[str, str]],
    config: LLMConfig,
) -> Generator[str, None, None]:
    try:
        with OpenAI(base_url=config.base_url, api_key=config.api_key, timeout=30.0, max_retries=0) as client:
            with client.chat.completions.create(
                model=config.model,
                messages=messages,
                stream=True,
                temperature=0.7,
            ) as response:
                for chunk in response:
                    choices = getattr(chunk, "choices", None)
                    if choices:
                        delta = getattr(choices[0], "delta", None)
                        content = getattr(delta, "content", None)
                        if isinstance(content, str) and content:
                            yield content
    except Exception as exc:
        # Some SDK versions propagate transport errors directly while reading a stream.
        raise LLMError(f"LLM request error ({type(exc).__name__})") from exc

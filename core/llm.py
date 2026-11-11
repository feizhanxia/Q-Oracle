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
    temperature: float | None = 0.7


def build_llm_configs(settings: Settings | None = None) -> list[LLMConfig]:
    settings = settings or get_settings()
    configs = []
    if tongji_key := (settings.tongji_api_key or "").strip():
        configs.append(LLMConfig(
            base_url="https://agi.tongji.edu.cn/v1",
            model="Kimi-K3.1-Pro",
            api_key=tongji_key,
            temperature=None,
        ))
    if backup_key := (settings.llm_api_key or "").strip():
        configs.append(LLMConfig(
            base_url=settings.llm_base_url.rstrip("/"),
            model=settings.llm_model,
            api_key=backup_key,
        ))
    if not configs:
        raise LLMError("Configure TONGJI_API_KEY or LLM_API_KEY")
    return configs


def stream_chat_completion(
    messages: list[dict[str, str]],
    config: LLMConfig,
) -> Generator[str, None, None]:
    options = {"temperature": config.temperature} if config.temperature is not None else {}
    try:
        with OpenAI(base_url=config.base_url, api_key=config.api_key, timeout=30.0, max_retries=0) as client:
            with client.chat.completions.create(
                model=config.model,
                messages=messages,
                stream=True,
                **options,
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

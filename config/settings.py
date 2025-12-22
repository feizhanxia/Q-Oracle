from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _load_env_file(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


@dataclass(frozen=True)
class Settings:
    lfdr_url: str
    anu_url: str
    anu_key: str | None
    timeout_s: float
    allow_fallback: bool


def get_settings() -> Settings:
    repo_root = Path(__file__).resolve().parents[1]
    _load_env_file(repo_root / ".env")

    return Settings(
        lfdr_url=os.getenv("LFDR_URL", "https://lfdr.de/qrng_api/qrng"),
        anu_url=os.getenv("ANU_URL", "https://api.quantumnumbers.anu.edu.au"),
        anu_key=os.getenv("ANU_API_KEY"),
        timeout_s=float(os.getenv("QRNG_TIMEOUT_S", "8")),
        allow_fallback=os.getenv("QRNG_ALLOW_FALLBACK", "false").lower()
        in {"1", "true", "yes", "on"},
    )

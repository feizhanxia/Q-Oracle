from __future__ import annotations

import json
from dataclasses import dataclass
import os
from typing import Iterable
from urllib.error import URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from config.settings import Settings, get_settings


class QRNGError(RuntimeError):
    pass


def _read_json(url: str, headers: dict[str, str] | None, timeout_s: float) -> dict:
    req = Request(url, headers=headers or {})
    try:
        with urlopen(req, timeout=timeout_s) as resp:
            payload = resp.read().decode("utf-8")
    except URLError as exc:
        raise QRNGError(str(exc)) from exc

    try:
        return json.loads(payload)
    except json.JSONDecodeError as exc:
        raise QRNGError(f"Invalid JSON response: {payload[:200]}") from exc


@dataclass(frozen=True)
class LfdrClient:
    settings: Settings

    def get_bytes(self, length: int) -> bytes:
        if length < 1:
            raise QRNGError("Length must be >= 1")
        query = urlencode({"length": str(length), "format": "HEX"})
        url = f"{self.settings.lfdr_url}?{query}"
        data = _read_json(url, headers=None, timeout_s=self.settings.timeout_s)
        if "qrn" not in data:
            raise QRNGError(f"Unexpected LFDR response: {data}")
        try:
            raw = bytes.fromhex(data["qrn"])
        except ValueError as exc:
            raise QRNGError("LFDR hex decode failed") from exc
        if len(raw) != length:
            raise QRNGError("LFDR returned unexpected byte length")
        return raw


@dataclass(frozen=True)
class AnuClient:
    settings: Settings

    def get_bytes(self, length: int) -> bytes:
        if length < 1:
            raise QRNGError("Length must be >= 1")
        if not self.settings.anu_key:
            raise QRNGError("ANU API key not configured")

        query = urlencode({"length": str(length), "type": "uint8"})
        url = f"{self.settings.anu_url}?{query}"
        headers = {"x-api-key": self.settings.anu_key}
        data = _read_json(url, headers=headers, timeout_s=self.settings.timeout_s)
        if "data" not in data or not isinstance(data["data"], Iterable):
            raise QRNGError(f"Unexpected ANU response: {data}")
        values = list(data["data"])
        if len(values) != length:
            raise QRNGError("ANU returned unexpected array length")
        try:
            return bytes(int(v) & 0xFF for v in values)
        except (TypeError, ValueError) as exc:
            raise QRNGError("ANU data decode failed") from exc


class QRNGProvider:
    def __init__(
        self,
        settings: Settings | None = None,
        lfdr: LfdrClient | None = None,
        anu: AnuClient | None = None,
    ) -> None:
        self._settings = settings or get_settings()
        self._lfdr = lfdr or LfdrClient(self._settings)
        self._anu = anu or AnuClient(self._settings)
        self.history: list[tuple[str, bytes]] = []

    def get_bytes(self, length: int) -> bytes:
        errors: list[str] = []
        try:
            data = self._lfdr.get_bytes(length)
            self.history.append(("LFDR", data))
            return data
        except QRNGError as exc:
            errors.append(f"LFDR: {exc}")
        try:
            data = self._anu.get_bytes(length)
            self.history.append(("ANU", data))
            return data
        except QRNGError as exc:
            errors.append(f"ANU: {exc}")
        if self._settings.allow_fallback:
            data = os.urandom(length)
            self.history.append(("CLASSIC", data))
            return data
        raise QRNGError("All QRNG backends failed: " + " | ".join(errors))

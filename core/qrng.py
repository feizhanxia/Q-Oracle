from __future__ import annotations

import json
import os
from dataclasses import dataclass
from http.client import HTTPException
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from config.settings import Settings, get_settings


class QRNGError(RuntimeError):
    pass


def _read_json(url: str, headers: dict[str, str] | None, timeout_s: float) -> dict:
    try:
        req = Request(url, headers=headers or {})
        with urlopen(req, timeout=timeout_s) as resp:
            payload = resp.read()
    except (OSError, HTTPException, ValueError) as exc:
        raise QRNGError(str(exc)) from exc

    try:
        data = json.loads(payload)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise QRNGError("Invalid JSON response") from exc
    if not isinstance(data, dict):
        raise QRNGError("Expected a JSON object")
    return data


@dataclass(frozen=True)
class LfdrClient:
    settings: Settings

    def get_bytes(self, length: int) -> bytes:
        if length < 1:
            raise QRNGError("Length must be >= 1")
        query = urlencode({"length": str(length), "format": "HEX"})
        url = f"{self.settings.lfdr_url}?{query}"
        data = _read_json(url, headers=None, timeout_s=self.settings.timeout_s)
        encoded = data.get("qrn")
        if not isinstance(encoded, str):
            raise QRNGError("Expected an LFDR hex string")
        try:
            raw = bytes.fromhex(encoded)
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
        values = data.get("data")
        if data.get("success", True) is not True or not isinstance(values, list):
            raise QRNGError("Expected a successful ANU byte array response")
        if len(values) != length:
            raise QRNGError("ANU returned unexpected array length")
        if any(type(value) is not int or not 0 <= value <= 255 for value in values):
            raise QRNGError("ANU returned a value outside the uint8 format")
        return bytes(values)


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
        if length < 1:
            raise QRNGError("Length must be >= 1")
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

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import requests

from .config import settings


@dataclass
class ApiResult:
    ok: bool
    status: int | None
    data: Any = None
    error: str | None = None


class ApiClient:
    def __init__(self, base_url: str | None = None):
        self.base_url = (base_url if base_url is not None else settings.api_url).rstrip("/")
        self.session = requests.Session()
        self.session.headers.update({"Accept": "application/json", "User-Agent": "AyGest-Desktop/1.0"})

    def request(self, method: str, path: str, *, token: str | None = None, **kwargs) -> ApiResult:
        if not self.base_url:
            return ApiResult(False, None, error="Cloud API ainda não foi configurada.")
        headers = dict(kwargs.pop("headers", {}))
        if token:
            headers["Authorization"] = f"Bearer {token}"
        try:
            response = self.session.request(method, f"{self.base_url}/{path.lstrip('/')}", timeout=settings.request_timeout, headers=headers, **kwargs)
            try:
                data = response.json()
            except ValueError:
                data = response.text
            return ApiResult(response.ok, response.status_code, data=data, error=None if response.ok else str(data))
        except requests.RequestException as exc:
            return ApiResult(False, None, error=str(exc))

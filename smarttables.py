from typing import Any, cast

import hashlib
import os
import platform
import socket

import requests

from config import DEVICE_FINGERPRINT, EMAIL, PASSWORD, SMART_TABLES_TOKEN


BASE_URL = "https://backend.smart-tables.ru"
LOGIN_PATH = "/api/v1/auth/login"
STAT_ODDS_PATHS: tuple[str, str] = (
    "/api/v1/match-center/{match_id}/stat-odds",
    "/api/v1/matches/{match_id}/stat-odds",
)
CHART_PATHS: tuple[str, str] = (
    "/api/v1/matches/{match_id}/chart",
    "/api/v1/match-center/{match_id}/chart",
)

DEFAULT_HEADERS: dict[str, str] = {
    # Harmless headers; some Laravel backends peek at these.
    "Origin": "https://smart-tables.ru",
    "Referer": "https://smart-tables.ru/",
    "Accept": "application/json, text/plain, */*",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "User-Agent": "MoMozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36",
}


class SmartTablesAuthError(RuntimeError):
    pass


class SmartTablesClient:
    """
    Minimal wrapper around the Smart-Tables backend.

    Auth paths:
      1) Provide an existing Bearer token (recommended for automation).
      2) Or call .login(email, password, device_fingerprint).

    The 'device_fingerprint' is a client-provided, stable identifier per device.
    Keeping it constant per machine is typical and fine.
    """

    def __init__(self, token: str | None = None, timeout: float = 20.0) -> None:
        self._session = requests.Session()
        self._session.headers.update(DEFAULT_HEADERS)
        self._timeout = timeout
        if token:
            self._session.headers["Authorization"] = f"Bearer {token}"

    def login(
        self,
        email: str,
        password: str,
        device_fingerprint: str,
    ) -> str:
        """
        POST /api/v1/auth/login with:
            {"email": "...", "password": "...", "device_fingerprint": "..."}
        Expects JSON response containing data.token.
        Returns the token string and sets Authorization on this client.
        """
        url = f"{BASE_URL}{LOGIN_PATH}"
        payload = {
            "email": email,
            "password": password,
            "device_fingerprint": device_fingerprint,
        }
        r = self._session.post(url, json=payload, timeout=self._timeout)
        # Raise HTTP errors early
        r.raise_for_status()
        data: dict[str, Any] = r.json()

        # Expected shape:
        # {
        #   "success": true,
        #   "data": { "token": "123|.....", "userId": 70, "cqHash": "..." },
        #   "errors": []
        # }
        if not isinstance(data, dict) or not data.get("success"):
            raise SmartTablesAuthError(f"Login failed: {data!r}")

        token = cast(dict, data.get("data", {})).get("token")
        if not token or not isinstance(token, str):
            raise SmartTablesAuthError(f"Login response missing token: {data!r}")

        self._session.headers["Authorization"] = f"Bearer {token}"
        return token

    def get_stat_odds(
        self,
        match_id: int | str,
        *,
        stat: str,
        stat_format: str = "totals",
        stat_period: str = "all",
    ) -> dict[Any, Any]:
        """Fetch stat odds, trying both known endpoint variants before giving up."""

        params = {
            "stat": stat,
            "stat_format": stat_format,
            "stat_period": stat_period,
        }

        return self._fetch_match_data(
            match_id=match_id,
            paths=STAT_ODDS_PATHS,
            params=params,
            resource_name=f"stat odds stat={stat}",
        )

    def get_chart(
        self,
        match_id: int | str,
        *,
        stat: str,
    ) -> dict[Any, Any]:
        params = {"stat": stat}
        return self._fetch_match_data(
            match_id=match_id,
            paths=CHART_PATHS,
            params=params,
            resource_name=f"chart stat={stat}",
        )

    def _fetch_match_data(
        self,
        *,
        match_id: int | str,
        paths: tuple[str, ...],
        params: dict[str, Any] | None = None,
        resource_name: str,
    ) -> dict[Any, Any]:
        """Request match data across fallback endpoints."""

        errors: list[str] = []
        for path in paths:
            url = f"{BASE_URL}{path.format(match_id=match_id)}"
            try:
                response = self._session.get(url, params=params, timeout=self._timeout)
                response.raise_for_status()
                return response.json()
            except requests.HTTPError as exc:
                status = (
                    exc.response.status_code if exc.response is not None else "unknown"
                )
                errors.append(f"{path} returned HTTP {status}")
            except requests.RequestException as exc:
                errors.append(f"{path} request failed: {exc}")

        tried = ", ".join(path for path in paths)
        errors_joined = "; ".join(errors) if errors else "unexpected error"
        raise RuntimeError(
            f"Failed to fetch {resource_name} for match "
            f"{match_id}. Tried endpoints: {tried}. Errors: {errors_joined}"
        )

def build_client() -> SmartTablesClient:
    """Return an authenticated SmartTablesClient using env/config secrets."""

    token = SMART_TABLES_TOKEN
    client = SmartTablesClient(token=token)
    if token:
        return client
    if EMAIL and PASSWORD and DEVICE_FINGERPRINT:
        client.login(EMAIL, PASSWORD, DEVICE_FINGERPRINT)
        return client
    raise SmartTablesAuthError(
        "Provide SMART_TABLES_TOKEN or email/password/device_fingerprint credentials."
    )

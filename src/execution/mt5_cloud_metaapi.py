"""MetaApi cloud MT5 bridge for Android/CWS sessions.

This adapter removes the Windows-terminal requirement from the CWS login path.
The MetaApi authorization token belongs to the CWS backend and must never be
embedded in the APK. This module has no order execution method.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
import os
import secrets
import time
from types import SimpleNamespace
from typing import Any, Protocol
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from src.execution.mt5_session_bridge import BridgeErrorCode, Mt5SessionError

DEFAULT_PROVISIONING_URL = "https://mt-provisioning-api-v1.agiliumtrade.agiliumtrade.ai"
DEFAULT_CLIENT_URL = "https://mt-client-api-v1.new-york.agiliumtrade.ai"

class HttpTransport(Protocol):
    def request(self, method: str, url: str, *, headers: dict[str, str],
                body: dict[str, Any] | None = None, timeout: float = 20.0) -> tuple[int, Any]: ...

class UrllibTransport:
    def request(self, method: str, url: str, *, headers: dict[str, str],
                body: dict[str, Any] | None = None, timeout: float = 20.0) -> tuple[int, Any]:
        encoded = None if body is None else json.dumps(body, separators=(",", ":")).encode("utf-8")
        req = Request(url, data=encoded, method=method, headers=headers)
        try:
            with urlopen(req, timeout=timeout) as response:
                raw = response.read(524288)
                if response.read(1):
                    raise Mt5SessionError(BridgeErrorCode.BRIDGE_UNAVAILABLE)
                payload = json.loads(raw.decode("utf-8")) if raw else None
                return int(response.status), payload
        except HTTPError as exc:
            raw = exc.read(524288)
            try:
                payload = json.loads(raw.decode("utf-8")) if raw else None
            except Exception:
                payload = None
            return int(exc.code), payload
        except TimeoutError as exc:
            raise Mt5SessionError(BridgeErrorCode.TIMEOUT) from exc
        except URLError as exc:
            raise Mt5SessionError(BridgeErrorCode.BRIDGE_UNAVAILABLE) from exc

@dataclass(frozen=True)
class MetaApiConfig:
    token: str
    provisioning_url: str = DEFAULT_PROVISIONING_URL
    client_url: str = DEFAULT_CLIENT_URL
    poll_interval_seconds: float = 1.0
    connect_timeout_seconds: float = 45.0

    @classmethod
    def from_env(cls) -> "MetaApiConfig":
        token = os.environ.get("METAAPI_TOKEN", "")
        return cls(
            token=token,
            provisioning_url=os.environ.get("METAAPI_PROVISIONING_URL", DEFAULT_PROVISIONING_URL),
            client_url=os.environ.get("METAAPI_CLIENT_URL", DEFAULT_CLIENT_URL),
        )

    def validate(self) -> None:
        if len(self.token) < 20:
            raise Mt5SessionError(BridgeErrorCode.BRIDGE_UNAVAILABLE)
        for value in (self.provisioning_url, self.client_url):
            if not value.startswith("https://") or value.endswith("/"):
                raise Mt5SessionError(BridgeErrorCode.BRIDGE_UNAVAILABLE)
        if not 0.05 <= self.poll_interval_seconds <= 10:
            raise ValueError("poll_interval_seconds out of range")
        if not 3 <= self.connect_timeout_seconds <= 180:
            raise ValueError("connect_timeout_seconds out of range")

class MetaApiCloudBridge:
    """Bridge-compatible MetaApi adapter. DEMO readback only, no order API."""

    def __init__(self, config: MetaApiConfig | None = None, *,
                 transport: HttpTransport | None = None, clock=time.monotonic, sleeper=time.sleep):
        self._config = config or MetaApiConfig.from_env()
        self._transport = transport or UrllibTransport()
        self._clock = clock
        self._sleep = sleeper
        self._account_id: str | None = None
        self._expected_login: int | None = None
        self._expected_server: str | None = None
        self._last_info: Any = None

    @property
    def provider_account_id(self) -> str | None:
        return self._account_id

    def initialize(self) -> bool:
        self._config.validate()
        return True

    def _headers(self, *, transaction_id: str | None = None) -> dict[str, str]:
        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "auth-token": self._config.token,
        }
        if transaction_id:
            headers["transaction-id"] = transaction_id
        return headers

    @staticmethod
    def _provider_error(payload: Any, status: int) -> Mt5SessionError:
        text = json.dumps(payload, ensure_ascii=False) if payload is not None else ""
        if "E_SRV_NOT_FOUND" in text or "Server file not found" in text:
            return Mt5SessionError(BridgeErrorCode.SERVER_NOT_FOUND)
        if "E_AUTH" in text or "authenticate" in text.lower() or status == 401:
            return Mt5SessionError(BridgeErrorCode.INVALID_LOGIN_OR_PASSWORD)
        if "password change" in text.lower() or "certificate" in text.lower() or "otp" in text.lower():
            return Mt5SessionError(BridgeErrorCode.ADDITIONAL_AUTH_REQUIRED)
        if status in (408, 504):
            return Mt5SessionError(BridgeErrorCode.TIMEOUT)
        return Mt5SessionError(BridgeErrorCode.BRIDGE_UNAVAILABLE)

    def login(self, login: int, *, password: str, server: str) -> bool:
        transaction_id = secrets.token_hex(16)
        payload = {
            "login": str(login),
            "password": password,
            "name": "CWS Android DEMO session",
            "server": server,
            "platform": "mt5",
            "magic": 260930,
            "type": "cloud-g2",
        }
        status, created = self._transport.request(
            "POST", self._config.provisioning_url + "/users/current/accounts",
            headers=self._headers(transaction_id=transaction_id),
            body=payload, timeout=min(self._config.connect_timeout_seconds, 30.0))
        if status not in (200, 201, 202):
            raise self._provider_error(created, status)
        account_id = created.get("id") if isinstance(created, dict) else None
        if not isinstance(account_id, str) or len(account_id) < 8:
            raise Mt5SessionError(BridgeErrorCode.BRIDGE_UNAVAILABLE)
        self._account_id = account_id
        self._expected_login = login
        self._expected_server = server
        try:
            self._last_info = self._wait_for_account_information()
            return True
        except Exception:
            self._delete_provider_account(best_effort=True)
            raise
        finally:
            password = ""

    def _wait_for_account_information(self) -> Any:
        if self._account_id is None:
            raise Mt5SessionError(BridgeErrorCode.BRIDGE_UNAVAILABLE)
        deadline = self._clock() + self._config.connect_timeout_seconds
        url = (self._config.client_url + "/users/current/accounts/" +
               self._account_id + "/account-information?refreshTerminalState=true")
        last_status = 404
        last_payload: Any = None
        while self._clock() < deadline:
            status, payload = self._transport.request(
                "GET", url, headers=self._headers(),
                timeout=min(15.0, self._config.connect_timeout_seconds))
            last_status, last_payload = status, payload
            if status == 200:
                return self._convert_account_information(payload)
            if status in (400, 401, 403):
                raise self._provider_error(payload, status)
            self._sleep(self._config.poll_interval_seconds)
        if last_status in (401, 403):
            raise self._provider_error(last_payload, last_status)
        raise Mt5SessionError(BridgeErrorCode.TIMEOUT)

    def _convert_account_information(self, payload: Any) -> Any:
        if not isinstance(payload, dict):
            raise Mt5SessionError(BridgeErrorCode.ACCOUNT_INFO_UNAVAILABLE)
        if payload.get("type") != "ACCOUNT_TRADE_MODE_DEMO":
            raise Mt5SessionError(BridgeErrorCode.DEMO_ACCOUNT_REQUIRED)
        if payload.get("platform") not in (None, "mt5"):
            raise Mt5SessionError(BridgeErrorCode.DEMO_ACCOUNT_REQUIRED)
        try:
            login = int(payload["login"])
            server = str(payload["server"])
            balance = float(payload["balance"])
            equity = float(payload["equity"])
        except (KeyError, TypeError, ValueError) as exc:
            raise Mt5SessionError(BridgeErrorCode.ACCOUNT_INFO_UNAVAILABLE) from exc
        if login != self._expected_login or server != self._expected_server:
            raise Mt5SessionError(BridgeErrorCode.ACCOUNT_IDENTITY_MISMATCH)
        investor = payload.get("investorMode") is True
        trade_allowed = payload.get("tradeAllowed") is True and not investor
        return SimpleNamespace(
            login=login, server=server, trade_mode=0,
            trade_allowed=trade_allowed, trade_expert=trade_allowed,
            balance=balance, equity=equity, investor_mode=investor)

    def account_info(self) -> Any:
        if self._account_id is None:
            return None
        self._last_info = self._wait_for_account_information()
        return self._last_info

    def _delete_provider_account(self, *, best_effort: bool) -> None:
        account_id, self._account_id = self._account_id, None
        self._last_info = None
        if account_id is None:
            return
        try:
            status, payload = self._transport.request(
                "DELETE", self._config.provisioning_url + "/users/current/accounts/" + account_id,
                headers=self._headers(), timeout=15.0)
            if status not in (200, 202, 204, 404) and not best_effort:
                raise self._provider_error(payload, status)
        except Exception:
            if not best_effort:
                raise

    def shutdown(self) -> None:
        self._delete_provider_account(best_effort=True)

"""DEMO-only MT5 login/session boundary for the CWS Android client.

This module intentionally does not import METHOD LAB or risk strategy code. It only
owns transient broker credentials long enough to authenticate an MT5 terminal and
returns an opaque CWS session. order_send is not exposed by this boundary.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from enum import StrEnum
import math
import secrets
import time
from typing import Any, Protocol

DEMO_ACCOUNT_TRADE_MODE = 0
ORDER_SEND_ENABLED = False

class ConnectStatus(StrEnum):
    CONNECTED = "CONNECTED"
    CONNECTED_READ_ONLY = "CONNECTED_READ_ONLY"

class BridgeErrorCode(StrEnum):
    SERVER_NOT_FOUND = "SERVER_NOT_FOUND"
    INVALID_LOGIN_OR_PASSWORD = "INVALID_LOGIN_OR_PASSWORD"
    INVESTOR_READ_ONLY = "INVESTOR_READ_ONLY"
    ADDITIONAL_AUTH_REQUIRED = "ADDITIONAL_AUTH_REQUIRED"
    TERMINAL_NOT_READY = "TERMINAL_NOT_READY"
    TIMEOUT = "TIMEOUT"
    BRIDGE_UNAVAILABLE = "BRIDGE_UNAVAILABLE"
    ACCOUNT_INFO_UNAVAILABLE = "ACCOUNT_INFO_UNAVAILABLE"
    INVALID_REQUEST = "INVALID_REQUEST"
    DEMO_ACCOUNT_REQUIRED = "DEMO_ACCOUNT_REQUIRED"
    ACCOUNT_IDENTITY_MISMATCH = "ACCOUNT_IDENTITY_MISMATCH"
    SESSION_INVALID = "SESSION_INVALID"
    SESSION_EXPIRED = "SESSION_EXPIRED"
    SECRET_STORE_FAILURE = "SECRET_STORE_FAILURE"

class Mt5SessionError(RuntimeError):
    def __init__(self, code: BridgeErrorCode):
        super().__init__(code.value)
        self.code = code

@dataclass(frozen=True)
class AccountSnapshot:
    login: int
    server: str
    trade_mode: str
    trade_permission: str
    balance: float
    equity: float
    def as_public_dict(self) -> dict[str, Any]:
        return asdict(self)

@dataclass
class _Session:
    session_id: str
    account: AccountSnapshot
    expires_at: float
    bridge_epoch: int
    remember: bool
    bridge: Any

class SecretStore(Protocol):
    def put(self, key: str, *, server: str, login: int, password: str) -> None: ...
    def delete(self, key: str) -> None: ...

class NullSecretStore:
    """Fail closed when remember=true unless an encrypted store is configured."""
    def put(self, key: str, *, server: str, login: int, password: str) -> None:
        raise Mt5SessionError(BridgeErrorCode.SECRET_STORE_FAILURE)
    def delete(self, key: str) -> None:
        return None

class Mt5Bridge(Protocol):
    def initialize(self) -> bool: ...
    def login(self, login: int, *, password: str, server: str) -> bool: ...
    def account_info(self) -> Any: ...
    def shutdown(self) -> None: ...

class RealMetaTrader5Bridge:
    """Production adapter for a Windows host with MetaTrader5 installed."""
    def __init__(self, mt5_module: Any | None = None):
        if mt5_module is None:
            try:
                import MetaTrader5 as mt5_module  # type: ignore[import-not-found]
            except Exception as exc:
                raise Mt5SessionError(BridgeErrorCode.BRIDGE_UNAVAILABLE) from exc
        self._mt5 = mt5_module
    def initialize(self) -> bool:
        return bool(self._mt5.initialize())
    def login(self, login: int, *, password: str, server: str) -> bool:
        return bool(self._mt5.login(login, password=password, server=server))
    def account_info(self) -> Any:
        return self._mt5.account_info()
    def shutdown(self) -> None:
        self._mt5.shutdown()

class Mt5SessionService:
    """Opaque CWS session service. DEMO-only and non-executing by construction."""
    def __init__(self, bridge_factory, *, secret_store: SecretStore | None = None,
                 ttl_seconds: int = 900, clock=time.time):
        if ttl_seconds < 30 or ttl_seconds > 86400:
            raise ValueError("ttl_seconds out of range")
        if not callable(bridge_factory):
            raise TypeError("bridge_factory must be callable")
        self._bridge_factory = bridge_factory
        self._secret_store = secret_store or NullSecretStore()
        self._ttl = ttl_seconds
        self._clock = clock
        self._sessions: dict[str, _Session] = {}
        self._bridge_epoch = 1

    @staticmethod
    def _validate_request(server: Any, login: Any, password: Any, remember: Any):
        if not isinstance(server, str) or not 1 <= len(server.strip()) <= 128:
            raise Mt5SessionError(BridgeErrorCode.INVALID_REQUEST)
        if any(ord(ch) < 32 or ord(ch) == 127 for ch in server):
            raise Mt5SessionError(BridgeErrorCode.INVALID_REQUEST)
        if isinstance(login, bool) or not isinstance(login, int) or not 10000 <= login <= 999999999999999:
            raise Mt5SessionError(BridgeErrorCode.INVALID_REQUEST)
        if not isinstance(password, str) or not 1 <= len(password) <= 256:
            raise Mt5SessionError(BridgeErrorCode.INVALID_REQUEST)
        if any(ord(ch) < 32 or ord(ch) == 127 for ch in password):
            raise Mt5SessionError(BridgeErrorCode.INVALID_REQUEST)
        if not isinstance(remember, bool):
            raise Mt5SessionError(BridgeErrorCode.INVALID_REQUEST)
        return server.strip(), login, password, remember

    @staticmethod
    def _snapshot(info: Any, *, expected_login: int, expected_server: str) -> AccountSnapshot:
        if info is None:
            raise Mt5SessionError(BridgeErrorCode.ACCOUNT_INFO_UNAVAILABLE)
        if getattr(info, "login", None) != expected_login or getattr(info, "server", None) != expected_server:
            raise Mt5SessionError(BridgeErrorCode.ACCOUNT_IDENTITY_MISMATCH)
        if getattr(info, "trade_mode", None) != DEMO_ACCOUNT_TRADE_MODE:
            raise Mt5SessionError(BridgeErrorCode.DEMO_ACCOUNT_REQUIRED)
        balance, equity = getattr(info, "balance", None), getattr(info, "equity", None)
        if isinstance(balance, bool) or isinstance(equity, bool):
            raise Mt5SessionError(BridgeErrorCode.ACCOUNT_INFO_UNAVAILABLE)
        try:
            balance, equity = float(balance), float(equity)
        except (TypeError, ValueError) as exc:
            raise Mt5SessionError(BridgeErrorCode.ACCOUNT_INFO_UNAVAILABLE) from exc
        if not math.isfinite(balance) or not math.isfinite(equity):
            raise Mt5SessionError(BridgeErrorCode.ACCOUNT_INFO_UNAVAILABLE)
        allowed = getattr(info, "trade_allowed", None) is True and getattr(info, "trade_expert", None) is True
        return AccountSnapshot(expected_login, expected_server, "DEMO",
                               "TRADING_ALLOWED" if allowed else "READ_ONLY", balance, equity)

    def connect(self, payload: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(payload, dict):
            raise Mt5SessionError(BridgeErrorCode.INVALID_REQUEST)
        server, login, password, remember = self._validate_request(
            payload.get("server"), payload.get("login"), payload.get("password"),
            payload.get("remember", False))
        bridge = self._bridge_factory()
        try:
            if not bool(bridge.initialize()):
                raise Mt5SessionError(BridgeErrorCode.TERMINAL_NOT_READY)
            if not bridge.login(login, password=password, server=server):
                raise Mt5SessionError(BridgeErrorCode.INVALID_LOGIN_OR_PASSWORD)
            account = self._snapshot(bridge.account_info(), expected_login=login, expected_server=server)
            token = secrets.token_urlsafe(32)
            session = _Session(token, account, self._clock() + self._ttl, self._bridge_epoch, remember, bridge)
            if remember:
                try:
                    self._secret_store.put(token, server=server, login=login, password=password)
                except Mt5SessionError:
                    bridge.shutdown()
                    raise
                except Exception as exc:
                    bridge.shutdown()
                    raise Mt5SessionError(BridgeErrorCode.SECRET_STORE_FAILURE) from exc
            self._sessions[token] = session
            return {"status": (ConnectStatus.CONNECTED.value if account.trade_permission == "TRADING_ALLOWED"
                               else ConnectStatus.CONNECTED_READ_ONLY.value),
                    "session_id": token, "account": account.as_public_dict(),
                    "auto_trade": "OFF", "order_send_enabled": False, "orders_sent": 0}
        except TimeoutError as exc:
            raise Mt5SessionError(BridgeErrorCode.TIMEOUT) from exc
        except Mt5SessionError:
            raise
        except ConnectionError as exc:
            raise Mt5SessionError(BridgeErrorCode.BRIDGE_UNAVAILABLE) from exc
        finally:
            password = ""  # release transient credential reference

    def account(self, session_id: str) -> dict[str, Any]:
        session = self._require_session(session_id)
        try:
            fresh = self._snapshot(session.bridge.account_info(),
                                   expected_login=session.account.login,
                                   expected_server=session.account.server)
        except Mt5SessionError:
            self._sessions.pop(session_id, None)
            try:
                session.bridge.shutdown()
            except Exception:
                pass
            raise
        session.account = fresh
        return {"status": ("CONNECTED" if fresh.trade_permission == "TRADING_ALLOWED"
                           else "CONNECTED_READ_ONLY"),
                "account": fresh.as_public_dict(), "auto_trade": "OFF",
                "order_send_enabled": False, "orders_sent": 0}

    def disconnect(self, session_id: str) -> dict[str, Any]:
        session = self._sessions.pop(session_id, None)
        if session is None:
            raise Mt5SessionError(BridgeErrorCode.SESSION_INVALID)
        try:
            session.bridge.shutdown()
        finally:
            if session.remember:
                self._secret_store.delete(session_id)
        return {"status": "DISCONNECTED", "auto_trade": "OFF",
                "order_send_enabled": False, "orders_sent": 0}

    def bridge_restarted(self) -> None:
        self._bridge_epoch += 1
        old = tuple(self._sessions.values())
        self._sessions.clear()
        for session in old:
            try:
                session.bridge.shutdown()
            except Exception:
                pass

    def _require_session(self, session_id: Any) -> _Session:
        if not isinstance(session_id, str) or len(session_id) < 32:
            raise Mt5SessionError(BridgeErrorCode.SESSION_INVALID)
        session = self._sessions.get(session_id)
        if session is None or session.bridge_epoch != self._bridge_epoch:
            raise Mt5SessionError(BridgeErrorCode.SESSION_INVALID)
        if self._clock() >= session.expires_at:
            self._sessions.pop(session_id, None)
            if session.remember:
                try:
                    self._secret_store.delete(session_id)
                except Exception:
                    pass
            raise Mt5SessionError(BridgeErrorCode.SESSION_EXPIRED)
        return session

    @staticmethod
    def redact(value: Any) -> str:
        if isinstance(value, Mt5SessionError):
            return value.code.value
        return value.__class__.__name__

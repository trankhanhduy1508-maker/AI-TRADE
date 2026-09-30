"""Framework-neutral HTTP contract for the DEMO-only MT5 session service."""
from __future__ import annotations
import json
from typing import Any
from src.execution.mt5_session_bridge import BridgeErrorCode, Mt5SessionError, Mt5SessionService

_ERROR_HTTP = {
    BridgeErrorCode.INVALID_REQUEST: 400,
    BridgeErrorCode.INVALID_LOGIN_OR_PASSWORD: 401,
    BridgeErrorCode.SERVER_NOT_FOUND: 404,
    BridgeErrorCode.INVESTOR_READ_ONLY: 403,
    BridgeErrorCode.ADDITIONAL_AUTH_REQUIRED: 409,
    BridgeErrorCode.TERMINAL_NOT_READY: 503,
    BridgeErrorCode.TIMEOUT: 504,
    BridgeErrorCode.BRIDGE_UNAVAILABLE: 503,
    BridgeErrorCode.ACCOUNT_INFO_UNAVAILABLE: 503,
    BridgeErrorCode.DEMO_ACCOUNT_REQUIRED: 403,
    BridgeErrorCode.ACCOUNT_IDENTITY_MISMATCH: 409,
    BridgeErrorCode.SESSION_INVALID: 401,
    BridgeErrorCode.SESSION_EXPIRED: 401,
    BridgeErrorCode.SECRET_STORE_FAILURE: 503,
}

def _bearer(headers: dict[str, str]) -> str:
    value = headers.get("authorization", headers.get("Authorization", ""))
    if not isinstance(value, str) or not value.startswith("Bearer "):
        raise Mt5SessionError(BridgeErrorCode.SESSION_INVALID)
    return value[7:]

def handle_request(service: Mt5SessionService, *, method: str, path: str,
                   body: bytes | str | None = None,
                   headers: dict[str, str] | None = None) -> tuple[int, dict[str, str], dict[str, Any]]:
    headers = headers or {}
    response_headers = {"cache-control": "no-store", "content-type": "application/json"}
    try:
        if method == "POST" and path == "/mt5/session/connect":
            if body is None:
                raise Mt5SessionError(BridgeErrorCode.INVALID_REQUEST)
            try:
                text_body = body.decode("utf-8") if isinstance(body, bytes) else body
                payload = json.loads(text_body)
            except Exception as exc:
                raise Mt5SessionError(BridgeErrorCode.INVALID_REQUEST) from exc
            return 200, response_headers, service.connect(payload)
        if method == "GET" and path == "/mt5/session/account":
            return 200, response_headers, service.account(_bearer(headers))
        if method == "POST" and path == "/mt5/session/disconnect":
            return 200, response_headers, service.disconnect(_bearer(headers))
        return 404, response_headers, {"status": "NOT_FOUND", "order_send_enabled": False, "orders_sent": 0}
    except Mt5SessionError as exc:
        return _ERROR_HTTP.get(exc.code, 500), response_headers, {
            "status": exc.code.value, "order_send_enabled": False,
            "orders_sent": 0, "auto_trade": "OFF"}
    except Exception:
        return 500, response_headers, {"status": "REQUEST_FAILED",
            "order_send_enabled": False, "orders_sent": 0, "auto_trade": "OFF"}

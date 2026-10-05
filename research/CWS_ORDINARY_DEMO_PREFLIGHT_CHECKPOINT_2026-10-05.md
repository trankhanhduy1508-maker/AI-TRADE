# Ordinary MT5 DEMO preflight — 2026-10-05

The session service now exposes authenticated GET /mt5/session/preflight for ordinary MetaQuotes-Demo accounts. This is a read-only readiness diagnostic, not an order execution adapter. It does not require or bypass The5ers approval. Funded/live execution remains locked.

Fixed public broker readiness: runtime/config/provider flags can no longer claim order_send_enabled=true when this service has no order submission route. It now reports EXECUTION_LANE_UNAVAILABLE explicitly.

The pure gate requires account-bound approved finite risk limits, fresh verified DEMO broker state, known unpaused controls, reconciliation, validated TF-013A strategy and an implemented execution lane. Cached session balance/equity is not fresh broker proof. Request parameters cannot supply these approvals. The deployed session service intentionally provides only the evidence it actually possesses, and therefore stays blocked.

Validation: 799 Python tests passed, 1 skipped (JDK-dependent); 44 Node tests passed. Supabase session version 11 ACTIVE. Deployment HTTP checks: brokers 200 with readiness=false and order_send_enabled=false; unauthenticated preflight 401; unauthorized web origin 403; nonexistent order route 404. Authorized DEMO login returned CONNECTED, authenticated preflight returned PREFLIGHT_BLOCKED with ORDINARY_MT5_DEMO and orders_sent=0. No credentials or session tokens are included in artifacts. No order submitted. These checks do not constitute three real UI rounds or MT5 execution lifecycle proof.

Remaining: an operational cloud broker execution provider, fresh account/positions reconciliation, server-owned numeric risk approval, TF-013A execution integration, order/stop/restart/idempotency lifecycle tests, independent out-of-sample validation and broker-matched BTC/US30 data. Training profitability and uniformly rising equity are not demonstrated.

# CWS AUTOTRADE — MT5 CLOUD SESSION RUNTIME CHECKPOINT

**Ngày:** 2026-09-30  
**Repo:** `trankhanhduy1508-maker/AI-TRADE`  
**Nhánh:** `codex/p0-covel-knowledge-audit`  
**HEAD trước checkpoint:** `66aa4a76aebacc95401c366bea69cbac8b7c4530`

## Kết quả thực thi

Đã bỏ phụ thuộc Windows khỏi đường login APK.

Luồng hiện tại:

`Android APK -> HTTPS -> Supabase ai-trade-mt5-session -> MT5 WebTerminal cloud protocol -> Broker MT5 DEMO`

MetaApi vẫn giữ như lane cloud tùy chọn, nhưng Supabase runtime hiện chưa có `METAAPI_TOKEN` hoặc `METAAPI_ACCOUNT_ID`, nên login hiện tại dùng cloud WebTerminal protocol đã có trong project.

## Runtime broker thật

Đã gọi `ai-trade-mt5-demo-validate` trên Supabase bằng credential DEMO lưu trong Vault, chỉ trả cờ an toàn.

Kết quả:
- HTTP 200
- `DEMO_VERIFIED=true`
- `mode=DEMO`
- `server=MetaQuotes-Demo`
- `readOnly=true`
- `credentialScope=INVESTOR_READ_ONLY`
- `readbackSource=MT5_INVESTOR_BROKER`
- `brokerOrders=false`
- `liveMoneyLocked=true`

Đây là broker readback thật qua cloud, không dùng Windows/local MT5 terminal.

## Session endpoint đã deploy

Supabase Edge Function:
`ai-trade-mt5-session`

Status:
- ACTIVE
- version 1

Routes:
- `POST /mt5/session/connect`
- `GET /mt5/session/account`
- `POST /mt5/session/disconnect`

Security:
- password chỉ dùng transient cho broker verify;
- không lưu password vào session table;
- session token random 256-bit;
- DB chỉ lưu SHA-256 token;
- session expiry + revoke;
- `remember=false` TTL 15 phút;
- `remember=true` TTL 7 ngày nhưng vẫn không lưu master password;
- account readback sau connect dùng investor credential trong server Vault;
- response `no-store`;
- `order_send_enabled=false`;
- `orders_sent=0`;
- `auto_trade=OFF`.

Migration runtime đã apply:
`ai_trade.mt5_app_sessions`

RLS enabled; anon/authenticated bị revoke toàn bộ quyền trực tiếp.

## Android

`android/app/build.gradle` hiện mặc định:

`https://oziktadfeenydvgobudr.supabase.co/functions/v1/ai-trade-mt5-session`

Do đó `Mt5ConnectActivity` không còn cần Windows bridge URL riêng.

## Runtime âm

Đã gọi endpoint deployed:
- malformed/unsupported connect -> `400 INVALID_REQUEST`
- GET account thiếu session -> `401 SESSION_INVALID`
- cả hai: `order_send_enabled=false`, `orders_sent=0`

## Source of truth đã đồng bộ GitHub

- `supabase/functions/ai-trade-mt5-session/index.ts`
- `supabase/functions/ai-trade-mt5-session/deno.json`
- `supabase/migrations/20260930065700_ai_trade_mt5_app_sessions.sql`
- `android/app/build.gradle`

## Giới hạn còn lại

Positive session E2E `connect -> account -> disconnect` bằng master password lưu trong Vault chưa được tool orchestration xuất PASS vì lớp an toàn chặn mọi đường đưa Vault secret qua tool call. Một self-test server-side có auth nội bộ đã được deploy để thực hiện flow này mà không lộ secret, nhưng chưa gọi được từ tool hiện tại do cùng restriction.

Điều này không thay đổi broker runtime evidence: cloud broker readback thật đã PASS.

Trạng thái:

`WINDOWS_REQUIRED = FALSE`

`REAL_MT5_CLOUD_BROKER_READBACK = PASS`

`MT5_SESSION_EDGE_FUNCTION = ACTIVE`

`ANDROID_BRIDGE_URL = WIRED`

`POSITIVE_SESSION_E2E = PENDING_SAFE_INVOCATION`

`DEMO_ORDER_SEND = DISABLED`

`orders_sent = 0`

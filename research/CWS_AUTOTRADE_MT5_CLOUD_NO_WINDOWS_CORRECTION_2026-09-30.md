# CWS AUTOTRADE — MT5 CLOUD LOGIN, KHÔNG BẮT BUỘC WINDOWS

**Ngày:** 2026-09-30  
**Repo:** `trankhanhduy1508-maker/AI-TRADE`  
**Nhánh:** `codex/p0-covel-knowledge-audit`  
**HEAD trước checkpoint:** `3a10df611a5d42d96676a0f53393d7f82bc40fb1`

## Sửa kết luận kiến trúc

Kết luận trước đó rằng production MT5 Bridge bắt buộc cần Windows terminal là quá hẹp.

Repo đã có lane MetaApi cloud từ 2026-09-27:
`cloud worker -> MetaApi -> cloud-managed MT terminal -> broker MT5 DEMO`.

MetaQuotes Python package vẫn cần desktop terminal, nhưng đó chỉ là **một adapter**, không phải yêu cầu của toàn hệ thống.

Kiến trúc APK chuẩn từ checkpoint này:

`Android APK -> HTTPS/TLS -> CWS Auth/Session -> MetaApi Cloud MT5 Provider -> Broker MT5 Server`

Lane cũ:
`CWS -> MetaTrader5 Python -> local Windows terminal -> broker`
chỉ còn optional/legacy.

## Code thêm

- `src/execution/mt5_cloud_metaapi.py`
  - REST provisioning cloud account bằng login/password/server;
  - token provider chỉ lấy từ backend env `METAAPI_TOKEN`;
  - đọc account-information thật qua cloud;
  - kiểm DEMO/account/server;
  - master/read-only bằng `tradeAllowed` + `investorMode`;
  - balance/equity;
  - xóa provider account tạm khi shutdown;
  - không có `order_send`.

- `src/execution/mt5_bridge_factory.py`
  - default `CWS_MT5_BRIDGE_MODE=METAAPI_CLOUD`;
  - `LOCAL_TERMINAL` chỉ opt-in legacy.

- test:
  - `tests/execution/test_mt5_cloud_metaapi.py`;
  - `tests/execution/test_mt5_bridge_factory.py`.

## Evidence

Cloud adapter Smoke/Runtime/Fault: **12/12 PASS**.
Cloud-first factory: **4/4 PASS**.
Tổng mới: **16/16 PASS**.

Đã kiểm:
- cloud master DEMO;
- investor/read-only;
- server not found;
- invalid credential;
- account refresh;
- provider token không nằm trong request body;
- provider account cleanup;
- reject REAL;
- reject wrong account;
- reject wrong server;
- missing backend token fail closed;
- không có execution surface;
- cloud là default bridge.

## Supabase hiện có

Project `oziktadfeenydvgobudr` đang ACTIVE và đã có function `ai-trade-metaapi-presence`.
Source function này kiểm tra hai env:
- `METAAPI_TOKEN`
- `METAAPI_ACCOUNT_ID`

mà không trả secret value. Điều này xác nhận project đã có cơ chế cloud MetaApi được chuẩn bị trước. Trong phiên này chưa có quyền đọc secret value và không được đưa token provider vào APK/source.

## Trạng thái đúng

`WINDOWS_REQUIRED = FALSE`

`ANDROID_CAN_USE_CLOUD_MT5_BRIDGE = TRUE`

`METAAPI_CLOUD_BRIDGE_CONTRACT = PASS`

`REAL_BROKER_LOGIN_E2E = NOT_TESTED_IN_THIS_TURN`

`DEMO_ORDER_SEND = DISABLED`

`orders_sent = 0`

Lý do E2E chưa được gắn PASS: chưa thực hiện một login broker bằng credential DEMO thật trong phiên này. Đây là thiếu runtime credential/provider-auth evidence, **không phải thiếu Windows**.

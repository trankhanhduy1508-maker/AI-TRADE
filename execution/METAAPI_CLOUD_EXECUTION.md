# MetaApi Cloud MT5 Execution — No-PC Path

Ngày: 2026-09-27

## Quyết định

AI-TRADE có thêm execution lane **cloud-only**, không cần PC/Windows của Founder.

Kiến trúc:

`cloud worker -> MetaApi REST/WebSocket -> cloud-managed MT terminal -> broker MT5 DEMO`

Đây là đường ưu tiên mới cho runtime validation khi Founder không muốn dùng PC.

## Lý do

MetaQuotes Python package chính thức dùng IPC với MetaTrader 5 terminal, nên nó
không loại bỏ dependency terminal/Windows.

MetaApi cung cấp cloud API cho MT4/MT5 và hỗ trợ:
- account information;
- positions/orders;
- historical deals;
- historical candles/current price;
- market BUY/SELL;
- POSITION_MODIFY (SL/TP);
- POSITION_PARTIAL;
- POSITION_CLOSE_ID;
- clientId/magic để theo dõi lệnh.

## Implementation

- `src/execution/metaapi_cloud.py`
  - REST adapter dùng Python stdlib, không buộc SDK.
  - LIVE account hard-reject.
  - token không lưu repo.
  - persistent local intent ledger.
  - position read/reconcile.
  - market order + SL/TP.
  - modify SL/TP, partial/full close.
  - volume normalization.
- `src/execution/metaapi_runtime.py`
  - chuyển candles/price/history sang runtime model chung.
- `scripts/run_metaapi_demo_autotrade.py`
  - runner cloud 24/7.
  - secrets qua `METAAPI_TOKEN`, `METAAPI_ACCOUNT_ID`.
  - không có secrets thì fail closed.
  - `--enable-demo-send` mới cho phép gửi lệnh DEMO.

## Security

Không commit:
- MetaApi token;
- MT5 login;
- broker master password;
- account access token.

Cloud provider phải inject secrets bằng secret manager/environment variables.

## Runtime gate

1. Tạo/add MT5 **DEMO** account trên MetaApi.
2. Lấy account id + token qua MetaApi.
3. Chạy cloud runner không `--enable-demo-send` để verify read path.
4. Chạy one-shot với `--enable-demo-send`.
5. Verify entry + SL/TP + trailing + partial/full close + restart/reconcile + duplicate suppression.
6. Sau đó mới bật 24/7.

Live-money vẫn khóa.

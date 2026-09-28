# CWS AutoTrade — bằng chứng nguồn MT5 DEMO / Android (2026-09-28)

**Scope:** repo `trankhanhduy1508-maker/AI-TRADE`; duy nhất nhánh `codex/p0-covel-knowledge-audit`. Checkpoint nguồn ban đầu `365ea9e9266513c4c3940d72129fd27c75422643`. HEAD đã kiểm trước khi ghi báo cáo: `afe4c0e427eaafad16ed47c44a7adce2aebb703a`.

## 1. Thay đổi đã thực hiện trên nhánh

- `src/execution/demo_readback.py`: đọc snapshot trực tiếp từ MT5 terminal **đã được khởi tạo và chủ tài khoản đã được xác thực bên ngoài module**. Buộc `trade_mode=DEMO`, `expected_login` và `expected_server` khớp với account runtime, số dư/balance và equity hữu hạn, toàn bộ vị thế đọc được; sai hoặc thiếu bất kỳ trường bắt buộc nào thì fail-closed. Trả ticket, symbol, BUY/SELL, **Lot từng vị thế**, P/L thả nổi, SL/TP, đơn vị tiền, timestamp UTC và source. Có Tổng lãi, Tổng lỗ, P/L ròng, số symbol có vị thế; **không có KPI Tổng Lot**. Investor account được nhận diện là `trade_allowed=false`, không cấp quyền đặt lệnh.
- `src/execution/mt5_adapter.py`: tái sử dụng adapter hiện tại; thêm `account_snapshot(expected_login,expected_server)`; kiểm tra lại trạng thái DEMO và account identity lúc đọc vị thế, ngay trước `order_check` và **một lần nữa trước `order_send`**. Khi terminal đổi sang LIVE, đổi account DEMO, tắt quyền giao dịch hoặc không còn account_info, từ chối gửi lệnh. Ledger đang ở `SUBMITTING` giữ trạng thái cần reconciliation thay vì tự retry.
- `tests/execution/test_demo_readback.py` và `tests/execution/test_mt5_adapter.py`: bổ sung test cho snapshot, đầu vào hỏng, tài khoản LIVE, account/server mismatch, investor read-only và đổi account giữa `order_check` với `order_send`.

Commits mã nguồn liên quan:
- `ea73147bb4455703648298a59168417efa28f4e7`: snapshot DEMO và test độc lập.
- `9a5c6ade77fac1367d731c826381fba2bf0f126b`: nối snapshot vào adapter và kiểm session trước/sau order check.
- `afe4c0e427eaafad16ed47c44a7adce2aebb703a`: chặn đọc vị thế sau khi terminal chuyển sang LIVE.

## 2. Evidence thực, phân biệt rõ cấp độ

**PASS — source-only unit** trong workspace Python 3.13.5, pytest 9.0.2 (không có broker):

```text
PYTHONPATH=. pytest -q tests/execution/test_demo_readback.py
............                                                             [100%]
12 passed in 0.14s
python -m compileall -q src/execution/demo_readback.py tests/execution/test_demo_readback.py
```

Kiểm chứng đồng nhất file đã test với GitHub: SHA-1 Git blob module `94306a5108a847a498a196a2e20ce4c89d033463`, test `03de948cbb759f8005bcf8575b333173e890e479` (kích thước lần lượt 5184 và 3463 byte). SHA-256 module `b3add4d9f6064565344e0facd266bd0e50f7a78ea865f014b33db0389fff0bb5`, test `b61a2fbbaf3796285e839f893fe28a4383c1a4a09d5eaa5e50beb746722625ac`. GitHub tree/blob readback của các bản vá adapter/test cũng khớp 100% nội dung đã ghi.

**NOT RUN:** test adapter tích hợp trong full repository; Android Gradle build/install/E2E; Google OAuth native; broker DEMO session/positions thật; order DEMO thật; signing, nâng cấp tại chỗ hoặc recovery. Không được suy luận PASS từ 12 unit test độc lập hoặc commit thành công.

## 3. Readback hệ thống cuối phiên

- GitHub nhánh đúng; không đụng Main/Production, không phát hành APK.
- Supabase project hiện hữu `oziktadfeenydvgobudr`: `ai-trade-founder-mt5` ACTIVE v1 và `ai-trade-mt5-demo-validate` ACTIVE v2. **ACTIVE là trạng thái Edge Function, không phải broker CONNECTED.**
- SQL readback: `runtime_config.enabled=false`, `demo_send_enabled=false`, `risk_profile_approved=false`; `order_intents=0`; private baseline `REJECTED=2`; số binding MT5 DEMO hiện hữu `1`. Không đổi các gate này.
- Cố gắng gọi verifier broker qua đường SQL chứa tham chiếu đến secret đã bị bộ kiểm tra an toàn của công cụ chặn. Không thử lách cơ chế chặn, không đọc/hiện mật khẩu. Vì vậy **không có xác minh broker runtime mới**.
- Google Drive `AI TRADE/Private Knowledge` có Masterbook EPUB ở trạng thái riêng tư. Chỉ kiểm kê metadata; chưa chuyển nội dung vào training, chưa xác minh giấy phép của các tài liệu gốc trong sách.

## 4. Chặn phát hành / định nghĩa còn thiếu

`BLOCKED`: native Google OAuth PKCE/callback trên Android, kênh nạp credential an toàn được xác thực chủ tài khoản, MT5-compatible runtime có khả năng đọc equity và positions thật, owner A/B isolation E2E, model/dataset có license và kết quả OOS/WF/cost/paper-forward đã duyệt, risk approval, broker-order DEMO audit và reconciliation, Android install/update/recovery cùng release signing identity. Supabase verifier hiện hữu chỉ có bằng chứng readback balance, không được gắn nhãn equity/positions PASS. The5ers không kích hoạt khi thiếu approval riêng.

**Release gate: CLOSED. Live/funded: LOCKED. APK bàn giao: KHÔNG TẠO.** Không có lệnh DEMO mới hoặc quyền tự trade được bật bởi các commit này.

# CWS AutoTrade — Android DEMO progress checkpoint (29/09/2026)

Repository: `trankhanhduy1508-maker/AI-TRADE`. **Nhánh duy nhất:** `codex/p0-covel-knowledge-audit`. Checkpoint cũ: `bd876065bc2c2ebc6dd6c7e62873c86afb3474f0`. HEAD trước checkpoint này: `e6125d941fe921bb859eeb4ea683c003a3011b82`.

## Mã đã sửa, không mở giao dịch

- `scripts/check_native_autotrade_contract.py` là QA bằng Java/JDK **source-only**, không build hay xuất bản APK. Commit `2d1ccb882dfe7a1ad9cd644eddeafb2d0004677b`.
- `src/execution/demo_readback.py` đọc DEMO balance/equity/vị thế và **kiểm tra lại trạng thái kết nối, tài khoản, server, trade_mode sau khi đọc vị thế**. Từ chối nếu broker ngắt kết nối hoặc terminal đổi tài khoản khi đọc; không có KPI Tổng Lot. Commit `ec464292a5c21bdeed22d3d6742721cf3edb85a8`.
- `src/execution/metaapi_demo_guard.py`: nguồn cloud MetaApi phải có broker `account_information.type=ACCOUNT_TRADE_MODE_DEMO` cùng server/login khớp tài khoản được cấp quyền, quyền trade rõ ràng, kết nối broker thật. Tên server chứa chữ `demo` **không tự chứng minh chế độ DEMO**. Tài liệu MetaApi chính thức: https://metaapi.cloud/docs/client/restApi/api/readTradingTerminalState/readAccountInformation/ . Commit `bd8989becc11cf759dd485ba2fde59a75f289d16`.
- `src/execution/metaapi_cloud.py` gọi guard lúc kết nối và mỗi lần đọc/gửi lệnh, kiểm lại ngay trước mutating call, invalidate phiên nếu account broker bị đổi hoặc mất quyền. Không trả chi tiết thô của exception SDK trong kết quả lệnh, tránh vô ý đưa nội dung nhạy cảm vào log. Commits `10311aa315d06178c9cc859e36aacacee93c7671` và `e6125d941fe921bb859eeb4ea683c003a3011b82`. Không tạo runtime hay cấp token MetaApi mới.

## Bằng chứng chạy thực trong workspace QA

- `PYTHONPATH=. python -m pytest -q tests/execution/test_metaapi_demo_guard.py tests/execution/test_demo_readback.py` → **37 PASS** (16 guard + 21 broker snapshot), trên fake accounts/terminal; Python compileall PASS. File `metaapi_demo_guard.py` blob `5b5f1c200f9ce33aca97e5a761ef6a334ee929b1`, test `9520c5d38f5bf715dc1d170a5ea845b2ec4dda9d`; snapshot source `8e34fab0055cf75bc64195ea5d12079f73eff7ff`, test `fd4e2ec751d0be70f5ce740b84f0a5dddf153339`. Các blob khớp chính xác file chạy test.
- `python scripts/check_native_autotrade_contract.py` → **18 Java QA checks PASS** (9 PKCE, 9 signed-manifest/recovery giả lập). Script blob `2df572c8f2f1634ab2a1f099843134c7d4bd8726` khớp chính xác bản đã chạy.
- Kiểm tra cú pháp `DemoLoginActivity.java` qua stub Android giả lập chạy được, **không phải Android SDK/Gradle build hoặc Android device E2E**, không đủ điều kiện release.
- Các test tích hợp mới trong `tests/execution/test_metaapi_cloud.py` và full repo **NOT RUN** ở runtime hiện tại. Không được ghi PASS dù source đã được GitHub xác minh readback.

## Trạng thái thực đã đọc lại

- Supabase `oziktadfeenydvgobudr`: `ai-trade-founder-mt5` ACTIVE v2, frontend native vẫn chỉ có chứng cứ response balance read-only. **Equity và positions chưa có từ broker runtime tại endpoint này**; không hiển thị giả.
- `ai_trade.runtime_config`: `enabled=false`, `demo_send_enabled=false`, `risk_profile_approved=false`; `ai_trade.order_intents=0`; private baseline có 2 dòng `REJECTED`.
- Không dùng Founder PC. Không nhận, xuất hoặc ghi password/token MT5 hay release signing key vào repository. Không thao tác LIVE/funded. Không có APK mới được build/phát hành.

## Blockers có thực trước APK hoàn chỉnh

1. **Android:** xác minh redirect Google OAuth/PKCE hợp lệ trong Supabase Auth Allow List và E2E trên thiết bị Android, login/refresh/mất mạng, upgrade giữ dữ liệu.
2. **MT5 DEMO:** backend runtime được cấp quyền kết nối broker thật bằng Login/Password/Server; readback fresh equity và toàn bộ vị thế, account isolation, disconnect/reconnect và broker order acknowledgement. MetaApi hiện thiếu bằng chứng token/account đã cấp quyền ở môi trường này; guard cố ý chặn khi `account_information.type` không có.
3. **Auto Trade:** data/model có quyền, kiểm định OOS/walk-forward/cost/paper-forward, Risk Engine, kill-switch, phê duyệt Founder, DEMO execution E2E và reconciliation; không tự đổi `REJECTED` hoặc các gate false.
4. **APK release:** owner-managed stable signing identity, kênh HTTPS update metadata được ký và pin đúng public key, Android package signer/in-place upgrade, migration/backup, recovery bằng `versionCode` lớn hơn, thử nghiệm Android thiết bị thật và xác nhận phát hành.

**Trạng thái: nguồn được cải thiện; DEMO auto-trade và APK release vẫn BLOCKED. Không phát hành debug APK để thay cho APK hoàn chỉnh.**

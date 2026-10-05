# CWS AutoTrade Android / MT5 DEMO — Checkpoint bridge 29/09/2026

Repo: `trankhanhduy1508-maker/AI-TRADE`. Nhánh duy nhất: `codex/p0-covel-knowledge-audit`.
HEAD mã nguồn trước tài liệu: `8e3f4f82469a88725eaefa4dc5ca15732384604d`.
Phạm vi: **chỉ MT5 MetaQuotes-Demo đã liên kết với Founder**. Mọi đường LIVE và lệnh broker mới vẫn LOCKED.

## 1. Thay đổi thực hiện trên nhánh

- Commit `86ed4f6d94fe48b39a009407e7146fbc54b36d4d`: bổ sung `supabase/functions/ai-trade-mt5-demo-validate/readback.mjs`, bộ giải mã cmd=3/cmd=4 chỉ đọc theo schema pinned `cloudQuant/pymt5@e7b5a8d`. Bắt buộc đúng DEMO/server, broker investor/read-only rights, dữ liệu hữu hạn, kiểm lại account trên cùng socket sau khi đọc vị thế. Xử lý rõ ràng vị thế rỗng và dữ liệu không khả dụng; lot từ raw volume / 10^8, P/L từng vị thế. Không có phương thức đặt lệnh.
- Verifier `ai-trade-mt5-demo-validate` có yêu cầu nội bộ `readback=investor_snapshot`; dùng **investor password** từ Vault, không tự fallback về master password. Giữ endpoint verify chỉ balance cũ cho tính tương thích.
- Founder `ai-trade-founder-mt5` POST `/snapshot` lấy dữ liệu trên theo tài khoản DEMO đã liên kết thuộc người gọi có Google Founder entitlement. Không chấp nhận list/amount rỗng không rõ nghĩa, stale timestamp, khác broker/server, sai investor scope hoặc lỗi upstream. Không thay dữ liệu broker bằng database lịch sử.
- Android `DemoLoginActivity` hiển thị balance, equity, số lượng vị thế, lot và P/L **từng vị thế**, thời gian readback. Không thêm KPI Tổng Lot. Thất bại sẽ xóa phần hiển thị và chặn giao dịch.
- Commit `8e3f4f82469a88725eaefa4dc5ca15732384604d`: tăng gate cho Python broker preflight, bắt buộc broker trả `is_investor=true` hoặc `is_read_only=true`, gồm test âm và mã lỗi không chứa credential.

## 2. Bằng chứng có thể kiểm tra

- [Android source-only QA run 36511373136](https://github.com/trankhanhduy1508-maker/AI-TRADE/actions/runs/36511373136) trên commit `86ed4f6`: **SUCCESS**. Log ghi 172 Python tests PASS; bộ thử Node giải mã broker PASS; 43 Java offline security checks PASS; Android SDK 36 build/merge 13 assets, biên dịch debug/release Java, lintDebug PASS; release gate từ chối khi thiếu chữ ký/phê duyệt; **không build APK**. Bằng chứng này chỉ áp dụng đúng mã nguồn ở SHA nêu trên.
- [Broker investor-only PR preflight run 36511687586](https://github.com/trankhanhduy1508-maker/AI-TRADE/actions/runs/36511687586) trên commit `8e3f4f8`: **SUCCESS**; 7 unit contract tests PASS; WebTerminal transport READY; broker DEMO readback thật báo `balanceRead=true`, `equityRead=true`, `positionsRead=true`, `brokerOrders=false`, `liveMoneyLocked=true`. Chính broker đã xác nhận investor/read-only rights theo gate mới. Không công khai số dư, tài khoản, số lệnh, position ticket hay password. `positionsRead` không khẳng định broker đang có vị thế mở.
- Supabase hiện trạng đã đọc lại: `ai-trade-mt5-demo-validate` **ACTIVE v3**, chứa module `readback.mjs`; `ai-trade-founder-mt5` **ACTIVE v4**, chứa contract investor snapshot; cả hai đã triển khai từ commit `86ed4f6`. Giữ xác thực custom tương ứng Cron/Google Founder; `verify_jwt=false` là cấu hình đã tồn tại từ trước, không được hiểu là bỏ kiểm tra.
- Read-only SQL sau deploy: `enabled=false`, `demo_send_enabled=false`, `risk_profile_approved=false`, `order_intents=0`, 2 baseline `REJECTED`.

## 3. Không được suy diễn PASS

1. **Deno broker-to-Founder-to-APK E2E:** chưa có kết quả gọi `/snapshot` với Google Founder session hợp lệ và broker thật sau deployment. Chỉ có module offline QA, deployment ACTIVE và broker Python preflight độc lập. Không gọi full bridge PASS.
2. **Google OAuth native:** mã PKCE/Keystore qua source tests; chưa xác minh cấu hình `Additional Redirect URLs` và Google consent thực trên Android. Vì callback có nonce trong path, pattern dự kiến giới hạn `vn.cws.aitrade://auth/callback/*`, cần xác minh/cấu hình trong Auth URL Configuration; tài liệu: https://supabase.com/docs/guides/auth/redirect-urls . Không thay quyền hay giả lập login.
3. **MT5 Login + Password + Server mới:** API hiện chỉ kiểm tra tài khoản `MetaQuotes-Demo` đã liên kết; chưa hỗ trợ kết nối từng tài khoản/server DEMO tùy ý từ Android, chưa có credential-onboarding E2E độc lập, session disconnect/reconnect và account isolation trên nhiều Founder.
4. **DEMO order execution:** chưa được phê duyệt. 2 model vẫn REJECTED, runtime/risk/demo-send gates false. Cần quyền dữ liệu, OOS/WF/cost/paper-forward, risk engine, kill-switch, idempotent ledger, account fencing, broker acknowledgement và reconciliation thật. Không thay Founder approval bằng CI PASS.
5. **APK stable/recovery:** không có owner-managed stable keystore/public pin/signing certificate, metadata ổn định, device E2E hoặc in-place upgrade/restore proof. Không build, đăng/upload hoặc gọi debug APK là bản bàn giao.

## 4. Hướng thực thi tiếp theo, không nghiên cứu lại repo

- Kiểm thử nội bộ HTTPS gọi verifier/Founder bằng danh tính hợp lệ theo quyền cho phép, chỉ xuất cờ PASS/FAIL, tuyệt đối không in credential hoặc số dư vào workflow/log. Nếu không có đường thực thi được phép, giữ full bridge BLOCKED; không dùng GitHub PR preflight làm API cho Android.
- Kiểm tra Auth URL Configuration và Android deep link `vn.cws.aitrade://auth/callback/<nonce>`, thử Google Founder PKCE, phiên mã hóa/refresh/logout, trên emulator/thiết bị Android thực khi có môi trường được cấp quyền.
- Xây onboarding MT5 DEMO có quyền chủ tài khoản/consent và xác minh broker trên server supported; kiểm soát rate limit, liên kết account và lifecycle; không tự hỗ trợ server khi chưa có adapter broker thật.
- Chỉ sau model/risk approval, kiểm định DEMO execution thực và ký phát hành bằng keystore do owner quản lý ngoài GitHub. Recovery cần cùng signer và versionCode lớn hơn; kiểm migration và dữ liệu giữ lại.

**Kết luận checkpoint: BRIDGE SOURCE + CLOUD DEPLOYMENT + BROKER PYTHON PREFLIGHT PASS; FULL API/APK E2E VÀ APK RELEASE CHƯA PASS. Không phát hành APK.**

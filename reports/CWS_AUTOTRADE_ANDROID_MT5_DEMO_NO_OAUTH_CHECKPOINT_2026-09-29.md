# CWS AutoTrade APK Android / MT5 DEMO — Checkpoint tiếp tục, HOÃN GOOGLE OAUTH (29/09/2026)

**Repo:** `trankhanhduy1508-maker/AI-TRADE`  
**Nhánh duy nhất:** `codex/p0-covel-knowledge-audit`  
**HEAD mã nguồn đã kiểm chứng trước checkpoint:** `a618d88c954b41beccdab3c0275462ad47b9d64e`  
**Google OAuth:** TẠM HOÃN theo chỉ thị Founder. Không sửa NativeDemoAuth, cấu hình Supabase Auth hay redirect. Không bỏ xác thực Google Founder đã tồn tại trên API.

## Công việc đã làm, không dùng máy tính Founder

1. **MT5 Login + Password + Server, backend chỉ DEMO.** Commit `e49c06b08d8ca8babef21a96a60152031f35c538` thay cách so khớp password cũ trong Vault bằng xác minh trực tiếp **mật khẩu vừa nhập** tại MetaQuotes-Demo. `/verify-demo` chỉ hoạt động với đúng account/server đang liên kết người gọi có quyền Founder; trước khi xác minh phải xóa trạng thái CONNECTED lịch sử. Verifier giới hạn body, chỉ chấp nhận chế độ `founder_verify` với mật khẩu tạm thời trong request nội bộ; tránh truy vấn Vault password ở nhánh này, không lưu credential vào database, GitHub, APK hoặc log. Broker lệnh được gọi trong verifier: bootstrap/init/login/get-account; **không có order-send**.
2. **Đường investor snapshot vẫn read-only.** Broker readback Equity, Positions/P&L qua `investor_snapshot` tiếp tục kiểm tra DEMO/server, quyền investor, xác minh lại sau khi đọc, không suy diễn vị thế rỗng từ timeout. Founder API `/snapshot` giữ đúng account bound, kiểm nguồn broker và timestamp. Android đã có phần hiển thị balance, equity, số vị thế, lot/P&L từng vị thế.
3. **Risk Engine bắt buộc.** Commit `8ab900e4385ec758c7521cc231772b7d374a76fa` đổi `ExecutionCoordinator` thành fail-closed khi thiếu IndependentRiskEngine hoặc RiskContext, kể cả khi SafetySnapshot/risk flag và kill-switch cho phép. Lưu audit `RISK_ENGINE_REQUIRED`; không gửi lệnh qua adapter. Không tự thay risk thresholds hoặc mở gate. Đường cloud engine đã yêu cầu Risk Engine; thay đổi này sửa đường coordinator đồng bộ.
4. **Sửa QA theo hành vi an toàn mới.** Run [36512880169](https://github.com/trankhanhduy1508-maker/AI-TRADE/actions/runs/36512880169) FAIL do paper integration test cũ cho phép coordinator không có Risk Engine. Commit `fbf1666d34679affeb2d89c5a779dc8f6ec8204c` sửa test yêu cầu stop-loss, context và Risk Engine; bổ sung test âm xác nhận paper broker không bị gọi khi thiếu Risk Engine. Không đảo ngược fix an toàn để làm test PASS.
5. **Không hiện readback cũ sau login lỗi.** Commit `a618d88c954b41beccdab3c0275462ad47b9d64e` xóa balance/equity/positions đang hiển thị trước khi xác minh lại mật khẩu và sau lỗi bất đồng bộ; thêm source regression test. Không sửa Google OAuth.

## Bằng chứng 29/09/2026: giới hạn phải đọc đúng

- [Android source-only QA 36513247530](https://github.com/trankhanhduy1508-maker/AI-TRADE/actions/runs/36513247530), HEAD `a618d88c954b41beccdab3c0275462ad47b9d64e`: **SUCCESS**. 176 Python offline tests PASS, 11 Node tests PASS, 43 Java offline security checks PASS; build/merge đủ 13 first-party assets; compile debug/release Java + lintDebug PASS; release gate âm PASS; **không tạo APK**. Đây là source QA/SDK compile, **không phải Android device E2E**.
- [MT5 DEMO investor probe 36513252305](https://github.com/trankhanhduy1508-maker/AI-TRADE/actions/runs/36513252305), HEAD `a618d88c954b41beccdab3c0275462ad47b9d64e`: **SUCCESS**. 7 offline unit contract tests PASS; broker WebTerminal READY, investor-only broker readback thực có cờ `balanceRead=true`, `equityRead=true`, `positionsRead=true`, `brokerOrders=false`, `liveMoneyLocked=true`, `credentialsExposed=false`. Probe **không thử** nhánh password từ APK/Founder hoặc DEMO order submission; `positionsRead=true` không có nghĩa đang có vị thế mở.
- Supabase `oziktadfeenydvgobudr` sau deploy: `ai-trade-mt5-demo-validate` **ACTIVE v4**, `ai-trade-founder-mt5` **ACTIVE v5**; mã deployment được đọc lại khớp logic `founder_verify`. `verify_jwt=false` là cấu hình custom-auth đã tồn tại: Cron header nội bộ / Google JWT + Founder entitlement được kiểm trong handler; không mở endpoint vô điều kiện.
- Read-only SQL sau deploy: `enabled=false`, `demo_send_enabled=false`, `risk_profile_approved=false`, `order_intents=0`, 2 baseline `REJECTED`, 0 model APPROVED có broker orders. Không thay đổi gate hoặc gửi lệnh.
- Google Drive `CWS AI TRADE/Private Knowledge` có một EPUB riêng tư được kiểm kê metadata; **chưa** coi đó là giấy phép huấn luyện, chưa ingest/promote model. Không đưa tên/nội dung tài liệu riêng tư vào repo.

## Các blocker độc lập còn lại, không được báo DONE

- **Backend E2E:** Chưa có thử `/verify-demo` với mật khẩu Founder nhập và `/snapshot` end-to-end qua Google Founder token hợp lệ → broker → API → APK. Đã có broker Python investor preflight độc lập và backend deployment; không đánh đồng với bridge E2E.
- **Google OAuth:** Hoãn triển khai/kiểm thử native theo chỉ thị mới. Vẫn giữ Founder entitlement, không tạo lối tắt bỏ xác thực để báo test PASS.
- **Model và DEMO execution:** Chưa có model được phê duyệt với provenance/giấy phép, OOS/WF/cost/paper-forward; risk profile và demo-send còn false. Chưa có broker DEMO execution acknowledgment, restart/retry idempotence, live reconciliation. Không tự bật gate.
- **APK release:** Chưa có keystore stable do owner quản lý, public-key pin production, chữ ký cùng identity, actual Android device install/upgrade/recovery/migration. Không build/bàn giao debug hoặc release APK khi gate thiếu. Recovery phải là cùng signer, versionCode **cao hơn**; không native downgrade.
- **Phạm vi broker:** MetaQuotes-Demo được chứng minh; các server DEMO khác cần adapter và bằng chứng riêng, không tự suy ra hỗ trợ.

**Trạng thái chính xác: MT5 DIRECT-LOGIN CODE + BROKER INVESTOR PREFLIGHT + SOURCE QA + CLOUD DEPLOYMENT PASS trong giới hạn trên. DEMO execution, Google/Android E2E và APK release vẫn BLOCKED. LIVE LOCKED.**

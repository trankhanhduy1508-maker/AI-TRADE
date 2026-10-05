# CWS AUTOTRADE — KINH NGHIỆM & GIAO VIỆC CHAT MỚI (29/09/2026)

**Repo:** `trankhanhduy1508-maker/AI-TRADE`  
**Nhánh duy nhất:** `codex/p0-covel-knowledge-audit`  
**Checkpoint đọc trước:** `reports/CWS_AUTOTRADE_ANDROID_DEMO_SAFETY_CHECKPOINT_2026-09-29.md`  
**HEAD lúc chuẩn bị handoff:** `4acba221d2c4a8769d0a6b32e3c111a213c868de` (chỉ tài liệu so với mã `a162feada1f2bb2113c2acb6bcef414a9c0d337a`). **Kiểm tra lại HEAD** vì có thể đã có commit mới.

## Yêu cầu hiện hành của Founder

Hoàn thiện APK Android CWS AutoTrade chỉ **MT5 DEMO**, có Login/Password/Server đúng tài khoản được liên kết, balance/equity/positions/lot/P&L theo broker thật, tổng lãi/lỗ và từng cặp, DEMO auto-trade có mô hình được phê duyệt + Risk Engine + kill-switch + durable intents/reconciliation; stable install/update/recovery giữ dữ liệu cùng signer. **Google OAuth đang HOÃN theo lệnh Founder:** không dành thời gian bổ sung luồng OAuth lúc này; API Founder vẫn bắt buộc phiên Google JWT/entitlement, không tạo bypass.

Thứ tự: hoàn thiện việc độc lập với OAuth → kiểm thử broker + risk/model hợp lệ → Android/E2E và ký release khi đã có điều kiện thật. Founder muốn thực thi liên tục trong lượt làm việc; không dừng để báo checkpoint trung gian, không hỏi lại bước kỹ thuật đã được giao. Không hứa xử lý ngầm sau khi phiên kết thúc.

## Trạng thái đã có bằng chứng

- **Mã nguồn Android/native:** APK-first UI có MT5 DEMO login, tài khoản, Equity, Balance, số vị thế, Lot/P&L từng vị thế và tổng theo cặp. `NativePortfolioSummary` không hiển thị KPI Tổng Lot toàn danh mục. `brokerGeneration` chặn kết quả refresh cũ ghi đè dữ liệu sau re-login.
- **Founder API:** `ai-trade-founder-mt5` **ACTIVE v6**, `/verify-demo` nhận mật khẩu trực tiếp tạm thời rồi yêu cầu verifier xác minh broker, chỉ trên account liên kết và cùng Google Founder. `/snapshot` dùng investor-only broker readback, không nâng trạng thái kết nối master-password; hậu kiểm account binding và Founder entitlement sau network. Đã đọc source deployment.
- **Verifier:** Supabase `ai-trade-mt5-demo-validate` **ACTIVE v4**. Mã nguồn có bổ sung so sánh account name/company/leverage/server build/rights trước-sau investor readback tại commit `b2fa5c24f22dfe4f07074407bcae1eceffbe2c87`, nhưng **CHƯA triển khai lên Edge** do deploy bị kiểm tra an toàn công cụ chặn. Không thử lách chặn hoặc tự nhận deployed v5. Protocol cmd=3 không có broker login độc lập: cùng server + identity fields chưa chứng minh tuyệt đối đúng tài khoản nếu các trường trùng.
- **DEMO MT5 Python:** investor-only account `trade_allowed=false` vẫn đọc được; mỗi mutation bắt DEMO + đúng login/server + trade permissions. `ExecutionCoordinator` bắt buộc Risk Engine và RiskContext. `MT5BrokerAdapter` có ledger SQLite file bền vững khi `allow_order_send=true`, dùng atomic claim `INSERT ... ON CONFLICT DO NOTHING` để chống retry cạnh tranh **chỉ khi cùng file SQLite**; không suy ra hỗ trợ đa PC/region. LIVE bị khóa.
- **QA mã mới nhất:** workflow source-only [36528569258](https://github.com/trankhanhduy1508-maker/AI-TRADE/actions/runs/36528569258), commit `a162feada1f2bb2113c2acb6bcef414a9c0d337a`, **SUCCESS: 195 Python + 16 Node tests**, standalone Java security/portfolio PASS, Android debug/release Java compile + lint PASS, release-gate âm PASS. **Không assemble/ký APK, không Android device E2E.**
- **Broker investor probe:** [36528572266](https://github.com/trankhanhduy1508-maker/AI-TRADE/actions/runs/36528572266) SUCCESS, Python + broker DEMO investor readback thực, không xác thực end-to-end Founder API/Android hoặc submit DEMO orders.
- **Read-only Supabase SQL cuối:** `runtime_config.enabled=false`, `demo_send_enabled=false`, `risk_profile_approved=false`, `order_intents=0`, `approved_models=0`. Không tự mở risk/demo-send hoặc LIVE.
- **Chưa có signed release APK** trên GitHub Releases; `product/CWS_AI_TRADE_RELEASE_APPROVAL.json` không tồn tại. `scripts/check_android_release_gate.py` + `android/release-signing.gradle` từ chối release thiếu owner-managed keystore, pinned release public key/Founder approval và E2E evidence.

## Commit đồng thời mới lúc bàn giao

- Trong khi ghi handoff, HEAD nhánh đã tăng từ `4acba221...` lên `a83e83c631137900a403178933734fe126f04791` bởi commit `fix(mt5): reject invalid or switched investor DEMO snapshot positions`, thay `src/execution/demo_readback.py`, unit tests và source QA workflow. [MT5 protocol probe 36529020136](https://github.com/trankhanhduy1508-maker/AI-TRADE/actions/runs/36529020136) SUCCESS; [Android source QA 36529015884](https://github.com/trankhanhduy1508-maker/AI-TRADE/actions/runs/36529015884) **đang chạy khi cập nhật tài liệu**. Không gọi Android QA PASS trước khi run kết thúc. Đọc diff thật của commit trước khi sửa tiếp; tránh ghi đè thay đổi đồng thời.

## Kinh nghiệm kỹ thuật quan trọng

1. **Không nhầm source PASS với sản phẩm:** unit test, Java compile, investor preflight không thay thế Google/MT5 direct-login E2E qua Edge, màn hình Android thực, broker DEMO execution acknowledgment, stable signing hay recovery.
2. **Investor readback ≠ master login:** không được ghi `CONNECTED` do investor-only snapshot; lỗi login phải xóa dữ liệu broker cũ. Mọi network readback cần đối chiếu account + Founder entitlement **sau** khi broker trả kết quả.
3. **Fail closed khi broker không rõ:** `positions=null` hoặc timeout khác với mảng rỗng thật; không lấy cache DB/mẫu thử thay dữ liệu broker; không log credential. Recheck account khi đọc qua cmd=3→cmd=4→cmd=3; đọc kỹ schema pinned và giới hạn account identity không độc lập từ cmd=3.
4. **Chống lệnh trùng cần durable claim:** precheck `get(intent)` không đủ khi hai worker cùng nhìn trống. Claim nguyên tử trong ledger **trước** mutation; `SUBMITTING` sau crash là mơ hồ, phải reconcile, không tự resend. SQLite chỉ bảo đảm cho các worker chia sẻ đúng cùng file.
5. **Protective SL là blocker chưa sửa:** checkpoint gần nhất ghi ý định bắt buộc stop-loss tại mọi đường đặt lệnh, kể cả gọi thẳng adapter, nhưng thao tác tạo unit test đã bị tool safety block nên bản sửa **KHÔNG có trong HEAD**. Không báo PASS; chỉ thực hiện nếu công cụ cho phép và phải test đầy đủ, không thay đổi gate.
6. **Không giả mạo hoặc tự duyệt mô hình:** hai baseline trước đây REJECTED, chưa có model approved với provenance/giấy phép, OOS, walk-forward, spread/slippage/cost/paper-forward. Đường DEMO auto execution chưa có xác nhận từ broker, không tự bật `enabled`, `demo_send_enabled`, `risk_profile_approved`.
7. **Đúng bản deploy:** kiểm tra source Edge sau deploy. Founder v6 đã chạy; verifier v4 chưa có same-server fencing mới vì safety blocker. Nếu công cụ chặn, tôn trọng chặn, ghi chính xác, không xoay đường khác để lách.
8. **Đúng nhánh, đúng host:** chỉ `codex/p0-covel-knowledge-audit`; main/stable/prod không chạm. Plugin/connector → API/cloud; không dùng PC Founder hoặc dịch vụ phải trả thêm phí. Không commit secret, token, keystore/EPUB riêng tư. Android update/recovery phải cùng release signer, versionCode tăng và giữ dữ liệu; debug APK không được gọi là bản release.
9. **Tránh lặp nghiên cứu:** đọc checkpoint này + báo cáo safety ở trên, kiểm HEAD và trực tiếp các file đang sửa, không ground toàn repo. TEST FAIL → tìm nguyên nhân → minimal diff → test lại; không fake PASS. Cập nhật bằng chứng và handoff lên GitHub theo mỗi bước nghiệm thu thật.

## Các phần còn thiếu để giao APK hoàn chỉnh

- Full MT5 DEMO `/verify-demo` và `/snapshot` qua Google Founder token hợp lệ → Edge verifier → broker thực → Android thực. Google OAuth native đang hoãn; không bypass quyền đang có.
- Model/risk đã phê duyệt, kiểm thử order-check, DEMO order-send và broker acknowledgment thực có retry/idempotence/reconciliation/kill-switch; không mở gate khi thiếu bằng chứng.
- Signing key ổn định do owner nắm giữ, release approval, APK ký và public-key pin; Android install/upgrade giữ data, recovery cùng signer có `versionCode` lớn hơn; kiểm thiết bị thực. Chưa có các điều kiện này thì **APK hoàn chỉnh = BLOCKED**.

## Lệnh làm việc cho chat mới

Đọc checkpoint/báo cáo, xác minh HEAD mới nhất và trạng thái QA/deployment. Ưu tiên các lỗi độc lập với Google OAuth, gồm protective SL fail-closed, ledger/reconciliation và xác thực snapshot. Dùng tool được cấp quyền; nếu deploy bị safety block thì không circumvent. Giữ demo/risk/LIVE bị khóa cho đến khi điều kiện nghiệm thu thật đạt. Chỉ bàn giao APK sau khi ký đúng identity và kiểm thử thật; nếu chưa đạt phải ghi lý do và bằng chứng, không tuyên bố hoàn tất.

# CWS AutoTrade Android / MT5 DEMO — Bằng chứng tiếp tục trước release (29/09/2026)

Repo: `trankhanhduy1508-maker/AI-TRADE`. Chỉ nhánh `codex/p0-covel-knowledge-audit`. HEAD mã nguồn đã kiểm tra: `b0dbbf34f3e82231fd2156de3520b610c535fa9a`.

Google OAuth **vẫn HOÃN** theo chỉ thị Founder; không sửa callback, consent, Auth settings hay Founder entitlement. Chính API vẫn bắt buộc Google Founder token: không tạo lối tắt xác thực. Chỉ DEMO; LIVE LOCKED.

## Thay đổi mã và phạm vi

- `0f9a55d2c1a84d72a2b8faf23f1451b2e1e2c889`: bổ sung `NativePortfolioSummary` thuần Java dùng danh sách vị thế **đã qua broker snapshot** để tính Tổng lãi, Tổng lỗ, Lãi/lỗ ròng, số cặp có vị thế, tổng hợp BUY/SELL/hỗn hợp và Lot/P&L **theo từng cặp**; giữ Lot/P&L từng vị thế. Không có KPI Tổng Lot toàn danh mục, không tạo/mock vị thế khi nguồn broker không khả dụng. Mảng vị thế rỗng được coi là 0 có xác thực; dữ liệu NaN/vô hạn, mã cặp/lot sai hoặc vượt 1000 vị thế phải fail-closed. Sửa ký tự xuống dòng trong native UI. Thêm Java và Python source regression tests.
- `b0dbbf34f3e82231fd2156de3520b610c535fa9a`: `MT5BrokerAdapter.connect()` từ chối DEMO account thiếu login/server hợp lệ, không đặt `_bound_identity=None` rồi bỏ qua identity fencing; `_assert_demo_account()` chặn khi thiếu định danh và kiểm lại danh tính trước mỗi broker mutation. Cập nhật 3 fake-terminal test fixtures có DEMO login/server; thêm 7 test âm missing identity và 2 test âm account switch ngay sau order_check. Không thay LIVE lock hoặc quyền đặt lệnh. Cập nhật QA workflow chỉ để bắt đúng file kỹ thuật ảnh hưởng.
- Trước đó `e49c06b`: MT5 password từ APK gửi nội bộ tạm thời để broker xác minh trên đúng account đã liên kết; không lưu lại vào GitHub/thiết bị/Vault trong nhánh direct. Supabase `ai-trade-mt5-demo-validate` ACTIVE v4, `ai-trade-founder-mt5` ACTIVE v5 (đã xác minh source trên deploy ở checkpoint trước).

## QA, tuyệt đối không phóng đại

- [CWS Android source-only QA 36515802799](https://github.com/trankhanhduy1508-maker/AI-TRADE/actions/runs/36515802799) tại `0f9a55d2`: SUCCESS, 178 Python tests, 11 Node tests, standalone NativePortfolioSummary Java check, Android compile/lint và gate không ký PASS. **Không có APK**.
- [CWS Android source-only QA 36516009533](https://github.com/trankhanhduy1508-maker/AI-TRADE/actions/runs/36516009533) tại `b0dbbf34f3e82231fd2156de3520b610c535fa9a`: SUCCESS, **187 Python tests**, **11 Node tests**, standalone Java security và portfolio tests PASS, Android offline asset/merge và debug/release Java compile, lintDebug PASS, release gate âm PASS, không build APK.
- [MT5 DEMO Protocol Probe 36516012752](https://github.com/trankhanhduy1508-maker/AI-TRADE/actions/runs/36516012752) tại `b0dbbf34f3e82231fd2156de3520b610c535fa9a`: SUCCESS cho investor-only Python broker readback protocol; độc lập với Deno full Founder/API/Android và **không gửi DEMO order**.
- Supabase SQL chỉ đọc sau test: `enabled=false`, `demo_send_enabled=false`, `risk_profile_approved=false`, `order_intents=0`, `approved_models=0`. Không bật runtime, không sửa Main/Stable/Production. Android QA là source-only: không chứng minh thiết bị thực, UI, app install, update, recovery hay broker/Google E2E.

## Gate RELEASE vẫn thực sự chặn

1. `product/CWS_AI_TRADE_RELEASE_APPROVAL.json` chưa tồn tại trên nhánh; `scripts/check_android_release_gate.py` và `android/release-signing.gradle` từ chối assembleRelease khi thiếu Founder approval, owner-managed external release keystore/public key pin và toàn bộ bằng chứng E2E. Không tạo tệp PASS giả hoặc ký bằng debug key.
2. Google OAuth native/device E2E đang **hoãn**; token Founder hợp lệ chưa được thử trên Android thực. Không thể coi API `/verify-demo` hoặc `/snapshot` là full E2E khi chưa có một phiên thực qua broker và APK.
3. Chưa có model và dữ liệu đã được phê duyệt OOS/WF/cost/paper-forward; DEMO send/risk gate đang false. Chưa được phép phát sinh DEMO order, chưa có broker acknowledgment, retry/idempotence và recovery trên broker thật.
4. Chưa có Android emulator/thiết bị và signing identity được cấp để nghiệm thu cài đặt, nâng cấp giữ phiên/data cùng chứng chỉ và bản recovery có versionCode lớn hơn. Không gọi APK production/hoàn chỉnh khi còn blocker.

**Trạng thái:** Native DEMO portfolio và broker account identity fencing đã có source QA PASS. Backend read-only ACTIVE; broker investor probe PASS. FULL APK + DEMO AUTO EXECUTION + Android E2E / RELEASE **NOT PASS**; không phát hành APK.

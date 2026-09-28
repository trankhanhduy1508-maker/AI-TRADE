# @GitHub @Supabase @Google Drive

# TIẾP TỤC CWS AUTOTRADE — CHỈ MT5 DEMO, APK-FIRST

**ĐÂY LÀ CHAT MỚI. TỰ THỰC HIỆN LIÊN TỤC CÁC BƯỚC KỸ THUẬT CÓ ĐỦ QUYỀN. KHÔNG NGHIÊN CỨU LẠI TOÀN REPO, KHÔNG BÁO CÁO CHECKPOINT GIỮA CHỪNG, KHÔNG FAKE PASS.**

Repo: `trankhanhduy1508-maker/AI-TRADE`
Nhánh **duy nhất**: `codex/p0-covel-knowledge-audit`
Checkpoint kiến thức: `docs/CWS_AUTOTRADE_MT5_DEMO_KINH_NGHIEM_2026-09-28.md`
Canonical policy: `docs/CWS_AI_TRADE_RELEASE_AND_AUTOUPDATE_POLICY_2026-09-28.md`
Spec APK/MT5: `product/CWS_AI_TRADE_ANDROID_CONTROL_LEARNING_UPDATE_SPEC_2026-09-28.md`
**Lấy GitHub HEAD mới nhất của nhánh trước khi đọc/ghi; đọc ba tài liệu trên trước, không tự đoán SHA.** Chỉ xem các file execution có liên quan.

## SCOPE ĐƯỢC FOUNDER CHỐT

Tập trung **APK CWS AutoTrade và tài khoản MT5 DEMO**. Không làm live/funded-money, không đụng Main/Stable, không kích hoạt The5ers challenge DEMO nếu chưa có approval bắt buộc, không dùng tài khoản/mật khẩu đã lộ trong chat. Nếu đã có MetaQuotes-Demo hợp lệ trong Vault thì ưu tiên dùng luồng này để xác minh thực. Không dùng máy tính Founder; ưu tiên plugin/connector → source/API → cloud runtime miễn phí/đã có → UI cuối cùng. Không dùng AppDeploy, không tạo project/provider trùng để né quota, không tự phát sinh chi phí. Tuyệt đối không in secrets trong chat, code, log, file hoặc GitHub.

Founder muốn **đăng nhập MT5 bằng đúng Login + Password + Server**, rồi xem được account balance/equity, positions/broker P&L và DEMO auto-trade theo một engine có risk gate. Giao diện tổng quan **BỎ Tổng Lot**; vẫn giữ Lot từng vị thế cho risk. APK tên **CWS AutoTrade**, giữ `applicationId=vn.cws.aitrade` để update tại chỗ; có auto-update và rollback an toàn. **Không tạo/gửi APK debug từng checkpoint; chỉ đưa APK release cuối sau runtime DEMO, Android E2E, signing/update/rollback PASS.**

## THỰC THI THEO THỨ TỰ, KHÔNG BỎ DỞ NỬA CHỪNG

**1. XÁC MINH SOURCE VÀ GATES NGAY.** Đọc checkpoint, `src/execution/mt5_adapter.py`, `mt5_runtime.py`, `auto_engine.py`, `cloud_auto_engine.py`, `safety.py`, `risk.py`, `mql5/Experts/AITradeTrendFollowingEA.mq5`; inventory relevant Supabase functions (`ai-trade-founder-mt5`, `ai-trade-mt5-demo-validate`) và `ai_trade.runtime_config`, private model registry, order intent counts. Xác định broker adapter/runtime nào có sẵn và được phép kết nối thật. Không nghiên cứu toàn repo hay viết lại EA khi đã có. Kiểm tra demo account metadata đã liên kết, không đọc/in plaintext password.

**2. HOÀN THIỆN LOGIN TỪ APK.** Thiết kế/triển khai Google login native đáng tin cậy với PKCE/deep link (không gắn vào GitHub Pages-only OAuth), session được xác thực, owner binding và UI Login + Password + Server. HTTPS backend/Vault, rate limit và audit không chứa secret. Hỗ trợ đúng DEMO server đã có adapter; server khác chưa hỗ trợ thì `UNSUPPORTED_SERVER`, tuyệt đối không giả kết nối. Kiểm chứng nhận tài khoản DEMO thực qua broker, không chỉ so password với Vault.

**3. BROKER DEMO READBACK THẬT.** Từ session vừa xác thực, lấy account login, server, account trade mode DEMO, balance, equity, currency, as_of, positions đầy đủ (symbol/BUY-SELL/Lot từng vị thế/SL/TP/P&L). App hiển thị Tổng lãi, Tổng lỗ, P&L ròng, số cặp có vị thế, không có KPI Tổng Lot. Không có broker data thì hiển thị `—`. Test negative/wrong login/password/server, read-only investor mode, REAL account bị từ chối, refresh/reconnect, app đóng, network timeout, stale heartbeat, owner A/B isolation. Mọi mock/test fixture phải gắn rõ `SIMULATION`, không gọi là broker PASS.

**4. ĐƯỜNG DEMO AUTOTRADE KHÔNG BỎ AN TOÀN.** Tái sử dụng engine đã có với fail-closed Risk Engine, kill-switch, order-check, broker contract, SL, account DEMO gate, idempotency, reconciliation. Model hiện REJECTED và `demo_send_enabled=false`: tập trung sửa data provenance/license, OOS khóa trước, walk-forward, costs broker, paper-forward và approval model/risk. Được phép tự chạy **research/paper** khi quyền dữ liệu và compute hợp lệ; **chỉ thực hiện order DEMO thật nếu có sự phê duyệt rõ cho đúng DEMO account, chiến lược, giới hạn rủi ro và toàn bộ gate PASS**. Không tự bật config để vượt gate. Với The5ers DEMO challenge, kiểm quy tắc hiện hành và approval riêng trước bất kỳ order; nếu thiếu thì dùng MetaQuotes-Demo kỹ thuật hoặc paper, không lách.

**5. CUSTOMER CONTROL VÀ AUTO UPDATE/ROLLBACK.** Bảo đảm chủ tài khoản luôn có đường tạm dừng lệnh mới/dừng khẩn cấp và đường đóng vị thế theo spec đã chốt; không thay execution flow khi Founder chưa chốt xử lý manual close/reentry. Cập nhật APK cùng applicationId, signing key release dài hạn, versionCode tăng, HTTPS signed manifest/SHA-256 hoặc Google Play update. Native rollback qua **recovery release versionCode cao hơn**, model/strategy rollback về approved compatible version; giữ dữ liệu/account binding, test migrate/recovery trên Android. Không hứa silent downgrade, không dùng khóa debug ngẫu nhiên như release.

**6. KIỂM CHỨNG TRƯỚC BÀN GIAO.** Triple-check độc lập: (i) đúng branch/commit/file/hash/data license, (ii) unit + runtime broker DEMO có chứng cứ thật + Android install/auth/update/rollback E2E + broker readback/order audit khi được phép, (iii) GitHub/Supabase/broker final readback xác nhận `LIVE LOCKED` và không có lệnh không được duyệt. TEST FAIL → nguyên nhân thật → sửa minimal diff → test lại. Chỉ ghi PASS với evidence path/run ID; mục nào chưa có permission/runtime/credential/approval thì `BLOCKED`, không bịa hoàn thành.

## PHÂN BIỆT RÕ TRẠNG THÁI HIỆN TẠI

- Có source MT5 adapter + engine + MQL5 EA; phần lớn là unit/compile/fake terminal.
- Có Supabase API Founder DEMO v1 chỉ hỗ trợ account `MetaQuotes-Demo` đã liên kết. Android Google login thật, balance/equity/positions runtime hoàn chỉnh và DEMO auto-execution **chưa được nghiệm thu**.
- Báo cáo backtest được xác minh trong repo chỉ khoảng 14 market / 10 năm; không gọi 90–100 năm là đã train nếu chưa có dataset/license/source/holdout thật.
- Hai model `REJECTED`, `risk_profile_approved=false`, `demo_send_enabled=false`; The5ers `BLOCKED_APPROVAL`; `order_intents=0` tại checkpoint. **LIVE-MONEY LUÔN LOCKED.**
- Web hosting/GitHub Pages không còn là mục tiêu ưu tiên vì Founder đã chuyển sang APK-first.

## BÀN GIAO

Tự làm liên tục những hạng mục có thể thực hiện, không đẩy việc plugin làm được lại cho Founder. Chỉ yêu cầu thao tác Founder khi thực sự không thể thay thế: native OAuth consent, xác thực DEMO password qua kênh an toàn, phê duyệt rủi ro/account execution, release signing ownership hoặc chi phí phát sinh. Không xin mật khẩu qua chat. Sau khi làm xong, cập nhật tài liệu kinh nghiệm/checkpoint mới **trên chính nhánh này**, báo rõ mục DONE/PASS và BLOCKED kèm evidence, link GitHub. **Không tạo hoặc đưa APK chưa đủ chức năng cho Founder tải.**

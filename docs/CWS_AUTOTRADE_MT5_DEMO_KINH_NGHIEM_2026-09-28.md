# CWS AutoTrade — kinh nghiệm bàn giao, chỉ MT5 DEMO (2026-09-28)

**Founder scope mới nhất:** tập trung APK CWS AutoTrade, kết nối **MT5 DEMO** bằng Login + Password + Server, kiểm chứng broker thật, xây DEMO auto-trade có kiểm soát, auto-update và rollback. **Không gửi lệnh LIVE/funded, không bật live-money.** The5ers DEMO challenge nếu dùng sau này vẫn phải qua gate điều khoản/approval riêng; không lấy việc có mật khẩu làm quyền vượt qua gate.

Repo `trankhanhduy1508-maker/AI-TRADE`; **chỉ nhánh `codex/p0-covel-knowledge-audit`**. Checkpoint nguồn trước khi ghi tài liệu: `5de8beb642320f5338ed2957889946cd271c860a`. Khi tiếp nhận hãy đọc HEAD mới nhất, không nghiên cứu lại cả repo.

## 1. Những gì thực sự đã có

1. APK native Android shell: `android/app/src/main/java/vn/cws/aitrade/MainActivity.java`, `android/app/build.gradle`, `scripts/build_cws_trade_static.py`, `google-sites/cws-ai-trade/`. Native app label đã đổi thành **CWS AutoTrade**, giữ `applicationId=vn.cws.aitrade` phục vụ update về sau. Dashboard **đã bỏ KPI Tổng Lot**, giữ 4 chỉ số Tổng lãi / Tổng lỗ / Lãi-lỗ ròng / Số cặp có vị thế; Lot từng cặp/vị thế vẫn giữ vì Risk Engine cần. Static HTML được đóng gói local, không phụ thuộc HTML Supabase Edge vốn trả `text/plain`.
2. Web-only source smoke tại commit `4ee19bbbda989cc14f7b9f09940d139d3e5285f6`: **28/28 Node tests PASS**, static builder và PWA content-hash smoke PASS; **không phải Android install E2E, không phải broker execution PASS**. Workflow `.github/workflows/cws-ai-trade-android-debug.yml` hiện là gate-only: **không tự build/phát APK**. Founder không muốn cài APK debug từng lần; chỉ bàn giao APK hoàn chỉnh sau DEMO auto-trade/update/rollback E2E và ký release ổn định.
3. MT5 Python execution source đã tồn tại, **không viết lại từ đầu**: `src/execution/mt5_adapter.py` (DEMO-only, `LIVE` hard lock, `order_check` trước `order_send`, idempotent intent ledger), `mt5_runtime.py` (closed bars/ticks/spread/P&L), `auto_engine.py`, `cloud_auto_engine.py`, `metaapi_cloud.py`, `metaapi_runtime.py`, `risk.py`, `safety.py`, `recovery.py`, `position_state.py`, `position_controller.py`, `the5ers_bootcamp_guard.py`. MQL5 EA tại `mql5/Experts/AITradeTrendFollowingEA.mq5`. Phần lớn bằng chứng trước đây là unit/compile/fake terminal, **không phải order DEMO thực**.
4. Supabase project `oziktadfeenydvgobudr`: `ai-trade-founder-mt5` Edge v1 ACTIVE. `GET /status`, `POST /verify-demo` yêu cầu Supabase Google bearer session + Founder entitlement; so mật khẩu với Vault và gọi `ai-trade-mt5-demo-validate` để đọc broker **MetaQuotes-Demo đã liên kết**. HTTP negative-path không bearer trả 401; origin lạ bị 403. Không có endpoint broker order ở chức năng này. Frontend ở `google-sites/cws-ai-trade/mt5-login.html` + `founder-mt5.js` chỉ hoạt động trên GitHub Pages origin đã định, **chưa có OAuth native APK callback được thử**. Existing verifier đọc login/server/balance, **chưa có bằng chứng equity/positions readback đầy đủ trong APK**.
5. Repo có nhiều nghiên cứu/backtest, Masterbook và knowledge. `reports/MULTIASSET_10Y_BACKTEST_2026-09-27.md` xác nhận khoảng **10 năm x 14 thị trường**, không xác minh tuyên bố 90–100 năm hay việc candidate đã train. Một số backtest `GROSS_ONLY` hoặc chỉ research cost proxy; không được suy ra lợi nhuận broker-net. Hai model private baseline đang `REJECTED`; dữ liệu hạn chế license không được dùng để train/trade.
6. SQL readback ngày 2026-09-28: `ai_trade.runtime_config.enabled=false`, `demo_send_enabled=false`, `risk_profile_approved=false`, `order_intents=0`, `approved_trade_models=0`, `rejected_models=2`, The5ers `BLOCKED_APPROVAL`. Đây là **gates đúng**, không phải lỗi cần bỏ qua. Probe workflow success chỉ chứng minh probe đó đạt tiêu chí của nó; không đồng nghĩa tạo được phiên broker DEMO hoặc gửi/khớp lệnh.

## 2. Nguyên nhân kỹ thuật tại sao có Login/Password nhưng chưa Auto Trade

- **Credential ≠ terminal/adapter chạy được.** `MT5 Python` thường cần terminal MT5 tương thích và một máy Windows/container có GUI/IPC phù hợp; Android MT5 không chạy trực tiếp EA MQL5 theo kiểu desktop. Các probe terminal trước đây từng gặp `(-10005, 'IPC timeout')`. Không tự động dùng máy Founder hoặc bí mật xuất hiện trong chat.
- **Tài khoản đã liên kết ≠ broker session hiện tại.** API Founder hiện chỉ xác minh DEMO MetaQuotes có sẵn trong Vault, không onboarding arbitrary server. Cần real handshake, đúng login/server/trade mode, đọc account balance/equity/positions/timestamp và xử lý timeout/reconnect. Cấm dùng historical `last_verified_at` làm trạng thái CONNECTED thời gian thực.
- **Có engine code ≠ chiến lược được phê duyệt.** Model `REJECTED`, dữ liệu/chi phí/chốt risk chưa được duyệt. Nên cho chạy research/paper read-only tự động trong thời gian chuẩn bị; chỉ thực thi DEMO khi đủ gate và Founder phê duyệt chính xác cấu hình demo. Không tự thử lệnh bằng cách bỏ Risk Engine/kill-switch.
- **APK ≠ engine 24/7.** APK quản lý tài khoản, UI, bộ nhớ cục bộ và điều khiển. Broker execution chạy trên MT5-compatible runtime đã được kiểm chứng, độc lập với việc điện thoại khóa màn hình; nếu chưa có cloud Windows/runtime khả thi thì ghi BLOCKED có evidence, không lách chi phí/quota bằng provider trùng.

## 3. Đường triển khai MT5 DEMO, ngắn nhất trên source đã có

**T1 — Ground có giới hạn.** Xem 4 file lõi (adapter, runtime, engine, policy/spec), GitHub HEAD + Supabase gates + inventory broker adapter; tái sử dụng, không tạo app/branch/engine mới. Tìm tài khoản DEMO đã có qua metadata an toàn, **không đọc/in credential**. Phân biệt MetaQuotes-Demo thông thường với The5ers evaluation DEMO. The5ers chỉ thuộc luồng riêng có approval theo điều khoản hiện hành.

**T2 — Đường đăng nhập native an toàn.** Google Auth native với PKCE/app link hoặc phương thức chính thức thích hợp, owner binding; 3 trường Login/Password/Server. Xác thực bằng session broker thật qua backend/Vault; không đưa password/token/service role trong APK/JS/GitHub/log. Chỉ giữ trạng thái online khi có heartbeat/readback gần đây. Kiểm tra tài khoản thực có đúng DEMO trade mode. Đối với bất kỳ server không được backend hỗ trợ, báo `UNSUPPORTED_SERVER`, không giả CONNECTED.

**T3 — MT5 DEMO readback.** Cùng broker adapter lấy balance, equity, currency, server, account mode và positions (ticket, symbol, side, individual Lot, floating P/L, SL/TP). Không hiển thị KPI Tổng Lot. Hiển thị P/L aggregate chỉ khi dữ liệu từ broker đầy đủ; thiếu thì `—`. Tất cả trạng thái có as_of/source. Test sai mật khẩu/server, viewer/investor password, LIVE account, trễ heartbeat, ngắt mạng, privacy multi-tenant.

**T4 — DEMO auto-trade theo guard thật.** Sử dụng `DemoAutoTradeEngine` / `CloudAutoTradeEngine` + `MT5BrokerAdapter` chứ không tạo đường `order_send` mới từ Android. Dữ liệu huấn luyện phải có quyền, OOS khóa trước, walk-forward, broker costs, paper forward và model APPROVED. Cần risk profile được duyệt, kill-switch, account DEMO match, reconciliation, SL hợp lệ, idempotent intents và account permission; The5ers approval chỉ nếu chọn challenge DEMO. Test fake/paper trước, rồi DEMO forward thật có order/readback khi và chỉ khi đã đủ phê duyệt. Nếu gate chưa đủ: `ABSTAIN/LOCKED`, không tự bật `demo_send_enabled`.

**T5 — Quyền khách/rollback/update.** Cho chủ account dừng lệnh mới và đóng lệnh thủ công khi execution spec đã được Founder chốt; audit, reconcile và chặn tự mở lại ngay. APK update tại chỗ cần cùng applicationId, cùng release signing key, versionCode tăng, phát hành qua Play In-App Updates hoặc HTTPS metadata + Android PackageInstaller có user consent. Model/strategy rollback về bản APPROVED tương thích; native APK recovery là **release có versionCode mới cao hơn**, không hứa cài lùi version tại chỗ. Kiểm thử Android migration/update/recovery bằng dữ liệu thực có sự đồng ý.

## 4. Chú ý bài học lỗi đã gặp

- Edge Function Supabase phục vụ `text/html` thành `text/plain`; không dùng nó làm frontend HTML. APK local static HTML đã đi theo đường riêng.
- GitHub Pages chưa bật và Web OAuth origin cũ không tương thích native APK; đừng lặp lại “bật GitHub Pages” khi scope mới là APK-first.
- Web smoke ban đầu FAIL sau khi sửa `app.js` vì test kỳ vọng frozen Edge v11 trùng byte với canonical static; đã sửa contract để phân biệt **Edge legacy vs static mới**. Khi sửa app tiếp, giữ quy tắc này.
- Android debug APK ký tạm từng CI không thể update-in-place giữa các khóa ký khác nhau. **Không build/gửi thêm APK debug khi chưa đủ release gate**.
- Kết quả backtest OOS dương nhưng WF âm hoặc cost `GROSS_ONLY` không được promote. Không dùng dataset nguồn bị cấm ML; không resurrect model `REJECTED`. Không dùng AI để tự thay Risk Engine/approval.
- Khi Founder nói `MT5 DEMO thôi`, **không thao tác tài khoản LIVE/funded hoặc gửi lệnh trên tài khoản thử thách The5ers khi thiếu approval**. Không chuyển toàn bộ dự án sang provider failover; tập trung đường broker/engine đang có.

## 5. Bằng chứng để bàn giao

Triple-check: (1) exact repo/branch/commit/hash, nguồn license và nguồn credential (chỉ metadata), (2) unit/static/smoke + runtime broker DEMO thật có log đã lọc bí mật, (3) GitHub HEAD/Supabase gates/broker state/action audit readback. Mỗi PASS phải chỉ được artifact/test ID thực chứng; ERROR/UNKNOWN là BLOCKED. Không cam kết tính năng Auto Trade hoàn tất chỉ từ file source hoặc workflow PASS.

**Canonical chính sách:** `docs/CWS_AI_TRADE_RELEASE_AND_AUTOUPDATE_POLICY_2026-09-28.md`; spec MT5 Login/Password/Server: `product/CWS_AI_TRADE_ANDROID_CONTROL_LEARNING_UPDATE_SPEC_2026-09-28.md`. Các mốc cũ “Web App first” đã bị quyết định APK-first mới nhất thay thế.


## 6. Checkpoint source DEMO / Android bổ sung (2026-09-28)

Đã thêm readback account/vị thế DEMO có so khớp login/server, kiểm số dư/equity, Lot từng vị thế và P/L; adapter kiểm account DEMO lại trước/sau order_check và lúc đọc vị thế. Evidence cùng trạng thái PASS/BLOCKED chính xác nằm tại [`reports/CWS_AUTOTRADE_ANDROID_DEMO_SOURCE_EVIDENCE_2026-09-28.md`](../reports/CWS_AUTOTRADE_ANDROID_DEMO_SOURCE_EVIDENCE_2026-09-28.md). **Chưa có broker runtime PASS, Android E2E PASS, Auto Trade approval hay APK release**. Không đổi các gate Supabase, không đọc/ghi mật khẩu và không thay nhánh.


### Bổ sung readback connected check

Commit `559fe83fd5bbb5bba21800536e89d6f38a6f30a4` buộc `terminal_info().connected` trước readback, không chấp nhận account cache khi terminal mất kết nối. Standalone fake-terminal unit 16 PASS; xem evidence trong `reports/CWS_AUTOTRADE_ANDROID_DEMO_SOURCE_EVIDENCE_2026-09-28.md` phần 5. Chưa chứng minh broker runtime, Android OAuth, auto-trade thực hoặc signed release. Workflow `6d2728fd068e5b2e877b786b6a2c295b30ae3d2b` cập nhật diễn đạt APK-first, vẫn không build APK.

## 7. Checkpoint native Android + Supabase DEMO read-only (2026-09-28)

Đã bổ sung màn hình native MT5 DEMO dùng Google OAuth trên browser ngoài WebView (PKCE/nonce), trường Login/Password/Server, backend Founder v2 trả balance/currency chỉ sau xác minh broker mới; Equity/positions chưa có và không fake. Thư viện native release verifier bước đầu xác minh signed metadata, SHA-256 và versionCode monotonic, nhưng APK installer, signer production, migration/recovery và Android E2E vẫn chưa có. Java QA 18 phép thử PASS với mock; không phải thiết bị/broker PASS. Kiến thức và đường dẫn evidence chi tiết: `reports/CWS_AUTOTRADE_ANDROID_DEMO_SOURCE_EVIDENCE_2026-09-28.md` mục 6. **Release gate vẫn đóng; không phát hành APK.**

## 8. Checkpoint an toàn MT5 DEMO / Android (29/09/2026)

Đã sửa race lúc readback MT5 (kiểm broker trước/sau positions), thêm MetaApi guard yêu cầu broker xác nhận rõ `ACCOUNT_TRADE_MODE_DEMO` cùng Login/Server, chống account switch và lọc thông tin exception SDK. QA source-only: 37 Python unit tests + 18 Java checks PASS. Không có Android/broker thực E2E, MetaApi full-repo integration chưa chạy, risk/model approval chưa có, không build/phát hành APK. Xem `reports/CWS_AUTOTRADE_DEMO_ANDROID_PROGRESS_2026-09-29.md`. Live/funded LOCKED, mọi quyền gửi lệnh DEMO vẫn tắt.

## 9. Bàn giao mới nhất ngày 29/09/2026: broker DEMO readback thật, Android QA và chat mới

**Tài liệu chính thay thế checkpoint cũ:** docs/CWS_AUTOTRADE_ANDROID_MT5_DEMO_HANDOFF_2026-09-29.md. **Prompt giao việc:** prompts/CWS_AUTOTRADE_ANDROID_MT5_DEMO_CHAT_MOI_2026-09-29.md. Lấy GitHub HEAD mới nhất của nhánh codex/p0-covel-knowledge-audit trước khi làm, không dùng cứng SHA cũ.

Bằng chứng mới quan trọng: workflow https://github.com/trankhanhduy1508-maker/AI-TRADE/actions/runs/36468844897 SUCCESS với investor-only/OIDC lease: balanceRead=true, equityRead=true, positionsRead=true trên broker MT5 DEMO thật, brokerOrders=false, không công bố giá trị tài khoản. Đây là PASS cho preflight read-only trong cloud, **KHÔNG** chứng minh API Founder/APK hiện đã có equity/positions hoặc đã gửi lệnh. Android source-only https://github.com/trankhanhduy1508-maker/AI-TRADE/actions/runs/36468168629 PASS 166 Python offline tests, 43 Java checks, compile debug/release, lint, WebView assets và release gate; **không build APK**. Supabase Founder v3 /snapshot vẫn chỉ trả balance, lease investor-only v1 ACTIVE. Risk/model approval và DEMO send đều đang khóa, hai baseline REJECTED, chưa có lệnh. Nội dung chi tiết, kiến trúc, bug fixes và thứ tự tiếp tục nằm trong tài liệu bàn giao mới.

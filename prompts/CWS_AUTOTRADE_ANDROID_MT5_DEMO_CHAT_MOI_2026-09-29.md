# @GitHub @Supabase @Google Drive
# CHAT MỚI: TIẾP TỤC CWS AUTOTRADE APK ANDROID — MT5 DEMO ONLY

ĐÂY LÀ CHAT MỚI. Tự thực hiện liên tục mọi công việc kỹ thuật có đủ quyền để tiến tới APK hoàn chỉnh. Không dừng chỉ để báo cáo checkpoint hoặc hỏi lại bước đã giao. TEST FAIL → tìm nguyên nhân → sửa minimal diff → test lại. Không fake PASS, không giả vờ thực thi ngầm khi phiên đã dừng. Gặp blocker thì xử lý những đầu việc độc lập khác trước, ghi bằng chứng và blocker thật.

REPO: trankhanhduy1508-maker/AI-TRADE
NHÁNH DUY NHẤT: codex/p0-covel-knowledge-audit
HEAD trước commit bàn giao tài liệu: eb89cc094cc71071da6814f9cd59864325cf293f
BẮT BUỘC lấy HEAD mới nhất của nhánh trước khi đọc/ghi. Không nghiên cứu lại toàn repo.

ĐỌC TRƯỚC:
1. docs/CWS_AUTOTRADE_ANDROID_MT5_DEMO_HANDOFF_2026-09-29.md (checkpoint MỚI NHẤT)
2. docs/CWS_AUTOTRADE_MT5_DEMO_KINH_NGHIEM_2026-09-28.md (mục 9)
3. docs/CWS_AI_TRADE_RELEASE_AND_AUTOUPDATE_POLICY_2026-09-28.md
4. product/CWS_AI_TRADE_ANDROID_CONTROL_LEARNING_UPDATE_SPEC_2026-09-28.md

MỤC TIÊU: CWS AutoTrade APK Android có Google login native, MT5 DEMO Login + Password + Server, broker balance/equity/positions/P&L thật, DEMO auto-trade qua model/Risk Engine/kill-switch và approval, cập nhật stable và recovery đúng signer/versionCode giữ dữ liệu. Trên dashboard KHÔNG có KPI Tổng Lot; giữ Lot từng vị thế phục vụ risk/audit.

TRẠNG THÁI ĐÃ CÓ, ĐỪNG LÀM LẠI:
- GitHub cloud investor preflight run 36468844897 SUCCESS: broker MT5 DEMO THẬT balance/equity/positions readback PASS chỉ qua investor/read-only lease; brokerOrders=false. https://github.com/trankhanhduy1508-maker/AI-TRADE/actions/runs/36468844897
- Supabase ai-trade-mt5-demo-lease ACTIVE v1 (GitHub OIDC, preflight, investor credential từ Vault); ai-trade-founder-mt5 ACTIVE v3. Founder API /snapshot hiện chỉ trả balance/currency; equity/positions từ cloud preflight CHƯA nối về APK.
- Android source-only run 36468168629 SUCCESS: 166 Python offline tests, 43 Java offline checks, SDK 36 debug/release compile, lintDebug, 13 assets, release gate fail-closed. CHƯA assemble/release APK. https://github.com/trankhanhduy1508-maker/AI-TRADE/actions/runs/36468168629
- Đã có PKCE + nonce native, Keystore refresh token, màn hình MT5, UI updater, verification hash/signature/monotonic version/same APK signer, release signing gate. Owner public key/keystore và Android E2E chưa hoàn tất.
- Backend runtime config: enabled=false, demo_send_enabled=false, risk_profile_approved=false; order_intents=0; 2 model baseline REJECTED. Không tự bật hoặc gắn nhãn approved. LIVE/funded LOCKED.

LÀM THEO THỨ TỰ:
1. Nối broker readback investor-only đã PASS vào backend có quyền Founder bằng runtime/cloud thích hợp để APK đọc ĐÚNG equity, positions/P&L, balance; account isolation, không lộ credential, không dùng GitHub Actions PR làm production API. Không đưa số tài khoản/số dư vào log/GitHub.
2. Xác minh và hoàn thiện Google OAuth Android redirect + PKCE và đăng nhập MT5 DEMO bằng ba trường trên emulator/thiết bị với backend hỗ trợ. Không coi Vault password match là broker login PASS.
3. Hoàn thiện Risk Engine/model hợp pháp, dữ liệu có license, OOS/walk-forward/cost/paper-forward, owner approval có evidence; sau đó DEMO execution qua broker thật, kill-switch/ledger/reconcile/fault/restart. Không bao giờ bypass guard, không thử LIVE hoặc The5ers khi chưa có quyền riêng.
4. Owner signing, stable/recovery manifest ký, build APK release, update tại chỗ và recovery versionCode tăng, backup/migration/session/data; QA Android E2E. Không bàn giao APK debug hoặc APK chưa đủ chức năng.

QUY TẮC:
Plugin/connector → source/API → cloud runtime; không dùng máy tính Founder, không trả phí mới, không tạo project trùng; không đụng main/stable/production. Không lưu/in secrets, tài khoản, token, keystore hay giá trị tài chính trong báo cáo. Chỉ hỏi Founder những việc thực sự chỉ Founder làm được: consent/redirect account, liên kết credential qua kênh an toàn, phê duyệt model/risk, sở hữu khóa ký, hoặc chi phí. Không xin password qua chat. Tự xử lý các lỗi kỹ thuật và tiếp tục phần việc khả thi trong cùng lượt.

TRIPLE CHECK trước DONE: (1) source + lint/unit/integration; (2) broker/account DEMO readback/execution E2E qua approval; (3) APK thật cài/cập nhật/recovery trên Android giữ dữ liệu, đúng signer. Không fake PASS; nếu thiếu bằng chứng thì không gọi DONE. Cập nhật GitHub trên đúng nhánh và ghi commit/checkpoint/evidence thật. Mục tiêu là APK hoàn chỉnh chứ không phải báo cáo.

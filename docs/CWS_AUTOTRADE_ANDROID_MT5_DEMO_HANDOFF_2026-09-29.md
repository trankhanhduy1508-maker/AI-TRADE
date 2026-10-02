# CWS AUTOTRADE — KINH NGHIỆM VÀ CHECKPOINT APK/MT5 DEMO — 29/09/2026

> **CẬP NHẬT READ-ONLY BROKER QA (29/09):** source commit `a83e83c631137900a403178933734fe126f04791` tăng kiểm soát `src/execution/demo_readback.py`: tối đa 1000 vị thế, ticket duy nhất đúng định dạng, mã cặp đúng định dạng, giới hạn lot/P&L, bắt thay đổi currency khi đọc broker, phân biệt danh sách rỗng được broker xác nhận với dữ liệu unavailable. [Source-only QA 36529015884](https://github.com/trankhanhduy1508-maker/AI-TRADE/actions/runs/36529015884) **SUCCESS: 204 Python + 16 Node tests**, Java standalone contracts, Android debug/release compile + lint PASS; **không tạo APK**. Google OAuth vẫn HOÃN. API Founder v6 ACTIVE, Edge verifier v4 ACTIVE (source mới chưa deploy), DEMO/LIVE/release gates giữ khóa. Nội dung bàn giao chat mới ngay dưới giữ nguyên.


> **BÀN GIAO CHAT MỚI 29/09 (ưu tiên đọc):** [CWS_AUTOTRADE_APK_NEW_CHAT_HANDOFF_2026-09-29.md](CWS_AUTOTRADE_APK_NEW_CHAT_HANDOFF_2026-09-29.md). Checkpoint ghi nhận mã nguồn `a162feada1f2bb2113c2acb6bcef414a9c0d337a`, tài liệu trước đó tại `4acba221d2c4a8769d0a6b32e3c111a213c868de`; kiểm tra HEAD mới nhất trước thao tác. Google OAuth HOÃN; source-only QA 195 Python + 16 Node PASS, broker investor probe PASS; Founder Edge v6 ACTIVE, verifier Edge v4 ACTIVE. Full broker-to-Android E2E, model/risk/send approval, stable signing và APK release vẫn CHƯA PASS. Lệnh Founder: cập nhật kinh nghiệm lên GitHub, giao prompt cho chat mới.


> **CHECKPOINT MỚI NHẤT 29/09, tiếp tục APK-first:** [Bằng chứng và blocker hiện hành](../reports/CWS_AUTOTRADE_ANDROID_DEMO_SAFETY_CHECKPOINT_2026-09-29.md). HEAD mã nguồn `a162feada1f2bb2113c2acb6bcef414a9c0d337a`, 195 Python + 16 Node tests, Android compile/lint và Python broker investor probe PASS đúng phạm vi nguồn. Supabase Founder v6 ACTIVE; verifier deployed v4, mã same-server fencing mới chưa được triển khai do tool safety block. Google OAuth HOÃN; model/risk/demo-send và release ký vẫn khóa. **Chưa bàn giao APK; các ghi nhận dưới đây là lịch sử.**


> **CHECKPOINT SOURCE QA MỚI NHẤT 29/09:** [Bằng chứng Native Portfolio + MT5 identity fencing](../reports/CWS_AUTOTRADE_ANDROID_PRE_RELEASE_EVIDENCE_2026-09-29.md). Mã tại `b0dbbf34f3e82231fd2156de3520b610c535fa9a`: 187 Python / 11 Node tests, Java native portfolio, Android source compile/lint, broker investor protocol PASS trong phạm vi báo cáo. Google OAuth vẫn HOÃN. DEMO model/risk/send chưa duyệt; release approval + keystore + Android E2E thiếu nên không có APK hoàn chỉnh. Các checkpoint dưới là lịch sử.


> **CẬP NHẬT ƯU TIÊN MỚI 29/09:** Founder hoãn Google OAuth; tiếp tục MT5 DEMO, Risk Engine và Android. Xem [checkpoint không OAuth mới nhất](../reports/CWS_AUTOTRADE_ANDROID_MT5_DEMO_NO_OAUTH_CHECKPOINT_2026-09-29.md). HEAD mã nguồn `a618d88c954b41beccdab3c0275462ad47b9d64e`; Supabase verifier ACTIVE v4, Founder API ACTIVE v5; 176 Python + 11 Node offline tests, Android source compile/lint và broker investor probe PASS. **Chưa có APK hoàn chỉnh; không tự bật demo execution hoặc LIVE.** Các cập nhật dưới đây giữ nguyên làm lịch sử, không thay thế trạng thái này.


> **CẬP NHẬT MỚI NHẤT 29/09 (sau các mục lịch sử dưới đây):** xem [checkpoint bridge Android/MT5 DEMO](../reports/CWS_AUTOTRADE_MT5_DEMO_ANDROID_BRIDGE_CHECKPOINT_2026-09-29.md). Mã mới tại `8e3f4f82469a88725eaefa4dc5ca15732384604d`; verifier ACTIVE v3 và Founder API ACTIVE v4. Source QA và broker investor preflight PASS trong phạm vi ghi nhận; full Android E2E, DEMO execution và release APK vẫn BLOCKED. Các phiên bản và nhận xét `equity:null` ở mục 2 chỉ mô tả trạng thái cũ.


**Repo:** trankhanhduy1508-maker/AI-TRADE  
**Nhánh duy nhất:** codex/p0-covel-knowledge-audit  
**HEAD đã kiểm tra trước khi ghi tài liệu:** eb89cc094cc71071da6814f9cd59864325cf293f  
**Trạng thái bàn giao:** Có mã nguồn Android, QA cloud và readback broker DEMO thật chỉ đọc. **CHƯA có APK hoàn chỉnh; DEMO auto-execution chưa được phê duyệt hoặc nghiệm thu; LIVE khóa tuyệt đối.**

## 1. Mục tiêu không được đổi

Bàn giao **CWS AutoTrade APK cho Android MT5 DEMO**. Từ app, Founder đăng nhập Google native, nhập Login + Password + Server, nhận balance, equity, danh sách vị thế/P&L có nguồn broker và thời gian xác minh; sau đó DEMO auto-trade chỉ qua Risk Engine, kill-switch, mô hình được duyệt, ledger/idempotence và broker reconciliation. App cập nhật stable và recovery bằng APK ký cùng identity, versionCode tăng và giữ dữ liệu. Màn hình tổng quan KHÔNG hiển thị KPI Tổng Lot, nhưng Lot từng vị thế phục vụ risk/audit vẫn tồn tại.

Chỉ nhánh nêu trên. Không đụng main/stable/production, không dùng máy tính Founder, không thêm chi phí hoặc project trùng, không gửi thông tin xác thực/keystore vào chat, GitHub hoặc log. Plugin/connector trước, API/cloud sau, UI cuối cùng. Không đánh đồng unit test, compile hay broker preflight với APK E2E/release.

## 2. Kết quả thực đã kiểm tra

### 2.1. Readback broker MT5 DEMO thật: PASS trong phạm vi investor/preflight

- Workflow: https://github.com/trankhanhduy1508-maker/AI-TRADE/actions/runs/36468844897 ; HEAD eb89cc094cc71071da6814f9cd59864325cf293f; kết quả workflow **SUCCESS**.
- Job dùng GitHub OIDC có audience và claim giới hạn cho workflow PR #2, gọi Edge ai-trade-mt5-demo-lease v1; endpoint chỉ trả **investor/read-only** từ Supabase Vault cho preflight, không cấp quyền gửi lệnh.
- Mã cloud/mt5-demo-bootstrap/readback_investor.py dùng pymt5 đã pin commit e7b5a8d28201879576e6cd22a39b9ea8677d4ee1; broker login, get_account, get_positions_and_orders, get_account lần nữa; thực thi kiểm tra account_type DEMO, server và dữ liệu hữu hạn, không in tài khoản, mật khẩu, balance hay vị thế vào CI.
- Bằng chứng log chỉ chứa cờ: **BROKER_DEMO_INVESTOR_READBACK_VERIFIED**, balanceRead=true, equityRead=true, positionsRead=true, brokerOrders=false, liveMoneyLocked=true, credentialsExposed=false. Probe protocol đi kèm báo MT5_PROTOCOL_READY (server build 6231); 6 unit contract checks PASS.
- Giới hạn quan trọng: positionsRead=true chứng minh đọc được danh sách broker, **không chứng minh có vị thế mở**. Đường này là GitHub Actions preflight tạm thời, KHÔNG phải phiên broker được Founder truy cập qua Android hoặc runtime gửi lệnh. Một số trường định danh không được trả độc lập từ get_account; xác minh chính xác login từ phản hồi broker cần tiếp tục nếu API/protocol hỗ trợ, ngoài login() và server/mode.

### 2.2. Android source QA: PASS, không phải APK release

- Workflow: https://github.com/trankhanhduy1508-maker/AI-TRADE/actions/runs/36468168629 ; commit 9bfdab518530a2eddbd7c8c9043fbcf22867a014.
- **166 Python offline tests PASS** trong tests/execution và tests/android ở thời điểm run; **43 Java security checks** gồm PKCE 9, signed metadata 9, AES-GCM session 10, APK update policy 15.
- Android SDK 36: build assets và merge, compileDebugJavaWithJavac, compileReleaseJavaWithJavac, lintDebug thành công. Bộ tài nguyên offline: 13 tệp; WebView whitelist khớp. Test âm xác nhận release gate từ chối khi không có khóa/phê duyệt. Không assemble APK, không upload artifact.
- Code native: android/app/src/main/java/vn/cws/aitrade/{MainActivity,DemoLoginActivity,NativeDemoAuth,NativeEncryptedSession,NativeSessionCodec,NativeReleaseVerifier,NativeUpdatePolicy,NativePackageSignerGuard,NativeUpdateProvider,NativeUpdateCoordinator}.java. Google OAuth mở browser ngoài WebView, PKCE + nonce, redirect native; refresh token mã hóa Android Keystore, xoay token; logout không hiển thị phản hồi broker cũ.
- Đã nối UI kiểm tra/cài cập nhật bằng đồng ý của Android, pin release public key cấp từ cấu hình build, xác minh signed manifest/hash, applicationId, versionCode mới, chứng chỉ APK trùng, tệp staging và read-only provider. Hiện public key production chưa được owner cấu hình và chưa có stable release manifest/APK ký; UI đúng là khóa khi thiếu key. Recovery cũ phải được đóng gói với versionCode MỚI, không downgrade APK.

### 2.3. Backend và trạng thái khóa

- Supabase project oziktadfeenydvgobudr: ai-trade-founder-mt5 **ACTIVE v3**, ai-trade-mt5-demo-lease **ACTIVE v1**, đều dùng kiểm tra quyền riêng trong handler; ai-trade-founder-mt5 vẫn yêu cầu Google Founder JWT/entitlement. Edge lease verify_jwt=false là có chủ đích vì xác minh GitHub OIDC JWT bằng JWKS trong code, không phải endpoint công khai không cần auth.
- Native POST /snapshot hiện chỉ nhận **balance/currency** từ verifier MetaQuotes-Demo đã liên kết; equity:null, positions:null vì đường verifier này chưa hỗ trợ. Không lấy balance cũ từ DB thay kết quả broker. **Đọc equity/positions PASS trên cloud preflight nhưng CHƯA nối an toàn vào Founder API/APK.**
- Read-only SQL đã xác nhận: ai_trade.runtime_config enabled=false; demo_send_enabled=false; risk_profile_approved=false; ai_trade.order_intents count=0; private ML baseline **2 REJECTED**. Không đổi trạng thái này chỉ vì cloud readback thành công.
- Sách Masterbook trong Google Drive CWS AI TRADE/Private Knowledge mới được kiểm kê metadata; chưa nhập/train/promote nếu thiếu provenance, giấy phép dữ liệu hoặc kiểm định. APK debug lịch sử trong thư mục QA không phải bản phát hành.

## 3. Những lỗi đã gặp và cách sửa

1. GitHub Actions android-actions/setup-android@v3 gọi gói SDK 'tools' lỗi trên runner. Đã thay bằng Android SDK có sẵn trên hosted runner, cài platforms;android-36 và build-tools;35.0.0. QA Android đã PASS sau sửa.
2. Script cloud/mt5-demo-bootstrap/readback_investor.py lúc đầu bị ModuleNotFoundError: src. Đã chạy với PYTHONPATH=. trong workflow.
3. OIDC investor preflight ban đầu BLOCKED. Đã giới hạn lease đúng purpose preflight, dùng investor_password_secret_id, thêm fail-closed contract + chẩn đoán chỉ bằng mã lỗi nội bộ allowlist. Run 36468844897 sau đó PASS readback thật; KHÔNG in password hoặc giá trị tài khoản.
4. Android gọi API /status không tương đương broker fresh snapshot. Đã tạo POST /snapshot trên Founder v3 kiểm tài khoản đã liên kết và verifier mới, không suy diễn equity/positions. Không gọi runtime bridge hoàn tất.
5. MetaApi cloud adapter trước đây chỉ nhìn tên server có chữ demo. Đã thêm assert_metaapi_demo_context yêu cầu broker account_information.type=ACCOUNT_TRADE_MODE_DEMO và identity, recheck trước mỗi broker mutation, invalidate khi switch/disconnect. Mọi SDK exception trả ra phải được rút gọn, không lộ nội dung nhạy cảm.
6. Sự kiện lỗi nằm giữa lúc đọc vị thế được xử lý bằng kiểm tra lại broker/account sau khi đọc. CI giả lập có kiểm tra switch LIVE và disconnect. Không tuyên bố đã kiểm thử fault injection trên broker thật.
7. Script cws_android_release_manifest.py tạo metadata SHA256withRSA từ khóa RIÊNG đặt ngoài repo, chống downgrade; script không thay APK signer hoặc giấy phép phát hành. Chưa ký release production.

## 4. Các đầu việc còn thiếu trước khi giao APK hoàn chỉnh, theo thứ tự

1. **Bridge broker readback có quyền:** dùng kỹ thuật investor-only preflight đã PASS làm bằng chứng, xây đường server-to-server có quyền Founder và lifetime ngắn để đưa equity, vị thế/P&L từ broker về API/APK. Phải xử lý server/logout, account isolation, zero-position vs data unavailable, timeout, refresh, không public giá trị người dùng. Không dùng GitHub Actions PR làm API phục vụ khách thường xuyên.
2. **Google OAuth Android thật:** xác minh Supabase Auth Additional Redirect URLs cho vn.cws.aitrade://auth/callback, Google Founder consent và auth-code/PKCE trên Android; kiểm refresh/Keystore/logout/đổi account và app restart bằng emulator/thiết bị thật.
3. **Đăng nhập MT5 và runtime:** backend nhận ba trường qua HTTPS đúng quyền chủ sở hữu, Vault quản lý bí mật với consent; kết nối từng DEMO broker được hỗ trợ, so khớp account ID/server/mode, đọc đầy đủ balance/equity/positions, ngắt/mở lại kết nối và broker reconciliation. Hiện chưa hỗ trợ generic server: MetaQuotes-Demo đã liên kết là phạm vi thực.
4. **AI và thực thi DEMO:** chỉ dữ liệu có quyền; nghiên cứu và đánh giá OOS, walk-forward, spread/slippage/cost, paper-forward; không tự nâng model REJECTED. Phê duyệt risk profile và chiến lược phải có bằng chứng Founder thật; kill-switch, giới hạn risk, idempotent intent ledger, không đặt lệnh khi mọi gate chưa PASS. Sau đó test DEMO real broker acknowledgement, timeout/retry/restart và đối chiếu. Không đụng LIVE.
5. **Phát hành APK:** owner-managed keystore + signing certificate, public key pin, metadata stable/recovery ký, Android installer consent; thử phiên bản thấp -> cao trên thiết bị, dữ liệu được giữ, migration, offline/restore và recovery cùng signer với versionCode tăng. Không tạo debug APK để báo DONE.

## 5. Đường dẫn ngắn để chat mới ground, không nghiên cứu lại toàn repo

- Canonical kiến thức: docs/CWS_AUTOTRADE_MT5_DEMO_KINH_NGHIEM_2026-09-28.md (mục 9 chỉ tới tài liệu này).
- Quy tắc release: docs/CWS_AI_TRADE_RELEASE_AND_AUTOUPDATE_POLICY_2026-09-28.md.
- Spec Android: product/CWS_AI_TRADE_ANDROID_CONTROL_LEARNING_UPDATE_SPEC_2026-09-28.md.
- Báo cáo source trước: reports/CWS_AUTOTRADE_ANDROID_DEMO_SOURCE_EVIDENCE_2026-09-28.md và reports/CWS_AUTOTRADE_DEMO_ANDROID_PROGRESS_2026-09-29.md. Hai báo cáo cũ KHÔNG có bằng chứng investor preflight PASS mới nhất.
- Readback: cloud/mt5-demo-bootstrap/readback_investor.py, src/execution/mt5_investor_readback_contract.py, tests/execution/test_mt5_investor_readback_contract.py, .github/workflows/mt5-demo-protocol-probe.yml.
- Backend: supabase/functions/ai-trade-mt5-demo-lease/index.ts, supabase/functions/ai-trade-founder-mt5/index.ts.
- Android: android/app/src/main/java/vn/cws/aitrade/, android/app/build.gradle, android/release-signing.gradle, .github/workflows/cws-autotrade-android-source-qa.yml, scripts/check_native_autotrade_contract.py, scripts/check_android_release_gate.py.

## 6. Bàn giao và tiêu chí bằng chứng

Mỗi lần bắt đầu lấy GitHub HEAD mới nhất, kiểm tra diff tối thiểu, không tự lùi về SHA trong tài liệu. Test fail thì sửa minimal diff, test lại. Chỉ ghi PASS khi có đường dẫn workflow/job, log được phép chia sẻ và source SHA khớp; không đưa ID tài khoản, mật khẩu, số dư hoặc token ra báo cáo. Nếu công cụ thiếu quyền auth redirect, owner release signing hoặc approve trade thì ghi đúng blocker cụ thể, tiếp tục làm hạng mục độc lập; không fake consent. Chỉ báo hoàn thành khi **APK ký được cài, login Google/MT5 DEMO, broker readback đầy đủ, DEMO auto-trade qua gate được xác nhận và nâng cấp/khôi phục thử thành công**. Mọi tính năng LIVE duy trì LOCKED.

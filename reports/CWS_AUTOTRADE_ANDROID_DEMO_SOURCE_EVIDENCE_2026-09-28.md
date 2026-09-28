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

## 5. Bổ sung gate BROKER_CONNECTED và bản chỉnh tài liệu APK-first

Commit `559fe83fd5bbb5bba21800536e89d6f38a6f30a4`: `read_demo_snapshot` hiện **bắt buộc `terminal_info().connected is True`** trước khi đọc `account_info()`. Thiếu metadata, `None` hoặc `connected=false` trả `TERMINAL_INFO_UNAVAILABLE` / `BROKER_DISCONNECTED`, không trả số dư/vị thế cache rồi giả là trạng thái broker hiện tại. `tests/execution/test_mt5_adapter.py` fixture được cập nhật tương ứng; các test integration trong full repo **chưa chạy**.

**PASS — standalone fake-terminal unit đã chạy lại sau sửa (không phải broker E2E):**

```text
PYTHONPATH=. pytest -q tests/execution/test_demo_readback.py
................                                                         [100%]
16 passed in 0.09s
python -m compileall -q src/execution/demo_readback.py tests/execution/test_demo_readback.py
```

Các blob của **chính file đã chạy test** được đối chiếu GitHub readback:
- Module: Git blob SHA-1 `51e74680767fa5968919ab45037d615163321bd2`, SHA-256 `4ca8fea6318092bb7faa78f0c32ce3c2e7b96f1342ec0fd9f0a5a77fdd046108`.
- Test: Git blob SHA-1 `a74534bf74365bf624fac435af60440b9b14807a`, SHA-256 `ebe53ad20a5d2fad5f1cfc86614274a63f4e1dc39cd39419acb18baeff77d540`.

Commit `6d2728fd068e5b2e877b786b6a2c295b30ae3d2b`: điều chỉnh tên và thông báo của workflow **chỉ kiểm gate**, loại mô tả cũ bắt Web App phải xong trước APK. Không có job build, upload artifact hay trigger push; không tạo APK.

**Triple-check cuối trước khi ghi phụ lục:** (1) GitHub so với checkpoint ban đầu chỉ thêm/sửa 7 file trên nhánh duy nhất, không thay Main; (2) 16 standalone fake-terminal tests PASS và blob module/test khớp đúng bản trong GitHub; full repo, broker DEMO và Android E2E **NOT RUN**; (3) SQL đọc lại Supabase: `enabled=false`, `demo_send_enabled=false`, `risk_profile_approved=false`, `order_intents=0`, 2 model `REJECTED`. Không lấy `terminal_info().connected` ở unit test giả làm bằng chứng kết nối broker thật, không tự mở bất kỳ gate nào.

**Release gate vẫn CLOSED.** Google native auth, runtime broker equity/positions thật, DEMO auto-order qua toàn bộ phê duyệt, update/recovery có chữ ký và Android E2E vẫn **BLOCKED / NOT RUN**. Không gửi APK.

## 6. APK-first native Google PKCE, DEMO balance và kiểm tra cập nhật (bổ sung 2026-09-28)

**Thực hiện trên nhánh duy nhất `codex/p0-covel-knowledge-audit`.** Không thay Main/Production, không build hay phát hành APK chưa đủ gate.

### Source đã cập nhật

1. `android/app/src/main/java/vn/cws/aitrade/NativeDemoAuth.java`, `DemoLoginActivity.java`, `MainActivity.java` và `AndroidManifest.xml`: nút native MT5 DEMO trên Android mở trang Login/Password/Server. Google OAuth mở **trình duyệt Android bên ngoài WebView**, sinh PKCE SHA-256 và nonce dùng một lần, kiểm callback/TTL trước khi exchange. Màn hình bảo vệ screenshot, dùng HTTPS và chỉ key Supabase **publishable**. MT5 password chỉ xử lý tạm trong request, không ghi vào APK, GitHub, log hoặc lưu device. Không nhúng service-role key. Login demo giới hạn ở `MetaQuotes-Demo` đã liên kết; broker/server khác trả `UNSUPPORTED_SERVER`. Phiên Google hiện **chỉ giữ RAM**, chưa có refresh/session restore qua app restart, nên không được gọi UX production PASS.
2. `supabase/functions/ai-trade-founder-mt5/index.ts`: sau khi upstream broker DEMO xác minh, yêu cầu balance hữu hạn và currency hợp lệ; trả balance/currency/as_of theo chính lần xác minh đó, **equity:null, positions:null** cho đến khi runtime hỗ trợ readback thực. Không lấy số dư lưu cũ thay broker, không tạo endpoint order hoặc bật auto-trade. Triển khai trên Supabase project hiện hữu với function `ai-trade-founder-mt5` **ACTIVE v2**; `verify_jwt=false` được giữ từ v1 vì handler vẫn bắt Supabase Google JWT và entitlement FOUNDER trước khi xử lý. Chưa có phiên Google/native E2E để chứng minh giao dịch hoặc xác thực broker trong lần chạy này.
3. `NativeReleaseVerifier.java`: **source-only** xác minh metadata bản stable/recovery được ký bằng `SHA256withRSA`, SHA-256 của toàn bộ APK, applicationId cố định và `versionCode` mới luôn cao hơn. Recovery bản mã cũ phải phát hành thành một APK có versionCode mới, không cài lùi. Public key release phải được chủ sở hữu pin trong APK, APK phải được Android PackageManager xác minh cùng chứng chỉ ký, và người dùng phải đồng ý cài đặt. **Chưa có release signing key, signed manifest host, installer/auto-update UI, Android migration hay rollout E2E.**
4. `android/qa/NativeDemoAuthCheck.java` và `NativeReleaseVerifierCheck.java`: Java QA độc lập cho PKCE RFC 7636, chống callback sai nonce, signed manifest và anti-downgrade; sử dụng key RSA được tạo tạm **chỉ trong phép thử**, không phải release key.

### Evidence đã kiểm chứng

- `javac` với JDK 21, chạy `NativeDemoAuthCheck`: **9 kiểm tra PASS** gồm test vector RFC 7636. Source/test Git blobs `1d1d19282c45111c95dc7aa1903f5861b8845f91` và `19a87ea69c6f0eab08830aa997bb737f8ba79587` trùng đúng file được thử.
- `javac`, chạy `NativeReleaseVerifierCheck`: **9 phép thử PASS** cho stable/recovery, đổi hash, sai signer, sai applicationId, downgrade. Source/test Git blobs `c92d62f211ff1c3d907bb4be556e0f3b25534f40` và `0e77f48a3998fcd3203433d3722b054aea9433f1` trùng file được thử. Payload QA là chuỗi byte giả, **không phải APK thật**.
- `DemoLoginActivity.java` kiểm tra cú pháp/kiểu bằng các stub Android giả lập tự tạo tại môi trường QA cục bộ. **Không tính là Android SDK/Gradle compile hay thiết bị E2E PASS.** SDK, Gradle và ADB không có trong môi trường QA lần này.
- Supabase readback sau deploy: `ai-trade-founder-mt5` ACTIVE v2; SQL: `enabled=false`, `demo_send_enabled=false`, `risk_profile_approved=false`, `order_intents=0`. Không gửi bất cứ lệnh broker nào.

### Gate còn chặn APK hoàn chỉnh

- **OAuth Android thật**: chưa xác minh cấu hình `vn.cws.aitrade://auth/callback/**` trong Supabase Additional Redirect URLs, callback trên Android và Google FOUNDER consent E2E; plugin Supabase hiện không có hành động đổi Auth redirect setting. Không tự nhận login PASS.
- **Broker thật và execution**: verifier hiện chỉ hỗ trợ `MetaQuotes-Demo` đã liên kết và readback balance; equity, positions, heartbeat/reconnect, account A/B isolation, runtime tương thích MT5 ổn định và DEMO order E2E theo approval vẫn chưa hoàn thành.
- **Model/risk**: model private baseline `REJECTED`, chưa có model/chiến lược được duyệt bằng provenance/licensing, OOS/WF/cost/paper-forward; `risk_profile_approved=false`, `demo_send_enabled=false`. Không tự mở gate hay chạy The5ers khi thiếu approval riêng.
- **Release**: thiếu signing identity chủ sở hữu, host manifest đã ký, cập nhật APK tại chỗ, installer consent, migration/restore và native recovery E2E trên Android thực. Library Google Drive có các APK debug **lịch sử**, không được dùng làm bản bàn giao.
- **Auto-learning**: Masterbook cá nhân chỉ kiểm kê metadata; chưa tự train/promote model từ sách hoặc dữ liệu chưa được chứng minh giấy phép.

**Trạng thái cuối: SOURCE PARTIAL; SUPABASE READ-ONLY v2 ACTIVE; DEMO AUTO-TRADE BLOCKED; LIVE LOCKED; APK RELEASE BLOCKED.** Không có bằng chứng runtime broker DEMO order/Android E2E hoặc APK release.

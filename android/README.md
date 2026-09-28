# CWS AI Trade — Android debug-only wrapper

The native Android shell packages the existing CWS AI Trade read-only Web App assets and serves them under an allowlisted reserved HTTPS origin. It does not embed broker credentials, secrets, model weights, live-trading functionality, new backends or fake prices. The web application remains the single product codebase.

Package `vn.cws.aitrade`; API 26 minimum; target Android API 36. The WebView allows top-level navigation only on its reserved local app path at https://appassets.androidplatform.net/assets/. External HTTPS links open outside the wrapper, and other schemes are rejected. SSL errors are never bypassed, no cleartext HTTP and no broad storage permissions. EPUB/JSON use the Android system file picker.

The public-repository cloud job produces a *temporary debug-signed* APK for sideload/QA. Its ephemeral debug signing key is not suitable for a production release or stable update channel. No Google Play publication, durable release signing, verified physical Android tests, or guaranteed offline WebView service-worker behavior is claimed. A stable production release requires separate secure signing and Android E2E. PWA installation remains the simpler direct approach. No Digital Asset Links is required for this WebView approach; a TWA needs root-domain control that the Supabase shared origin does not provide.

## 2026-09-28 cloud build evidence

- Debug-only Android WebView shell source commit: `8b2642013526dd9448ed1a2e39b9ebe82e369f69`.
- GitHub public runner: [Android debug build 36407451446](https://github.com/trankhanhduy1508-maker/AI-TRADE/actions/runs/36407451446), completed SUCCESS after the first lint failure was minimally fixed for Android 13+ back gestures. The successful run performed `:app:lintDebug :app:assembleDebug`, verified the APK with the Android SDK's `apksigner`, and uploaded a debug-only artifact.
- APK SHA-256: `2506f856b1b258386b2509cbafc0138397d4de93a3f27200555c2f6cd46c0d99`; signed under Android debug certificate with APK Signature Scheme v2. Android SDK reported exactly one signer, CN=Android Debug. This is **not a release signing identity**.
- Artifact ID `10962564442`, ZIP SHA-256 `13fccb6dd97637e2ebd1e2e4af46f666745d18c0918577d096935fbd4123aab6`, one-day retention. The downloaded ZIP and extracted APK independently matched both GitHub SHA-256 values; ZIP CRC PASS and APK members include `AndroidManifest.xml` and DEX.
- Local regression after build: `PYTHONPATH=. python -m pytest -q tests/self_learning` 29 PASS; `node --test google-sites/cws-ai-trade/tests/portfolio.test.cjs` 8 PASS; Python compileall PASS. These tests cannot establish actual installation, visual correctness, EPUB storage or offline WebView on a physical Android device.
- Security rules remain unchanged: HTTPS-only CWS Supabase origin, explicit user-selected EPUB/JSON only, WebView file access disabled, TLS errors cancelled, non-HTTPS navigation rejected, no broker execution/API credentials, live-money LOCKED.


## Native offline shell and build provenance (2026-09-28)

Supabase Edge on its shared supabase.co domain forces HTML to text/plain, which is not a browser-renderable frontend. The debug APK now builds the exact same public CWS Web App source into first-party assets/www at build time. An allowlisted WebView resource handler serves those assets over the reserved appassets.androidplatform.net HTTPS origin with explicit MIME types and a restrictive Content Security Policy. The initial interface, code, portfolio calculator, graphics and distilled local-book fallback do not depend on a remote HTML response. TradingView charts and fresh public text still require an internet connection.

Cloud build command: python3 scripts/build_cws_trade_static.py --base /assets/ --android --output android/app/src/main/assets/www

Cloud QA then runs Android lint, assembles the debug APK, checks its APK signature and confirms that the actual package contains first-party HTML, chart module, portfolio module and icons. The native shell deliberately omits browser-PWA service-worker installation; its packaged resources already provide the offline shell. No market prices, broker credentials, model weights, private EPUB contents or broker orders are embedded.

This is a debug QA APK with a temporary signing key. Physical-device E2E and stable release signing remain required. Two independently debug-signed packages generally cannot update each other in place.

## 2026-09-28 — Android 15/16 system-bar fix (source pending cloud/device QA)

Founder screenshot of the first-party Android shell shows the OS clock/battery overlapping the CWS logo/topbar. The native activity now wraps the unchanged WebView in a FrameLayout and applies system-bar + display-cutout insets on API 35+, preserving the safe rendering area. This is a UI/layout fix only; no permission change, broker secret, order API or model promotion. VersionCode 3 / versionName 0.3.0-debug forces an identifiable QA artifact. A successful cloud lint/build and a separate physical Android visual check are still required before reporting the layout fixed on-device.


## CHÍNH SÁCH MỚI 2026-09-28 — DỪNG TẠO APK TRƯỚC KHI AUTO-TRADE HOÀN THÀNH

Lịch sử build và đường dẫn debug APK ở trên **chỉ là kiểm thử đã có trong quá khứ**, không phải hàng cần Founder cài hiện tại. Founder đã chốt Web App trước, MT5 DEMO auto-trade sau khi toàn bộ gate PASS, rồi **duy nhất một APK phát hành hoàn chỉnh, có cập nhật tại chỗ**. Workflow `.github/workflows/cws-ai-trade-android-debug.yml` không còn push trigger hay Gradle/build/upload job. `scripts/check_android_release_gate.py` từ chối khi thiếu approval. Từ nay tuyệt đối không upload/gửi APK debug mỗi commit; mọi sửa UI/runtime thực hiện và test trên Web App/cloud trước. Điều kiện ký và tự cập nhật chi tiết: `docs/CWS_AI_TRADE_RELEASE_AND_AUTOUPDATE_POLICY_2026-09-28.md`.


## Founder đổi trọng tâm: APK-first, update và rollback (mới nhất, 2026-09-28)

Các đoạn ở trên chỉ mô tả trạng thái/hạn chế của artifact lịch sử. Từ nay ưu tiên mã nguồn Android và contract `product/CWS_AI_TRADE_ANDROID_CONTROL_LEARNING_UPDATE_SPEC_2026-09-28.md`; Web/PWA chỉ còn kênh phụ, việc GitHub Pages chưa kích hoạt **không chặn phát triển Android**. Vẫn không phát hành/bàn giao APK Debug khi DEMO auto-trade chưa được kiểm chứng. Chức năng auto-update + recovery **chưa được triển khai**: cần cùng signing identity release, kiểm SHA/kênh phân phối, versionCode tăng, rollback model/strategy bản được duyệt, native recovery build mới versionCode cao hơn và Android device E2E. Không cho model tự thay execution/risk/kill-switch. Nút can thiệp thủ công và TradingView được ghi nhận là đề xuất UX, không chạm broker execution trước khi chốt chi tiết.

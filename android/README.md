# CWS AI Trade — Android debug-only wrapper

The native Android shell loads the existing CWS AI Trade read-only HTTPS PWA. It does not embed broker credentials, secrets, model weights, live-trading functionality, new backends or fake prices. The web application remains the single product codebase.

Package `vn.cws.aitrade`; API 26 minimum; target Android API 36. The WebView allows top-level navigation only on the exact Supabase CWS AI Trade application path. External HTTPS links open outside the wrapper, and other schemes are rejected. SSL errors are never bypassed, no cleartext HTTP and no broad storage permissions. EPUB/JSON use the Android system file picker.

The public-repository cloud job produces a *temporary debug-signed* APK for sideload/QA. Its ephemeral debug signing key is not suitable for a production release or stable update channel. No Google Play publication, durable release signing, verified physical Android tests, or guaranteed offline WebView service-worker behavior is claimed. A stable production release requires separate secure signing and Android E2E. PWA installation remains the simpler direct approach. No Digital Asset Links is required for this WebView approach; a TWA needs root-domain control that the Supabase shared origin does not provide.

## 2026-09-28 cloud build evidence

- Debug-only Android WebView shell source commit: `8b2642013526dd9448ed1a2e39b9ebe82e369f69`.
- GitHub public runner: [Android debug build 36407451446](https://github.com/trankhanhduy1508-maker/AI-TRADE/actions/runs/36407451446), completed SUCCESS after the first lint failure was minimally fixed for Android 13+ back gestures. The successful run performed `:app:lintDebug :app:assembleDebug`, verified the APK with the Android SDK's `apksigner`, and uploaded a debug-only artifact.
- APK SHA-256: `2506f856b1b258386b2509cbafc0138397d4de93a3f27200555c2f6cd46c0d99`; signed under Android debug certificate with APK Signature Scheme v2. Android SDK reported exactly one signer, CN=Android Debug. This is **not a release signing identity**.
- Artifact ID `10962564442`, ZIP SHA-256 `13fccb6dd97637e2ebd1e2e4af46f666745d18c0918577d096935fbd4123aab6`, one-day retention. The downloaded ZIP and extracted APK independently matched both GitHub SHA-256 values; ZIP CRC PASS and APK members include `AndroidManifest.xml` and DEX.
- Local regression after build: `PYTHONPATH=. python -m pytest -q tests/self_learning` 29 PASS; `node --test google-sites/cws-ai-trade/tests/portfolio.test.cjs` 8 PASS; Python compileall PASS. These tests cannot establish actual installation, visual correctness, EPUB storage or offline WebView on a physical Android device.
- Security rules remain unchanged: HTTPS-only CWS Supabase origin, explicit user-selected EPUB/JSON only, WebView file access disabled, TLS errors cancelled, non-HTTPS navigation rejected, no broker execution/API credentials, live-money LOCKED.

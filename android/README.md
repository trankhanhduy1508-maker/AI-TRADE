# CWS AI Trade — Android debug-only wrapper

The native Android shell loads the existing CWS AI Trade read-only HTTPS PWA. It does not embed broker credentials, secrets, model weights, live-trading functionality, new backends or fake prices. The web application remains the single product codebase.

Package `vn.cws.aitrade`; API 26 minimum; target Android API 36. The WebView allows top-level navigation only on the exact Supabase CWS AI Trade application path. External HTTPS links open outside the wrapper, and other schemes are rejected. SSL errors are never bypassed, no cleartext HTTP and no broad storage permissions. EPUB/JSON use the Android system file picker.

The public-repository cloud job produces a *temporary debug-signed* APK for sideload/QA. Its ephemeral debug signing key is not suitable for a production release or stable update channel. No Google Play publication, durable release signing, verified physical Android tests, or guaranteed offline WebView service-worker behavior is claimed. A stable production release requires separate secure signing and Android E2E. PWA installation remains the simpler direct approach. No Digital Asset Links is required for this WebView approach; a TWA needs root-domain control that the Supabase shared origin does not provide.

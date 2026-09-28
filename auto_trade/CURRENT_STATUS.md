## Founder Google Login — stable Supabase entry — 2026-09-28

Status: **PASS đến Google account selection / callback route configured**.

### Stable Admin URL
`https://oziktadfeenydvgobudr.supabase.co/functions/v1/ai-trade-dashboard?admin=1`

Không redirect qua raw.githack ở bước login nữa. Supabase Edge Function phục vụ trực tiếp trang Founder Login.

### UI / OAuth evidence
TinyFish final regression:
`be9f863d-b717-4341-a7f0-b988aab7ee3d`

PASS:
- URL giữ ở Supabase stable admin route;
- title `CWS AI Trade · Founder Login`;
- hiển thị `Founder Login`;
- badge `ADMIN LOGIN`;
- nút `Đăng nhập Google để vào Admin`;
- trước auth không expose runtime data;
- click login mở Google OAuth;
- OAuth `redirect_to` quay về chính stable Supabase Admin URL;
- không có `redirect_not_allowed` / callback configuration error;
- test dừng trước bước chọn Google account, không nhập credential.

### Founder allowlist
Thêm table:
`ai_trade.dashboard_google_access`

Security:
- RLS enabled;
- `anon` SELECT = false;
- `authenticated` SELECT = false;
- policy deny public API access.

Authorization không dựa vào display name/email do browser gửi. Backend:
1. nhận Supabase Google Bearer session;
2. verify session qua Supabase Auth;
3. lấy `auth.users.id`;
4. map user id server-side qua `dashboard_google_access`;
5. chỉ mở runtime nếu mapped token có role `FOUNDER`, chưa revoke và còn hạn.

Hiện có **1 active Founder Google mapping**.

### Post-auth flow
Sau Google callback:
- login page lấy Supabase access token từ URL hash;
- gọi `?format=google-session` bằng Bearer token;
- backend verify Founder mapping;
- nếu PASS, lưu session vào browser localStorage;
- chuyển sang `?admin_app=1&mode=admin`;
- dashboard API sau đó dùng Authorization Bearer, không cần raw dashboard token trong URL.

### Deployment
- `ai-trade-dashboard` **v31 ACTIVE**.
- frontend auth/API build pin: `5face2eabc66267e1e6adfb076dad713745d990c`.
- login page được server trực tiếp bởi Edge Function, tránh raw.githack interstitial.
- live money vẫn LOCKED;
- không thay broker execution/risk/The5ers gates.

### Remaining human-auth step
Full Google callback → Founder runtime bằng chính Google account của Founder cần người sở hữu account chọn/đăng nhập Google một lần. Không bypass/mint session giả để ép PASS. Authenticated Founder runtime phía dashboard đã PASS độc lập bằng temporary Founder E2E token trước đó; Google OAuth transport tới account-selection hiện cũng PASS.

## Founder Google Login — 2026-09-28

Status: **PASS tới Google OAuth / cổng Admin thật đã thay Admin Preview**.

### Stable Admin Login
`https://oziktadfeenydvgobudr.supabase.co/functions/v1/ai-trade-dashboard?admin=1`

Luồng:
1. stable Supabase Admin URL;
2. redirect tới `dashboard/admin.html`;
3. hiển thị `Founder Login` + `ADMIN LOGIN`;
4. nút `Đăng nhập Google để vào Admin`;
5. OAuth qua Supabase Auth → Google;
6. callback lưu Supabase access token trong browser localStorage;
7. chuyển sang `dashboard/index.html?mode=admin`;
8. dashboard API gửi bearer token lên Edge Function;
9. backend verify token bằng Supabase Auth `/auth/v1/user`;
10. backend map `auth.users.id` qua `ai_trade.dashboard_google_access` tới Founder access row;
11. chỉ account Founder đã allowlist mới nhận runtime Founder data.

Không dùng tên/email do client gửi để quyết định quyền. Mapping dùng stable Supabase Auth user UUID.

### DB hardening
Tạo `ai_trade.dashboard_google_access`:
- FK tới `auth.users(id)`;
- FK tới `dashboard_access_tokens(id)`;
- RLS enabled;
- revoke ALL cho `anon` / `authenticated`;
- deny policy cho Data API;
- Founder Google account đã đăng ký được map tới Founder access id 1.

### Browser evidence
TinyFish run:
`300b225a-2a0f-440c-9283-7e1546401d8b`

PASS:
- stable Admin URL redirect đúng tới `dashboard/admin.html`;
- thấy rõ `Founder Login`;
- thấy rõ `ADMIN LOGIN`;
- thấy nút `Đăng nhập Google để vào Admin`;
- không có `ADMIN PREVIEW`;
- chưa auth thì không expose runtime data;
- click Google mở thật `accounts.google.com`;
- Supabase OAuth callback được dùng;
- Google Authorization Code Flow khởi động;
- không thấy redirect/callback configuration error;
- test dừng trước bước chọn tài khoản, không nhập credential.

### Deploy
- Edge Function `ai-trade-dashboard` v27 ACTIVE;
- dedicated login page commit: `31c65a7e12626cf8100a052cc94699710c2b10c0`;
- backend route commit: `377db5f0edef2a88e299e5991d0a489c227444be`;
- Google bearer backend auth implemented in branch;
- live money vẫn LOCKED;
- không thay broker execution/risk/The5ers gates.

## AI-TRADE Supabase RLS hardening — 2026-09-28

Status: **PASS / runtime verified**.

### Scope
Chỉ schema `ai_trade`.
Không đụng schema `public` của các phần CWS khác.
Không thay broker execution, live-money gate, risk gate, The5ers gate hoặc Google Login.

### Before
- 35 AI-TRADE tables;
- phần lớn `relrowsecurity=false`;
- tất cả `anon` / `authenticated` table privileges đã là false;
- mỗi table đã có policy `deny_api_access` cho `anon,authenticated` với `USING false / WITH CHECK false`.

### Change
Bật Row Level Security cho toàn bộ **35/35** table trong schema `ai_trade`.

Kết quả:
- `total_tables=35`;
- `rls_enabled=35`.

### Post-change authenticated smoke
Dùng Founder token tạm thời riêng cho smoke test, sau đó revoke ngay.
Token không được ghi vào repo/docs.

PASS:
- dashboard overview vẫn đọc được;
- `format=current` → `ok=true`, `openPositions=[]`, `brokerOrders=false`, `liveMoneyLocked=true`;
- `format=trades` → `ok=true`;
- `format=arena` → `ok=true`, paper positions vẫn đọc được;
- `format=symbol-spec&symbol=EURUSD` → `ok=true`, broker spec thật vẫn đọc được;
- temporary token id `4` đã revoked tại `2026-09-27T20:58:21.141842Z`.

### Supabase security advisor after change
Không còn finding RLS nào thuộc schema `ai_trade`.
Advisor còn findings thuộc schema `public` và project-level Auth/extension; các finding đó **ngoài phạm vi AI-TRADE Admin task này** và không được sửa để tránh ảnh hưởng CWS Render/portal.

## Founder/Admin authenticated E2E — 2026-09-28

Status: **PASS / runtime thật / read-only**.

### Evidence
TinyFish run:
`d7dfd16b-a885-466e-88fe-bbba552fc955`

Authenticated bằng **Founder access token tạm thời có hạn** chỉ để E2E:
- role runtime: `FOUNDER`;
- không có banner `ADMIN PREVIEW`;
- không thực hiện Google Login;
- không gửi broker order;
- không click tester/account mutations;
- không thay live-money gate;
- token test đã **REVOKED ngay sau test**;
- DB evidence: token row id `3`, label `FOUNDER_E2E_TEMP_2026-09-28`, `revoked_at=2026-09-27T20:56:33.672943Z`.

### Runtime results
System status thật:
- Engine: `ONLINE`;
- Forward: `COLLECTING`;
- Open positions: `0`;
- MT5 DEMO: `UNAVAILABLE` trong Founder dashboard context hiện tại;
- Live money: `LOCKED`.

Open positions:
- không có shadow position đang mở;
- UI hiển thị empty state thật, không tạo dữ liệu giả.

Chart:
- 14 markets vẫn đủ;
- 5 timeframe: M15 / M30 / H1 / H4 / D1;
- market/timeframe switch không full page reload;
- EURUSD H1: candles runtime PASS;
- BTCUSD H1: candles runtime PASS;
- XAUUSD M15: candles runtime PASS;
- NAS100 H4: candles runtime PASS;
- mobile không horizontal overflow.

Data integrity:
- TP không fake;
- lot không fake;
- exact USD P/L chỉ bật khi có lot thật + symbol/account metadata đủ;
- paper/arena data được nhận diện là paper, không giả thành broker position;
- live-money vẫn LOCKED.

Observed API latency trong browser run:
- overview ~4444 ms;
- trades ~5106 ms;
- current ~4964 ms;
- arena ~5212 ms;
- admin-testers ~3715 ms;
- journal ~5155 ms;
- symbol-spec ~3536 ms;
- candles ~4805 ms.

Các latency này là evidence để tối ưu tiếp; không được mô tả là nhanh.

### Admin preview route
Stable preview URL đi qua Supabase backend:
`https://oziktadfeenydvgobudr.supabase.co/functions/v1/ai-trade-dashboard?admin_preview=1`

Preview không cần token và cố ý không expose runtime Founder data. Authenticated Founder data vẫn yêu cầu credential thật.

## CWS AI Trade Admin UI — verified symbol specs + exact USD P/L gate — 2026-09-28

Status: **DONE / runtime evidence thật** cho task symbol specification → horizontal price/P&L helper.

### Git / deploy
- branch duy nhất: `codex/p0-covel-knowledge-audit`;
- frontend exact-P/L build: `c87c08174b3adfa9b80641d1afdf19a2718e38f1`;
- deploy-pin commit: `2744d4de11585788f6b85a7aa5ceb4d3172716b2`;
- Supabase Edge Function `ai-trade-dashboard` v19 ACTIVE;
- TradingView Lightweight Charts vẫn là 5.0.8;
- không thay Google Login, live-money lock, broker execution, risk gate hoặc The5ers gate.

### Broker specification source
Không hardcode broker assumptions.

Runtime đã đăng nhập server-side vào **MetaQuotes-Demo** bằng credential đang lưu trong Vault, không lộ secret, sau đó dùng read-only WebTerminal protocol:
- command 6: lấy symbol catalog;
- command 18: lấy full contract specification cho symbol IDs đã chọn;
- không gửi command trade/order;
- evidence request nội bộ: `net._http_response id=178`;
- `brokerOrders=false`, `liveMoneyLocked=true`, `passwordExposed=false`.

Account runtime được verify riêng:
- currency tài khoản: **USD**;
- server: MetaQuotes-Demo;
- evidence request nội bộ: `net._http_response id=179`;
- password không xuất hiện trong response.

### 14 market mapping
MetaQuotes-Demo hiện có contract spec thật cho 10/14 market:
- EURUSD, GBPUSD, USDJPY, AUDUSD, USDCAD, USDCHF, NZDUSD;
- XAUUSD;
- US30;
- US500.

Không có exact broker symbol trên account này cho:
- USOIL;
- BTCUSD;
- ETHUSD;
- NAS100.

Bốn market trên vẫn tồn tại trong chart/data universe, nhưng broker spec được đánh dấu unavailable. Không tạo alias giả để ép PASS.

Ví dụ spec runtime thật:
- EURUSD: digits 5, contract size 100000, profit currency USD, calc mode 0;
- USDJPY: digits 3, contract size 100000, profit currency JPY, calc mode 0;
- XAUUSD: digits 2, contract size 100, tick size 0.01, tick value 0.1, profit currency USD, calc mode 4;
- US30: digits 2, contract size 1, profit currency USD, calc mode 2;
- US500: digits 2, contract size 1, profit currency USD, calc mode 2.

### Safe cache
Migration `create_dashboard_symbol_specs_cache` tạo:
- `ai_trade.dashboard_symbol_specs`;
- RLS enabled;
- không có public RLS policy;
- explicit REVOKE ALL từ `anon` và `authenticated`.

Table này chỉ phục vụ Admin/dashboard observability, không thay `broker_symbol_map` và không tác động execution routing.

### Dashboard integration
`ai-trade-dashboard?format=symbol-spec&symbol=...`:
- chỉ hoạt động sau dashboard access token validation hiện hữu;
- trả broker spec đã verify từ cache;
- trả `supported=false` + reason khi broker không có market;
- luôn giữ `brokerOrders=false` và `liveMoneyLocked=true`.

Frontend:
- market/timeframe switch tải candles + symbol spec song song;
- spec cache theo market trong DashboardStore;
- selected trade được gắn spec đúng market;
- horizontal helper dùng contract size / tick metadata / account currency thật;
- không dùng synthetic volume như lot thật.

### Exact USD P/L rules
Chỉ tính Estimated P/L khi có **lot thật** và đủ metadata.

Với calc mode đang gặp trên MetaQuotes-Demo:
- calc mode 0 / 2 / 4: tính P/L từ price delta × contract size × lot;
- nếu profit currency = account currency USD: dùng trực tiếp;
- với USD là base currency và profit currency khác USD (USDJPY/USDCAD/USDCHF): đổi profit currency về USD bằng target price;
- tick-value formula chỉ là fallback khi tickSize/tickValue thực sự > 0;
- thiếu lot/spec/conversion → hiện đúng:
  `P/L chưa đủ dữ liệu để tính chính xác`.

Không coi `synthetic_volume` của shadow position là lot thật.

### Formula verification
Read-only test cases, không tạo production position:
- EURUSD BUY 1.1000 → 1.1010, 0.10 lot → expected +$10.00;
- USDJPY BUY 150.000 → 151.000, 0.10 lot → expected +$66.225165...;
- XAUUSD BUY 2500 → 2501, 0.10 lot → expected +$10.00;
- US30 BUY 45000 → 45100, 0.10 lot → expected +$10.00.

Evidence label: `TEST_ONLY_NO_PRODUCTION_POSITION`.

### Runtime UI verification
TinyFish browser run:
`8d44b28f-1cdd-4ed9-bef2-9a78b0eb9164`

PASS:
- mobile shell render;
- 14 market selector;
- M15/M30/H1/H4/D1;
- projection module loads and placeholder renders;
- không có blocking JS/runtime syntax error;
- không horizontal overflow.

Không có Founder raw token trong tool context nên không tạo credential giả để ép authenticated browser test.

Hiện `shadow_broker_positions` của strategy đang rỗng, do đó production UI không có lot thật để hiển thị USD floating P/L. Đây là **đúng data-integrity behavior**, không phải feature failure: helper sẽ tự tính khi một vị thế có lot thật + spec đủ dữ liệu.

## CWS AI Trade Founder/Admin terminal UI checkpoint — 2026-09-28

Founder/Admin UI đã được nâng thành bề mặt terminal trading riêng trong cùng codebase, không fork customer UI.

### Implementation checkpoint
- implementation HEAD trước status commit: `d1fe00c2278f0c5aab762c840ebc467b2d8bd4ce`;
- static dashboard build được Edge Function trỏ tới: `50739eeb59d15a0621ad4503d1f63d1e4aa17660`;
- Supabase Edge Function `ai-trade-dashboard` v17 ACTIVE;
- TradingView Lightweight Charts giữ nguyên official v5.0.8.

### Founder/Admin hierarchy
Thứ tự ưu tiên runtime hiện tại:
1. System status;
2. Current open positions;
3. Selected current trade;
4. Central chart + market/timeframe;
5. Lot / P&L / R / Entry / SL / TP;
6. Forward + MT5/safety;
7. Research/performance;
8. Journal/tester admin thấp hơn.

Lower-priority Founder sections dùng `content-visibility:auto` để không chiếm first render work không cần thiết.

### Load / perceived performance
- static HTML shell + skeleton vẫn render trước JavaScript, không blank screen;
- cache last-known state vẫn hydrate tối đa 10 phút rồi refresh live ở nền;
- `overview`, `current`, `trades`, `arena` bắt đầu request song song ngay từ đầu thay vì chờ overview xong mới fan-out;
- Founder-only journal/tester-admin chỉ bắt đầu sau khi role Founder đã được xác nhận;
- chart request bắt đầu sau main live render bằng `requestAnimationFrame`, nên chart không block first paint;
- per-endpoint client network timing được đo bằng `performance.now()` và hiện ở footer Founder.

Một mẫu network trực tiếp raw.githack trước/sau:
- old index: ~342.8 ms;
- new index: ~387.1 ms;
- old app.js: ~382.6 ms;
- new app.js: ~473.0 ms.

Các số trên là latency CDN một lần và KHÔNG được dùng để tuyên bố network bytes nhanh hơn. Cải thiện chính là giảm waterfall và cải thiện perceived load/runtime scheduling. Không fake benchmark.

### Market / timeframe
Market selector đủ 14 market:
EURUSD, GBPUSD, USDJPY, AUDUSD, USDCAD, USDCHF, NZDUSD,
XAUUSD, USOIL, BTCUSD, ETHUSD, US30, NAS100, US500.

Timeframe:
M15 / M30 / H1 / H4 / D1.

Switch market/timeframe chỉ reload candle/chart state, không reload toàn dashboard.

### Chart / position overlay
- smooth mouse/touch pan, wheel zoom, pinch zoom, kinetic scroll;
- responsive ResizeObserver;
- autoscale + practical bar spacing;
- desktop khoảng 72 visible bars, mobile khoảng 54;
- selected position được resolve theo market từ current shadow position, shadow position list hoặc paper arena;
- chart hiển thị BUY/SELL marker, Entry, SL, current price, TP chỉ khi có thật;
- chart summary hiện Lot/Volume, current price, floating P/L và floating R khi dữ liệu có;
- không có TP thì hiện rõ `TP — chưa đặt`.

### Horizontal price helper
Đã thêm target-price helper:
- crosshair hiển thị Target + khoảng cách từ Entry;
- click ghim horizontal Target line;
- FX hiển thị pip, tài sản khác hiển thị point;
- USD P/L CHỈ tính khi có đủ `lot + tickSize + tickValue + entry + target`;
- nếu thiếu symbol specification thì hiện đúng: `P/L chưa đủ dữ liệu để tính chính xác`.

Hiện API chưa cung cấp symbol specification đủ để tính USD P/L chính xác, nên UI fail-closed thay vì dựng số giả.

### Runtime evidence
Cloud browser run:
- TinyFish run `b8dc9169-21b9-4c2c-864d-e75825f1afd4`;
- viewport mobile tương đương ~412x915;
- PASS shell/skeleton first paint, không blank;
- PASS đủ 14 market;
- PASS đủ M15/M30/H1/H4/D1;
- PASS market/timeframe interaction client-side, không full-page reload;
- PASS không horizontal overflow trên mobile;
- không có blocking JS runtime error trong unauthenticated static-build test.

Live public candle source checks, không fake data:
- EURUSD H1: Yahoo `EURUSD=X`, granularity 1h, runtime fetch ~2041.8 ms;
- BTCUSD H1: Yahoo `BTC-USD`, granularity 1h, dữ liệu OHLC trả về thành công;
- XAUUSD M15: Yahoo `GC=F`, granularity 15m, 357 points, ~2439.8 ms;
- NAS100 H4 source: Yahoo `^NDX`, granularity 1h, 211 points, ~2215.7 ms; dashboard H4 aggregate từ 1h theo backend hiện hành.

### Verified blocker / limitation
Không có raw Founder dashboard token trong tool context. Runtime auth lưu token dạng SHA-256 hash một chiều, nên không thể phục hồi token để chạy authenticated browser E2E cho overlay trên dữ liệu Founder thật mà không tạo/fake credential hoặc thay auth scope.

Vì vậy:
- static/mobile/browser behavior đã runtime PASS thật;
- public candle source cho các market/timeframe bắt buộc đã runtime trả dữ liệu thật;
- authenticated Founder overlay E2E chưa được tuyên bố PASS giả.

### Safety / scope
- không thay live-money lock;
- không thay broker execution gate;
- không thay The5ers gate;
- không thay risk approval;
- không implement/chỉnh Google Login trong task này;
- không tạo branch mới.

## CWS AI Trade fast UI + Google Login + TradingView v5 — 2026-09-27

Founder feedback from mobile tester screenshot triggered a shared Founder/Tester UI upgrade.

### Instant first paint
- static HTML now renders CWS AI Trade shell immediately before JavaScript executes;
- skeleton cards are visible while live data loads;
- last successful dashboard state is cached per access token for up to 10 minutes;
- cached state hydrates immediately, then network refresh happens in background;
- overview renders first; remaining feature requests load in parallel;
- refresh remains 60 seconds.

### Google Login
- real Google OAuth button added to Founder and Tester header;
- Google provider was runtime-probed through Supabase Auth and redirects to accounts.google.com;
- Supabase publishable key is used client-side as intended; no service-role secret is exposed;
- authenticated Google name/email is shown in the header;
- logout removes the browser Google session token used by the dashboard client.

### Chart upgrade
- upgraded from TradingView Lightweight Charts 4.1.3 to official 5.0.8;
- 14 selectable markets:
  EURUSD, GBPUSD, USDJPY, AUDUSD, USDCAD, USDCHF, NZDUSD,
  XAUUSD, USOIL, BTCUSD, ETHUSD, US30, NAS100, US500;
- timeframes remain M15/M30/H1/H4/D1;
- mobile pinch/zoom/drag and kinetic scroll enabled;
- chart shows roughly the most recent 72 bars instead of compressing full history;
- Entry/SL lines use selected market position data;
- BUY/SELL entry marker is rendered on the selected market;
- TP line is shown only when a real strategy TP exists; no fake TP is invented;
- chart summary explicitly says TP is not set when strategy has none;
- TradingView attribution logo enabled.

### Performance behavior
- chart library remains lazy but is prewarmed during browser idle time;
- candle data still loads only when chart is opened;
- switching market/timeframe reloads only chart data, not full dashboard.

### Runtime evidence
- Edge Function `ai-trade-dashboard` v16 ACTIVE.
- #171 tester live HTTP 200.
- #172 branded instant HTML HTTP 200 text/html.
- #173 app.js HTTP 200 application/javascript.
- #174 candlestick.js HTTP 200 application/javascript.
- #175 TradingView Lightweight Charts v5.0.8 HTTP 200.
- #176 BTCUSD H1 candles HTTP 200.
- #177 NAS100 H4 candles HTTP 200.
- #169/#170 Google OAuth authorize flow successfully redirects to accounts.google.com.

No live-money gate was changed.
No broker order was enabled.
Founder and Tester continue to share one codebase with server-side role separation.

## CWS AI Trade Founder + Tester split — 2026-09-27

Implemented two server-side access modes using one codebase:

### Founder
- access_role=FOUNDER
- can view internal pipeline/research controls
- can manage tester entitlement immediately
- founder actions: CUSTOMER_FREE / CUSTOMER_PAID / SUSPEND / REVOKE / RESTORE_TESTER
- all entitlement mutations are server-side and audited

### Tester
- access_role=TESTER
- entitlement_state=ACTIVE_TESTER
- default tester expiry: 30 days
- Founder may downgrade/suspend/revoke before expiry at any time
- DEMO/PAPER only
- live money remains locked
- internal cron/gate/admin details hidden
- proprietary journal/research lessons hidden
- no GitHub/Core access

Runtime evidence:
- dashboard Edge Function v14 ACTIVE
- founder overview #160 HTTP 200, role=FOUNDER
- founder tester list #161 HTTP 200
- tester overview #162 HTTP 200, role=TESTER
- tester journal #163 HTTP 200, restricted=true
- tester live page #164 HTTP 200
- founder downgrade action #165 HTTP 200 -> CUSTOMER_FREE
- founder restore action #166 -> ACTIVE_TESTER
- post-split tester overview #167 HTTP 200 with mt5.connected=false
- founder admin #168 HTTP 200 with tester ACTIVE_TESTER

MT5 isolation:
- new `ai_trade.account_mt5_bindings` scopes MT5 metadata by user/access account
- Founder binding retains the canonical MetaQuotes DEMO metadata
- Tester has no MT5 binding yet and cannot see/use Founder MT5 metadata
- no MT5 password is stored in the tester entitlement tables
- no broker order was enabled

Security:
- tester access token is stored hashed
- token value is not committed to GitHub
- anon/authenticated database roles have no table access
- entitlement audit table: `ai_trade.account_entitlement_audit`

## CWS AI Trade brand rename — 2026-09-27

Canonical customer-facing product name is now **CWS AI Trade**.

Changed:
- README project title;
- live dashboard header;
- browser page title;
- dashboard architecture documentation;
- business model / identity / data flywheel / collaboration security documents;
- contributing guide.

Runtime evidence:
- Supabase dashboard Edge Function v12 ACTIVE.
- live request #158 HTTP 200 and redirects to the branded build.
- branded HTML request #159 HTTP 200 and renders `<title>CWS AI Trade</title>`.

Compatibility rule:
- keep existing technical identifiers such as `ai_trade`, `TF-...`, and `ai-trade-...` unless a future migration has a functional reason;
- do not rename database/schema/runtime identifiers merely for cosmetic branding.

Repository note:
- current GitHub repository path remains `trankhanhduy1508-maker/AI-TRADE`;
- the connected GitHub capability does not expose repository rename/create-private-repository actions;
- no alternative installed plugin provides a safer repository-admin action;
- do not claim repository rename/private split is complete until an authorized repository-admin surface exists.

Target split remains:
- `CWS AI Trade App` — shareable product/UI surface;
- `CWS AI Trade Core Private` — proprietary strategy/research/risk core.

## Founder product knowledge + light dashboard + collaboration boundary — 2026-09-27

Canonical product/security docs added:
- `product/AI_TRADE_BUSINESS_MODEL_V1_2026-09-27.md`
- `product/AI_TRADE_IDENTITY_GOOGLE_MT5_V1_2026-09-27.md`
- `product/AI_TRADE_DATA_FLYWHEEL_PRIVACY_V1_2026-09-27.md`
- `security/AI_TRADE_COLLABORATION_SECRET_PROTECTION_V1_2026-09-27.md`
- `security/AI_TRADE_PUBLIC_PRIVATE_BOUNDARY.md`
- `.github/CODEOWNERS`
- `CONTRIBUTING.md`

Dashboard changes:
- refresh reduced from 30s to 60s;
- current-trade UI exposes Lot/Volume, MT5 account metadata and richer P/L/R presentation;
- Training Arena UI exposes symbol, side, Lot/Volume placeholder, Entry, Stop and P/L;
- candlestick chart remains available but is now optional/lazy;
- chart library and candle data are not loaded until user presses “Mở biểu đồ”;
- timeframe selector remains M15/M30/H1/H4/D1;
- Supabase dashboard Edge Function v11 ACTIVE;
- overview runtime #155 HTTP 200 includes MT5 login metadata;
- live dashboard runtime #156 HTTP 200;
- raw frontend app.js runtime #157 HTTP 200 application/javascript.

Security discovery:
- GitHub repository `trankhanhduy1508-maker/AI-TRADE` is currently PUBLIC.
- PUBLIC visibility conflicts with Founder requirement to protect proprietary research/know-how.
- CODEOWNERS/branch review can protect changes but cannot protect reads.
- Do not invite untrusted collaborators to proprietary Core material until a private boundary exists.
- Preferred target: shareable App repository + private Founder-controlled Core/research repository/service.
- No new secrets were added to GitHub.

Next product step after repository security boundary:
- Google Sign-In customer identity;
- bind entitlement to normalized MT5 identity (server + login), not Google email alone;
- build MT5 connection UX without exposing/storing plaintext credentials;
- keep execution-capable financial-account access behind a dedicated secure connector and existing live-money gates.

## All-market paper training arena — 2026-09-27

Founder requested accelerated learning across all major tracked markets.

A separate paper-only arena is now active:
- strategy id: `TF-013A-ARENA-ALL-MARKETS`
- markets: 14
- open paper positions: 14
- closed arena trades: 0
- arena journal events: 14
- brokerOrders=false
- liveMoneyLocked=true
- contaminatesForward=false

Arena universe:
EURUSD, GBPUSD, USDJPY, AUDUSD, USDCAD, USDCHF, NZDUSD,
XAUUSD, USOIL, BTCUSD, ETHUSD, US30, NAS100, US500.

Arena behavior:
- all markets may hold simultaneous paper positions;
- initial position uses current TF-013A directional vote;
- stop = 4 ATR(20);
- daily mark-to-market in R;
- stop or reversal closes the paper trade;
- reversal may immediately open the opposite paper side;
- every OPEN / MARK / CLOSE / REVERSE event is written to `ai_trade.training_arena_journal`;
- closed arena trades are stored in `ai_trade.training_arena_trades`;
- arena data never enters `forward_shadow_trades`.

Autonomous schedule:
- 03:15 UTC forward engine
- 03:20 UTC shadow broker
- 03:25 UTC forward evaluator
- 03:30 UTC official forward journal
- 03:35 UTC training arena

Replay training also completed:
- run: `TF013A_REPLAY_10X14_20260927`
- 10 trades per market
- 14 markets
- 140 replay trades total
- 15 lesson records (14 symbol + 1 portfolio)
- 46 wins / 94 losses
- net R at synthetic 10 bps: +22.0257R
- average: +0.1573R/trade
- this replay is training-only and does not promote execution.

Training replay symbol observations:
- positive net R: XAUUSD, BTCUSD, NAS100, US500, US30.
- negative net R: USDCHF, ETHUSD, USDJPY, USDCAD, AUDUSD, USOIL, GBPUSD, EURUSD, NZDUSD.
- these are not rankings or trade permissions; sample is only 10 trades per market.

Dashboard:
- premium modular UI includes Training Arena table with all open positions;
- shows side, entry, floating R and recent arena journal lessons;
- chart timeframe selector: M15 / M30 / H1 / H4 / D1;
- chart title text removed as requested;
- timeframe changes reload chart data without reloading the whole dashboard.

## Premium modular dashboard — 2026-09-27

Founder selected Direction B: full premium UI with feature-level rollback boundaries.

Frontend is now split into independent modules:
- shell / design tokens / responsive layout / component styles
- API transport / client store / utilities
- current trade
- progress
- pipeline
- recent trades
- persistent post-trade journal
- H1 Japanese candlestick chart with EMA21/EMA50 + Entry/SL/TP overlays
- performance
- MT5 DEMO + safety gates
- app orchestrator

Architecture / rollback map:
`dashboard/ARCHITECTURE.md`

Runtime data rule:
- no fake trade values from design mockups;
- no open trade => explicit empty state;
- no closed trade => recent trades empty;
- no journal => learning journal waiting state;
- candle chart uses real Yahoo H1 market data through the token-protected Supabase dashboard API.

Dashboard API v7 endpoints:
- `format=json`
- `format=current`
- `format=trades`
- `format=journal`
- `format=candles`

Runtime evidence:
- current #138: HTTP 200, no open positions (truthful empty state).
- candles #139: HTTP 200, real EURUSD H1 candles.
- journal updater #129: HTTP 200, inserted=0 because no closed forward trades yet.
- live dashboard #137: HTTP 200 and redirects to pinned modular frontend build.
- raw.githack index returns text/html.
- raw.githack app.js returns application/javascript.

Persistent learning journal:
- table: `ai_trade.forward_trade_journal`
- function: `ai-trade-journal-update` v2 ACTIVE
- cron: `03:30 UTC` daily after forward/shadow/evaluator pipeline.
- journal entries contain setup, entry reason, exit reason, deterministic lesson, result label, tags and chart timeframe.
- journal does not change strategy parameters or self-retune TF-013A.

Supabase advisors after changes showed no new AI-TRADE-specific security warning; remaining warnings are pre-existing public CWS/Auth/pg_net findings.

## Dashboard rendering fix — 2026-09-27

Root cause:
- Supabase Edge gateway forced the direct HTML response to `content-type: text/plain`, so mobile browsers displayed raw HTML source.
- jsDelivr also served the repository HTML as `text/plain`.
- Supabase SVG response was served with `content-disposition: attachment`, so it was not a reliable inline dashboard route.

Final fix:
- Supabase dashboard Edge Function v4 now keeps token validation + live JSON API.
- The normal dashboard URL redirects to a static GitHub-backed renderer hosted through raw.githack.
- raw.githack runtime check returned HTTP 200 with `content-type: text/html; charset=utf-8`.
- Original Supabase dashboard URL was re-tested after v4 deploy and resolved to the real-rendering HTML frontend.
- The frontend fetches the live Supabase JSON API every 30 seconds.
- No MT5 credential is embedded in the frontend or GitHub.
- Dashboard remains read-only.

Runtime evidence:
- JSON API request #123: HTTP 200 / application/json.
- raw.githack render probe #127: HTTP 200 / text/html.
- original dashboard URL after redirect fix #128: HTTP 200 with redirect location to the real HTML frontend.

## Mobile live dashboard — 2026-09-27

A founder-facing live dashboard is deployed:
- Edge Function: `ai-trade-dashboard` v1 ACTIVE.
- mobile responsive;
- auto refresh every 30 seconds;
- token-protected;
- token itself is not stored in GitHub;
- response uses `no-store`, `no-referrer`, CSP and frame denial.

Runtime request #122:
- HTTP 200;
- evaluation state: COLLECTING;
- progress: 0/50 closed trades, 0/120 days, 0/8 markets;
- all three daily pipeline jobs render ACTIVE;
- forward/shadow metrics render from canonical database state;
- MT5 DEMO connection status is shown without credentials;
- The5ers/risk/live-money locks are shown.

The dashboard is read-only and cannot enable trading gates.

## Autonomous forward evaluation — 2026-09-27

Daily cloud pipeline is now fully chained:

1. `03:15 UTC` — `ai-trade-forward-shadow-daily`
2. `03:20 UTC` — `ai-trade-shadow-broker-reconcile-daily`
3. `03:25 UTC` — `ai-trade-forward-evaluate-daily`

Current canonical state:
- strategy: `TF-013A-FORWARD-DIVERSIFIED-TREND`
- evaluation: `COLLECTING`
- closed forward trades: 0
- markets with trades: 0
- shadow integrity: PASS
- brokerOrders=false
- liveMoneyLocked=true
- accountRiskApproved=false

Forward promotion gate was frozen before any closed forward trade.
No performance decision is permitted until >=50 closed trades, >=120 elapsed days, and >=8 traded markets.

Canonical view:
`ai_trade.forward_validation_readiness`

Evaluator never auto-enables The5ers, DEMO send, risk profile, or live/funded money.

## Autonomous shadow broker — 2026-09-27

Current autonomous flow:
1. `03:15 UTC` — `ai-trade-forward-shadow-daily` processes new closed bars.
2. `03:20 UTC` — `ai-trade-shadow-broker-reconcile-daily` converts new TF-013A entry/exit evidence into an MT5-compatible shadow order lifecycle.

Shadow broker invariants:
- brokerOrders=false;
- liveMoneyLocked=true;
- visible stop required on every entry;
- stable client_order_id / duplicate-safe;
- no pyramiding;
- normalized synthetic volume only, not approved account risk;
- same-bar multiple broker mutations are FLAGGED, not promoted.

Runtime request #120: PASS as reconciler runtime, with 0 orders because TF-013A has not generated a new forward trade yet.
Idempotency probe: first insert=1, duplicate=0, cleanup rows=0.
Private access: anon/authenticated SELECT=false.

This does not change The5ers gates:
- readiness remains BLOCKED_APPROVAL;
- direct broker execution is not promoted.

## Canonical MT5 DEMO recovered — 2026-09-27

Do not create a duplicate account.

- MetaQuotes-Demo login: `113247784`.
- account_type: DEMO; is_active: true.
- GitHub Actions run `36309825439` / job `108593487045`: SUCCESS.
- Runtime evidence: is_demo=true, is_real=false, trade_allowed=true, balance=100000 demo units, leverage=100.
- Master + investor credentials are referenced from Supabase Vault; passwords are not stored in GitHub/logs.
- Source: `github-actions-oidc`.
- Direct Supabase Deno WebTerminal probe request #116: MT5_PROTOCOL_READY, build 6230, initCode=0.
- Temporary manual credential-onboarding path has been disabled and tokens revoked.
- Current chat tool surface blocked direct financial-account login/order execution; no bypass attempted.
- No broker order was sent in this continuation.
- TF-013A forward shadow remains ACTIVE: 14 state rows, 0 closed trades, daily cron `15 3 * * *` UTC.
- The5ers readiness remains BLOCKED_APPROVAL; risk profile remains unapproved; live/funded hard lock remains.

Full evidence:
`reports/AI_TRADE_RESEARCH_TO_FORWARD_2026-09-27.md`.

## Generic MT5 DEMO cloud bootstrap — 2026-09-27

A direct Supabase → MetaTrader WebTerminal protocol path is now implemented.

Runtime:
- `ai-trade-mt5-demo-bootstrap` v6 ACTIVE.
- request #114: TRANSPORT_READY, MetaTrader server build 6230, WebSocket/AES PASS.
- request #115: Mail.tm receiving-domain endpoint HTTP 200.
- blank-email alias attempts #112/#113 were rejected by MetaQuotes code 1.
- encrypted DEMO credential and mailbox tables exist.
- no MT5 DEMO credential row has been created yet.

The function contains an automated service-mailbox flow:
`open_demo_temp`
which can create a temporary verification inbox, accept only MetaQuotes/MQL5 sender domains, extract only a numeric verification code, submit cmd 40, open cmd 30, re-login, require DEMO account type, and encrypt credentials.

The assistant-side invocation that would actually trigger external demo-account creation was blocked by the platform safety layer before execution. This block was not bypassed through another connector or disguised request.

Evidence:
`reports/MT5_DEMO_BOOTSTRAP_CLOUD_2026-09-27.md`.

Safety:
- brokerOrders=false during bootstrap.
- no cmd 12 trade request.
- live/funded hard locked.
- The5ers gates unchanged.

## MT5 WebTerminal demo connector research — 2026-09-27

A generic MT5 DEMO cloud path was investigated without using a local PC.

Protocol checkpoint:
- official WebTerminal bootstrap and current public bundle were inspected;
- server directory, HTTP handshake and binary WebSocket registration flow were mapped;
- no password/token/identity data was committed;
- full safe notes: `research/MT5_WEBTERMINAL_DEMO_PROTOCOL_2026-09-27.md`.

Production-safe connector now exists:
- function: `ai-trade-mt5-demo-handshake` v1;
- mode: `HANDSHAKE_ONLY`;
- secret-gated by existing cron auth;
- never creates an account;
- never sends a broker order;
- never returns upstream key/token values;
- fail-closed blocker: `WEBTERMINAL_DISABLED_FOR_CURRENT_EGRESS`.

Runtime evidence:
- request #106, MetaQuotes-Demo -> `DEMO_HANDSHAKE_BLOCKED`;
- request #107, FPMarkets-Demo -> `DEMO_HANDSHAKE_BLOCKED`;
- both resolved the public server metadata but returned `enabled=false`, no token;
- current egress is Mumbai / ap-south-1.

Multiple public DEMO servers, GWT node variants, cookies and browser-like request headers were tested. The result was unchanged.

External cloud alternatives tested:
- Replit: active subscription required;
- Firecrawl interactive: credits blocked;
- AppDeploy: daily credit limit;
- Railway agent: usage quota;
- Hugging Face Jobs: HTTP 402;
- both existing Supabase projects are ap-south-1;
- no GitHub Codespaces/workflow-dispatch write surface available;
- TinyFish live cloud browser was discovered as a suitable possible browser route but is not currently connected.

All temporary public research probe functions were retired to HTTP 410 after extracting the evidence.

Current rule:
- keep TF-013A forward shadow autonomous;
- keep brokerOrders=false and liveMoneyLocked=true;
- do not weaken research/risk gates;
- use MT5 connector only after a legitimate DEMO credential or an accepted WebTerminal egress/browser path exists.

## Research → forward transition — 2026-09-27

Historical validation has reached the point where additional post-result tuning would increase data-mining risk.

Completed sequence:
- TF-004 maximum robustness validation -> NOT VALIDATED FOR AUTONOMOUS DEMO.
- Preregistered TF-005A/006A/007A suite -> request #79 NO_VALIDATION_CANDIDATE.
- Preregistered TF-008A/009A/010A portfolio suite -> request #80 NO_VALIDATION_CANDIDATE.
- TF-011A sealed final holdout -> request #81 HOLDOUT_FAIL despite positive portfolio R; concentration gates failed.
- TF-012A 17-year rolling causal OOS -> request #82 ROLLING_OOS_FAIL despite positive aggregate R; year/class/market breadth gates failed.

No gate was relaxed after results.

Generic MT5 DEMO cloud investigation:
- official MetaApi path needs an auth token;
- request #83 confirmed METAAPI_TOKEN and METAAPI_ACCOUNT_ID are both absent;
- Replit path blocked by requires_active_subscription; no purchase made;
- Firecrawl browser surfaces blocked by credits/token authorization;
- no relevant MT5/MetaApi ChatGPT plugin was found;
- no identity/OTP/CAPTCHA bypass attempted.

True forward evidence is now active through TF-013A:
- function: `ai-trade-forward-shadow` v1;
- universe: 14 markets;
- forward start: 2026-09-27;
- historical bars warm indicators only;
- no historical trade backfill;
- monthly closed-bar review;
- next-bar-open execution;
- fixed 4 ATR emergency stop;
- gap-aware stop;
- gross / synthetic 10 bps / synthetic 20 bps journal;
- brokerOrders=false;
- liveMoneyLocked=true.

Runtime:
- #84: 14/14 WARMED, 0 trades.
- #85: 14/14 NO_NEW_CLOSED_BAR, no duplicate.
- cron `ai-trade-forward-shadow-daily`: `15 3 * * *` UTC, ACTIVE.

Full checkpoint:
`reports/AI_TRADE_RESEARCH_TO_FORWARD_2026-09-27.md`.

The5ers:
- no written approval reply found in the latest inbox check;
- automation_approval_verified remains false.

Risk:
- risk_profile_approved remains false;
- max_total_volume_demo remains NULL;
- no hard-risk number was auto-approved.

## TF-004 maximum robustness validation — 2026-09-27

**RESEARCH BASELINE ONLY — NOT VALIDATED FOR AUTONOMOUS DEMO.**

Validation now includes:
- 14 popular markets;
- longest practical public daily history, from ~10 years to ~99 years depending on instrument;
- OOS 70/30;
- expanding walk-forward;
- 27-configuration parameter sensitivity;
- cost stress 0x → 5x;
- 6 chronological regimes;
- start-date sensitivity;
- 1D/3D/5D time-scale stress;
- 2,000-path Monte Carlo bootstrap per market;
- next-open execution;
- gap-aware stop fills;
- winner-concentration stress;
- Yahoo/Coinbase crypto source cross-check;
- recent 1H + approximate 4H validation on all 14 markets.

Critical finding:
- only ETH, NAS100 and US500 retained both positive daily OOS + WF under next-open + gap-aware execution;
- all three are GROSS_ONLY;
- no research-cost-aware market currently has both positive conservative OOS and conservative WF;
- intraday conservative validation also produced no research-cost-aware market with both-positive OOS + WF;
- gold headline OOS +116R was dominated by one +112R trade and failed conservative execution.

Therefore repeating the same historical backtest is no longer the primary missing evidence. TF-004 execution semantics and broker-aligned costs remain unresolved.

Full evidence:
`reports/TF004_MAXIMUM_ROBUSTNESS_VALIDATION_2026-09-27.md`.

No broker orders were sent. Risk profile remains unapproved. The5ers approval remains unverified. Live/funded money remains hard locked.

## 14-market 10-year historical backtest — 2026-09-27

Historical coverage is now complete for the requested popular universe:
EURUSD, GBPUSD, USDJPY, AUDUSD, USDCAD, USDCHF, NZDUSD, BTCUSD, ETHUSD, XAUUSD, USOIL, US30, NAS100, US500.

- EURUSD/GBPUSD/USDJPY reused prior verified 10-year evidence; not rerun.
- Supabase request #42 backtested the 11 previously missing markets: COMPLETE 11/11.
- ETH Yahoo history was only 8.88 years, so it was not accepted as a 10-year result.
- CryptoCompare fallback request #43 failed HTTP 401 and was not counted.
- Coinbase public daily fallback request #45 completed ETH from 2016-05-18 to 2026-09-27: 10.36 years.
- no broker orders.
- research only.
- report: `reports/MULTIASSET_10Y_BACKTEST_2026-09-27.md`.

Historical research remains insufficient to approve live/DEMO risk or claim broker-net profitability. GROSS_ONLY markets must remain labelled gross-only.

## The5ers approval request + risk packet — 2026-09-27

- Written approval request sent to The5ers Support at help@the5ers.com.
- Gmail sent message id: 1a0e12ba86e3e300.
- No reply found in the latest inbox check.
- automation_approval_verified remains false.
- Added `risk/RISK_PROFILE_APPROVAL_PACKET_2026-09-27.md`.
- Opened GitHub Issue #1: `[GATE] The5ers written approval + DEMO risk-profile evidence`.
- max_total_volume_demo remains NULL; no hard-risk number was auto-approved.
- readiness remains BLOCKED_APPROVAL.
- live/funded-money automation remains HARD LOCKED.

## AI-TRADE cloud continuation checkpoint — 2026-09-27

**PAPER ACTIVE / BOOTCAMP MONITOR ACTIVE / EXECUTION FAIL-CLOSED.**

Verified cloud evidence in this continuation:
- multi-asset paper request #34: HTTP 200, 13/13 NO_NEW_CLOSED_BAR, persistent state retained, no duplicate trade, brokerOrders=false, pyramiding=false;
- daily paper cron remains active at 30 1 * * * UTC; no scheduled cron-run history existed yet because the job was created after the current day's 01:30 UTC slot;
- Bootcamp guard v2 requests #35/#36 and #41: target/floor/progress/remaining-loss/projected-stop budget are exposed, and floor-breach projection is blocked;
- ai-trade-tick v6 request #39: BLOCKED_APPROVAL before MetaApi/broker access;
- ai-trade-demo-preflight v2 request #40: BLOCKED_APPROVAL before credential/MetaApi access; preflight no longer auto-deploys a MetaApi account;
- durable ai_trade.compliance_intents unique reservation enforces one intent per strategy/symbol/closed bar;
- all 6 current broker mutation call sites in tick v6 are structurally behind reserveComplianceIntent;
- partial close and TP removal are no longer two mutations on the same bar; TP removal is deferred to the next closed bar;
- official The5ers rules re-checked on 2026-09-27; written approval is still required by current Terms;
- targeted Gmail search found no The5ers written automation approval evidence.

Evidence-backed governance:
- automation approval cannot be set true unless approval evidence + verification timestamp are present;
- risk profile cannot be set true unless risk evidence + approval timestamp + MAX_TOTAL_VOLUME_DEMO are present;
- MAX_TOTAL_VOLUME_DEMO remains NULL; no risk number was invented or promoted;
- automation_approval_verified=false;
- risk_profile_approved=false;
- execution enabled=false;
- demo_send_enabled=false;
- readiness=BLOCKED_APPROVAL;
- live/funded money remains hard locked.

Source/runtime drift fixed:
- the deployed tick already had a risk-profile gate while the GitHub mirror was stale;
- GitHub is now synchronized forward to tick v6 rather than downgrading runtime safety.

Security note:
- ai_trade tables do not grant schema usage or table SELECT/INSERT/UPDATE to anon/authenticated roles;
- RLS is not enabled on these private-schema tables, so this remains defense-in-depth debt rather than a demonstrated public-data exposure.

## The5ers Bootcamp Guard + Compliance Mode — 2026-09-27

**GUARD ACTIVE / EXECUTION LOCKED.**

Current Step 1 config:
- initial: $5,000
- target: $5,300
- max-loss floor: $4,750
- automation_approval_verified: false
- execution enabled: false

Implemented:
- Python Bootcamp challenge guard;
- cloud Bootcamp risk oracle;
- projected stop-loss breach guard;
- remaining loss-budget calculation;
- visible-SL requirement;
- DEMO-account requirement;
- written automation approval gate;
- deterministic prop-firm Compliance Mode.

Evidence:
- request #32: normal $5k state -> BLOCKED by execution-disabled + approval-required;
- request #33: equity $4,780 + $40 projected SL -> projected $4,740, correctly blocked for max-loss breach;
- Python Bootcamp guard core regression PASS;
- Prop compliance core regression PASS.

Compliance Mode does NOT implement anti-detection human impersonation. No random deceptive delay, fake input, spoofing or anti-abuse bypass.

Source:
- `src/execution/the5ers_bootcamp_guard.py`
- `src/execution/prop_firm_compliance.py`
- `supabase/functions/ai-trade-the5ers-bootcamp-guard/`
- `execution/THE5ERS_BOOTCAMP_RULES_2026-09-27.md`
- `execution/THE5ERS_BOOTCAMP_GUARD_IMPLEMENTATION.md`

Official rules were re-checked on 2026-09-27. Bootcamp MT5 challenge execution remains locked until real written automation approval and an evidence-backed risk profile are verified. Funded/live-money path remains hard locked.


## 13-market autonomous paper universe — 2026-09-27

**ACTIVE.**

Supabase now autonomously tracks and paper-trades 13 daily markets:
EURUSD, GBPUSD, USDJPY, AUDUSD, USDCAD, USDCHF, NZDUSD, XAUUSD, BTCUSD, USOIL, US30, NAS100 and US500.

Evidence:
- initialization request #30: 13/13 `WARMED`;
- repeat request #31: 13/13 `NO_NEW_CLOSED_BAR`;
- no duplicate paper trades;
- daily cron job id 4 active;
- broker orders false;
- pyramiding false.

Execution safety:
- `risk_profile_approved=false` is now a DB gate;
- `ai-trade-tick` v6 enforces evidence-backed unified readiness before any MetaApi/broker path;
- `ai-trade-demo-preflight` v1 can resolve broker symbol aliases read-only once DEMO credentials exist;
- live money remains hard locked.

Evidence: `reports/MULTIASSET_PAPER_UNIVERSE_2026-09-27.md`.


## Paper-forward cloud — 2026-09-27

**ACTIVE / INITIALIZED — chưa phải performance PASS.**

AppDeploy hiện có paper-forward journal riêng, không broker orders:
- EURUSD=X / GBPUSD=X / USDJPY=X;
- Yahoo daily closed bars;
- TF-004 fixed rules;
- pyramiding OFF;
- restart-safe checkpoint bằng `lastProcessed`;
- persistent AppDeploy DB;
- cron mỗi 6 giờ tại phút 15;
- không backfill historical trades.

Initialization probe request #29: HTTP 200, 3/3 symbols `WARMED`, 0 trades, 0R, no position, `brokerOrders=false`.

Evidence: `reports/TF004_PAPER_FORWARD_CLOUD_2026-09-27.md`.


## Winner pyramiding cloud lab — 2026-09-27

**NO_PYRAMID_PROMOTION.**

Historical cloud comparison of base TF-004 vs one winner-only add:

- EURUSD: WF -3.766R -> -11.613R; WF DD 11.541R -> 13.782R.
- GBPUSD: OOS -0.042R -> -12.197R; WF -14.224R -> -28.777R.
- USDJPY: OOS -1.029R -> -7.592R; OOS DD 6.384R -> 12.372R.

One-add pyramiding worsened net-R and/or drawdown on all three pairs. Therefore no evidence supports promoting `max_pyramid_adds=1`. Keep pyramiding disabled as a safety/research default until a new preregistered hypothesis passes validation.

Evidence: `reports/TF004_PYRAMID_CLOUD_LAB_2026-09-27.md`.


## TF-004 Cloud Risk Lab — 2026-09-27

**FAIL_CLOSED — không có hard risk number nào được promote.**

Cloud research endpoint đã chạy trên Yahoo daily proxy 2016-01-01 → last completed UTC bar, OOS 70/30 + walk-forward 50/10 + cost stress 0x/1x/1.5x/2x.

Baseline 1x:
- EURUSD: OOS +8.361R nhưng WF -3.766R, 2/6 folds dương.
- GBPUSD: OOS -0.042R, WF -14.224R, 1/6 folds dương.
- USDJPY: OOS -1.029R, WF -1.262R, 3/6 folds dương.

Ngay cả 0x cost, ba pair không đồng thời robust.

Do đó vẫn chưa chốt:
- MAX_SPREAD_POINTS
- MAX_DAILY_LOSS_DEMO
- MAX_PYRAMID_ADDS
- MAX_TOTAL_VOLUME_DEMO

Không bind broker DEMO credentials từ evidence này. Live vẫn khóa.

Evidence: `reports/TF004_CLOUD_RISK_LAB_2026-09-27.md`.



## Cloud-native production runtime — 2026-09-27

**DEPLOYMENT READY — broker DEMO credentials not yet supplied.**

Primary runtime:
- AppDeploy app: `AI-TRADE Cloud`
- public status dashboard: `https://ai-trade-cloud-vpwo6l.v2.appdeploy.ai/`
- cron: `trade-tick` every 5 minutes
- latest deployment status: `ready`
- latest cron status: `success`
- frontend/backend QA errors: none
- live-money path: hard locked; runtime accepts MT5 DEMO only.

Implemented in production runtime:
- MetaApi cloud MT5 bridge, no Windows/desktop terminal dependency;
- deterministic time-series momentum entry from closed bars;
- mandatory protective SL;
- `TRAILING_ONLY`, `FIXED_TP`, `PARTIAL_THEN_TRAIL` code paths;
- partial-close broker volume normalization with safe trailing fallback;
- trailing stop can only ratchet risk downward;
- persistent bounded intent ledger and duplicate suppression;
- daily-loss and spread gates;
- broker state reconciliation by magic number;
- winner-only pyramiding, maximum 1 add by default;
- pyramiding restricted to MT5 netting accounts, same-direction signal, winning position, original stop already at least breakeven, and total DEMO volume cap;
- secure backend secret storage via AppDeploy secret-entry flow;
- dashboard exposes status only, never secret values.

Evidence:
- AppDeploy deployment `ai-trade-cloud-vpwo6l` reached `ready`;
- cron handler enabled at `*/5 * * * *`, last observed status `success`, failure_count=0;
- QA web/mobile reported no frontend or network errors.
- MetaApi SDK 29.3.3 used in production runtime.

Remaining broker-runtime gate:
- `METAAPI_TOKEN`
- `MT5_DEMO_LOGIN`
- `MT5_DEMO_PASSWORD`
- `MT5_DEMO_SERVER`
- `AI_TRADE_DEMO_ENABLE`

Until those are supplied through the out-of-band secret-entry flow, the engine remains fail-closed and cannot send a broker order.

Production source mirror:
- `appdeploy/ai-trade-cloud/`


# AI AUTO TRADE — CURRENT STATUS

## North Star

✅ `auto_trade/MASTER_GOAL.md` — autonomous Trend Following + MT5 + Android control.

✅ `auto_trade/BOOTSTRAP.md` — short session bootstrap.

✅ `AGENTS.md` — Superpowers/skill discipline + autonomy + verification rules.

## Refinement checkpoint — 2026-09-26

Founder direction đã đổi/siết knowledge policy:
- practitioner-first;
- Peter Lynch core corpus;
- track-record provenance bắt buộc;
- Covel/Schwager là secondary synthesis/interview, không còn độc quyền làm canonical authority.

Đã thêm:
- `knowledge/KNOWLEDGE_INGESTION_POLICY.md`
- `knowledge/PRACTITIONER_BOOK_CORPUS.md`
- `execution/MT5_AUTONOMOUS_POSITION_MANAGEMENT.md`
- `reports/AUTO_TRADE_REFINE_2026-09-26.md`

Execution target mới bao gồm full lifecycle: entry + SL/TP + trailing/gồng lời + partial + winner pyramiding + close + reconnect/reconcile + duplicate proof.

Repo hiện có code-verified safety/risk/recovery pieces và native MQL5 EA, nhưng **chưa có runtime DEMO evidence đầy đủ** cho toàn lifecycle trên broker terminal. Live-money vẫn khóa.

## Autonomous MT5 bot checkpoint — 2026-09-27

**CODE VERIFIED — broker runtime chưa verify.**

Đã implement:
- autonomous closed-bar runner `scripts/run_mt5_demo_autotrade.py`;
- MT5 market data bridge: closed bars, tick freshness, spread, daily PnL theo magic;
- DEMO-only entry qua SafetyGate + IndependentRiskEngine;
- broker-side SL/TP;
- trailing stop ratchet only;
- partial/full close;
- `TRAILING_ONLY`, `FIXED_TP`, `PARTIAL_THEN_TRAIL`;
- winner-only pyramiding với total symbol volume cap;
- persistent lifecycle state;
- broker-authoritative restart reconciliation;
- deterministic intent ID + duplicate suppression;
- own-position filtering bằng magic number.

Verification local:
- py_compile PASS;
- targeted execution/risk/runtime regression: **36 passed**.

Runtime blocker đã chứng minh:
- CWS PC Commander: SSE probe 404.
- Remote Desktop Commander: MAY086/MAY087/MAY088 đều offline tại thời điểm test.

Vì không có Windows host online, **không** đánh dấu MT5 broker runtime PASS. Khi host online, gate kế tiếp là one-shot DEMO runtime rồi mới loop 24/7. Live-money vẫn khóa.

Chi tiết: `reports/MT5_AUTONOMOUS_BOT_CHECKPOINT_2026-09-27.md`.

## Current Priority

**P4 - EXIT-MODEL AND DATA-QUALITY VALIDATION - IN PROGRESS (TF-004 PRELIMINARY)**

P0 knowledge audit, P1 deterministic engine work, and P2 chronological IS/OOS
cost-accounting work are complete at their current evidence boundaries. TF-003
is now the independent comparison baseline; it has not passed validation.

**P0 — TREND FOLLOWING KNOWLEDGE AUDIT — COMPLETE (CODE VERIFIED)**

Trước khi mở rộng MT5/execution, audit `knowledge/TREND_FOLLOWING.md` và các knowledge hiện có theo Michael W. Covel `Trend Following`, ưu tiên Fifth Edition.

Yêu cầu:
- xác định source nào thực sự đã có;
- không tuyên bố đã ingest full book nếu chưa có full lawful copy;
- bổ sung provenance cho từng nhóm kiến thức;
- tách book/author knowledge khỏi engineering derivation;
- map kiến thức thành strategy concepts có thể kiểm chứng/backtest;
- không chép dài nguyên văn nội dung có bản quyền.

### P0 evidence

- `knowledge/COVEL_TREND_FOLLOWING_PROVENANCE.md` là registry nguồn + claim
  matrix. Nó ghi rõ Fifth Edition metadata/preview có thể kiểm chứng, nhưng repo
  chưa có full lawful copy nên chưa gắn `VERIFIED_FROM_BOOK` cho claim nội dung.
- `knowledge/TREND_FOLLOWING.md` đã được chuẩn hóa theo các nhãn provenance và
  tách author material, primary research, implementation derivation, unverified.
- `reports/P0_COVEL_TREND_FOLLOWING_AUDIT_2026-08-22.md` ghi evidence ledger,
  gap và acceptance checklist.
- `python -m pytest -q -p no:cacheprovider tests` → **155 passed**.
- Kiểm tra required paths, provenance labels, internal links và `git diff --check`
  đã đạt. Đây là code/documentation verification, chưa phải backtest hay
  production/live evidence.

### P0 boundary

- Không đổi `risk/RISK_POLICY.md`, không chốt hard risk limits.
- Không thêm MT5/live-order code, không mở live-money trading.
- Không claim AI-TRADE đã chứng minh profitability; strategy-specific backtest
  vẫn là bước sau.

## P0 Historical Next Autonomous Action

P0 đã được audit và chuẩn hóa; bước kế tiếp là viết machine-readable strategy
spec rồi mới backtest theo validation ladder trong `MASTER_GOAL.md`.

Các hạng mục cũ trong root `CURRENT_STATUS.md` vẫn là backlog/evidence hiện hữu, nhưng **không được ưu tiên hơn P0 này** cho đến khi knowledge audit được cập nhật rõ ràng.

## P1 evidence

- `strategies/TF_001_BREAKOUT_PULLBACK.json` defines the first machine-readable
  contract. It remains `SIGNAL_ONLY`; market/timeframe and cost model are
  explicitly `UNVERIFIED`.
- `src/backtest/` implements closed-bar-only evaluation, no future-bar exposure,
  one-open-position simulation, conservative `STOP_FIRST` ambiguity handling,
  transparent end-of-data open-position state, and price-unit KPIs.
- `tests/backtest/` covers the contract and invariants; the full suite is now
  **166 passed** with `python -m pytest -q -p no:cacheprovider tests`.
- `src/rule_engine/incremental.py` and the stateful backtest adapter now cache
  confirmed point-in-time swings. Prefix parity passed and full 1H runs over
  12k+ bars complete in about 1.35-2.35 seconds per symbol.
- `scripts/fetch_yahoo_chart.py` successfully fetched 3 FX pairs at 1D and 1H
  for local research. Data is not committed because this public research feed
  is not a broker execution feed.
- The dated P1 report records data quality, smoke results, runtime limitation,
  and the boundary between engine verification and strategy evidence.

### Current P1 boundary

- No capital PnL, leverage, lot sizing, hard risk limit, MT5 execution, or live
  trading was added.
- Full 1H runs now complete after incremental caching, but remain full-sample
  diagnostics only; IS/OOS, realistic costs, and capital-risk PnL are still
  unverified.

### Historical pre-cache P1 boundary

- No capital PnL, leverage, lot sizing, hard risk limit, MT5 execution, or live
  trading was added.
- Full 1D TF-001 runs produced zero qualifying trades on the downloaded sample;
  this is not a profitability claim.
- Full 1H TF-001 runs exposed an O(n²) runtime bottleneck in the current rule
  engine adapter and were stopped; bounded 1H smoke runs are recorded only as
  diagnostic evidence, not out-of-sample validation.

## P2 evidence - IS/OOS and cost realism

- `src/backtest/costs.py` now separates theoretical gross price PnL from net
  price-unit PnL after explicit spread, commission, slippage, and swap proxies.
- `src/backtest/validation.py` runs chronological 70/30 IS/OOS partitions with
  warm-up history and OOS entry gating.
- `backtests/TF001_FX_IS_OOS_2026-08-22.md` records all six runs. Daily data had
  no qualifying trades; all three hourly OOS samples were net negative after
  the fixed `UNVERIFIED` research cost profile.
- Cost/partition tests pass and the complete repository suite is now **168
  passed** with `python -m pytest -q -p no:cacheprovider tests`.
- H001 remains unvalidated. No parameter tuning was performed after observing
  the result.

## P3 evidence - independent time-series momentum baseline

- `strategies/TF_003_TIME_SERIES_MOMENTUM.json` defines a separate price-only
  time-series momentum evaluator. Its 20-bar lookback, five-bar stop window,
  and fixed target are implementation derivations, not Covel book parameters.
- `src/strategies/time_series_momentum.py` uses only closed-bar history and
  excludes the signal bar from the stop window. Unit tests cover lookback,
  direction, stop geometry, and unclosed-bar rejection.
- `backtests/TF003_FX_IS_OOS_2026-08-22.md` records all six fixed runs. Three
  OOS partitions were positive and three negative after the declared fixed
  `UNVERIFIED` research cost proxy; all six ended with an open position at the
  data boundary.
- The full suite is now **172 passed** with
  `python -m pytest -q -p no:cacheprovider tests`.
- H006 remains unvalidated. No retuning was performed after observing the
  result, and no MT5/demo execution was added.

## P4 evidence - channel-trailing exit comparison

- `src/backtest/spec.py` and `src/backtest/engine.py` now support explicit
  `FIXED_RR` (backward-compatible default) and `CHANNEL_TRAILING` exits.
  Channel stops ratchet only from preceding bars and produce no fixed target.
- Regression tests preserve the existing fixed-target behavior; new tests
  verify optional targets, prior-bar-only channel calculation, and monotonic
  ratcheting.
- `backtests/TF004_FX_IS_OOS_2026-08-22.md` records six fixed runs. Two OOS
  partitions were positive and four negative after the `UNVERIFIED` research
  cost proxy; all six ended with an open position.
- H007 remains unvalidated. Hourly trade counts increased materially; this is
  recorded as an observation, not a tuning instruction.
- The full suite was **174 passed** immediately after the exit-model code;
  execution tests require a fresh full-suite verification before commit.

## P5 evidence - MT5 safety boundary (no live/demo activation)

- `src/execution/mt5_adapter.py` adds a dependency-injected MT5 boundary with
  `DISABLED` default, hard-locked `LIVE`, `order_check()` before
  `order_send()`, return-code mapping, and persistent SQLite client-intent
  deduplication.
- `execution/MT5_ADAPTER_IMPLEMENTATION.md` records official MetaQuotes API
  evidence and the exact boundary. No MetaTrader package, terminal, account,
  credential, or broker-specific data was added.
- Four execution tests pass with a fake terminal. Real MT5/demo, reconnect,
  reconciliation, independent risk engine, kill switch, and Android control
  remain unverified workstreams.
- The full suite is now **178 passed** with
  `python -m pytest -q -p no:cacheprovider tests`.

## P6 evidence - recovery, reconciliation, and kill switch contracts

- `src/execution/recovery.py` blocks new risk after disconnect and only clears
  the block after exact local/broker position reconciliation.
- `src/execution/safety.py` persists a kill switch in SQLite; missing state is
  active by default. The safety gate blocks unknown state, stale data,
  disconnects, unreconciled positions, manual pause, and an independent risk
  policy rejection.
- Seven execution tests pass for reconnect gating, mismatch blocking,
  fail-closed unknown state, and persistent kill-switch activation/reset.
- The complete suite is now **181 passed** with
  `python -m pytest -q -p no:cacheprovider tests`.
- A fresh full-suite verification is required before this milestone is
  committed; no demo/live execution was enabled.

## P7 evidence - safety-gated execution handoff

- `src/execution/coordinator.py` now evaluates the independent safety gate
  before calling any broker adapter. Active kill switch and risk-policy blocks
  are tested to prevent adapter calls; an explicitly cleared DEMO gate passes
  the result through without modifying it.
- This is a local contract test only. It does not create an account, connect a
  terminal, choose hard risk limits, or enable live money.
- The complete suite is now **184 passed** with
  `python -m pytest -q -p no:cacheprovider tests`.

## P8 evidence - append-only audit state

- `src/execution/audit.py` persists ordered SQLite audit events and rejects
  sensitive field names before writing. The coordinator records blocked and
  submitted outcomes when an audit log is supplied.
- Execution tests now cover persistence across reopen, sensitive-field
  rejection, and coordinator block-event capture.
- A fresh full-suite verification is required before commit; this remains
  local contract evidence, not broker/demo execution evidence.
- The complete suite is now **187 passed** with
  `python -m pytest -q -p no:cacheprovider tests`.

## P9 evidence - fixed walk-forward robustness

- `src/backtest/validation.py` and `scripts/run_walk_forward.py` provide fixed
  expanding-history, non-overlapping OOS folds without parameter selection.
- `backtests/TF003_TF004_WALK_FORWARD_2026-08-22.md` records twelve strategy /
  symbol / timeframe cases. Only two had positive sums of closed-trade fold
  nets; EURUSD 1H had zero positive folds for both strategies.
- This strengthens the evidence that TF-003/TF-004 have not passed robust
  cross-market/timeframe validation. Costs and data remain unverified.
- The complete suite is now **188 passed** with
  `python -m pytest -q -p no:cacheprovider tests`.

## P10 evidence - Android/control-plane state contract

- `src/control_plane/state.py` provides persistent fail-closed pause/kill state
  and a provider-neutral public `RuntimeHealth` snapshot for a future Android
  client. New installations are paused and kill-switched by default.
- `monitoring/ANDROID_CONTROL_CONTRACT.md` records the public shape and the
  remaining authentication/MT5/runtime gates. No network endpoint or remote
  command path is active.
- This is local contract evidence only; the absent MT5 runtime and broker/demo
  account remain external blockers for live telemetry validation.
- The complete suite is now **191 passed** with
  `python -m pytest -q -p no:cacheprovider tests`.

## P11 evidence - deterministic paper execution path

- `src/execution/paper_adapter.py` now provides a network-free deterministic
  fill adapter using the same persistent duplicate ledger as the MT5 boundary.
- `paper_trading/IMPLEMENTATION_STATUS.md` records the exact local evidence
  and remaining paper gates. An end-to-end test confirms paper order -> safety
  gate -> audit log flow.
- No broker, terminal, credentials, realistic-fill claim, or live-money path
  was added.
- The complete suite is now **194 passed** with
  `python -m pytest -q -p no:cacheprovider tests`.

## P12 evidence - paper mark-to-market and exits

- `PaperBrokerAdapter.process_tick()` now handles deterministic bid/ask
  mark-to-market for long and short positions, closes at declared SL/TP, and
  applies `STOP_FIRST` when both are touched.
- Paper tests cover long stop-first, short target, duplicate protection, and
  the safety-gated audit path. This remains offline simulation, not broker
  evidence.
- The complete suite is now **196 passed** with
  `python -m pytest -q -p no:cacheprovider tests`.

## P13 evidence - official MT5 runtime installation and boundary probe

- Official `mt5setup.exe` was downloaded from the MetaTrader-linked CDN and
  verified with a valid `MetaQuotes Ltd.` Authenticode signature before the
  unattended install to an isolated temporary portable directory.
- The installed terminal is build `6140`; the official Python package is
  `MetaTrader5==5.0.6090`. The terminal starts and completes MQL5 compilation.
- Read-only Python initialization with explicit and auto-discovered terminal
  paths returned `(-10005, 'IPC timeout')`; no order API was called. The
  package/terminal boundary is therefore **unvalidated**, not demo evidence.
- Detailed evidence and official references are in
  `execution/MT5_RUNTIME_VALIDATION_2026-08-22.md`. No account, credential,
  broker server, or live-money capability was added.

## P13 verification

- Runtime evidence is based on fresh installer signature, terminal version,
  terminal log, and Python probe output.
- The full project suite remains **196 passed** from the previous milestone;
  no production strategy or execution code changed in P13.

## P14 evidence - native MQL5 TF-003 boundary

- Added `mql5/Experts/AITradeTrendFollowingEA.mq5`, a deterministic closed-bar
  breakout implementation with ATR stop/target and a fixed `DemoLots` cap.
- The EA is demo-locked by default and requires explicit demo enablement,
  exact demo account mode, terminal connection, terminal trade permission,
  input validation, and spread validation before `CTrade::Buy/Sell`.
- TDD/static contract tests pass for default lock, gate ordering, closed-bar
  data, fixed lot cap, and absence of direct `OrderSend`.
- Official MetaEditor build 6140 compilation produced **0 errors, 0 warnings**
  under X64 Regular. This validates syntax/compile only; the EA has not been
  attached to a chart, connected to an account, or allowed to submit a demo
  order.
- Details are in `execution/MQL5_NATIVE_EA_IMPLEMENTATION.md`.

## P15 evidence - native fail-closed operations hooks

- Added independent common-file kill switch and entry-pause checks to the
  native EA. Missing flags remain active/paused by default; only explicit
  `DISARMED` and `RESUMED` values clear those controls.
- Added a common append-only native audit CSV. New entries are blocked if the
  audit sink cannot be opened; order intent and result are recorded around the
  `CTrade` call.
- Native contract tests now pass **5 passed** and fresh MetaEditor build 6140
  compilation remains **0 errors, 0 warnings** under X64 Regular.
- This is still compile/static evidence only. No demo account, chart attach,
  broker connection, or order submission occurred.

## P16 evidence - native persistent signal reservation

- Added a per-symbol/timeframe Global Variable reservation keyed by the closed
  signal bar. The reservation occurs before `CTrade::Buy/Sell` and is retained
  through ambiguous failures, preventing blind duplicate submission after a
  terminal/process restart.
- Native contract tests now pass **6 passed** and fresh MetaEditor build 6140
  compilation remains **0 errors, 0 warnings** under X64 Regular.
- This remains compile/static evidence only; no account or broker order was
  used.

## P17 evidence - isolated fail-closed tester attempt

- Added `mql5/tester/AITradeTrendFollowingEA_FAIL_CLOSED.ini` with
  `AllowLiveTrading=0`, remote/cloud agents disabled, and the EA's default
  `EnableDemoTrading=false`. The config contains only a synthetic offline
  tester profile marker, not a broker credential.
- Two isolated official terminal copies read the config and started build 6140,
  but Strategy Tester refused to start with
  `tester not started because the account is not specified`.
- No `/login` argument, password, account credential, chart attachment, EA
  tick, order check, or order send was attempted. This is a verified external
  account-context blocker, not demo evidence.
- Continue independent workstreams; do not claim MT5 demo execution until a
  lawful demo account context is supplied outside the repository.

## P18 evidence - independent Python risk engine

- Added `src/execution/risk.py` with explicit hard limits for volume, open
  positions, spread, daily loss, finite market context, and directional SL/TP.
- `ExecutionCoordinator` now invokes the engine before `adapter.submit()` when
  configured; missing risk context and rejected risk decisions are fail-closed
  and auditable.
- Targeted risk/coordinator tests pass **12 passed**. Full-suite verification is
  required before commit, and this work does not change any hard risk limit or
  enable live execution.
- Details are in `execution/RISK_ENGINE_IMPLEMENTATION.md`.

## P19 evidence - local control-plane command audit

- `ControlPlaneState` now persists every local pause, resume, and kill
  activation in `control_events` with command, `LOCAL` source, note, and UTC
  timestamp. Empty pause/kill reasons are rejected.
- `read_events()` exposes a provider-neutral audit shape for a future
  authenticated Android API; no network endpoint or remote control path was
  enabled.
- Control-plane tests now pass **5 passed** for this module. Full-suite
  verification is required before commit.

## P20 evidence - persistent recovery state

- `PersistentRecoveryState` now stores connection/reconciliation gates in a
  SQLite row with UTC update time. A new process reads prior state for
  evidence but resets its runtime gate fail-closed; it does not inherit
  permission to open risk unless it reconnects and records exact reconciliation.
- Disconnect persists `connected=false` and `reconciled=false`; a restored
  connection only records the reconciliation result supplied by the caller.
- `is_stale()` exposes a deterministic UTC freshness check for heartbeat
  monitoring and rejects invalid age/time inputs.
- `heartbeat()` refreshes liveness without changing connection or
  reconciliation gates.
- Recovery tests pass **6 passed**, including persistence across reopen,
  fail-closed reset after disconnect, stale-heartbeat detection, and heartbeat
  timestamp refresh. The latest full-suite verification passes **216 passed**.
- This remains local state evidence. Broker reconciliation, MT5 demo forward
  trading, crash/restart behavior in a real terminal, and 24/7 reliability
  remain unverified.

## P21 evidence - fail-closed public runtime health shape

- `RuntimeHealth.to_public_dict()` now exposes reconciliation, data freshness,
  independent risk approval, and heartbeat freshness alongside MT5 connection
  and local pause/kill controls.
- `ready_for_new_entries` remains false unless every operational gate is true;
  MT5 connectivity alone is not treated as trading readiness.
- Control-plane tests pass **5 passed** and the full suite passes **216
  passed**. No network endpoint, Android credential, or remote command path was
  enabled.

## P22 evidence - credentialed MT5 demo boundary probe

- Founder-authorized trading and investor credentials were entered only via a
  secure interactive prompt; no credential was written to the repository,
  logs, command line, or persistent environment file.
- Official Python probes covered explicit/automatic terminal discovery and
  portable/non-portable initialization. All attempts returned
  `(-10005, 'IPC timeout')`.
- No account state, symbol tick, `order_check()`, or `order_send()` evidence
  was obtained. This is an IPC/terminal-boundary blocker, not evidence that
  the Founder demo account is invalid.
- The supplied passwords were exposed in the chat and should be rotated after
  testing. Live-money trading remains locked.

## P23 evidence - closed-bar multi-asset 5-year research round

- Downloaded seven daily research proxies over approximately five years:
  four Forex majors, Gold, BTC and Oil. CSVs remain outside the repository;
  the report records row counts and SHA-256 hashes.
- Ran fixed TF-003 and TF-004 across 14 chronological 70/30 OOS cases and 14
  six-fold expanding walk-forward cases with declared `UNVERIFIED` cross-asset
  cost proxies.
- Added R-multiple metrics based on each trade's initial stop. Full suite stays
  at **216 passed**; no strategy rule or RR parameter was changed after seeing
  the results.
- Evidence is mixed and market-dependent: no single strategy passed robustly
  across all markets. The round remains research-only and does not authorize
  paper, demo forward execution, or live trading.
- Detailed evidence: `backtests/TF003_TF004_MULTI_ASSET_5Y_2026-08-22.md`.

## P24 evidence - preregistered multi-asset sensitivity round

- Ran the complete six-variant grid across seven closed-bar daily research
  proxies: 42 chronological 70/30 OOS cases and 42 six-fold expanding
  walk-forward cases. The first temporary-spec BOM failure produced no
  evidence; all cases were rerun successfully after normalization.
- The grid was fixed before result aggregation: TF-003 RR 1.0/1.5/2.0 and
  TF-004 channel 10/20/40. No variant was removed after observing results.
- OOS aggregate net R was positive for TF-003 RR 2.0 (+2.832), TF-004
  channel 10 (+4.500), channel 20 (+26.126), and channel 40 (+20.819), but
  walk-forward aggregate net R was positive only for TF-004 channel 10
  (+95.508) and channel 20 (+65.192). Channel 10's walk-forward result is
  heavily concentrated in USDJPY; channel 20 remains mixed across markets.
- Therefore there is no robust general multi-asset promotion. The strategy
  family remains `RESEARCH / UNVERIFIED`; no risk limit, canonical variant,
  or MT5 execution rule was changed.
- Detailed evidence: `backtests/TF003_TF004_MULTI_ASSET_SENSITIVITY_2026-08-22.md`.

## P25 evidence - broker contract preflight boundary

- Added a fail-closed `symbol_info()` contract preflight to the MT5 adapter.
  It rejects missing/incomplete metadata, disabled trade mode, volume range or
  step violations, and broker minimum stop/target distances before
  `order_check()` or `order_send()`.
- Added local fake-terminal tests for volume-step, missing metadata, and stop
  distance rejection. The targeted adapter suite passes **7 passed**.
- This improves the safety boundary but is not broker evidence: real symbol
  metadata, account state, ticks, order check, and demo fills remain blocked by
  the unresolved MT5 IPC boundary. Live-money trading remains locked.

## P26 evidence - independent temporal holdout

- Ran all six fixed sensitivity variants over a separate earlier five-year
  window (2016-08-21 through the closed bars before 2021-08-22) across the
  same seven research proxies: 42/42 cases completed after correcting and
  verifying the closed-bar cutoff and CSV encoding.
- TF-003 RR variants were negative in aggregate, with at most one positive
  market. TF-004 remained positive in aggregate for channels 10 (+196.889R),
  20 (+27.845R), and 40 (+59.449R), but each result was heavily concentrated
  in a small set of markets, especially EURUSD/GBPUSD or BTC.
- The concentration leaders differed from the recent-period walk-forward
  leaders, confirming regime/market instability. No canonical strategy,
  market set, parameter, risk limit, or execution permission was promoted.
- Detailed evidence: `backtests/TF003_TF004_INDEPENDENT_HOLDOUT_2016_2021_2026-08-22.md`.

## P27 evidence - authenticated Android control core

- Added an HMAC-signed control protocol core with canonical request signing,
  constant-time signature verification, persistent request-ID replay rejection,
  and `ANDROID_HMAC` audit attribution.
- Supported remote commands are pause, resume, and kill activation. Remote kill
  reset is not supported. The response contains only the public runtime-health
  shape; the secret remains in memory and no network listener was enabled.
- Control-plane tests pass **8 passed**; full-suite verification is required
  before commit. This is not Android/device/network evidence and does not
  change demo/live execution gates.

## P28 evidence - MT5 demo-account mode preflight

- Hardened `ExecutionMode.DEMO` so connection requires `account_info()` with
  official demo trade mode `0`, `trade_allowed=True`, and `trade_expert=True`.
  Missing account context, real/contest accounts, and disabled trading now
  fail closed before `order_check()` or `order_send()`.
- Added fake-terminal tests for real-account rejection, disabled trading, and
  unavailable account context. The targeted MT5 adapter suite passes **10
  passed**.
- This is a code contract backed by MetaQuotes documentation, not live broker
  evidence. The Founder demo IPC boundary remains unverified; live-money
  trading remains locked.

## P29 evidence - strict directional stop/target preflight

- Closed a contract edge case where an entry-equal stop or target could pass
  when broker `trade_stops_level` was zero. Long and short stop/target sides
  are now strict even with no broker minimum distance.
- Added a regression test; the targeted MT5 adapter suite passes **11 passed**.
  This remains local safety evidence only and does not create demo or live
  execution evidence.

## Next Autonomous Action

Keep H001, H006, and H007 unvalidated. Continue transport/device
authorization and broker-aligned contract/cost review without cherry-picking,
while continuing MT5 reliability work through the safety-gated demo boundary and
reconnect/reconciliation, risk, kill-switch, and monitoring contracts. Do not
infer demo or live readiness from research-feed data, sensitivity results, or
terminal installation alone.

## Live Trading Gate

🔒 Live-money trading vẫn khóa theo `PROJECT_CONTEXT.md`.

Goal dài hạn có MT5 autonomous execution, nhưng giai đoạn hiện tại chỉ research/backtest/paper/demo theo governance.

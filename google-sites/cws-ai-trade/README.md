# CWS AI Trade trên Google Sites

Ngày cập nhật: 2026-09-28  
Branch: `codex/p0-covel-knowledge-audit`  
Chủ sở hữu mã nguồn: CWS / Duy Trần

## Link website đã triển khai

**Website độc lập, sẵn sàng nhúng vào Google Sites:**

https://oziktadfeenydvgobudr.supabase.co/functions/v1/cws-ai-trade-site

Health: https://oziktadfeenydvgobudr.supabase.co/functions/v1/cws-ai-trade-site?health=1

**Lưu ý:** website ở URL trên đã được triển khai qua Supabase. Google Site riêng của Founder **chưa được tạo/xuất bản**, vì không có phiên chỉnh sửa Google Sites của đúng tài khoản trong connector hiện tại. Đừng gọi việc dựng website độc lập là Google Site đã publish.

## Cách nhúng vào Google Sites

1. Trong trình duyệt thông thường, đăng nhập Google account muốn sở hữu Site rồi mở https://sites.google.com/new.
2. Tạo Google Site, đặt tên `CWS AI Trade`.
3. Dùng **Trang → Thêm → Nhúng toàn trang (Full page embed)** hoặc **Chèn → Nhúng → URL**.
4. Dán URL website Supabase ở trên. Chọn full width, chỉnh chiều cao để dashboard không bị cắt.
5. Dùng Preview trên mobile và desktop, sau đó mới bấm Publish.
6. Kiểm tra Site URL thực tế và quyền truy cập sau Publish.

Website được nhúng là bản **đọc và nghiên cứu**, không phải Founder Secure chứa dữ liệu riêng.

## Thành phần hiện tại

- Giao diện trading xanh đen, tối ưu desktop/mobile.
- 16 dòng thị trường theo thứ tự nhất quán.
- Chart nến lấy từ `ai-trade-dashboard?format=preview-candles` bằng public market data.
- Chỉ 14/16 symbols hiện có feed công khai; EURJPY/XAGUSD hiển thị trạng thái `Feed chưa hỗ trợ`, không vẽ nến giả.
- Bảng danh mục: từng symbol chỉ một dòng, cộng Lot và P/L của nhiều position cùng cặp.
- Tổng lãi, tổng lỗ, net P/L và tổng Lot; nếu dữ liệu thiếu thì hiển thị `—`.
- Nạp JSON position trực tiếp vào browser RAM; không upload file, **chưa được broker xác minh**.
- Dữ liệu DEMO UI luôn gắn nhãn `MINH HỌA`.
- Knowledge Search tự tải bản đúc kết Masterbook công khai ở GitHub.
- Người dùng nạp EPUB Masterbook để tra cứu **toàn bộ chương ngay trên thiết bị**. EPUB không tự đăng lên website hoặc backend.
- AI Chat trong Site là tìm kiếm có nguồn, **không phải mô hình ChatGPT**.
- Nút `Sao chép câu hỏi + nguồn`, `Mở ChatGPT` và `Kết nối CWS AI Trade Knowledge` chuyển nghiên cứu sang tài khoản ChatGPT của người dùng.

Plugin ChatGPT riêng:

https://chatgpt.com/plugins/plugins_6aba1b6ee1fc8191a5c446b1558538d3

MCP read-only:

https://oziktadfeenydvgobudr.supabase.co/functions/v1/cws-ai-trade-knowledge-mcp

Tools: `search_masterbook`, `search_backtest_evidence`, `get_public_candles`, `read_safety_gates`.

MCP chỉ đọc các tài liệu **đúc kết công khai** và report public ở repo. Nó **không** đọc EPUB cá nhân trừ khi người dùng chủ động nạp vào trình duyệt hoặc cung cấp tài liệu cho phiên ChatGPT. Không gọi việc index bản đúc kết là đã ingest trọn 49 trang.

## Kiến trúc không phụ thuộc AppDeploy

- Mã nguồn trang: thư mục này.
- HTTPS site: Supabase Edge Function `cws-ai-trade-site`.
- Market chart: public endpoint hiện có của `ai-trade-dashboard`.
- Masterbook distilled: GitHub public, commit pin cố định.
- EPUB import: JSZip (CDN), parse trong browser.
- ChatGPT: plugin MCP public read-only, chạy bằng tài khoản ChatGPT đã kết nối.
- Original Founder Secure giữ nguyên; không dùng AppDeploy làm dependency cho site mới.

**Miễn phí có giới hạn:** CWS không tính quota riêng cho thao tác UI, không cần OpenAI API key cho search/lookup hiện tại. Supabase, GitHub, CDN và ChatGPT vẫn có giới hạn gói/dung lượng/lưu lượng và chính sách của bên cung cấp; không hứa unlimited hoặc miễn phí vĩnh viễn. Nếu sau này cần GPT tự trả lời ngay *trong website*, phải có model inference riêng với tài nguyên thực tế hoặc API được cấp phép; hiện **không** tự kích hoạt billing.

## Data contract mẫu

```json
[
  {"symbol":"EURUSD","side":"BUY","lot":1,"floatingPL":20},
  {"symbol":"EURUSD","side":"BUY","lot":2,"floatingPL":-5}
]
```

Kết quả: EURUSD hiển thị **3.00 lot**, P/L **+$15.00**, một dòng duy nhất. Bản ghi không có `lot` hoặc `floatingPL` -> phần tổng liên quan = `—`, không thay thế bằng synthetic volume, R hoặc lot giả.

## Bảo mật và ranh giới

- Không lấy token/cookie của Founder Secure từ Google Sites iframe hay từ nguồn công khai.
- Không có API đặt lệnh, quản lý tiền hoặc gửi tín hiệu lệnh broker.
- `brokerOrders=false`; live-money/risk/The5ers gate nguyên trạng.
- Public MCP không có quyền truy cập position, account balance hoặc broker secrets.
- Local JSON/EPUB chỉ lưu trên bộ nhớ phiên; reload cần nạp lại.
- Không dùng thành tích practitioner hoặc backtest làm bằng chứng chắc thắng.

## Tình trạng kiểm thử

- GitHub JS parse / mock client startup PASS.
- Pure aggregation PASS: cộng Lot, gom symbol, missing-value guard, mixed BUY/SELL.
- Supabase site ACTIVE v3, health và JS asset URLs HTTP thực tế PASS.
- Public EURUSD H1 candles endpoint HTTP thực tế PASS.
- MCP initialize/tools/list/search thực tế HTTP PASS.
- **Google Sites embed/publish, Android visual QA, EPUB import live browser và ChatGPT plugin install trên tài khoản vẫn PENDING**. Không fake PASS.

## Cập nhật

Sau khi sửa `index.html`, `app.js`, `portfolio.js` hoặc `styles.css`, phải cập nhật bundle trong `supabase/functions/cws-ai-trade-site/index.ts` và deploy lại Edge Function có evidence thực tế. Git push không tự xuất bản site; đây là manual deploy có chủ đích.


## Hướng nghiên cứu tiếp theo — CWS Trading Engine tự học

Founder intent và form bàn giao mới nhất:
- `knowledge/CWS_AI_TRADE_SELF_LEARNING_ENGINE_FOUNDER_INTENT_2026-09-28.md`
- `product/CWS_AI_TRADE_SELF_LEARNING_WEBAPP_HANDOFF_2026-09-28.md`

Mục tiêu: model học máy riêng do CWS kiểm soát, nạp kiến thức có provenance từ Masterbook và dữ liệu market/backtest/forward, không lấy GPT làm bộ não bắt buộc. Cập nhật knowledge → candidate dataset/model → OOS/WF/cost/stress → approval → promote; có lựa chọn `ABSTAIN` và risk gate độc lập.

**Trạng thái:** đây là kiến trúc/Founder intent đã checkpoint, **chưa có bằng chứng model mới được train hoặc triển khai**. Google Sites thuộc tài khoản Founder vẫn chưa publish. Giữ live-money locked, không chạm broker/risk/The5ers và không biến trang public thành Founder Secure.

## 2026-09-28 — PWA đầu tiên, dùng Web App trước APK

**Link cài trực tiếp:**
https://oziktadfeenydvgobudr.supabase.co/functions/v1/cws-ai-trade-site/app/

Bản Supabase Edge Function `cws-ai-trade-site` **v7 ACTIVE**.
- PWA HTML manifest `?asset=manifest.webmanifest`, tên `CWS AI Trade`, mode `standalone`, start/scope `/functions/v1/cws-ai-trade-site/app/`.
- Biểu tượng PNG 192px và 512px sinh từ mã nguồn `supabase/functions/cws-ai-trade-site/pwa-icon.ts`, cả hai đã kiểm tra có trả ảnh thật.
- Service worker `?asset=sw.js`, cache `cws-ai-trade-static-v2` lưu static shell, manifest, icons và tùy chọn cache JSZip/CDN + public distilled Masterbook; không cache API giao dịch hay private files.
- PWA có nút Cài ứng dụng khi browser thực sự phát `beforeinstallprompt`; nếu không có, hướng dẫn dùng menu trình duyệt.
- Tab Masterbook có tùy chọn **Lưu kiến thức sách trên thiết bị** bằng IndexedDB, mặc định **không** chọn; có nút xóa. EPUB luôn đọc trong browser và không upload server.
- Google Sites chỉ nhúng/gắn link Web App trực tiếp; không coi iframe Google Sites là bề mặt cài PWA.
- Bản giao diện ngoại tuyến có thể mở và tìm trong sách đã lưu; quote/biểu đồ thị trường cần mạng và không trả dữ liệu giá giả.

### Vì sao chọn PWA trước

| Tiêu chí | PWA trực tiếp | APK Android |
| --- | --- | --- |
| Giữ một codebase HTML/CSS/JS | Có | Có nếu APK chỉ bọc web |
| Cài icon lên màn hình chính | Có trên browser hỗ trợ | Có |
| Build lại APK mỗi khi sửa UI | Không | Có nếu bundle nội dung web |
| Cần Android SDK / signing key | Không | Có |
| Có thể truy cập khi không có mạng | Static shell và EPUB đã lưu | Chỉ nếu nội dung đóng gói/cached |
| Đưa lên Google Play | Không cần để phát hành web | Cần quy trình ký/phát hành |

Android APK có thể tạo sau qua Capacitor hoặc TWA/Bubblewrap. TWA chuẩn đòi Digital Asset Links nằm ở đường dẫn `/.well-known/assetlinks.json` tại origin của site và chứng chỉ ký đúng. URL Supabase Edge dưới đường dẫn con hiện tại **không cho CWS kiểm soát root origin** đó; vì vậy chưa được gọi là TWA APK production-ready. Nếu chỉ cần trải nghiệm app trên Android, PWA giải quyết được mà chưa cần APK.

### Kiểm thử PWA

- Static PWA manifest/script contract + mock browser install: **13/13 PASS**, bao gồm button prompt, đúng SW scope, shortcuts, PNG 192/512 declarations và không cache private market API.
- Site v7 Edge ACTIVE, manifest/JS/HTML/SW trước v7 đã được GET thực tế qua URL query chính xác; icon 192/512 live GET có image output thực.
- Trên v7 cần smoke lại endpoint nếu source có sửa meaningful.
- **Android Chrome thực tế / nút install / offline reload / EPUB IndexedDB end-to-end chưa có device-browser evidence**, không đánh dấu PASS.
- Google Sites Publish vẫn PENDING do thiếu phiên chỉnh sửa Google Sites của đúng account.

### Giới hạn miễn phí

PWA không cần AppDeploy và không dùng OpenAI API chỉ để hiển thị giao diện/tra cứu cục bộ. Hosting Supabase, tài nguyên trình duyệt, feed công khai, ChatGPT account và CDN có quota/chính sách thực tế. Không hứa chi phí bằng 0 hoặc unlimited vĩnh viễn. Full generative chatbot nhúng trong website cần inference backend có nguồn lực được duyệt; tính năng hiện tại là local search + ChatGPT plugin qua ứng dụng ChatGPT.

### Final runtime smoke v7

Verified against the actual live URL `/functions/v1/cws-ai-trade-site/app/`:
- **8/8 live HTTP checks PASS**: HTML, manifest, worker v2, PWA client, EPUB/IndexedDB client, actual 192x192 icon, actual 512x512 icon, health.
- **13/13 PWA static/mock install checks PASS**: manifest scope, icons, controls, no private cache, browser install prompt event and SW registration scope.
- Service worker mock lifecycle additionally PASS: static shell precache, optional public Masterbook/JSZip cache, cache upgrade cleanup, no private API interception, navigation fallback while offline.
- Verified Supabase Edge deployment: `cws-ai-trade-site` v7 ACTIVE.

This evidence **does not** establish Android Chrome installability end-to-end, offline EPUB IndexedDB persistence on the real phone, or published Google Sites. Those remain explicit pending checks.

## 2026-09-28 — Supabase v8: trạng thái model trung thực, read-only

- GitHub web/source checkpoint: `7798cc4abe4ad6a1e5adabc30e3267b120170765` trên đúng nhánh `codex/p0-covel-knowledge-audit`.
- Supabase Edge Function `cws-ai-trade-site` **v8 ACTIVE**, lấy trực tiếp bản `supabase/functions/cws-ai-trade-site/index.ts` khớp `google-sites/cws-ai-trade/index.html`.
- Giao diện bổ sung nhãn `MODEL_NOT_TRAINED`, `CHƯA HUẤN LUYỆN`, `ABSTAIN`, `LOCKED`, không tự phát tín hiệu khi chưa có model đã duyệt.
- HTTP live GET trên v8: 4/4 đường dẫn được truy cập và trả nội dung thực tế gồm `?health=1`, `/app/`, `/app/?asset=manifest.webmanifest`, `/app/?asset=portfolio.js`. HTML live độc lập có `MODEL_NOT_TRAINED` và `ABSTAIN · Gate: LOCKED`; health báo `publicReadOnly=true` và `liveMoneyLocked=true`.
- Giữ nguyên 16 cặp, mã nguồn aggregation Lot/P&L, biểu đồ, EPUB, PWA/SW/manifest và luật không cache private API. Không thay execution/broker/risk/The5ers; Supabase `ai_trade.runtime_config` đã đọc lại: `enabled=false`, `demo_send_enabled=false`, `risk_profile_approved=false`.
- Kiểm thử Python nghiên cứu: 13/13 unit tests PASS trên fixture tạo riêng cho unit test, cùng `compileall` PASS. Không gọi đó là model thực trên dữ liệu thị trường.
- **Chưa xác minh Android Chrome install/offline bằng thiết bị thật**, chưa publish Google Site dưới tài khoản Founder, chưa tạo APK, chưa triển khai production ML hay tích hợp broker. Không đánh dấu PASS các mục này.

## 2026-09-28 — Supabase v9 xác minh

- GitHub source: `23b22ab8e1ab3a0c195895ad68fdd928cb1e95c1`; Supabase `cws-ai-trade-site` v9 ACTIVE; SHA-256 `046222b77d1520b45dba4e475d107e876b8961f307e245d6b24281f917cc8e1b`.
- Sửa đúng phép cộng lãi dương và lỗ âm theo từng vị thế trước khi gộp thành một dòng cho mỗi symbol. Kiểm thử hồi quy Node: 8/8 PASS trên fixture riêng; các trường thiếu trả null.
- Nâng bộ nhớ đệm static PWA lên `cws-ai-trade-static-v3`; live HTTP có dữ liệu thật cho 5 endpoint: health, HTML, JS danh mục, service worker và manifest.
- Python self-learning tests: 13/13 PASS trên unit fixtures; model trên dữ liệu thực vẫn chưa được huấn luyện.
- Sau triển khai `enabled=false`, `demo_send_enabled=false`, `risk_profile_approved=false` và giao diện vẫn thể hiện `MODEL_NOT_TRAINED`, `ABSTAIN`, `LOCKED`.
- Google Sites publication, Android device installation và APK chưa có bằng chứng kiểm thử hoàn thành.

## 2026-09-28 — Supabase PWA v10: model không được duyệt, không phụ thuộc AppDeploy

- GitHub Web App source: `773722edc6055936b592025cd628f2db14fe76db`; Supabase Edge Function `cws-ai-trade-site` **v10 ACTIVE**, deployment digest `cf6c0ba8166ff1348e0bf69728666e001fde5a729d8ff086e2565168376557ab`.
- Điều chỉnh thông báo UI từ “chưa huấn luyện” sang **`MODEL_NOT_APPROVED`**, vì nghiên cứu nội bộ đã thực sự train nhưng hai candidate bị loại, không có model production. Tín hiệu sản phẩm tiếp tục `ABSTAIN` và `LOCKED`.
- Loại liên kết Founder Secure AppDeploy cũ khỏi Web App. Hướng dẫn nhập JSON chỉ đọc không còn phụ thuộc phiên đăng nhập tên miền cũ. Footer ghi rõ Google Sites **chưa xuất bản** thay vì gọi bản web hiện hành là Google Sites.
- Nâng cache static PWA lên `cws-ai-trade-static-v4`; chỉ có `index.html` và `sw.js` thay đổi trong bundle so với v9; không chỉnh bộ tính 16 cặp, Lot/P&L, biểu đồ, EPUB hay broker.
- Ba lớp kiểm tra: (1) GitHub index/worker trùng chính xác bundle, so với deployed v9 trước khi sửa; (2) deployed v10 source đọc lại trùng chính xác GitHub bundle, HTTP live GET health/HTML/worker/manifest không lỗi, HTML thể hiện `MODEL_NOT_APPROVED`, `ABSTAIN · Gate: LOCKED`, không còn AppDeploy; footer live xác nhận `Google Sites chưa xuất bản`; (3) SQL sau triển khai: `enabled=false`, `demo_send_enabled=false`, `risk_profile_approved=false`, order intents = 0, hai private model vẫn không có public inference.
- Kiểm thử hồi quy không đổi mã nguồn Python/portfolio: **29/29 Python** và **8/8 Node** PASS; không gọi các bài fixture là kết quả thị trường.
- **Không khẳng định** Android Chrome cài/khởi động offline E2E trên điện thoại, Google Sites Founder đã publish, hoặc APK đã build/ký. Chưa có model đủ chuẩn OOS, broker-net cost và forward paper để mở sản phẩm trading.

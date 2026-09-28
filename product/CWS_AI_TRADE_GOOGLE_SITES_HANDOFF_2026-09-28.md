# CWS AI Trade Google Sites + ChatGPT Integration — Handoff 2026-09-28

## Founder intent

- Website CWS AI Trade dùng giao diện Trading Terminal xanh đen như Founder Secure/ảnh mô phỏng, **không phải chatbot generic**.
- Google Sites là trang chính cho người dùng; nội dung động của ứng dụng được nhúng từ URL HTTPS độc lập.
- 16 cặp; một dòng cho mỗi symbol; cộng toàn bộ Lot/P/L cùng cặp, không hiển thị nhiều dòng cùng symbol.
- Tổng lãi, tổng lỗ, net P/L, số cặp, tổng Lot phải rõ.
- Không giữ panel `AI Trading Assistant` bên cạnh; AI Chat là một tab.
- Tra cứu kiến thức CWS Trading Masterbook V3, cả sách và CWS backtest; ChatGPT plugin dùng nguồn thật.
- Không AppDeploy, không sử dụng OpenAI API tính phí mặc định, không thêm quota giả, không dùng local Founder PC.
- Không can thiệp live-money/broker execution/risk/The5ers.
- Hạ tầng gói free thực tế có giới hạn; không tự nhận unlimited.

## Canonical

Repo: `trankhanhduy1508-maker/AI-TRADE`  
Branch: `codex/p0-covel-knowledge-audit` (không tạo branch khác).

Mã nguồn:
- `google-sites/cws-ai-trade/index.html`
- `google-sites/cws-ai-trade/styles.css`
- `google-sites/cws-ai-trade/portfolio.js`
- `google-sites/cws-ai-trade/app.js`
- `supabase/functions/cws-ai-trade-site/index.ts`
- `supabase/functions/cws-ai-trade-knowledge-mcp/index.ts`

Book distilled:
`knowledge/CWS_TRADING_MASTERBOOK_V3_DISTILLED_2026-09-28.md`

## Runtime endpoints

Site: https://oziktadfeenydvgobudr.supabase.co/functions/v1/cws-ai-trade-site  
Health: https://oziktadfeenydvgobudr.supabase.co/functions/v1/cws-ai-trade-site?health=1  
Site Edge: `cws-ai-trade-site` v3 ACTIVE.

MCP: https://oziktadfeenydvgobudr.supabase.co/functions/v1/cws-ai-trade-knowledge-mcp  
MCP Edge: `cws-ai-trade-knowledge-mcp` v1 ACTIVE; 4 read-only tools.

Private ChatGPT plugin:
- Name: `cws-ai-trade-knowledge`
- Version: `0.1.0`
- Plugin ID: `plugins_6aba1b6ee1fc8191a5c446b1558538d3`
- Release: `pluginrel_6aba1b709614819197bfe904f16f60cf`
- URL: https://chatgpt.com/plugins/plugins_6aba1b6ee1fc8191a5c446b1558538d3

## QA evidence verified

Source JS parse PASS. Aggregation pure tests PASS (EURUSD 1+2 lots, missing null guard, mixed BUY/SELL). Simulated DOM startup PASS for table/empty state/knowledge/candle call.
Live public fetch PASS:
- website HTML;
- site health JSON;
- bundled JavaScript assets;
- existing public EURUSD 1h candles.
MCP initialize HTTP200 PASS; tools/list HTTP200 PASS; search_masterbook HTTP200 returned actual grounded snippets, source paths.
No real Android visual/browser test and no actual published Google Site. Mark both PENDING.

## Real blockers / follow-up

1. Connected Google Drive account belongs to a different Google identity than intended Founder and supports Drive/Docs/Sheets/Slides only, not Google Sites; Opera Browser Connector currently disconnected. No authorized Google Sites editor/browser session. Therefore real Site ownership/create/embed/publish **not yet performed**.
2. Do not spend TinyFish browser credits repeatedly trying to bypass Google login; no password requests in chat. If Founder authorizes a browser editor via Work or connects Opera, use only that browser and publish Site after visual/mobile QA.
3. Current dashboard displays `—` for live position Lot/P&L because no authorized broker snapshot is passed to this public Site. Manual JSON is labelled unverified; DEMO labelled MINH HỌA. Do not map synthetic volume or R to USD/Lot.
4. Full EPUB can be loaded locally in website; public MCP only includes the distilled GitHub document and public reports. Do not claim full private 49-page book is in MCP. If deeper private book search is added, implement private access control and lawful upload, not public text leakage.
5. ChatGPT Plus does not grant free OpenAI API for custom site; plugin and copy-to-ChatGPT use the user's ChatGPT account with its own usage limits. No hidden paid API.
6. Check whether embedding passes Google Sites iframe and mobile layout after Site is created, and validate clipboard fallback on Android.
7. Source bundle in `supabase/functions/cws-ai-trade-site/index.ts` is static: update and manually redeploy it after frontend changes; no automatic deployment on git push.

## Recommended next execution order

- Connect authorized Google Sites editor (not user-supplied password).
- Create Google Site and Full-page embed the live app URL.
- QA desktop/mobile iframe, session clipboard and EPUB import.
- Install/enable CWS private plugin in ChatGPT.
- Ask founder to attach EPUB to ChatGPT session if full private book Q&A is needed before a secure personal book store exists.
- For future fully in-site generative chat, plan a resource-budgeted model; do not disguise ChatGPT Plus as a website API entitlement.
- Only after QA PASS checkpoint and publish public Site URL.

FAIL → root cause → minimal diff → retest. No fake PASS.

## 2026-09-28 — PWA delivery checkpoint

Founder đổi ưu tiên: trước tiên làm **Web App cài như ứng dụng Android (PWA)**, chưa build APK.

PWA URL:
https://oziktadfeenydvgobudr.supabase.co/functions/v1/cws-ai-trade-site/app/

Supabase Function: `cws-ai-trade-site` v7 ACTIVE.

Đã tạo mới:
- `google-sites/cws-ai-trade/manifest.webmanifest`
- `google-sites/cws-ai-trade/sw.js`
- `google-sites/cws-ai-trade/pwa.js`
- `supabase/functions/cws-ai-trade-site/pwa-icon.ts`

Đã sửa `index.html`, `styles.css`, `app.js` để có Android install button, biểu tượng, SW và tùy chọn IndexedDB lưu EPUB trên thiết bị.

Quan trọng: Supabase gateway chuẩn hóa/không giữ đủ path suffix khi vào Edge Function. Dùng route `/app/?asset=manifest.webmanifest`, `/app/?asset=sw.js`, `/app/?asset=icon-192.png`, `/app/?asset=icon-512.png`; **không** quay lại `/app/sw.js` hoặc `/app/manifest.webmanifest` vì đã trả sai HTML trong runtime trước khi fix.

Đã xác minh live: manifest JSON, SW JavaScript, icon 192/512 image, health. Static/mock install flow 13/13 PASS nhưng Android Chrome install E2E còn PENDING. SW cache chỉ public static + public Masterbook/JSZip tùy chọn; không cache broker position, token hoặc market feed.

Không coi APK là hoàn thành. Nếu về sau cần APK, đánh giá Capacitor hoặc TWA, nhưng TWA cần root `/.well-known/assetlinks.json` thuộc origin CWS kiểm soát và signing-key validation.

Giữ nguyên Founder Secure production, live-money/risk/The5ers gate. Không tự đổi Google Site chưa đăng nhập hoặc tự publish.

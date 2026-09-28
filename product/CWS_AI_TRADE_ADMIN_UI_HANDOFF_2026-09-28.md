# CWS AI Trade — Admin UI + Auth + Knowledge Handoff

## Repo / branch
Repo:
`trankhanhduy1508-maker/AI-TRADE`

Branch DUY NHẤT:
`codex/p0-covel-knowledge-audit`

Không tạo branch mới.
Không ground lại toàn repo.
Chỉ đọc đúng file cần thiết.

## Current checkpoint
Git HEAD tại checkpoint UI:
`5394f0029d444859f9b5c50ec7900114a6f08631`

CURRENT_STATUS đã cập nhật Founder checkpoint ở commit:
`34dd197347b4aba6685c2d049bcfbb320ec2fbc7`

## Mandatory 3-round PASS rule
Không được báo PASS sau 1 test.

Mỗi thay đổi quan trọng phải có:
1. Round 1 — backend / HTTP / data contract.
2. Round 2 — browser/runtime thật.
3. Round 3 — fresh session + reload/reopen + mobile regression.

Nếu bất kỳ round nào FAIL:
- tự tìm nguyên nhân;
- sửa minimal diff;
- chạy lại;
- chỉ báo PASS khi đủ 3 vòng thật.

## Founder Admin URL
Stable entry:
`https://oziktadfeenydvgobudr.supabase.co/functions/v1/ai-trade-dashboard?admin=1`

AppDeploy Secure frontend:
`https://cws-ai-trade-founder-secure-sm4gs9.v2.appdeploy.ai/`

AppDeploy backend Founder verifier:
`https://api-v2.appdeploy.ai/app/cws-ai-trade-founder-secure-sm4gs9/api/verify-founder`

Founder Google account:
`trankhanhduy1508@gmail.com`

Supabase Edge:
`ai-trade-dashboard` v34 ACTIVE tại checkpoint này.

## Auth state
Supabase OAuth cũ từng fallback sang:
`https://cws-lab-frontend.onrender.com`

Render service đó bị suspend và gây:
`bad_oauth_state`.

Đã chuyển Founder login sang AppDeploy Google Auth.
Không quay lại Render callback cũ.

Đã verify:
- invalid Bearer vào Founder verifier → 401;
- invalid Bearer vào Supabase dashboard → 403;
- AppDeploy backend health → 200;
- source AppDeploy mới không chứa `onrender.com` / `cws-lab-frontend` / Supabase OAuth authorize cũ.

Auth Round 1/3: PASS.
Auth Round 2/3: PASS.
Auth Round 3/3: còn cần Founder login thật rồi reload/reopen để xác minh post-login runtime.
Không fake session để ép PASS.

## Current Founder UI intent
Founder KHÔNG muốn clone nguyên MT5.

Open/current position UI hiện tại chỉ cần:
- Symbol / cặp giao dịch;
- BUY / SELL;
- Lot thật;
- P/L từng lệnh;
- Tổng P/L tất cả lệnh đang mở.

Không cần hiển thị ở list/card position hiện tại:
- Entry;
- Stop Loss;
- Take Profit.

Không fake Lot.
Không dùng synthetic/paper volume làm Lot thật.
Thiếu data → `—`.

## Files already changed
- `dashboard/js/modules/admin-positions.js`
- `dashboard/js/modules/current-trade.js`
- `dashboard/js/modules/training-arena.js`
- `dashboard/styles/components.css`

Latest UI change:
- tổng P/L header;
- Symbol / Side / Lot / P/L rows;
- current trade compact card;
- Arena main row bỏ Entry/Stop;
- mobile vẫn giữ P/L visible.

UI mới **chưa PASS 3/3**.

## Chart stack
Giữ TradingView Lightweight Charts 5.x.
Không đổi library nếu không có lý do kỹ thuật rõ.

Markets:
EURUSD, GBPUSD, USDJPY, AUDUSD, USDCAD, USDCHF, NZDUSD,
XAUUSD, USOIL, BTCUSD, ETHUSD, US30, NAS100, US500.

Timeframes:
M15 / M30 / H1 / H4 / D1.

## Product rule: Free vs Pro
Founder phản biện đúng:
Nếu Free/Demo hiện exact Entry/SL/TP realtime, user có thể copy lệnh mà không mua Pro.

Do đó định hướng sản phẩm:
- Free: learning + delayed/history + bias/setup.
- Pro: realtime actionable position info.
- Founder/Admin: full runtime/diagnostics.

Chưa tự áp paywall vào code nếu chưa có Founder approve chi tiết.

## E-book / knowledge task after UI
Sau khi UI PASS:
- truy repo để lấy toàn bộ backtest/research/history thật;
- không dựa vào trí nhớ mơ hồ nếu có evidence trong repo;
- gom cả chiến lược thành công và thất bại;
- phân tích lý do fail;
- market/cặp nào hợp hoặc không hợp chỉ khi có evidence;
- include spread / commission / slippage;
- include in-sample / OOS / walk-forward;
- include drawdown / expectancy / risk;
- include những rule bị loại và lý do.

E-book tiếng Việt phải có hình/biểu đồ minh họa:
- trend;
- breakout;
- false breakout;
- ATR stop;
- trailing stop;
- equity curve;
- drawdown;
- OOS vs IS;
- walk-forward;
- spread/slippage;
- case theo market thật nếu evidence có.

Không viết “bí kíp thắng chắc”.
Không hứa lợi nhuận.

## Known strategy context to verify from repo before writing e-book
Tên strategy được nhắc gần nhất:
`TF-013A-FORWARD-DIVERSIFIED-TREND`

Các ý từng xuất hiện:
- trend following;
- closed-bar signal;
- next-bar entry;
- stop khoảng 4 ATR(20);
- gap-aware execution;
- pyramiding OFF;
- đa market;
- forward collection.

Nhưng chat mới PHẢI verify lại từ repo/backtest evidence trước khi đưa vào e-book như fact.

## Do not touch without explicit need
- live-money gate;
- broker execution;
- risk gate;
- The5ers gate;
- Google customer onboarding;
- unrelated CWS Render repo;
- local Founder PC.

## Execution style
- plugin/connector first;
- GitHub + Supabase/AppDeploy evidence là source of truth;
- test FAIL → tự sửa minimal diff → test lại;
- không fake PASS;
- không báo cáo giữa chừng;
- chỉ dừng ở checkpoint thật / evidence thật / blocker thật.

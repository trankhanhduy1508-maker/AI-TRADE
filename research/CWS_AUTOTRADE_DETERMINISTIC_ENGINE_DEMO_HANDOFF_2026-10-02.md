# CWS AUTOTRADE — DETERMINISTIC ENGINE + DEMO HANDOFF — 2026-10-02

## Mục tiêu đã chốt

Founder muốn AutoTrade chạy bằng **engine deterministic/rule-based đã học và backtest**, không dùng LLM làm trading brain trong hot path.

AI chỉ được dùng để:
- nghiên cứu;
- backtest;
- audit;
- cải thiện rule/engine;
- sửa code và kiểm thử.

Runtime trading phải có thể chạy tự động khi không có AI:
`market data -> frozen strategy engine -> risk/compliance gates -> order-intent dedupe -> DEMO executor`.

Không xây lại engine từ đầu.

## Repository / branch

- Repo: `trankhanhduy1508-maker/AI-TRADE`
- Branch duy nhất: `codex/p0-covel-knowledge-audit`
- HEAD khi handoff này bắt đầu viết: `a8776745bcb61da28a72b9caa3878ca57b27b558`

Ground-first:
1. đọc file này;
2. đọc `CURRENT_STATUS.md`;
3. đọc `research/CWS_AUTOTRADE_MT5_DIRECT_ANDROID_RECOVERY_2026-10-02.md`;
4. đọc `research/CWS_AUTOTRADE_MT5_LOGIN_PYMT5_FALLBACK_CHECKPOINT_2026-10-02.md`;
5. đọc `research/TF_013A_FORWARD_SHADOW_PROTOCOL_2026-09-27.md`;
6. đọc `research/TF_013A_FORWARD_PROMOTION_GATE_2026-09-27.md`;
7. kiểm tra HEAD mới nhất bằng GitHub/Supabase runtime, SHA ở đây chỉ là checkpoint.

## Engine deterministic hiện có

Engine ưu tiên tiếp tục:
`TF-013A-FORWARD-DIVERSIFIED-TREND`

Signal frozen:
- RETURN_21 sign;
- RETURN_252 sign;
- SMA10 vs SMA200 sign;
- majority vote 2/3.

Luật forward:
- timeframe 1D;
- review trên closed bar;
- entry/reversal ở next bar open;
- ATR(20);
- emergency stop = 4 ATR;
- no pyramiding;
- một paper position mỗi market;
- không historical trade backfill;
- không LLM inference trong runtime decision path.

Universe 14 market:
EURUSD, GBPUSD, USDJPY, AUDUSD, USDCAD, USDCHF, NZDUSD, XAUUSD, USOIL, BTCUSD, ETHUSD, US30, NAS100, US500.

## Autonomous runtime đã xác minh trên Supabase

Các cron đang ACTIVE:
- `ai-trade-forward-shadow-daily` — 03:15 UTC;
- `ai-trade-shadow-broker-reconcile-daily` — 03:20 UTC;
- `ai-trade-forward-evaluate-daily` — 03:25 UTC;
- `ai-trade-journal-update-daily` — 03:30 UTC;
- `ai-trade-training-arena-daily` — 03:35 UTC;
- `ai-trade-knowledge-quarantine-daily` — 03:45 UTC.

Run ngày 2026-10-02 của forward-shadow, reconcile, evaluate và training-arena đều có cron status `succeeded`.

### Training arena

`TF-013A-ARENA-ALL-MARKETS` là lane test nhanh, paper-only.

Runtime snapshot 2026-10-02:
- positions open: 14/14;
- trades closed: 0;
- 9 market floating R > 0;
- 5 market floating R < 0;
- aggregate floating R xấp xỉ +0.475652 R.

Điều này chứng minh engine deterministic đang tự cập nhật paper positions không cần LLM.

Không được gọi 14 paper positions này là broker orders.

### True forward lane

`TF-013A-FORWARD-DIVERSIFIED-TREND` là lane true-forward preregistered.

Snapshot:
- evaluation_state: `COLLECTING`;
- closed forward trades: 0;
- markets_with_trades: 0;
- flagged_bars: 0;
- entry_without_visible_stop: 0.

Pending directions đã xuất hiện cho một số market sau review tháng 10, nhưng chưa được relabel thành broker fills.

Promotion gate vẫn yêu cầu tối thiểu:
- 50 closed forward trades;
- 120 calendar days từ first closed forward trade;
- >= 8 markets có closed forward trades;
- sau đó mới xét các performance/integrity gates.

Không rút ngắn hoặc bypass gate để lấy PASS nhanh.

## Shadow broker integrity

Latest reconciler:
- `SHADOW_BROKER_RECONCILED`;
- brokerOrders=false;
- liveMoneyLocked=true;
- accountRiskApproved=false;
- flaggedBarCount=0;
- visible stop required on entry;
- no pyramiding;
- idempotent client_order_id;
- same-bar multi mutation -> FLAG_NOT_EXECUTE.

## Existing ai-trade-tick

Không xây lại trading brain.

`ai-trade-tick` đã có:
- deterministic closed-bar decision logic;
- risk gate;
- daily loss gate;
- spread gate;
- projected stop-loss guard;
- kill/fail-closed behavior;
- compliance reservation;
- order_intents dedupe;
- visible stop requirement;
- broker mutation isolation.

Nhưng runtime hiện đang:
- `BLOCKED_APPROVAL`;
- automation_approval_verified=false;
- risk_profile_approved=false;
- execution_enabled=false;
- demo_send_enabled=false;
- `max_total_volume_demo=NULL`.

Không tự bịa risk approval number.

## MT5 DEMO account / login checkpoint

Founder-authorized existing MetaQuotes DEMO credential đã được chứng minh hợp lệ trước đó:
- PC pinned pymt5 direct: PASS nhiều variants;
- raw Deno/Supabase verifier từng reject broker code 3;
- Render stateless pymt5 verifier fallback: PASS / DEMO_VERIFIED;
- Android direct APK v0.6.0-demo-direct đã build/device-smoke/source-QA PASS;
- physical Android direct broker login vẫn chưa có evidence PASS.

Không đổ lỗi lại cho credential Founder.

Không lưu password vào:
- GitHub;
- log;
- APK;
- plaintext DB.

## Phát hiện mới: Supabase deployed demo-bootstrap runtime

Supabase deployed Edge Function:
`ai-trade-mt5-demo-bootstrap` runtime v6

Runtime deployed hiện có logic mạnh hơn bản source cục bộ đã đọc trước đó:
- direct MetaQuotes WebTerminal transport;
- create demo flow;
- verify login/readback;
- encrypted persistence;
- mode `open_demo_temp`;
- temporary mailbox flow qua mail.tm;
- allowlist sender domain MetaQuotes;
- chỉ extract numeric verification code;
- không execute instruction/link trong inbound email;
- existing verified demo reuse;
- `brokerOrders=false`;
- `liveMoneyLocked=true`.

Quan trọng:
- đây là **runtime evidence từ Supabase connector**;
- không claim `open_demo_temp` E2E PASS trong phiên này;
- tool call để trigger account creation bị safety layer của môi trường chặn;
- do đó tuyệt đối không ghi DEMO_CREATED nếu chưa có response thật.

### Source/runtime drift

Local/GitHub source của `supabase/functions/ai-trade-mt5-demo-bootstrap/index.ts` có thể stale so với deployed Supabase v6.

Chat mới phải:
1. fetch deployed function từ Supabase;
2. so sánh GitHub source;
3. sync runtime -> GitHub theo hướng không làm giảm safety;
4. test source parity;
5. không deploy downgrade.

## Mục tiêu gần nhất

1. Ground repo + Supabase runtime.
2. Đồng bộ GitHub mirror với deployed `ai-trade-mt5-demo-bootstrap` nếu xác nhận drift.
3. Tự tạo **một MetaQuotes DEMO mới** bằng flow hợp lệ, không bypass OTP/CAPTCHA/identity.
4. Verify:
   - MetaQuotes-Demo;
   - accountType DEMO;
   - tradeAllowed;
   - balance/currency/leverage;
   - password encrypted, không log.
5. Kết nối account mới vào DEMO execution path.
6. Reuse deterministic TF-013A / existing engine. Không thêm LLM trading brain.
7. Trước broker send:
   - server-authoritative DEMO gate;
   - liveMoneyLocked=true;
   - visible SL;
   - risk gate;
   - kill switch;
   - order-intent dedupe;
   - max volume approved explicitly;
   - no duplicate position policy.
8. Gửi **chỉ DEMO order** khi toàn bộ gate PASS.
9. Readback broker order/position thật.
10. Restart/reopen/recovery test.
11. Ghi evidence GitHub sau khi PASS.
12. Live/funded money tiếp tục HARD LOCKED.

## Không fake PASS

Không được biến:
- paper position;
- training arena position;
- shadow broker order;
- Supabase intent;
- synthetic fill

thành “broker order PASS”.

Broker DEMO PASS chỉ khi có broker-authoritative readback từ tài khoản DEMO thật.

## Render rule

Render làm ít nhất có thể:
- stateless verifier/proxy nếu cần;
- không trading brain;
- không DB;
- không durable files/state;
- không keep-alive hack;
- Supabase là source of truth cho state/risk/compliance/audit.

## Workflow

- plugin/connector first;
- không reboot/shutdown;
- không reset working tree;
- gặp lỗi: source -> runtime evidence -> fix -> retest;
- không commit vụn;
- commit/push khi checkpoint có giá trị;
- không để secrets lọt vào diff/log/artifact;
- không mở live money.


## 2026-10-02 late checkpoint — MetaQuotes phone gate + bootstrap v7

Cloud grounding:
- Supabase project: `oziktadfeenydvgobudr`
- `ai-trade-mt5-demo-bootstrap` deployed version: **7**
- deployed ezbr sha256: `873adfafa0e67ec2218e4de0c9f0f090076053484cfbbc4f485c8b8206a9fb4e`
- GitHub/source byte parity after deploy: **TRUE**
- source fix commit: `b68133ad36860e7c58b76afa6896b0674e0308cc`

What changed:
- Added explicit `phone` input and `phone_code` field to the DEMO opening contract.
- Phone is serialized into the exact `request.phone` 64-byte UTF-16 slot used by pinned `cloudQuant/pymt5`.
- Added international-format validation `^\\+[1-9]\\d{7,14}$`.
- Phone is not persisted or logged by this function.
- `open_demo_temp` now fails closed before broker transport when phone is absent/invalid.
- `brokerOrders=false` and `liveMoneyLocked=true` remain unchanged.

Runtime evidence after v7 deploy:
- Authenticated cloud invocation with no phone:
  - HTTP 400
  - `status=PHONE_INPUT_REQUIRED`
  - `brokerOrders=false`
  - `liveMoneyLocked=true`
- Authenticated cloud invocation with invalid phone `123`:
  - HTTP 400
  - `status=INVALID_PHONE_FORMAT`
  - `phoneStored=false`
  - `brokerOrders=false`
  - `liveMoneyLocked=true`
- DB remains:
  - verified new DEMO credentials: 0
  - one active encrypted temporary mailbox

Official MetaTrader 5 account-opening documentation requires a contact phone in international format. Android help further says a mobile number is required and landline numbers are not accepted.

Current legal blocker:
- A legitimate Founder-controlled mobile phone number in international format is required for the next `cmd 27` attempt.
- Do not invent/use temporary SMS numbers.
- If MetaQuotes requests SMS/phone verification, expose `PHONE_VERIFICATION_REQUIRED` and stop for human verification. Do not bypass.
- No new DEMO account has been created yet.
- No broker DEMO order has been sent.
- `MAX_TOTAL_VOLUME_DEMO` remains unset and must not be invented.
- Live/funded money remains HARD LOCKED.

Engine boundary unchanged:
`TF-013A-FORWARD-DIVERSIFIED-TREND` only; no LLM in the hot path, no pyramiding, visible-stop/risk/kill-switch/dedupe/server-authoritative DEMO gates remain mandatory.

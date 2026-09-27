# AI-TRADE — Founder Execution Order 2026-09-27

## Thứ tự bắt buộc

### Task 1 — Multi-asset autonomous research/paper

Mở rộng universe:
- EURUSD
- GBPUSD
- USDJPY
- AUDUSD
- USDCAD
- USDCHF
- NZDUSD
- Gold / XAUUSD
- Bitcoin / BTCUSD
- WTI Oil / USOIL
- US30 / Dow Jones
- NAS100 / Nasdaq 100
- US500 / S&P 500

Trạng thái:
- 13-market paper autonomy ACTIVE trên Supabase cloud.
- Daily cron ACTIVE.
- Broker orders = false.
- Pyramiding = false.
- Risk profile = FAIL_CLOSED.
- Broker execution không được unlock chỉ từ research proxy.

Evidence:
- `reports/MULTIASSET_PAPER_UNIVERSE_2026-09-27.md`

### Task 2 — The5ers Bootcamp challenge integration

Founder hiện đang thi Bootcamp.

Canonical challenge rules cần guard:
- Step 1: initial $5,000.
- Step 2: initial $10,000.
- Step 3: initial $15,000.
- Profit target mỗi challenge step: 6%.
- Max loss mỗi challenge step: 5% initial balance.
- Không có daily pause trong 3 challenge steps.
- Leverage headline 1:30; margin requirements theo asset group.
- Unlimited evaluation time.
- >30 ngày không activity có thể bị đóng account.
- Stop-loss phải visible trên trading platform.
- Challenge là DEMO evaluation; funded stage là rule-set khác.

Không hard-code rule funded vào challenge guard.

Automation/EA governance:
- Current The5ers terms require written notification/approval before automated trading software is used.
- Execution gate phải fail closed nếu chưa có evidence approval.
- Founder owns source code của AI-TRADE automation.
- Không HFT, tick scalping, latency/reverse/hedge arbitrage, emulator, third-party copy signals.

Target architecture:
`The5ers MT5 DEMO -> read-only account snapshot -> Bootcamp Guard -> Strategy -> Risk Gate -> compliant execution adapter`

Trước approval:
`monitor + paper only`

Sau written approval + all safety gates:
`DEMO challenge execution eligible`

Live/funded money không tự unlock.

### Task 3 — Compliance Mode, không stealth/evasion

Founder yêu cầu hệ thống không thao tác kiểu máy quá nhanh vì sợ quỹ đánh dấu automation.

Implementation policy:
- KHÔNG xây stealth mode để che giấu AI/EA.
- KHÔNG random delay nhằm đánh lừa detection.
- KHÔNG giả mouse/keyboard human pattern để né rule.
- KHÔNG spoof identity/device/fingerprint.
- KHÔNG bypass anti-bot/anti-abuse controls.

Thay vào đó xây `PROP_FIRM_COMPLIANCE_MODE`:
- only closed-bar decisions;
- one intent per signal/bar;
- deterministic cool-down;
- no HFT/tick scalping;
- minimum meaningful decision interval từ strategy timeframe, không phải deceptive jitter;
- no duplicate order;
- visible broker-side SL;
- bounded retries/backoff cho lỗi kỹ thuật;
- full audit trail;
- owner-written automation approval gate;
- violation -> block new risk.

Mục tiêu: hành vi giao dịch hợp lệ, chậm, kiểm toán được, không phải hành vi che giấu automation.

## Không được đảo thứ tự

1. Hoàn tất multi-asset paper/research.
2. Dựng The5ers Bootcamp Guard và approval gate.
3. Dựng Compliance Mode.
4. Chỉ sau đó mới xem xét MT5 DEMO challenge execution.
5. Live/funded-money execution tiếp tục hard locked cho tới gate riêng.

# Kiến trúc Code — Rule Engine (Phase 2)

> Deliverable bắt buộc theo `ROADMAP.md` Giai đoạn 2. Mô tả cấu trúc code
> Python đã triển khai, tương ứng 1-1 với đặc tả trong `rule_engine/*.md` và
> `RULE_ENGINE.md`. Đây là code **kiểm chứng logic**, chưa phải production
> (chưa kết nối dữ liệu giá thật — xem `CURRENT_STATUS.md`).

## Cấu trúc thư mục

```
src/rule_engine/
  types.py                 Bar, RuleResult — contract dùng chung mọi module
  trend_detection.py       RULE_001 — evaluate(bars, n=2)
  market_structure.py      RULE_002 — evaluate(bars, trend_status, n=2)
  breakout_detection.py    RULE_003 — evaluate(bars, structure_level, direction, body_ratio_min=0.6)
  pullback_validation.py   RULE_004 — evaluate(bars, breakout_level, direction, lookback_bars=20)
  volume_confirmation.py   RULE_005 — evaluate(bars, sma_period=20)
  rsi_filter.py             RULE_006 — evaluate(bars, direction, period=14)
  ema_filter.py             RULE_007 — evaluate(bars, direction, period=50)
  risk_validation.py        RULE_008 — evaluate(entry, stop, target, direction, rr_min=1.5)
  liquidity_check.py        RULE_009 — evaluate(spread_pips, depth_ok=True)
  exit_rules.py             RULE_010 — evaluate_exit(bars, entry, stop, target, direction) -> ExitSignal
  scoring.py                Orchestrator — evaluate_setup(bars, entry, stop, target, direction) -> SetupScore

tests/rule_engine/          Unit test (pytest) 1-1 với từng module + test tích hợp không mock
```

## Nguyên tắc thiết kế

- **Pure functions**: không I/O, không side-effect, không phụ thuộc thời gian hệ thống.
- **Chỉ Python standard library** — chưa dùng pandas/numpy, vì đây là code kiểm chứng logic, không phải hiệu năng.
- **Chỉ dùng nến đã đóng**: `Bar.closed` mặc định `True`; các rule không tự lọc `closed=False`, tầng gọi (Data Loader/Backtest Engine) chịu trách nhiệm không đưa nến chưa đóng vào `bars` (nhất quán `backtests/POINT_IN_TIME_AI_BACKTEST.md`).
- **`RuleResult.reject=True`** dừng Decision Flow ngay (theo `RULE_ENGINE.md` mục 2) — `scoring.evaluate_setup()` return sớm, không chạy các rule sau.

## Luồng dữ liệu trong `scoring.evaluate_setup()`

```
RULE_001 (tự phát hiện trend từ bars)
   │  status phải khớp `direction` đề xuất, nếu không → REJECT
   ▼
RULE_002 (nhận trend_status thật từ RULE_001)
   │  trả swing_high/swing_low trong .detail
   ▼
structure_level = swing_high (UP) hoặc swing_low (DOWN)
   ▼
RULE_003 (breakout tại structure_level)  →  RULE_004 (pullback tại structure_level)
   ▼
RULE_005 (volume) → RULE_006 (RSI) → RULE_007 (EMA) → RULE_008 (risk) → RULE_009 (liquidity)
   ▼
Tổng điểm 0-100 → TRADE (>=80) / WAIT (60-79) / REJECT (<60)
```

`direction` là hướng đề xuất bởi caller; RULE_001 tự phát hiện xu hướng thật từ
dữ liệu và setup bị reject nếu không khớp — tránh giao dịch ngược xu hướng
chính (`DECISIONS.md`).

`spread_pips`/`depth_ok` (input cho RULE_009) hiện chưa có nguồn dữ liệu
order-book thật — mặc định giả định thanh khoản tạm ổn cho tới khi Data Loader
cung cấp dữ liệu thật.

## Test

```
python -m pytest tests/rule_engine/ -v
```

103 test, bao gồm test đơn vị từng rule (dùng ví dụ số liệu từ các file `.md`
gốc khi có) và `test_scoring_integration.py` — chạy `evaluate_setup()` qua các
module RULE_001-005 **thật, không mock**, xác nhận hợp đồng dữ liệu giữa các
module khớp nhau.

## Giới hạn hiện tại (chưa làm)

- RULE_009 (Liquidity) chưa có nguồn spread/order-book thật.
- Tham số rủi ro trong `risk_validation.py` (`rr_min=1.5`) là giá trị đề xuất
  từ `RULE_ENGINE.md`, **chưa được Project Owner chốt chính thức** — xem
  `risk/RISK_POLICY.md`.
- Chưa có Data Loader — chưa test được với dữ liệu giá lịch sử thật.

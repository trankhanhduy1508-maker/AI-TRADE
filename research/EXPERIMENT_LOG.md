# Nhật ký thử nghiệm

> Ghi lại **mọi lần chạy backtest/thử nghiệm thật**, kể cả khi kết quả xấu. Không
> xóa thử nghiệm thất bại — đây chính là dữ liệu quan trọng để tránh lặp lại sai
> lầm (xem thêm `research/FAILURE_CASES.md` cho các ca thất bại điển hình).

## Cách dùng file này

Mỗi thử nghiệm ghi: ngày, chiến lược/giả thuyết được test, dữ liệu dùng, thay đổi
so với lần trước (nếu có), link kết quả trong `backtests/`, nhận xét ngắn.

---

## 2026-08-22 - TF-003 fixed 70/30 IS/OOS with research costs

- Data: Yahoo chart downloads, EURUSD/GBPUSD/USDJPY at 1D and 1H; exact rows
  and split timestamps are recorded in `backtests/TF003_FX_IS_OOS_2026-08-22.md`.
- Change from prior run: added an independent price-only time-series momentum
  evaluator with fixed lookback/stop settings and explicit strategy-model
  dispatch. No retuning followed the run.
- Result: three of six OOS partitions were positive and three negative after
  the fixed `UNVERIFIED` research cost proxy; every run ended with an open
  position at the data boundary.
- Interpretation: preliminary comparison evidence only; not broker, MT5, or
  live evidence.

## 2026-08-22 - TF-001 fixed 70/30 IS/OOS with research costs

- Data: Yahoo chart downloads, EURUSD/GBPUSD/USDJPY at 1D and 1H; exact rows
  and split timestamps are recorded in `backtests/TF001_FX_IS_OOS_2026-08-22.md`.
- Change from prior run: added point-in-time swing cache, chronological IS/OOS
  gating, and explicit fixed price-unit cost profile.
- Result: 1D produced no trades; all three 1H OOS samples had negative net
  price-unit PnL after costs.
- Interpretation: preliminary and not live/broker evidence; no parameter was
  tuned after observing the result.

## Historical note

Trước các mục thử nghiệm ngày 2026-08-22, hệ thống chưa có backtest thực tế;
các mục bên trên là evidence log hiện hành.

### Template cho mỗi lần thử nghiệm (copy khi có thử nghiệm thật)

```
### [YYYY-MM-DD] — [Mã chiến lược] trên [thị trường/timeframe]

- Dữ liệu: [nguồn, khoảng thời gian]
- Thay đổi so với lần trước: [nếu có]
- Kết quả: xem backtests/[tên file kết quả].md
- Nhận xét: [ngắn gọn, khách quan — không diễn giải quá mức từ 1 lần chạy]
```

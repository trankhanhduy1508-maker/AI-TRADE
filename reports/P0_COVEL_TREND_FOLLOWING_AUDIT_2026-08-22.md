# P0 Audit — Michael W. Covel Trend Following Knowledge

> Ngày: 2026-08-22
> Repo: `trankhanhduy1508-maker/AI-TRADE`
> Scope: knowledge/provenance only; MT5 và live execution không thuộc P0.

## Kết luận ngắn

P0 đã xác định được nguồn công khai hợp pháp đủ để củng cố phần triết lý của
Trend Following: price-focused decisions, reaction thay vì prediction, loss
containment, để lợi nhuận chạy, giảm discretionary override, và tư duy theo rule.
Trang catalog chính thức xác nhận Fifth Edition tồn tại, nhưng checkout hiện tại
không có full lawful copy; vì vậy không claim `VERIFIED_FROM_BOOK` cho nội dung
chương sách nào.

Bằng chứng độc lập từ các paper time-series momentum được giữ riêng với Covel
author material. Các rule cụ thể của AI-TRADE (HH/HL, BOS/CHoCH, EMA, volume,
scoring, timeframe và threshold) được phân loại là engineering derivation hoặc
unverified cho tới khi có strategy spec/backtest phù hợp.

## Evidence ledger

| Evidence | Level | Finding |
|---|---|---|
| `auto_trade/BOOTSTRAP.md`, `MASTER_GOAL.md`, `CURRENT_STATUS.md` | `CODE VERIFIED` | P0 yêu cầu audit canonical Trend Following knowledge/provenance trước MT5. |
| `knowledge/TREND_FOLLOWING.md` trước audit | `CODE VERIFIED` | Có reaction/structure/EMA prose nhưng thiếu claim IDs, source registry và ranh giới book/author/engineering. |
| Official Covel catalog + Fifth Edition preview | `VERIFIED_FROM_AUTHOR` | Xác nhận metadata/preview; không phải full book. |
| Official Covel Ten Tenets/Theory/Research pages | `VERIFIED_FROM_AUTHOR` | Củng cố các principle đã ghi trong registry bằng diễn giải riêng. |
| Moskowitz–Ooi–Pedersen (2012) | `VERIFIED_FROM_PRIMARY_RESEARCH` | Có kết quả nghiên cứu về time-series momentum trong universe/horizon được paper nêu; không phải backtest AI-TRADE. |
| Hurst–Ooi–Pedersen (2014) | `VERIFIED_FROM_PRIMARY_RESEARCH` | Có nghiên cứu lịch sử dài và portfolio/correlation findings trong phạm vi paper. |
| AI-TRADE own backtest | `UNKNOWN` | Chưa có dữ liệu lịch sử/đầu ra backtest đủ để kết luận hiệu quả. |

## Gaps còn lại

1. Chưa có full lawful copy Fifth Edition trong workspace: không được nói đã
   ingest toàn bộ sách.
2. Chưa có provenance riêng cho mọi file knowledge cũ; registry hiện chỉ rõ
   canonical claim boundary và các vùng cần review tiếp.
3. Chưa có strategy-specific backtest chứng minh HH/HL, BOS/CHoCH, EMA, volume,
   pullback hoặc scoring threshold.
4. Risk limits số cụ thể vẫn là Founder-controlled unknown trong
   `risk/RISK_POLICY.md`; P0 không tự chốt.

## P0 acceptance checklist

- [x] Source availability and lawful-copy boundary recorded.
- [x] Covel author principles separated from primary research.
- [x] Engineering-derived rules separated from Covel/book knowledge.
- [x] Required knowledge domains mapped with provenance and gaps.
- [x] No copyrighted long-form reproduction added.
- [x] No MT5/live-order/risk-limit change made.
- [ ] Reproducible strategy/backtest evidence — P1/P2, not P0.

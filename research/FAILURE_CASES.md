# Các ca thất bại (Failure Cases)

> Mục đích: ghi lại **cụ thể** những lần một giả thuyết/chiến lược thất bại —
> không phải để đổ lỗi, mà để tránh lặp lại cùng một sai lầm logic. Đây là tài
> liệu **sống**, cập nhật liên tục khi có bằng chứng thật, không phải danh sách
> lý thuyết viết một lần.

## Cách dùng file này

Mỗi ca ghi: mô tả thất bại, nguyên nhân gốc (không chỉ triệu chứng), giả
thuyết/chiến lược liên quan, hành động khắc phục đã áp dụng.

---

## 2026-08-22 - TF-003 mixed OOS result did not pass the validation gate

- Strategy/hypothesis: H006 / `strategies/TF_003_TIME_SERIES_MOMENTUM.json`.
- Description: three of six fixed FX symbol/interval OOS partitions were
  negative after the declared research cost proxy; the remaining positives do
  not establish robustness. The feed and cost assumptions are not broker
  verified.
- Root cause status: not proven. The result may reflect the translation, fixed
  target limitation, data source, period, or proxy costs; this run cannot
  isolate the cause.
- Corrective action: preserve the fixed baseline, do not retune against this
  sample, and improve data/cost/exit-model evidence before MT5 expansion.

## 2026-08-22 - TF-001 hourly OOS negative after declared costs

- Strategy/hypothesis: H001 / `strategies/TF_001_BREAKOUT_PULLBACK.json`.
- Description: EURUSD, GBPUSD, and USDJPY 1H OOS partitions all had negative
  net price-unit PnL after the fixed research cost proxy; daily partitions had
  no qualifying trades.
- Root cause status: not proven. The evidence shows the current translation,
  data source, period, and cost assumptions did not pass the OOS gate; it does
  not isolate whether the rule translation, source quality, or proxy costs are
  responsible.
- Corrective action: do not optimize on this sample; keep H001 unvalidated,
  preserve the raw evidence, and obtain broker/demo data plus an independently
  specified strategy comparison before execution work.

## Historical note

Các ca backtest thực tế đầu tiên đã được ghi ở phía trên; chưa có paper trade
hoặc giao dịch live nào.

## Các loại lỗi chủ quan đã biết trước (từ `knowledge/`, chưa phải "ca thất bại"
thật, chỉ là điều cần cảnh giác)

Tham khảo mục "Lỗi thường gặp" trong từng file `strategies/*.md` — đây là dự đoán
trước các lỗi có thể xảy ra dựa trên kinh nghiệm chung, **không thay thế** việc
ghi lại ca thất bại thật khi nó xảy ra.

### Template cho mỗi ca thất bại thật (copy khi có ca thật)

```
### [YYYY-MM-DD] — [Mô tả ngắn]

- Chiến lược/giả thuyết liên quan: [link]
- Mô tả: [chuyện gì đã xảy ra]
- Nguyên nhân gốc: [không chỉ triệu chứng — vì sao nó xảy ra]
- Hành động khắc phục: [đã sửa gì trong strategies/risk/knowledge]
```

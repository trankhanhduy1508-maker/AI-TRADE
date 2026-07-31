# Data Requirements — Định nghĩa và Yêu cầu Dữ liệu Backtest

> **Tài liệu chi tiết các loại dữ liệu hỗ trợ Backtest Engine**, định nghĩa, định dạng, và lý do tại sao từng loại cần thiết.

---

## 1. OHLCV (Open, High, Low, Close, Volume)

### 1.1 Định nghĩa

**OHLCV** là dữ liệu cơ bản nhất của từng nến (candle):
- **Open (O):** Giá mở của nến (giá giao dịch đầu tiên trong khoảng thời gian)
- **High (H):** Giá cao nhất trong nến
- **Low (L):** Giá thấp nhất trong nến
- **Close (C):** Giá đóng của nến (giá giao dịch cuối cùng trong khoảng thời gian)
- **Volume (V):** Khối lượng giao dịch (số hợp đồng/lô/đơn vị tiền tệ)

### 1.2 Định dạng

```
timestamp          | Open   | High   | Low    | Close  | Volume
2024-01-01 09:00   | 1.1000 | 1.1050 | 1.0980 | 1.1030 | 1500000
2024-01-01 10:00   | 1.1030 | 1.1080 | 1.1020 | 1.1070 | 1800000
...
```

**Yêu cầu:**
- Timestamp: Định dạng ISO 8601 (YYYY-MM-DD HH:MM:SS hoặc YYYY-MM-DDTHH:MM:SSZ)
- O, H, L, C: Số thập phân, ít nhất 4 chữ số thập phân (tùy cặp tiền/chỉ số)
- V: Số nguyên hoặc số thập phân (tùy từng sàn)
- **Yêu cầu:** H >= max(O, C), L <= min(O, C), H >= L
- **No duplicates:** Không có 2 nến cùng timestamp
- **Sorted:** Timestamp tăng đơn điệu

### 1.3 Tại sao cần

OHLCV là dữ liệu **tối thiểu** để:
- Xác định breakout (so sánh close vs level trước)
- Xác định pullback (kiểm tra high/low)
- Tính RSI, EMA, các indicator khác
- Mô phỏng vào lệnh (entry = close), xử lý SL/TP (kiểm tra high/low)

**Không có OHLCV** → backtest không thể chạy.

---

## 2. Tick Data (Tùy chọn, cho độ chính xác cao)

### 2.1 Định nghĩa

**Tick data** là dữ liệu từng giao dịch lẻ:
- **Timestamp:** Thời điểm giao dịch (chính xác tới millisecond hoặc microsecond)
- **Bid:** Giá mua (bên mua sẵn sàng)
- **Ask:** Giá bán (bên bán sẵn sàng)
- **Bid Volume / Ask Volume:** Khối lượng ở mức bid/ask
- **Trade Price / Trade Volume:** Giá và khối lượng giao dịch thực tế

### 2.2 Định dạng

```
timestamp            | Bid    | Ask    | Bid Vol | Ask Vol | Trade Price | Trade Vol
2024-01-01 09:30:00 | 1.1000 | 1.1001 | 100000  | 120000  | 1.1000      | 50000
2024-01-01 09:30:05 | 1.1000 | 1.1001 | 150000  | 100000  | 1.1001      | 75000
...
```

**Yêu cầu:**
- Timestamp: Chính xác tới millisecond nếu có thể
- Bid, Ask, Trade Price: Số thập phân
- Bid < Ask (luôn đúng)
- Sorted by timestamp

### 2.3 Tại sao cần (tùy chọn)

Tick data cho phép:
- **Tính spread thực tế** (Ask - Bid) thay vì giả định
- **Mô phỏng entry chính xác** (entry tại bid hoặc ask tùy direction)
- **Phát hiện slippage thực tế** (order fill tại giá nào)
- **Phân tích order book depth** (RULE_009 Liquidity)

**Lưu ý:** Tick data rất lớn (gigabytes/ngày). Nếu không cần độ chính xác cao, dùng OHLCV là đủ.

**Hiện tại:** AI-TRADE chưa hỗ trợ tick data. Để backtest chính xác hơn, có thể thêm ở giai đoạn sau.

---

## 3. Multi Timeframe (Khung thời gian đa level)

### 3.1 Định nghĩa

**Multi Timeframe** nghĩa là backtest cùng chiến lược trên nhiều khung thời gian:
- Ví dụ: TF_001 trên 1H, 4H, 1D
- Hoặc: Entry trên 15M, but filter dùng 4H trend

### 3.2 Tại sao cần

- **Không có chiến lược nào tốt ở mọi timeframe:** TF_001 có thể tốt ở 4H nhưng tệ ở 15M.
- **Quyết định:** Nếu chiến lược tốt ở 4H, chỉ kết luận "TF_001 hiệu quả trên EURUSD 4H", không phải "TF_001 hiệu quả mọi nơi".
- **Điều chỉnh tham số:** Nếu dùng EMA(50), có thể ở 1H là EMA(50 * 4) = EMA(200) khi chuyển sang 4H (vì 4H = 4 × 1H).

### 3.3 Ví dụ

```
Chiến lược TF_001_BREAKOUT_PULLBACK:
- Timeframe 1H:   Backtest 2015-2020, Win Rate = 52%, Expectancy = 10 pips
- Timeframe 4H:   Backtest 2015-2020, Win Rate = 58%, Expectancy = 25 pips
- Timeframe 1D:   Backtest 2015-2020, Win Rate = 48%, Expectancy = 50 pips

Kết luận: "TF_001 tốt nhất ở 4H, không khuyên dùng 1H"
```

---

## 4. Timezone (Múi giờ)

### 4.1 Định nghĩa

**Timezone** xác định múi giờ của timestamp. Quan trọng vì:
- Forex: GMT (hoặc UTC)
- US Stock: EST/EDT
- Japan Stock: JST
- Crypto: thường UTC

### 4.2 Tại sao cần

- **Session boundary:** Forex mở 9:00 GMT, đóng 17:00 GMT. Nếu dữ liệu là EST, bạn sẽ nhầm (9:00 EST = 14:00 GMT, không phải mở chợ).
- **Indicator tính sai:** EMA trên dữ liệu EST nhưng logic là GMT → chênh lệch 5-8h.
- **Backtest tín hiệu sai:** Setup tại 1:00 AM EST = 6:00 AM GMT (chợ vừa mở), nhưng dữ liệu chưa có.

### 4.3 Quy định

- **Quy tắc cứng:** Convert tất cả timestamp về UTC trước khi backtest (xem BACKTEST_ENGINE.md step 3 Data Cleaning).
- **Ghi rõ:** "Dữ liệu gốc là GMT, chuyển đổi thành UTC để xử lý".

### 4.4 Ví dụ

```
Dữ liệu gốc (EST):
2024-01-01 09:00 EST (open time New York)

Chuyển UTC:
2024-01-01 14:00 UTC (giờ phổ quát)

Có thể mapping lại EST nếu cần:
2024-01-01 09:00 EST (original local)
```

---

## 5. Session (Phiên giao dịch)

### 5.1 Định nghĩa

**Session** là khoảng thời gian chợ giao dịch (mở → đóng).

### 5.2 Ví dụ theo sàn

| Sàn | Session (local) | Session (UTC) | Ghi chú |
|---|---|---|---|
| Forex (London) | 09:00-17:00 GMT | 09:00-17:00 UTC | Cố định |
| US Stock (NYSE) | 09:30-16:00 EST | 14:30-21:00 UTC | Phụ thuộc daylight saving |
| Japan Stock (Tokyo) | 09:00-15:00 JST | 00:00-06:00 UTC | Tính từ 00:00 hôm trước |
| Crypto (24/7) | 00:00-23:59 UTC | Full day | Không có session break |
| Futures (CME) | 17:00-16:00 CT | Nearly 24/5 | Mở Chủ nhật 17:00, đóng Thứ 6 16:00 CT |

### 5.3 Tại sao cần

- **Loại bỏ dữ liệu ngoài session:** Nếu dữ liệu có "afterhour trading" (sau 17:00 GMT), cần quyết định:
  - Loại bỏ nó (chỉ dùng 09:00-17:00)
  - Hoặc đánh dấu "afterhour" để phân tích riêng
- **Xử lý gap:** Weekend hoặc holiday, không có dữ liệu, cần bỏ qua khi tính trend.
- **Depth liquidity:** Trong session, liquidity tốt. Ngoài session (afterhour), liquidity tệ.

### 5.4 Quy định

- **Ghi rõ:** "Backtest chỉ trong session 09:00-17:00 GMT, bỏ qua afterhour".
- **Logging:** Ghi lại nếu phát hiện dữ liệu ngoài session, yêu cầu human review.

---

## 6. Spread (Biên độ giá)

### 6.1 Định nghĩa

**Spread** = Ask - Bid (chi phí giao dịch tức thời).

### 6.2 Ví dụ

```
Bid = 1.1000, Ask = 1.1001 → Spread = 1 pip
Bid = 1.1000, Ask = 1.1002 → Spread = 2 pips

Entry Long: Buy at Ask = 1.1001 (mất 1 pip ngay lập tức)
Entry Short: Sell at Bid = 1.1000
```

### 6.3 Tại sao cần

Spread là **chi phí giao dịch bắt buộc**. Nếu:
- Entry = Close price (giả định 0 spread)
- → R/R lý thuyết = 50 pips
- Nhưng thực tế entry tại Ask = +2 pips chi phí
- → R/R thực tế = 50 - 2 = 48 pips (giảm 4%)

**Không tính spread** → kết quả backtest lạc quan quá.

### 6.4 Từ đâu lấy

- **Tick data:** Tính trực tiếp (Ask - Bid)
- **Nguồn cố định:** Sàn cung cấp "typical spread" (ví dụ EURUSD = 1-2 pips)
- **Giả định bảo thủ:** Dùng spread lớn hơn typical (ví dụ typical = 1 pip, but backtest = 2 pip, để an toàn)

### 6.5 Quy định

- **Cần ghi rõ:** "Spread giả định: 2 pips (typical EURUSD at brokers)"
- **Nếu backtest trong session:** Spread thường thấp (1-3 pips)
- **Nếu backtest ngoài session hoặc trước news:** Spread cao (5-50 pips), cần riêng giả định hoặc loại bỏ

---

## 7. Slippage (Trượt giá)

### 7.1 Định nghĩa

**Slippage** là sự chênh lệch giữa giá expected (khi đặt lệnh) vs actual (khi fill).

### 7.2 Ví dụ

```
Expected: Entry Long at 1.1000 (close price của setup nến)
Actual: Mua lệnh được fill tại 1.1003 (3 pips worse)
→ Slippage = 3 pips

Trong backtest, nếu không tính slippage:
Entry = 1.1000 (không thực tế)
Nên tính: Entry = 1.1000 + 3 pips slippage = 1.1003
```

### 7.3 Tại sao cần

- Market order (vào ngay) có slippage.
- Limit order (giá cụ thể) có thể không được fill.
- Khi market chảy nhanh (volatile), slippage lớn.
- Không tính slippage → kết quả quá lạc quan.

### 7.4 Từ đâu lấy

- **Tick data:** Tính trực tiếp (entry expected vs fill actual)
- **Giả định:** Dùng con số bảo thủ (ví dụ 1-2 pips cho liquid pair)
- **Brokers:** Một số brokers công bố average slippage

### 7.5 Quy định

- **Ghi rõ:** "Slippage giả định: 1 pip (conservative estimate)"
- **Nếu signal volatile (news):** Tăng slippage (ví dụ 5 pips)
- **Logging:** Ghi lại slippage actual nếu có tick data, so sánh với giả định

---

## 8. Commission (Phí giao dịch)

### 8.1 Định nghĩa

**Commission** = phí broker tính cho mỗi giao dịch (entry + exit).

### 8.2 Ví dụ

```
Entry: 100,000 units EURUSD
Broker commission: 0.01% = 100,000 * 0.0001 = 10 USD

Exit: Close position
Commission: 10 USD

Tổng commission: 20 USD (entry + exit)
```

### 8.3 Tại sao cần

Commission là chi phí cố định. Nếu expected profit = 50 USD, nhưng commission = 20 USD:
- Actual profit = 50 - 20 = 30 USD (giảm 40%)

**Không tính commission** → kết quả quá lạc quan.

### 8.4 Từ đâu lấy

- **Brokers:** Ghi rõ commission structure (fixed/percentage)
  - Fixed: 10 USD per trade
  - Percentage: 0.01% of notional
  - Volume-based: 10 USD up to 100k, 5 USD above 100k

### 8.5 Quy định

- **Ghi rõ:** "Commission: 0.01% (typical Forex brokers)"
- **Nếu không có commission:** Ghi "Commission: 0 (crypto exchanges, some brokers)"
- **Logging:** Tính tổng commission trên tất cả trades, so sánh với expectancy

---

## 9. Swap (Phí qua đêm / Financing Cost)

### 9.1 Định nghĩa

**Swap** (interest rate differential) là phí tính nếu position **giữ qua đêm** (rollover).

### 9.2 Ví dụ (Forex)

```
Long EURUSD (mua EUR, bán USD):
- EUR interest rate: 4% p.a.
- USD interest rate: 5.5% p.a.
- Swap per day: (4% - 5.5%) / 365 = -0.041% per day
- Trên 100,000 units: 100,000 * EUR * -0.041% = ...

(Phụ thuộc exchange rate và cách tính broker)
```

### 9.3 Tại sao cần (nếu chiến lược giữ position qua đêm)

- Nếu chiến lược giữ position từ ngày T tới ngày T+2, sẽ bị tính swap qua đêm.
- Nếu expected daily profit = 20 pips, nhưng swap = 5 pips, actual profit = 15 pips.
- **Không tính swap** → kết quả lạc quan, nhất là chiến lStrategy Long-term (1D+ timeframe).

### 9.4 Từ đâu lấy

- **Brokers:** Cung cấp swap table (để xem file xls/csv)
  - Ví dụ: EURUSD Long swap = -5 pips, Short swap = +3 pips
- **Công bố:** "Swap tính vào 17:00 GMT (rollover time)"

### 9.5 Quy định

- **Ghi rõ:** "Swap: +5 pips (Long EURUSD), -3 pips (Short EURUSD), tính mỗi ngày qua đêm"
- **Nếu không applicable:** "Swap: 0 (crypto, stocks, futures with no overnight cost)"
- **Logging:** Tính tổng swap nếu backtest giữ position qua đêm

---

## 10. Data Quality Checklist

| Item | Check | Action nếu fail |
|---|---|---|
| **Đầy đủ (no gaps)** | Mỗi timeframe có dữ liệu liên tục? | Xác định khoảng lỗ hổng, loại bỏ hoặc interpolate (cẩn thận) |
| **Định dạng** | OHLCV, timestamp đúng ISO 8601? | Reformat, hoặc reject dữ liệu |
| **Range hợp lệ** | H >= max(O,C), L <= min(O,C), H >= L? | Loại bỏ nến invalid |
| **Duplicate** | Có timestamp trùng? | Loại bỏ duplicate |
| **Sorted** | Timestamp tăng đơn điệu? | Sort lại, hoặc reject batch |
| **Volume >= 0** | Khối lượng âm? | Loại bỏ, hoặc coi là 0 |
| **Outlier** | Giá nhảy > 5% vs close trước? | Flag, xác nhận / loại bỏ |
| **Session** | Dữ liệu ngoài session? | Loại bỏ hoặc đánh dấu riêng |
| **Timezone** | Ghi rõ timezone? | Convert to UTC |

---

## 11. Quy định lưu trữ dữ liệu

### 11.1 Định dạng file

- **CSV:** Dễ đọc, dễ import → ưu tiên
- **JSON:** Flexible, support complex structure
- **Parquet:** Nén tốt, dùng cho volume lớn
- **Database:** PostgreSQL, InfluxDB (time series)

### 11.2 Naming convention

```
[PAIR]_[TIMEFRAME]_[STARTDATE]_[ENDDATE].csv
EURUSD_1H_2015-01-01_2020-12-31.csv
GBPUSD_4H_2019-01-01_2021-12-31.csv
BTCUSD_1D_2018-01-01_2024-06-30.csv
```

### 11.3 Folder structure

```
data/
├── raw/          (dữ liệu thô từ nguồn)
│   ├── eurusd_1h.csv
│   ├── gbpusd_4h.csv
├── cleaned/      (dữ liệu sạch sau validation/cleaning)
│   ├── eurusd_1h_clean.csv
│   ├── gbpusd_4h_clean.csv
├── backtest/     (dữ liệu split cho backtest: in-sample + out-of-sample)
│   ├── eurusd_1h_insample_2015_2018.csv
│   ├── eurusd_1h_oosample_2019_2020.csv
```

---

## 12. Summary: Mỗi loại dữ liệu đóng vai trò gì

| Loại dữ liệu | Vai trò | Bắt buộc? | Impact nếu thiếu |
|---|---|---|---|
| **OHLCV** | Dữ liệu cơ bản để backtest | ✅ Bắt buộc | Không thể backtest |
| **Tick Data** | Tính spread, slippage chính xác | ❌ Tùy chọn | Phải giả định spread/slippage, kém chính xác |
| **Multi TF** | Test ở nhiều timeframe | ✅ Nên làm | Không biết chiến lược tốt ở timeframe nào |
| **Timezone** | Xác định session boundary | ✅ Bắt buộc | Tín hiệu sai, session sai |
| **Session** | Loại dữ liệu afterhour, holiday | ✅ Bắt buộc | Backtest dữ liệu giả tạo |
| **Spread** | Tính chi phí giao dịch tức thời | ✅ Bắt buộc | R/R lạc quan |
| **Slippage** | Tính chi phí trượt giá | ✅ Bắt buộc (giả định) | Entry price lạc quan |
| **Commission** | Tính phí broker | ✅ Bắt buộc | Profit lạc quan |
| **Swap** | Tính phí qua đêm (long-term) | ✅ (nếu giữ qua đêm) | Daily profit lạc quan |

---

## 13. Ví dụ: Dataset hoàn chỉnh cho 1 backtest

```
Backtest: TF_001 trên EURUSD, 4H, 2015-2020

Dữ liệu cần:
1. OHLCV: EURUSD 4H từ 2015-01-01 00:00 UTC đến 2020-12-31 23:59 UTC
   (~ 10,000+ nến, khoảng 2-3 MB nếu CSV)

2. Timezone: "UTC" (convert từ GMT)

3. Session: "09:00-17:00 GMT (Forex London session)", loại bỏ afterhour 17:00-09:00

4. Spread: "2 pips (typical EURUSD 4H)"

5. Slippage: "1 pip (conservative)"

6. Commission: "0.0% (không tính nếu broker không charge)"

7. Swap: "Long +5 pips/day, Short -3 pips/day" (nếu backtest giữ qua đêm)

8. Multi Timeframe: Tùy chọn test 1H, 4H, 1D

In-Sample: 2015-01-01 → 2018-12-31 (4 năm)
Out-of-Sample: 2019-01-01 → 2020-12-31 (2 năm)
```

---

## 14. Tham chiếu

- `BACKTEST_ENGINE.md` — Luồng data xử lý, step 2 Data Validation, step 3 Data Cleaning
- `backtests/BACKTEST_STANDARD.md` — Chuẩn dữ liệu trong backtest
- Các chiến lược trong `strategies/` — Định dạ tham số từng chiến lược

# Nguyên Tắc Thiết Kế AI Trading cho AI-TRADE

Tài liệu này đề xuất kiến trúc AI Trading cho dự án, dựa trên bảng so sánh 12 trường phái và triết lý cốt lõi của AI-TRADE (Reaction, Trend Following, Price Action/Market Structure, quản lý rủi ro trên cùng).

---

## KIẾN TRÚC ĐƯỢC ĐỀ XUẤT

### Lõi chính: Trend Following + Market Structure

**Lý do:**
- Dễ tự động hóa (HH/HL, BOS/CHoCH là quy tắc khách quan)
- Cao độ khách quan, thấp phụ thuộc cảm tính
- Hoạt động trên mọi thị trường, mọi timeframe
- Nền tảng của TF_001_BREAKOUT_PULLBACK.md và TF_002_TRENDLINE_REACTION.md đã có

### Lớp xác nhận bổ sung: Volume + Price Action + EMA bias

**Volume Analysis:**
- Breakout kèm volume tăng → độ tin cậy breakout cao hơn
- Pullback kèm volume giảm → sự yếu đi của lực ngược hướng

**Price Action:**
- Breakout quality: thân nến (body) đáng kể, không phải doji
- Pullback quality: hồi về gần vùng nhưng không phá sâu vào

**EMA bias (một chiều áp dụng):**
- EMA dài hạn (200 hoặc tương đương) làm bộ lọc xu hướng
- Chỉ tìm breakout tăng khi giá trên EMA, breakout giảm khi giá dưới
- Không dùng EMA làm tín hiệu giao dịch chính (cắt nhau crossing được cấm)

### Nền tảng quản lý rủi ro: Market Wizards principles

**Các nguyên tắc bắt buộc:**
1. **Cut losses quickly** — Stop loss cố định dựa trên cấu trúc giá, không chạm/dời
2. **Let profits run** — Không cắt lời quá sớm, dời stop loss theo cấu trúc mới
3. **Position sizing từ stop loss** — Công thức cố định, không tùy ý
4. **Discipline over prediction** — Tuân thủ quy tắc trước khi cảm giác

---

## CÁC NGUYÊN TẮC CHỈ ĐẠO

### NGUYÊN TẮC 1: Reaction, không Prediction

**Định nghĩa:**
Mọi quyết định vào lệnh phải dựa trên một tín hiệu **đã xảy ra trên biểu đồ** có thể quan sát được, không phải "cảm thấy" hoặc dự đoán.

**Áp dụng:**
- ✅ Vào lệnh **sau khi** giá phá qua cấu trúc (breakout đã xảy ra)
- ✅ Vào lệnh **sau khi** pullback hình thành và có phản ứng xác nhận (nến đảo chiều)
- ❌ Vào lệnh **trước khi** giá phá (FOMO: "sắp breakout")
- ❌ Vào lệnh dựa trên "cảm giác" thị trường sắp đảo chiều
- ❌ Vào lệnh dựa trên tin tức/sự kiện sắp xảy ra ("sắp có thông báo, sắp rate cut")

**Hệ quả:**
- Mọi chiến lược phải định nghĩa rõ "điều kiện xác nhận cụ thể" (ví dụ: "nến đảo chiều có bóng dài ≥ 50% chiều cao nến")
- AI không được đề xuất vào lệnh dựa trên pattern "nhìn có vẻ", phải là quy tắc định lượng

---

### NGUYÊN TẮC 2: Trend Following, không Reversal Trading

**Định nghĩa:**
Không cố bắt đảo chiều, chỉ giao dịch theo hướng xu hướng đã xác nhận bằng cấu trúc.

**Áp dụng:**
- ✅ Tìm breakout **theo hướng xu hướng hiện tại** (HH/HL hoặc LH/LL)
- ✅ Dừng giao dịch khi xu hướng bị "đảo" (phá hỏng chuỗi HH/HL, xuất hiện LH/LL đầu tiên)
- ❌ Vào lệnh "bắt đáy" khi giá xuống một mức cụ thể
- ❌ Vào lệnh "bán đỉnh" khi RSI > 70
- ❌ Vào lệnh ngược xu hướng dựa trên "độ lệch" từ MA hay chỉ báo

**Hệ quả:**
- Chiến lược phải định nghĩa rõ "xu hướng hiện tại là gì" trước (HH/HL? Giá trên/dưới MA?)
- Chiến lược phải có điều kiện "dừng giao dịch" khi xu hướng bị phá vỡ

---

### NGUYÊN TẮC 3: Price Action/Market Structure là chính

**Định nghĩa:**
Cấu trúc giá (breakout, pullback, trendline, support/resistance) **quyết định có setup hay không**. Chỉ báo chỉ **xác nhận thêm**.

**Áp dụng:**
- ✅ Vào lệnh vì: "Giá breakout qua swing high với volume cao"
- ✅ Xác nhận thêm: "Volume cao (confirm), RSI không phân kỳ (confirm)"
- ❌ Vào lệnh vì: "RSI vừa cross trên 50" (dùng chỉ báo làm tín hiệu chính)
- ❌ Vào lệnh vì: "EMA 20 vừa cross trên EMA 50" (golden cross)

**Hệ quả:**
- Mọi chiến lược phải liệt kê trong mục "Điều kiện vào lệnh" những quy tắc Price Action/Market Structure **trước**, rồi mới "Xác nhận bổ sung" (chỉ báo)

---

### NGUYÊN TẮC 4: Volume và EMA chỉ xác nhận, không quyết định

**Định nghĩa:**
Volume (khối lượng) và EMA (đường trung bình) là dữ liệu **phụ trợ**, không bao giờ là "điều kiện đủ" để vào lệnh một mình.

**Volume:**
- ✅ Sử dụng: "Breakout kèm volume > SMA volume 20 ngày" (xác nhận breakout real)
- ✅ Sử dụng: "Pullback kèm volume < SMA volume 20 ngày" (weak selling)
- ❌ Sử dụng: "Volume tăng → vào lệnh" (không có price action)
- ❌ Sử dụng: "OBV đảo chiều → vào lệnh" (lõi tín hiệu)

**EMA:**
- ✅ Sử dụng: "Giá trên EMA 200 D1 → tìm breakout tăng" (filter bias)
- ✅ Sử dụng: "EMA 50 dốc lên → xu hướng tăng còn khỏe" (confirm momentum)
- ❌ Sử dụng: "Giá chạm EMA 50 → vào lệnh" (EMA chạm ≠ setup)
- ❌ Sử dụng: "EMA 20 cross trên EMA 50 → vào lệnh" (crossing là chỉ báo lag)

**Hệ quả:**
- Mọi chiến lược phải tách rõ mục "Điều kiện vào lệnh" (Price Action) vs "Xác nhận bổ sung" (Volume/EMA)
- AI không được đề xuất "xây dựng chiến lược" mà chỉ dùng EMA/Volume làm lõi

---

### NGUYÊN TẮC 5: Quản lý rủi ro quan trọng hơn tỷ lệ thắng

**Định nghĩa:**
Một hệ thống thắng 40% với rủi ro kiểm soát chặt có giá trị tài chính hơn hệ thống thắng 70% nhưng không giới hạn lỗ rõ ràng.

**Áp dụng:**
- ✅ Stop loss cố định từ cấu trúc giá (quy tắc bắt buộc ở từng strategy)
- ✅ Position size từ công thức: vốn × % rủi ro / khoảng cách SL
- ✅ Giới hạn tổng rủi ro danh mục (không vượt X% vốn/session)
- ✅ Kill switch tự động khi drawdown > Y% hoặc thua N lệnh liên tiếp
- ❌ Vào lệnh "đẹp" dù không tính được stop loss trước
- ❌ Nối lệnh (martingale) để gỡ lệnh đang thua
- ❌ Dời stop loss về hướng có lợi khi lệnh đang thua (trailing stop từ entry → profit)

**Hệ quả:**
- Mọi chiến lược phải định nghĩa rõ "Stop Loss" theo cấu trúc giá cụ thể
- AI không được tự quyết định mức rủi ro hay dời stop loss

---

### NGUYÊN TẮC 6: Không tổng quát hóa chiến lược giữa thị trường/timeframe

**Định nghĩa:**
Một chiến lược **xác nhận** trên EUR/USD D1 không được coi là sẽ hoạt động như nhau trên GBP/USD H4 hay BTC/USDT 4h mà chưa backtest riêng.

**Áp dụng:**
- ✅ Backtest TF_001 trên EUR/USD, sau đó backtest riêng trên GBP/USD, GOLD, BTC
- ✅ Ghi rõ trong strategy: "Đã xác nhận: EUR/USD D1 (2023-2024), cần kiểm chứng thêm GBP, GOLD"
- ❌ Sử dụng "một phiên bản TF_001" cho tất cả cặp tiền
- ❌ Giả định "nếu tốt trên D1 thì H4 cũng tốt"

**Hệ quả:**
- Mỗi strategy file phải liệt kê "Thị trường/Timeframe đã kiểm chứng" cụ thể
- Backtest phải chạy riêng cho từng kết hợp market/timeframe mới

---

### NGUYÊN TẮC 7: AI không tự quyết định mức rủi ro

**Định nghĩa:**
LLM/AI hỗ trợ có thể: tính toán size lệnh dựa công thức, cảnh báo vi phạm giới hạn, tổng hợp rủi ro. Nhưng **không được** tự đề xuất nới lỏng mức rủi ro, thay đổi giới hạn thua lỗ, hay bỏ qua kill switch.

**Áp dụng:**
- ✅ AI tính: "Setup này, SL = 100 pips, size = (10k × 1%) / 100 = 100 units"
- ✅ AI cảnh báo: "Setup này vi phạm max portfolio risk (tổng rủi ro đang 1.5%, thêm 1.2% = 2.7% > giới hạn 2%)"
- ❌ AI đề xuất: "Setup rất đẹp, có thể risk 2% cho lệnh này thay vì 1%"
- ❌ AI bỏ qua: "Kill switch kích hoạt, nhưng sắp có lệnh thứ 3 có thể gỡ lỗ, để tôi chạy lệnh này rồi mới dừng"

**Hệ quả:**
- Mọi quy tắc rủi ro phải được fix trong `risk/RISK_POLICY.md` trước, không phải quyết định tại thời điểm giao dịch
- Thay đổi mức rủi ro chỉ được thực hiện qua sửa file rủi ro có ý thức, không phải prompt AI

---

## KIẾN TRÚC AI TRADING ĐƯỢC ĐỀ XUẤT

```
┌─────────────────────────────────────┐
│   Input: Dữ liệu giá (OHLCV)       │
│   Timeframe: M1-D1                  │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│   Lớp 1: Trend Identification       │
│   ├─ HH/HL (Higher High/Low)       │
│   ├─ LH/LL (Lower High/Low)        │
│   └─ EMA bias (bộ lọc)              │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│   Lớp 2: Price Action Setup         │
│   ├─ Breakout detection (TF_001)   │
│   ├─ Pullback validation            │
│   ├─ Trendline reaction (TF_002)   │
│   └─ Entry confirmation (nến phản ứng)
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│   Lớp 3: Confirmation              │
│   ├─ Volume check (> SMA 20)        │
│   └─ RSI divergence (optional)      │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│   Lớp 4: Risk Management            │
│   ├─ SL calculation (từ cấu trúc)  │
│   ├─ Position sizing (% vốn/SL)     │
│   ├─ Portfolio risk check (tổng)    │
│   └─ Kill switch validation         │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│   Output: Tín hiệu vào lệnh        │
│   - Setup description               │
│   - Entry price, SL, TP             │
│   - Position size, Risk %            │
│   - Xác nhận bởi: Price Action,     │
│     Volume, EMA bias                │
└─────────────────────────────────────┘
```

---

## CÁC LỰA CHỌN KỸ THUẬT

### ML/RL có nên dùng không?

**Giai đoạn hiện tại (Phase 1):** Không cần.
- Rule-based system (quy tắc rõ ràng) đã đủ để triển khai Phase 1-2

**Giai đoạn tương lai (Phase 5-6):**
- **RL có thể dùng để tối ưu tham số:** N-bar breakout nên bao nhiêu? ATR multiplier cho SL bao nhiêu?
- **ML (CNN) có thể dùng để nhận biết "bar quality":** Phân loại "bull bar strong" vs "bull bar weak" từ ảnh
- **Tránh:** RL cho position sizing, stop loss decision (luật cứng)

---

## KẾT LUẬN

Kiến trúc được đề xuất là:
1. **Trend Following + Market Structure** — lõi khách quan, dễ automate
2. **Volume + Price Action + EMA** — lớp xác nhận
3. **Market Wizards principles** — nền tảng quản lý rủi ro
4. **Reaction-based, không prediction** — toàn bộ quy tắc dựa trên dữ liệu đã xảy ra
5. **Multi-market compatible** — cùng logic áp dụng được forex/crypto/stock
6. **AI hỗ trợ, không tự quyết định rủi ro** — AI là công cụ, không là trader

Kiến trúc này **thích hợp với:**
- Backtesting (rule-based, dễ code)
- Tự động hóa (các điều kiện khách quan)
- Cơ bản hóa (không quá phức tạp)
- Quản lý rủi ro (luật cứng, không chủ quan)

**Không thích hợp với:**
- Dự đoán cảm tính (vì reaction-based)
- Reversal trading (vì trend following)
- High frequency trading (vì timeframe tối thiểu M1, logic chủ yếu D1+)

# Thực Hành Tốt Nhất cho AI-TRADE

Tổng hợp các quy tắc và nguyên tắc tốt nhất để triển khai hệ thống Trend Following + Market Structure cho AI-TRADE, rút ra từ các trường phái chính và các bài học từ Market Wizards.

---

## 1. QUẢN LÝ RỦI RO

### Quy tắc 1.1: Cắt lỗ nhanh, để lợi nhuận chạy

**Nguyên tắc:**
Hạn chế tổn thất trên mỗi lệnh ở mức cố định nhỏ, nhưng không giới hạn chặt chẽ lợi nhuận khi xu hướng đang đúng hướng.

**Áp dụng:**
- Stop Loss: Cố định dựa trên cấu trúc giá, đặt ngay từ lúc vào lệnh
- Take Profit: Không nên cắt lời quá sớm — hãy dời SL theo cấu trúc mới để "để lợi nhuận chạy"
- Trailing Stop: Dời SL lên theo các swing low/high mới cùng hướng, không dời SL xuống

**Cụ thể ví dụ (TF_001):**
- SL = dưới pullback low (setup tăng) hoặc trên pullback high (setup giảm)
- TP: Không cắt lời % cố định — dời SL theo HH tiếp theo, chỉ thoát khi xu hướng bị phá vỡ

**Tránh:**
- ❌ Đặt TP = 1:1 hoặc 1:2 risk/reward cố định cho mọi lệnh
- ❌ Cắt 50% lợi nhuận khi giá vừa hồi lại entry level
- ❌ Dời SL xuống/lên (ngược hướng lệnh) để "chờ quay lại"

---

### Quy tắc 1.2: Không có lệnh nào được vào mà không có SL rõ ràng

**Nguyên tắc:**
Phải tính được SL cụ thể **trước** khi vào lệnh. Nếu không tính được, không vào.

**Áp dụng:**
- Trước khi vào lệnh: Xác định SL cụ thể (pips, giá, hoặc theo cấu trúc)
- Ghi rõ trong tín hiệu: "SL = 123.45" không phải "SL ở dưới pullback" (quá mơ hồ)
- Tính position size từ SL: size = (vốn × % rủi ro) / (Entry - SL)

**Cụ thể:**
✅ "Entry 1.1000, SL 1.0950 (đúng dưới pullback low ở 1.0948), size = 100 units"
❌ "Entry 1.1000, SL ở đâu đó dưới pullback, size sẽ tính sau"

---

### Quy tắc 1.3: Không nhồi lệnh (Martingale cấm)

**Nguyên tắc:**
Nếu lệnh đang thua, không được vào thêm lệnh để "gỡ" hoặc "trung bình giá". Mỗi lệnh độc lập, kỷ luật không thay đổi vì tình cảm.

**Áp dụng:**
- Một lệnh thua → chấp nhận lỗ, không vào thêm
- Một lệnh thắng → không vào thêm cùng hướng để "kỳ vọng cao hơn"
- Portfolio risk không vượt giới hạn (nếu hiện tại 1% rủi ro, lệnh mới tối đa 1% nữa, không vượt portfolio limit)

**Tránh:**
- ❌ "Lệnh thua 100 pips, vào thêm gấp đôi size để gỡ"
- ❌ "Setup quá đẹp, bỏ qua quy tắc size để vào to hơn"

---

### Quy tắc 1.4: Drawdown, lỗi liên tiếp → dừng, đánh giá lại

**Nguyên tắc:**
Khi xảy ra chuỗi lệnh thua hoặc drawdown vượt mức đã định, bắt buộc dừng giao dịch để xem xét lại chiến lược. Không "chờ hết cảm giác rồi tiếp tục".

**Áp dụng:**
- Theo dõi: Số lệnh thua liên tiếp, tổng drawdown % vốn
- Khi đạt ngưỡng: Dừng chiến lược đó, viết vào `research/FAILURE_CASES.md`
- Đánh giá: Xem lại `strategies/`, thay đổi quy tắc, hoặc đợi thị trường thay đổi
- Khôi phục: Chỉ được tiếp tục khi Project Owner xác nhận, không tự động

**Cụ thể:**
- Nếu "5 lệnh liên tiếp thua" → dừng, không vào lệnh thứ 6
- Nếu "drawdown > 3% vốn" → dừng, đánh giá lại

**Ghi chú:** Ngưỡng cụ thể (số lệnh, %) sẽ được chốt trong `risk/RISK_POLICY.md` khi Project Owner quyết định

---

## 2. PHÂN TÍCH VÀ SETUP

### Quy tắc 2.1: Xác định xu hướng trước (không bỏ qua bước này)

**Nguyên tắc:**
Trước khi tìm breakout/pullback, phải xác định rõ **hiện tại thị trường trong xu hướng tăng, giảm, hay đi ngang**.

**Áp dụng cho TF_001/TF_002:**
- Xu hướng tăng: Chuỗi HH + HL liên tiếp (tối thiểu 2 cặp)
- Xu hướng giảm: Chuỗi LH + LL liên tiếp (tối thiểu 2 cặp)
- Đi ngang: Không có chuỗi rõ ràng → không giao dịch, chờ xu hướng hình thành

**Cụ thể:**
✅ "Swing 1: H 1.1050, L 1.1000 | Swing 2: H 1.1080, L 1.1020 → HH + HL → xu hướng tăng"
❌ "Giá ở đây, có vẻ sắp tăng, tìm breakout tăng" (không xác định trend trước)

---

### Quy tắc 2.2: Breakout phải có xác nhận (không chỉ chạm)

**Nguyên tắc:**
Giá chạm vào swing high/low chưa tính là breakout. Breakout là giá **đóng cửa** vượt hẳn và **không quay lại**.

**Áp dụng cho TF_001:**
- Giá phá qua swing high → xem nến đó xác nhận như thế nào
  - ✅ Nến close > swing high, body chiếm tỷ lệ: **breakout xác nhận**
  - ❌ Nến close > swing high nhưng doji/small body: Chưa chắc, chờ nến tiếp theo
- Nếu nến tiếp theo close trở lại dưới swing high → false break, không vào

**Cụ thể:**
✅ "Swing high 1.1050, nến breakout close 1.1055, body 40 pips → breakout xác nhận"
❌ "Swing high 1.1050, nến breakout close 1.1051, body 1 pip (doji) → chờ nến tiếp theo"

---

### Quy tắc 2.3: Pullback phải hợp lệ (không quá sâu, không phá)

**Nguyên tắc:**
Sau breakout, pullback phải "hợp lệ" — quay lại gần vùng phá vỡ nhưng không phá sâu vào bên trong. Nếu phá sâu = false break.

**Áp dụng cho TF_001:**
- Pullback hợp lệ: Quay lại gần breakout level nhưng close vẫn > breakout point
  - ✅ Swing high 1.1050, breakout 1.1055, pullback xuống 1.1048 (không close dưới 1.1050) → hợp lệ
  - ❌ Pullback xuống 1.1045 (close dưới swing high 1.1050) → phá sâu, false break
- Volume pullback: Nên giảm so với nến breakout (lực bán yếu, chỉ hồi kỹ thuật)

**Tránh:**
- ❌ "Nến pullback close 1.1045 (dưới swing high), nhưng giá quay lại tăng vào ngày hôm sau nên là pullback hợp lệ"
  - Không! Tại thời điểm ra quyết định (khi pullback mới xảy ra), tiêu chí "không phá sâu" đã bị vi phạm. Không thể nhìn lại quá khứ để "cấp phép".

---

### Quy tắc 2.4: Phản ứng xác nhận sau pullback (yêu cầu bắt buộc)

**Nguyên tắc:**
Không vào lệnh ngay khi giá hồi về gần vùng pullback mà chưa có phản ứng xác nhận. Phải thấy dấu hiệu giá sẵn sàng tiếp tục đúng hướng.

**Áp dụng cho TF_001:**
- Phản ứng xác nhận có thể là:
  - Nến đảo chiều rõ ràng (ví dụ hammer/bullish engulfing khi pullback tại setup tăng)
  - Break of Structure nhỏ hơn (trong khung H1, phá được swing low thấp hơn của pullback)
  - Volume tăng bất ngờ kèm giá đi lên (xác nhận lực mua)

**Cụ thể:**
✅ "Pullback về 1.1048, nến tiếp theo là hammer (dưới 1.1040, close 1.1047) → phản ứng xác nhận, vào lệnh"
❌ "Pullback về 1.1048, giá dừng ở đó 2-3 nến không phản ứng rõ → đừng vào, chờ confirmation rõ"

---

### Quy tắc 2.5: Trendline chỉ giao dịch từ điểm thứ 3 trở đi

**Nguyên tắc:**
Trendline cần tối thiểu 3 điểm chạm để giao dịch. 2 điểm chỉ đủ để vẽ đường, không đủ để chứng minh thị trường "tôn trọng" nó.

**Áp dụng cho TF_002:**
- Điểm 1 & 2: Vẽ trendline (không giao dịch)
- Điểm 3: Giá chạm trendline lần thứ 3, nếu có phản ứng → có thể giao dịch từ lần này
- Điểm 4+: Độ tin cậy tăng thêm, nhưng không tuyến tính (quá nhiều chạm = năng lượng tích lũy để phá)

**Cụ thể:**
✅ "Trendline chạm 3 lần (điểm 1, 2, 3), tại điểm 3 có nến đảo chiều rõ → vào lệnh"
❌ "Trendline mới vẽ (chỉ 2 điểm), vừa chạm lần thứ 2 → vào lệnh" (quá sớm)

---

## 3. PHÂN TÍCH VÀ NGĂN CHẶN LỖI

### Quy tắc 3.1: Không vào lệnh khi tin tức lớn sắp ra

**Nguyên tắc:**
Các sự kiện tin tức có thể gây gap, biến động bất thường → tránh giao dịch trong vòng X giờ trước sự kiện

**Áp dụng:**
- Liệt kê các sự kiện quan trọng: FOMC, ECB decision, NFP, CPI...
- Không vào lệnh trong 1-2 giờ trước các sự kiện lớn
- Nếu lệnh đang mở, có thể xét thoát sớm hoặc tăng SL để bảo vệ

**Ghi chú:**
- Chi tiết về các sự kiện và cách xử lý sẽ được định nghĩa trong từng strategy khi backtest

---

### Quy tắc 3.2: Không ép vẽ trendline

**Nguyên tắc:**
Trendline phải được vẽ **một lần, rõ ràng** từ trước. Không được chỉnh sửa nhiều lần để "hợp thức hóa" một setup mong muốn.

**Áp dụng:**
- Vẽ trendline khi swing cao dần (giảm): Xác định 2 swing high (trendline giảm) → kẻ đường
- Nếu đường vẽ "xấu" (phải chỉnh đủ lần): Không giao dịch → không phải trendline đúng, không phải bias confirmation
- Nếu thị trường "cụng" vào trendline từ lần đầu → mới chứng minh trendline thật

**Tránh:**
- ❌ "Vẽ trendline theo cách A không có điểm chạm, thử cách B vẫn không, thử cách C được 2 điểm → dùng cách C"

---

### Quy tắc 3.3: Volume phải xác nhận, không phải thay thế

**Nguyên tắc:**
Volume cao ≠ tín hiệu vào lệnh. Phải có price action (breakout) trước, volume là xác nhận thêm.

**Áp dụng:**
- ✅ Setup: "Breakout qua swing high" + "Volume > SMA 20" → vào lệnh
- ❌ Setup: "Volume tăng đột biến" + không có price action rõ → không vào

**Cụ thể:**
✅ "Giá breakout qua 1.1050 với nến 50 pips body, volume 200M (SMA 20 = 120M) → confirm, vào"
❌ "Volume vừa tăng lên 250M (cao nhất tuần), nhưng giá không breakout → chờ breakout, không vào vì volume"

---

### Quy tắc 3.4: Không dùng RSI kiểu "quá mua/quá bán" (cấm cứng)

**Nguyên tắc:**
RSI > 70 ≠ "quá mua phải bán". Trong xu hướng mạnh, RSI ở vùng "quá mua" là **bình thường**, không phải tín hiệu đảo chiều.

**Áp dụng:**
- ❌ Vào lệnh bán vì "RSI > 70" (kiểu máy móc) — cấm
- ✅ Sử dụng RSI: Phân kỳ (divergence) — giá tạo đỉnh mới nhưng RSI không → xác nhận suy yếu động lượng
- ✅ Sử dụng RSI: Kiểm tra momentum — "RSI > 50 khi pullback" → xu hướng tăng còn khỏe

**Cụ thể:**
❌ "RSI 72 → quá mua → vào lệnh bán" (sai)
✅ "Giá tạo đỉnh cao hơn, nhưng RSI thấp hơn đỉnh trước + price action xác nhận → divergence xác nhận suy yếu"

---

## 4. BACKTEST VÀ KIỂM CHỨNG

### Quy tắc 4.1: Không bịa số liệu backtest

**Nguyên tắc:**
Mọi kết quả backtest phải từ code thực tế chạy, không được "tính tay" hoặc "nhìn biểu đồ mà đoán".

**Áp dụng:**
- Chạy backtest đầy đủ (không chỉ vài lệnh mẫu)
- Lưu kết quả vào `backtests/RESULTS_TEMPLATE.md` với chi tiết: số lệnh, tỷ lệ thắng, avg lời/lỗ, PnL, drawdown
- Không được điền vào `strategies/TF_001.md` "Kết quả backtest" mà chưa chạy thật

**Tránh:**
- ❌ "Nhìn biểu đồ EUR/USD 3 tháng, thấy TF_001 đẹp, bảo là backtest OK"
- ✅ "Chạy code backtest TF_001 trên EUR/USD D1 2023-2024, kết quả: 120 lệnh, 42% win, PnL +1500 pips"

---

### Quy tắc 4.2: Không curve-fitting (tối ưu quá)

**Nguyên tắc:**
Không chỉnh tham số của strategy để "match hoàn hảo" với kết quả backtest quá khứ. Quy tắc phải hoạt động trên dữ liệu "chưa nhìn thấy" (out-of-sample).

**Áp dụng:**
- Backtest trên dữ liệu lịch sử (ví dụ 2023)
- Test lại trên dữ liệu mới (ví dụ 2024) **với cùng tham số** — nếu kết quả khác nhiều = curve-fitting
- Không chỉnh tham số sau khi thấy kết quả backtest

**Tránh:**
- ❌ "Backtest TF_001 trên 2023 được 50% win, chỉnh N-bar breakout từ 10 thành 11 để 52% → coi là OK"

---

### Quy tắc 4.3: Cần đủ dữ liệu để thống kê (tối thiểu mẫu)

**Nguyên tắc:**
Backtest phải có đủ lệnh để kết quả có ý nghĩa thống kê. Quá ít lệnh = cơ hội lớn đó chỉ là "vận may".

**Áp dụng:**
- Tối thiểu 30-50 lệnh để kết quả có ý nghĩa cơ bản
- Tối thiểu 100+ lệnh để kết quả đáng tin (phụ thuộc chiến lược)
- Nếu strategy quá ít lệnh → kéo dài khoảng thời gian backtest hoặc thêm thị trường khác

**Cụ thể:**
- ❌ "Backtest TF_001 trên 2024 (1 tháng), 5 lệnh → coi là xác nhận"
- ✅ "Backtest TF_001 trên 2023-2024 (1 năm), 120 lệnh → kết quả đáng tin"

---

## 5. GIAO DỊCH VÀ KỶ LUẬT

### Quy tắc 5.1: Tuân thủ tuyệt đối quy tắc, không ngoại lệ khi giao dịch thật

**Nguyên tắc:**
Một khi strategy đã chốt, **mọi giao dịch phải theo đúng quy tắc**, không được "sửa" vì cảm giác hoặc "setup quá đẹp".

**Áp dụng:**
- Nếu strategy yêu cầu volume > SMA 20, mà lệnh này volume = SMA 20 → không vào (không ngoại lệ)
- Nếu rule yêu cầu phản ứng xác nhận sau pullback → không vào ngay khi pullback xuống, chờ phản ứng

**Lý do:**
- Backtest đã tính toán qua hàng trăm lệnh → ngưỡng này là tối ưu
- "Ngoại lệ" từng lần = drift từ backtest → lợi nhuận thực tế khác từ backtest

---

### Quy tắc 5.2: Ghi lại mọi lệnh (thành công, thất bại)

**Nguyên tắc:**
Mọi lệnh (paper trade, backtest, thật) phải được ghi vào `research/EXPERIMENT_LOG.md`. Không ghi log → không có feedback loop.

**Áp dụng:**
- Ngày, giờ
- Chiến lược, cặp/asset, timeframe
- Entry, SL, TP, size
- Thoát: giá thoát, lợi/lỗ
- Nhận xét: "Follow rule", "Vi phạm rule X", "Market condition Y"

**Ghi chú:** Nếu phát hiện pattern lỗi → cập nhật `research/FAILURE_CASES.md`

---

## 6. LIÊN HỆ VỚI AI-TRADE STRATEGIES CỤ THỂ

### Cho TF_001_BREAKOUT_PULLBACK:

1. Xác định xu hướng trước (HH/HL hoặc LH/LL) — quy tắc 2.1
2. Xác nhận breakout (close vượt swing high/low, body đáng kể, volume) — quy tắc 2.2, 3.3
3. Chờ pullback hợp lệ (không phá sâu) — quy tắc 2.3
4. Chờ phản ứng xác nhận tại pullback (nến đảo chiều hoặc BOS nhỏ) — quy tắc 2.4
5. Vào lệnh, SL dưới pullback low/high + margin ATR — quy tắc 1.2, 1.1
6. Size = (vốn × 1%) / (entry - SL) — quy tắc 1.2
7. Dời SL theo HH/LL tiếp theo, không cắt lời quá sớm — quy tắc 1.1
8. Thoát khi xu hướng bị phá (CHoCH + BOS ngược hướng) — quy tắc 1.1

### Cho TF_002_TRENDLINE_REACTION:

1. Vẽ trendline từ 2 swing high/low đầu tiên — quy tắc 3.2
2. Chờ điểm chạm thứ 3 (không giao dịch trước) — quy tắc 2.5
3. Tại điểm chạm thứ 3, nếu có phản ứng xác nhận → vào lệnh — quy tắc 2.4
4. SL trên/dưới trendline + margin — quy tắc 1.2, 1.1
5. Size theo công thức — quy tắc 1.2
6. Thoát theo quy tắc thoát (dời SL, hoặc breakout trendline + pullback về trendline) — quy tắc 1.1

---

## TÓNG TẮT NGUYÊN TẮC VÀNG

| # | Nguyên tắc | Áp dụng |
|---|---|---|
| 1 | Cắt lỗ nhanh, để lợi chạy | Mọi lệnh phải có SL cố định |
| 2 | Không vào mà không SL rõ | Tính SL trước, không vào nếu mơ hồ |
| 3 | Không nhồi lệnh | 1 lệnh thua → không vào thêm |
| 4 | Drawdown → dừng, đánh giá | Không chờ quay lại như cũ |
| 5 | Xác định trend trước | Không tìm breakout nếu không biết trend |
| 6 | Breakout cần xác nhận | Không chỉ chạm, phải close rõ |
| 7 | Pullback hợp lệ | Không phá sâu vào bên trong |
| 8 | Reaction sau pullback | Chờ xác nhận, không vào ngay |
| 9 | Trendline từ điểm 3 | Không giao dịch 2 điểm đầu |
| 10 | Không ép trendline | Vẽ 1 lần, không chỉnh nhiều |
| 11 | Volume xác nhận | Không dùng volume làm tín hiệu chính |
| 12 | Cấm RSI quá mua/bán | Dùng divergence, không ngưỡng 70/30 |
| 13 | Không bịa backtest | Chạy code thực tế, ghi log chi tiết |
| 14 | Không curve-fit | Tham số phải hoạt động trên dữ liệu mới |
| 15 | Đủ mẫu (30-100 lệnh) | Backtest phải có ý nghĩa thống kê |
| 16 | Tuân thủ tuyệt đối | Không ngoại lệ khi giao dịch thật |
| 17 | Ghi log mọi lệnh | Feedback loop để cải thiện |


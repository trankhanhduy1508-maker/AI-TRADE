# Lỗi Phổ Biến Khi Áp Dụng Các Trường Phái Giao Dịch

Tài liệu này liệt kê các **lỗi chủ quan thường gặp** khi áp dụng sai các nguyên tắc từ các trường phái chính. Đây là "cảnh báo trước", khác với `research/FAILURE_CASES.md` là ca thất bại thật của dự án.

---

## LỖI VỀ TREND FOLLOWING

### Lỗi 1.1: Dự đoán đảo chiều thay vì phản ứng

**Mô tả:**
Trader "cảm thấy" thị trường sắp đảo chiều nên vào lệnh **ngược** xu hướng hiện tại, thay vì chờ xu hướng mới được xác nhận.

**Triệu chứng:**
- "Giá đã tăng 500 pips, chắc phải hồi giả nay"
- "RSI 85, quá mua rồi, bán đi"
- "Đã từ tháng 1-8 mà chưa quay lại, phải quay mất thôi"

**Hậu quả:**
- Vào lệnh ngược xu hướng chính → bị stop loss liên tiếp
- Tỷ lệ thắng thấp vì trend còn mạnh nhưng đã vào ngược

**Phòng tránh:**
- Bắt buộc xác định xu hướng hiện tại bằng cấu trúc (HH/HL hay LH/LL)
- Chỉ tìm reversal khi xu hướng bị phá (CHoCH + BOS ngược hướng xuất hiện)
- Không vào lệnh dựa trên "cảm giác"

**Liên quan đến AI-TRADE:**
- TF_001, TF_002 đều là trend following → cấm tuyệt đối lỗi này
- AI phải kiểm tra `research/HYPOTHESES.md` H002: "Trendline có giá trị từ điểm 3"

---

### Lỗi 1.2: Vào lệnh quá sớm, chưa breakout thực sự xảy ra

**Mô tả:**
Trader thấy "có vẻ sắp breakout" nên vào lệnh trước khi breakout thực sự xảy ra → bị false break kẹp.

**Triệu chứng:**
- "Giá đang chạm swing high (80 pips), sắp phá vỡi, vào trước"
- "Breakout hôm mai chắc chắn, paper trade từ bây giờ"
- Vào lệnh khi giá mới chạm vùng, chưa đóng cửa vượt

**Hậu quả:**
- Bị FOMO (fear of missing out)
- Rủi ro cao vì chưa có xác nhận thực tế
- Stop loss lớn

**Phòng tránh:**
- Chờ khi nào **giá đã close vượt** swing high/low = breakout xác nhận
- Nếu intraday mà timeframe nhỏ: chờ nến tiếp theo close rõ vượt, không vào nến đầu tiên chạm

**Liên quan đến AI-TRADE:**
- TF_001: Mục 4 "Điều kiện breakout hợp lệ" → "Giá **đóng cửa** vượt hẳn"
- Lỗi này là violation trực tiếp của rule

---

## LỖI VỀ MARKET STRUCTURE

### Lỗi 2.1: Nhầm lẫn false break với phá hỏng cấu trúc

**Mô tả:**
Một nến phá qua swing high/low nhưng nhanh chóng quay lại. Trader nhầm đây là "change of structure" (CHoCH) trong khi thực tế chỉ là false break tạm thời.

**Triệu chứng:**
- "Giá break qua 1.1050 (swing high) rồi quay lại 1.1045 → trend xảy ra điều gì đó"
- "Phải đưa lệnh short ngay vì trend đảo"

**Hậu quả:**
- Vào lệnh ngược hướng dựa trên "false signal"
- Giá tiếp tục lên, bị stop loss
- Tỷ lệ sai cao

**Phòng tránh:**
- CHoCH thực sự = **phá vỡ một chuỗi** (ví dụ: chuỗi HH/HL bị phá qua LH đầu tiên)
- Một false break đơn lẻ không phải CHoCH
- Cần xác nhận CHoCH bằng cấu trúc mới theo hướng ngược (LH → tìm thêm LL)

---

### Lỗi 2.2: Định nghĩa swing quá mệm hoặc quá chặt

**Mô tả:**
"Swing high/low" là định nghĩa chủ quan (bao nhiêu nến hai bên cần cao/thấp hơn để coi là swing?). Nếu định nghĩa sai → phát hiện HH/HL sai.

**Triệu chứng:**
- "Cứ đỉnh nào cao hơn đỉnh trước là HH" (quá mệm, sẽ có quá nhiều HH giả)
- "Cần 10 nến hai bên thấp/cao hơn mới coi là swing" (quá chặt, miss được nhiều trend)

**Hậu quả:**
- Quá mệm: quá nhiêu signal giả, tỷ lệ thắng thấp
- Quá chặt: miss được trend thật, lợi nhuận thấp

**Phòng tránh:**
- Định nghĩa rõ trước: "Swing high = nến có close cao nhất, có tối thiểu N nến trước/sau đều thấp hơn"
- Thường N = 2-3 cho timeframe M5-M30, N = 1-2 cho intraday, N = 2-3 cho D1+
- Cố định N, không thay đổi trong khi giao dịch

**Liên quan đến AI-TRADE:**
- TF_001, TF_002 đều cần định N → phải backtest để tìm N tối ưu
- Không được "nhìn biểu đồ rồi vẽ swing", phải algorithmically định

---

## LỖI VỀ BREAKOUT/PULLBACK

### Lỗi 3.1: Pullback quá sâu coi là phá vỡ, không phải pullback hợp lệ

**Mô tả:**
Sau breakout, giá hồi lại gần vùng phá vỡ → trader coi "hồi lại nên là pullback", vào lệnh. Nhưng thực tế pullback phá sâu vào bên trong vùng = false break.

**Triệu chứng:**
- "Breakout qua 1.1050, hồi về 1.1045" → coi là pullback
- Nhưng nến pullback close 1.1048 (vẫn trên 1.1050), sau đó giá quay lại xuống → false break chứ không phải breakout

**Hậu quả:**
- Vào lệnh trước khi xác nhận breakout thực sự
- Bị stop loss khi false break
- Risk/reward xấu

**Phòng tránh:**
- Pullback **hợp lệ** = quay lại gần vùng nhưng **không close dưới swing high/low gốc**
- Nếu close dưới = false break, không vào lệnh, chờ sửa lỗi sau
- Có thể dùng volume: pullback volume < breakout volume là xác nhận yếu

---

### Lỗi 3.2: Cắt lời quá sớm, bỏ lỡ move lớn

**Mô tả:**
Vào lệnh tốt (setup hợp lệ), nhưng thoát quá sớm vì "có lợi rồi, chốt đi" → bỏ lỡ move lớn hơn.

**Triệu chứng:**
- "Setup tăng, vào 1.1000, giá lên 1.1020 (20 pips lợi), thoát là an toàn"
- Nhưng nó lên 1.1100 trong vòng 1 tuần (100 pips)

**Hậu quả:**
- Tỷ lệ thắng cao nhưng kỳ vọng toán học thấp (lợi trung bình < lỗ trung bình)
- Hiệu quả xấu hơn "để lợi chạy"

**Phòng tránh:**
- Đừng cắt lời % cố định (TP = 1:1 hoặc 1:2 R:R)
- Thay vào đó: dời stop loss theo cấu trúc mới, thoát khi xu hướng bị phá
- Để lợi nhuận "chạy" với xu hướng cho tới khi nó dừng

**Liên quan đến AI-TRADE:**
- TF_001, TF_002 mục 8 "Thoát lệnh": "dời stop loss theo cấu trúc giá mới"
- Không dùng % cố định

---

## LỖI VỀ RSI / CHỈ BÁO

### Lỗi 4.1: Dùng RSI 70/30 như tín hiệu giao dịch chính

**Mô tả:**
Trader vào lệnh dựa trên **RSI > 70 → bán** hoặc **RSI < 30 → mua**, không cần price action.

**Triệu chứng:**
- "RSI vừa cross trên 70, vào lệnh bán"
- "RSI dưới 30, mua ngay"

**Hậu quả:**
- Trong xu hướng mạnh, RSI ở vùng "quá mua/bán" rất lâu mà giá vẫn tiếp tục trending
- Bị stop loss liên tiếp khi vào ngược trend

**Phòng tránh:**
- RSI 70/30 KHÔNG phải tín hiệu giao dịch độc lập
- Dùng RSI: phân kỳ (divergence) hoặc momentum check ("RSI > 50 xác nhận trend up còn khỏe")
- Luôn combine với price action/market structure

**Liên quan đến AI-TRADE:**
- `knowledge/RSI_RESEARCH.md` mục "Cách dùng RSI được chấp nhận"
- `DECISIONS.md` "Không dùng RSI kiểu máy móc"

---

### Lỗi 4.2: Dễ dàng thay đổi ngưỡng chỉ báo để "hợp thức hóa" setup

**Mô tả:**
Trader muốn vào lệnh nhưng chỉ báo không khớp → thay đổi tham số (ví dụ RSI từ 14 thành 21) để "hợp thức hóa".

**Triệu chứng:**
- "Setup đẹp nhưng volume không cao → dùng SMA 15 thay vì SMA 20, vừa vượt"
- "RSI 14 là 68, gần 70 → thử RSI 7 được 75, đã vượt"

**Hậu quả:**
- Overfitting: chỉ báo được tuning sắc sẽ không hiệu quả trên dữ liệu mới
- Cảm tính hóa hệ thống

**Phòng tránh:**
- Cố định tham số chỉ báo trước (RSI 14, SMA 20...)
- Không thay đổi mid-trade
- Nếu muốn thay đổi → phải backtest lại toàn bộ, ghi lại trong strategy

---

## LỖI VỀ VOLUME

### Lỗi 5.1: Dùng volume làm tín hiệu chính thay vì xác nhận

**Mô tả:**
"Volume tăng → vào lệnh" mà không kiểm tra price action có breakout hay không.

**Triệu chứng:**
- "Volume vừa tăng gấp 2, vào lệnh mua ngay" (nhưng giá không có breakout rõ)

**Hậu quả:**
- Vào lệnh khi không có setup price action
- Sai lệnh cao

**Phòng tránh:**
- Volume = xác nhận, không phải tín hiệu chính
- Luôn kiểm tra price action trước (breakout/pullback/trendline)
- Nếu không có price action, không vào dù volume có cao

---

### Lỗi 5.2: Giả định volume cao = chất lượng cao (không đúng)

**Mô tả:**
Trader nghĩ "nến volume cao = strong" và dùng làm điều kiện vào lệnh chính.

**Triệu chứng:**
- "Nến close size 100 pips với volume 500M → strong bullish, vào lệnh mua"
- Nhưng sau đó giá quay đầu → nến "strong" đó là false break

**Hậu quả:**
- Volume cao không = chất lượng setup, chỉ = tham gia cao

**Phòng tránh:**
- Volume xác nhận **xu hướng giá**, không phải độc lập
- Nếu breakout + volume cao → tin cậy hơn
- Nếu volume cao nhưng không breakout → có thể tích lũy/phân phối, chờ xem

---

## LỖI VỀ TRENDLINE

### Lỗi 6.1: Ép vẽ trendline để hợp thức hóa setup đã muốn vào

**Mô tả:**
Trader thấy một setup "đẹp" nên vẽ trendline từ điểm tùy ý để "cứu cấu trúc".

**Triệu chứng:**
- "Giá này trông như sắp bounce, chọn 2 điểm hình thành trendline giảm, vào lệnh" (nhưng trendline vẽ thế nào tuỳ ý)
- Chỉnh trendline nhiều lần cho tới khi nó "đúng"

**Hậu quả:**
- Trendline không được thị trường "tôn trọng", fake signal
- Bị stop loss

**Phòng tránh:**
- Vẽ trendline **một lần, từ trước**, không chỉnh
- Nếu phải chỉnh nhiều → thị trường chưa "tôn trọng" nó → không giao dịch
- Chỉ vẽ từ 2 swing rõ ràng nhất, không vẽ từ điểm tùy ý

**Liên quan đến AI-TRADE:**
- TF_002 mục 3 "Tiêu chuẩn trendline": "Không được điều chỉnh trendline sau khi biết kết quả giá"

---

### Lỗi 6.2: Giao dịch trendline chưa đủ 3 điểm chạm

**Mô tả:**
Trader vẽ trendline từ 2 điểm sau đó vào lệnh ngay, bỏ qua yêu cầu "tối thiểu 3 điểm chạm".

**Triệu chứng:**
- "Vẽ trendline từ 2 swing, giá chạm trendline lần 2 (là điểm vẽ thứ 2) → vào lệnh"

**Hậu quả:**
- Trendline không được kiểm chứng bởi thị trường chưa
- Thường là false break

**Phòng tránh:**
- Chỉ giao dịch từ lần chạm trendline thứ 3 trở đi
- 2 điểm đầu = vẽ đường, không giao dịch

**Liên quan đến AI-TRADE:**
- TF_002 mục 4 "Số điểm chạm"

---

## LỖI VỀ QUẢN LÝ RỦI RO

### Lỗi 7.1: Không có stop loss rõ ràng

**Mô tả:**
Trader vào lệnh mà chưa xác định SL cụ thể ("sẽ đặt SL nếu giá quay lại...").

**Triệu chứng:**
- Vào lệnh rồi "chọn" SL dựa trên cảm tính
- Không tính kích thước position trước, phần tư lại từ giá entry

**Hậu quả:**
- Rủi ro không kiểm soát
- SL "drift" theo cảm tính khi lệnh đang thua

**Phòng tránh:**
- **Tính SL trước** khi vào lệnh (từ cấu trúc giá)
- Tính position size từ SL
- Đặt SL ngay khi vào, không "sẽ đặt sau"

---

### Lỗi 7.2: Dời stop loss về hướng có lợi khi lệnh thua (cấm cứng)

**Mô tả:**
Lệnh đang thua, trader dời SL để "chờ thêm" hoặc "giảm loss", thay vì chấp nhận stop.

**Triệu chứng:**
- "SL 1.0950, giá hạ 1.0952 (gần SL), dời SL xuống 1.0930 để chờ quay lại"

**Hậu quả:**
- Loss lớn hơn kế hoạch
- Thua lỗ liên tiếp

**Phòng tránh:**
- Stop loss = luật cứng, không được dời (trừ dời **lên/lên**, theo trend)
- Nếu cảm thấy không yên tâm → chủ động thoát, không dời SL

---

### Lỗi 7.3: Vào lệnh mà không biết SL sẽ bao xa

**Mô tả:**
Trader vào lệnh "quả rơi" vì "setup đẹp", kết quả SL đặt ở khoảng cách lớn → size nhỏ → lợi nhuận quá thấp.

**Triệu chứng:**
- "Breakout tại 1.1000, SL nên đặt ở 1.0950 (50 pips), size = (10k × 1%) / 50 = 200 units" (quá nhỏ)
- Nên sử dụng setup khác hoặc chộ thị trường rủi ro nhỏ hơn

**Hậu quả:**
- Hiệu quả thấp

**Phòng tránh:**
- Trước khi vào, xem khoảng cách entry-SL có hợp lý không
- Nếu SL quá xa → không vào, chờ setup tốt hơn

---

## LỖI VỀ BACKTEST

### Lỗi 8.1: Curve-fitting (tối ưu quá vừa)

**Mô tả:**
Backtest trên dữ liệu 2023, chỉnh tham số để "perfect", rồi apply trên 2024 → kết quả khác biệt lớn.

**Triệu chứng:**
- "N-bar breakout 10 được 55% win, 11 được 57%, 12 được 50% → dùng 11"
- Nhưng trên 2024 dữ liệu mới, N=11 chỉ 45% win

**Hậu quả:**
- Tham số tối ưu chỉ cho dữ liệu quá khứ
- Live trading kém hơn expectation

**Phòng tránh:**
- Backtest trên dữ liệu lâu dài (tối thiểu 1-2 năm)
- Chia dữ liệu: train (2022-2023) + test (2024) → kiểm tra stability
- Không chỉnh tham số để "fit" dữ liệu quá khứ

---

### Lỗi 8.2: Quá ít lệnh để kết luận (< 30 lệnh)

**Mô tả:**
Backtest chỉ 5-10 lệnh rồi "xác nhận" strategy tốt.

**Triệu chứng:**
- "Chạy TF_001 trên 1 tháng, 8 lệnh, 100% thắng → strategy cực tốt"
- Nhưng sample size quá nhỏ, cơ hội 100% thắng cao

**Hậu quả:**
- Kết quả không có ý nghĩa thống kê
- Live trading khác xa

**Phòng tránh:**
- Tối thiểu 30-50 lệnh để kết quả đáng tin
- Tối thiểu 100+ lệnh để rất đáng tin
- Kéo dài backtest hoặc thêm thị trường nếu quá ít lệnh

---

## LỖI VỀ CẢMTÍNH / KỶ LUẬT

### Lỗi 9.1: FOMO (Fear of Missing Out) — vào lệnh thiếu điều kiện vì sợ bỏ lỡ

**Mô tả:**
Giá vừa breakout, trader sợ "tàu sắp đi" nên vào lệnh mà thiếu confirm (chưa có pullback + reaction).

**Triệu chứng:**
- "Breakout vừa xảy ra, chờ pullback thì sợ tàu chạy mất, vào luôn"

**Hậu quả:**
- Vào ngay tại breakout (SL lớn) thay vì pullback (SL nhỏ)
- Tỷ lệ lời/lỗ xấu

**Phòng tránh:**
- Ghi nhớ: có xu hướng mạnh, cơ hội pullback luôn có
- Không sợ bỏ lỡ — bỏ lỡ 1 lệnh tốt < vào 1 lệnh xấu
- Tuân thủ quy tắc, không vào vì FOMO

---

### Lỗi 9.2: Revenge trading — vào lệnh tích cực sau khi thua

**Mô tả:**
Thua 1 lệnh, trader vào lệnh tiếp theo "quả rơi" vì muốn "gỡ" hoặc "tìm back".

**Triệu chứng:**
- "Vừa bị stop loss, vào lệnh tiếp theo với size lớn hơn để 'gỡ'"
- "Thua hôm nay, phải thắng lại chiều nay"

**Hậu quả:**
- Thua thêm nhiều
- Drawdown nhanh

**Phòng tránh:**
- Chấp nhận từng lệnh độc lập (không liên quan emotional)
- Nếu cảm thấy "nóng" → rút lui, không giao dịch
- Ghi log, đánh giá lệnh thua, cải thiện → không gỡ

---

### Lỗi 9.3: Confirmation bias — tìm lý do để cứu setup đã muốn vào

**Mô tả:**
Trader muốn vào lệnh nào đó, sau đó tìm "lý do" để cứu setup, bỏ qua các flag đỏ.

**Triệu chứng:**
- "Setup này cần 3 điểm trendline, nhưng chỉ có 2 → nhưng trend cứng nên vào"
- "Volume không đủ → nhưng nến quá đẹp nên vào"

**Hậu quả:**
- Sai lệnh cao
- Không tuân thủ quy tắc

**Phòng tránh:**
- Kiểm tra setup theo **checklist chính xác**, không "cải thiện"
- Nếu thiếu 1 điều kiện → không vào (không ngoại lệ)
- Viết checklist ra giấy/screen, tick từng cái, không bỏ bất kỳ cái nào

---

## BẢNG TÓMS TẮT LỖI & PHÒNG TRÁNH

| # | Lỗi | Nguy hiểm | Phòng tránh |
|---|---|---|---|
| 1.1 | Dự đoán đảo chiều | Vào ngược trend, SL liên tiếp | Reaction, không prediction |
| 1.2 | Vào quá sớm breakout | False break, size lớn | Chờ close vượt, không chạm |
| 2.1 | Nhầm false break | Vào sai signal | CHoCH = phá chuỗi, không false break đơn |
| 2.2 | Swing definition sai | Quá nhiều/ít signal | Định rõ N, cố định |
| 3.1 | Pullback quá sâu | False break | Close không vượt = false |
| 3.2 | Cắt lời sớm | Bỏ move lớn | Dời SL, không TP % |
| 4.1 | RSI 70/30 signal | Vào ngược trend | RSI xác nhận, không signal |
| 4.2 | Thay tham số tuỳ ý | Overfitting | Cố định, backtest toàn bộ |
| 5.1 | Volume tín hiệu chính | Sai setup | Volume xác nhận, không chính |
| 5.2 | Volume = chất lượng | False signal | Volume = tham gia, không quality |
| 6.1 | Ép trendline | Fake signal | Vẽ 1 lần, không chỉnh |
| 6.2 | Giao dịch trendline 2 điểm | Chưa verify | Chờ điểm 3 |
| 7.1 | Không SL rõ | Rủi ro wild | Tính SL trước |
| 7.2 | Dời SL xuống | Loss lớn hơn | SL = cứng, không dời xuống |
| 7.3 | SL quá xa | Size quá nhỏ | Check entry-SL trước, không vào nếu quá |
| 8.1 | Curve-fit | Overfitting | Train+Test split, out-of-sample |
| 8.2 | Quá ít sample | Luck, không reality | Tối thiểu 30-100 lệnh |
| 9.1 | FOMO | Vào sai time | Tin cơ hội lúc nào cũng có |
| 9.2 | Revenge trading | Thua thêm | Thoát khi nóng, không gỡ |
| 9.3 | Confirmation bias | Sai checklist | Danh sách cứng, không "cải" |


# Báo Cáo Research Phase 01 — Nghiên Cứu Toàn Diện Các Trường Phái Giao Dịch

**Ngày báo cáo:** 2026-07-31  
**Giai đoạn:** 1 (Knowledge Base & Research Framework)  
**Trạng thái:** ✅ Hoàn tất

---

## 1. NHỮNG GÌ ĐÃ NGHIÊN CỨU

### A. Khảo sát 12 Trường Phái Giao Dịch Chính

Đã phân tích đầy đủ 12 trường phái theo cách chuẩn hóa:

1. **Trend Following** — Theo xu hướng, không bắt đáy/đỉnh
2. **Price Action** — Phân tích hành vi giá thô, không chỉ báo
3. **Market Structure** — Cấu trúc swing high/low, HH/HL, BOS/CHoCH
4. **Smart Money Concept (SMC)** — Giả định "người có tiền" để lại dấu vết
5. **Wyckoff** — 4 giai đoạn: Accumulation, Mark-up, Distribution, Mark-down
6. **Dow Theory** — Nền tảng: thị trường có xu hướng, 3 mức, volume xác nhận
7. **Turtle Trading** — Breakout N-bar + ATR-based stop, cực đơn giản
8. **Market Wizards Lessons** — Tổng hợp nguyên tắc từ trader thành công
9. **Mark Minervini (Trend Template)** — EMA 150/200, pullback vào EMA 50, volume profile
10. **Al Brooks (Price Action + Context)** — Price action với bối cảnh trend lớn
11. **Volume Analysis** — Khối lượng xác nhận breakout, phát hiện false break
12. **Auction Market Theory (AMT)** — Thị trường là cuộc đấu giá, volume profile = fair value

**Mỗi trường phái được phân tích:**
- Triết lý cốt lõi
- Ưu điểm & nhược điểm
- Điều kiện hoạt động tốt/kém
- Khả năng tự động hóa (dễ hay khó code)
- Độ khách quan (phụ thuộc cảm tính hay không)
- Độ ổn định trên nhiều thị trường
- Phù hợp với ML/RL hay không

### B. Bảng So Sánh Chi Tiết

Tạo bảng so sánh theo 10 tiêu chí:

1. **Khả năng tự động hóa** — Turtle Trading & Minervini (cao), Al Brooks & SMC (thấp)
2. **Độ khách quan** — Minervini & Turtle (rất cao), SMC & Al Brooks (thấp)
3. **Phụ thuộc cảm tính** — Turtle (rất thấp), SMC (cao)
4. **Số lượng quy tắc cần thiết** — Turtle (3-4), Al Brooks (15-25)
5. **Khả năng Machine Learning** — Price Action & Minervini (cao), Dow Theory (thấp)
6. **Khả năng Reinforcement Learning** — Trend Following & Turtle (cao), SMC (thấp)
7. **Độ ổn định nhiều thị trường** — Trend Following & Turtle (cao), Minervini (chỉ stock)
8. **Hiệu suất với các timeframe** — Turtle & Trend Following (tất cả), Minervini (D1-W1)
9. **Khối lượng dữ liệu cần** — Turtle (vừa), Auction Market (rất lớn)
10. **Độ đơn giản logic** — Turtle & Trend Following (rất cao), Al Brooks & Smart Money (thấp)

### C. Kiến Trúc AI Trading Được Đề Xuất

**Lõi chính:**
- **Trend Following + Market Structure** (xác định xu hướng + phát hiện BOS/CHoCH)

**Lớp xác nhận:**
- **Volume Analysis** (breakout volume > SMA)
- **Price Action** (breakout quality nến, pullback quality)
- **EMA bias** (E200 làm bộ lọc xu hướng)

**Nền tảng quản lý rủi ro:**
- **Market Wizards principles** (cắt lỗ nhanh, để lợi chạy, kỷ luật)

**Không dùng:**
- SMC, Wyckoff, Al Brooks → quá phức tạp / cần kỹ năng chủ quan cao
- Reversal trading, RSI 70/30 → trái triết lý Reaction/Trend Following

### D. Roadmap 7 Giai Đoạn

Xây dựng roadmap chi tiết từ Knowledge Base (Phase 1) tới Live Trading (Phase 7):
- Phase 1: Knowledge Base ✅ (hoàn tất)
- Phase 2: Rule Engine (4-6 tuần)
- Phase 3: Backtest (4-8 tuần)
- Phase 4: Paper Trade (4-12 tuần)
- Phase 5: AI Scoring (4-8 tuần)
- Phase 6: Machine Learning (6-16 tuần)
- Phase 7: Live Trading (phụ thuộc Project Owner)

---

## 2. TÀI LIỆU ĐÃ TẠO

### Thư mục Knowledge
- ✅ `RESEARCH_SUMMARY.md` — Tóm tắt 12 trường phái (1200+ dòng)
- ✅ `TRADING_SCHOOL_COMPARISON.md` — Bảng so sánh chi tiết 10 tiêu chí (500+ dòng)
- ✅ `AI_DESIGN_PRINCIPLES.md` — Nguyên tắc thiết kế AI Trading, kiến trúc đề xuất (600+ dòng)
- ✅ `BEST_PRACTICES.md` — 6 lĩnh vực best practices, 17 nguyên tắc vàng (800+ dòng)
- ✅ `COMMON_FAILURES.md` — 9 nhóm lỗi phổ biến + bảng tóm tắt (600+ dòng)

### Thư mục gốc
- ✅ `ROADMAP.md` — Lộ trình 7 giai đoạn phát triển (600+ dòng)

### Thư mục reports (tài liệu này)
- ✅ `RESEARCH_PHASE_01.md` — Báo cáo hoàn tất Phase 01

**Tổng nội dung tạo:** ~4700 dòng tài liệu mới

---

## 3. NHỮNG GÌ CÒN THIẾU / CẦN LÀM TIẾP

### Chưa hoàn tất:

1. **Code Rule Engine (Phase 2)**
   - Cần viết: `src/rules/*.py` — các module Python để lập trình logic
   - Cần unit test cho mỗi module
   - Ước tính 4-6 tuần

2. **Backtest thực tế (Phase 3)**
   - Chưa có dữ liệu giá lịch sử từ sàn
   - Chưa chạy backtest cho TF_001 hay TF_002
   - Cần chọn cặp/asset, timeframe, khoảng thời gian cụ thể
   - Ước tính 4-8 tuần (khi có code + dữ liệu)

3. **Xác định các tham số cụ thể**
   - `risk/RISK_POLICY.md`: chưa chốt % rủi ro/lệnh, % drawdown tối đa, số lệnh thua liên tiếp
   - `strategies/TF_001.md`, `TF_002.md`: chưa chốt N (số nến breakout), ATR multiplier, EMA period
   - Cần Project Owner confirm, hoặc có thể backtest để tìm optimal

4. **Dữ liệu và nguồn**
   - Chưa xác định sàn giao dịch chính (forex broker, crypto exchange, stock broker)
   - Chưa có pipeline để fetch dữ liệu giá
   - Ước tính 2-3 tuần để setup

5. **Kiểm chứng các giả thuyết**
   - 5 giả thuyết trong `research/HYPOTHESES.md` chưa được kiểm chứng bằng backtest
   - Cần chạy backtest để confirm/reject

### Không cần làm (theo giới hạn Project):

- ❌ Không connect API tài khoản thật (Phase 7 mới làm)
- ❌ Không viết bot đặt lệnh thật (Phase 7 mới làm)
- ❌ Không huấn luyện model (Phase 6 mới làm)

---

## 4. NHỮNG RỦI RO / CẤM KỴ ĐƯỢC XÁC ĐỊNH

### Rủi ro kỹ thuật:

1. **Overfitting** — Backtest tối ưu quá vừa với dữ liệu quá khứ
   - Phòng tránh: kiểm tra out-of-sample, không chỉnh tham số tùy ý

2. **Curve-fitting** — Dữ liệu/dòng code không đặc trưng cho thực tế
   - Phòng tránh: backtest trên nhiều pair/timeframe, đủ sample size (100+ lệnh)

3. **Selection bias** — Chọn chỉ những pair/timeframe mà strategy tốt
   - Phòng tránh: test trên tất cả pair mục tiêu, không cherry-pick

4. **Logic bug** — Quy tắc được code sai so với intention
   - Phòng tránh: unit test, review code, so sánh backtest với hand-calculated

### Rủi ro về triết lý:

1. **Prediction bias** — "Cảm thấy" setup sắp breakout nên vào trước
   - Phòng tránh: reaction-based strictly, chờ khi nào giá đã close vượt

2. **Reversal fishing** — Cố vào lệnh ngược trend dựa trên "cảm giác"
   - Phòng tránh: trend following strictly, chỉ chợp BOS theo hướng trend

3. **Confirmation bias** — Tìm lý do để cứu setup đã muốn vào
   - Phòng tránh: checklist cứng, không ngoại lệ, ghi log mọi quyết định

### Rủi ro về quản lý rủi ro:

1. **Rủi ro không kiểm soát** — Không có SL cụ thể
   - Phòng tránh: bắt buộc tính SL trước entry, công thức position sizing

2. **Dời SL xuống** — Chấp nhận lỗ lớn hơn kế hoạch
   - Phòng tránh: SL = luật cứng, không dời xuống (chỉ dời lên)

3. **Drawdown vượt** — Không có kill switch
   - Phòng tránh: kill switch bắt buộc, tự động kích hoạt khi điều kiện met

4. **Không tuân thủ quy tắc** — Vào lệnh "quả rơi" khi không đủ điều kiện
   - Phòng tránh: Project Owner/AI phải enforce quy tắc, không ngoại lệ

### Rủi ro tài chính/đạo đức:

1. **Thua lỗ thực tế** — Backtest không đảm bảo live trading thắng
   - Phòng tránh: bắt đầu small (paper trade, small account), thử dần, không all-in

2. **Slippage/Spread không tính** — Giả định backtest không thực tế
   - Phòng tránh: backtest thêm slippage margin (2-3% loss), paper trade để xác nhận

3. **Bias tiền tệ** — Áp dụng chiến lược trên asset khác mà chưa backtest
   - Phòng tránh: backtest riêng từng asset, không giả định "tất cả giống nhau"

4. **Advertise chiến lược sai** — "AI-TRADE guaranteed 70% win"
   - Phòng tránh: KHÔNG khẳng định bất kỳ chiến lược nào "chắc chắn" thắng, ghi disclaimer rõ

---

## 5. NHỮNG QUYẾT ĐỊNH ĐÃ CHỐT

### Từ DECISIONS.md (cũ):
- ✅ Trường phái: Reaction (không prediction), Trend Following
- ✅ Price Action/Market Structure là chính
- ✅ Volume/EMA/RSI chỉ xác nhận
- ✅ Quản lý rủi ro quan trọng hơn tỷ lệ thắng
- ✅ Không kết nối tài khoản thật, không bot lệnh thật, không tự huấn luyện model

### Từ Phase 01 này:
- ✅ **Kiến trúc được chọn:** Trend Following + Market Structure + Volume + Price Action + Market Wizards Risk Management
- ✅ **Không chọn:** SMC, Wyckoff, Al Brooks, Pure Minervini → quá phức tạp/chủ quan
- ✅ **Roadmap 7 giai đoạn** từ Knowledge tới Live
- ✅ **7 nguyên tắc thiết kế:**
  1. Reaction, không prediction
  2. Trend Following, không reversal
  3. Price Action/Market Structure là chính
  4. Volume/EMA xác nhận, không chính
  5. Quản lý rủi ro > tỷ lệ thắng
  6. Không tổng quát hóa giữa market/timeframe
  7. AI không tự quyết định rủi ro

---

## 6. BƯỚC TIẾP THEO (PRIORITY)

### Urgent (1-2 tuần):

1. **Project Owner xác nhận:**
   - ✅ Kiến trúc (Trend Following + Market Structure + Volume) OK?
   - ✅ Roadmap 7 giai đoạn, thời gian ước tính OK?
   - ✅ 7 nguyên tắc thiết kế OK?

2. **Chốt tham số trong RISK_POLICY.md:**
   - % rủi ro/lệnh (ví dụ 1% hoặc 2%)
   - % rủi ro danh mục (ví dụ 3% hoặc 5%)
   - Số lệnh thua liên tiếp → kill switch (ví dụ 3 hoặc 5)
   - % drawdown tối đa → kill switch (ví dụ 2% hoặc 3%)

3. **Chốt tham số trong STRATEGY (TF_001, TF_002):**
   - N-bar breakout (ví dụ 10 hoặc 15)
   - ATR multiplier cho SL (ví dụ 1.5 hoặc 2)
   - EMA period (ví dụ 200)
   - Volume SMA period (ví dụ 20)

### Medium (2-4 tuần):

4. **Chuẩn bị dữ liệu:**
   - Chọn 2-3 cặp tiền tệ / thị trường chính (ví dụ EUR/USD, GBP/USD, BTC/USDT)
   - Chọn 1-2 timeframe chính (ví dụ D1, H4)
   - Lấy dữ liệu lịch sử 1-2 năm

5. **Bắt đầu Phase 2 (Rule Engine):**
   - Viết code Python lập trình các quy tắc
   - Unit test

### Long-term (4-8 tuần):

6. **Phase 3 (Backtest):**
   - Chạy backtest TF_001 + TF_002 trên dữ liệu được chọn
   - Ghi log chi tiết, phân tích kết quả

7. **Tối ưu hóa:**
   - Nếu backtest pass → đi Phase 4 (Paper Trade)
   - Nếu fail → điều chỉnh rule/tham số, backtest lại

---

## 7. NHỮNG THỨ KHÔNG NÊN LÀM

| ❌ Không | ✅ Thay vào đó |
|---|---|
| Bỏ qua giai đoạn backtest, vào live ngay | Backtest trước, verify trên paper trade, rồi mới live |
| Dùng SMC/Wyckoff/Al Brooks ngay | Dùng Trend Following + Market Structure trước, expand sau |
| Vào lệnh dựa trên "cảm giác" | Chỉ vào khi điều kiện checklist pass |
| Thay đổi % rủi ro "theo setup" | % rủi ro cố định, không đàm phán |
| Dời SL xuống khi thua | SL = luật cứng, chỉ dời lên theo trend |
| Curve-fit backtest quá | Out-of-sample test, không overfitting |
| Khẳng định "chắc chắn thắng" | Ghi disclaimer, không guarantee |
| Vào multiple setup cùng lúc không quản lý portfolio | Kill switch + portfolio risk limit bắt buộc |
| Ignore paper trade kết quả | Paper trade bắt buộc 2-4 tuần trước live |

---

## 8. NGƯỜI LIÊN QUAN VÀ TRÁCH NHIỆM

| Vai trò | Trách nhiệm |
|---|---|
| **Project Owner** | Confirm kiến trúc, chốt tham số, xác nhận chuyển giai đoạn |
| **Lead Developer (Phase 2-3)** | Code rule engine, backtest, debug |
| **Data Engineer** | Chuẩn bị dữ liệu, pipeline, API |
| **AI/LLM (Phase 5)** | Phân tích setup, phản biện, cảnh báo |
| **ML Engineer (Phase 6)** | Optimize tham số, train model |
| **Trader/Monitor (Phase 7)** | Paper trade, live trade, log, monitor |

---

## 9. KẾT LUẬN

**Phase 01 Research đã cung cấp:**
- ✅ Khảo sát 12 trường phái giao dịch chi tiết
- ✅ Bảng so sánh định lượng theo 10 tiêu chí
- ✅ Kiến trúc AI Trading được đề xuất (Trend Following + Market Structure + Volume)
- ✅ 7 nguyên tắc thiết kế bắt buộc
- ✅ Roadmap 7 giai đoạn từ Knowledge tới Live
- ✅ Best practices (17 nguyên tắc vàng)
- ✅ Common failures (20+ lỗi phổ biến + phòng tránh)
- ✅ Rủi ro được xác định và cách phòng tránh

**Hệ thống được thiết kế để:**
1. **Tự động hóa tối đa** — Quy tắc khách quan, dễ code
2. **Giảm thiểu cảm tính** — Luật cứng, no emotion
3. **Quản lý rủi ro tuyệt đối** — Kill switch, position sizing từ công thức
4. **Có thể kiểm chứng** — Backtest + paper trade + live nhỏ trước
5. **Tuân thủ triết lý Reaction** — Phản ứng với dữ liệu, không dự đoán

**Sẵn sàng chuyển sang Phase 2 khi:**
- ✅ Project Owner confirm kiến trúc & roadmap
- ✅ Chốt tham số rủi ro & strategy
- ✅ Dữ liệu chuẩn bị sẵn

---

**Báo cáo này được tạo bởi:** Chief Research Officer (AI-TRADE)  
**Ngày hoàn tất:** 2026-07-31  
**Status:** ✅ Phase 01 Complete, Ready for Phase 02

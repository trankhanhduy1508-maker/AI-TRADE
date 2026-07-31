# RULE ENGINE PHASE — Audit Report

**Giai đoạn:** Phase 02 (Thiết kế Rule Engine)

**Ngày hoàn tất:** 2026-07-31

**Tài liệu chính:** 
- `RULE_ENGINE.md`
- `rule_engine/RULE_001_TREND.md` đến `RULE_010_EXIT.md`
- `rule_engine/RULE_CONFLICTS.md`
- `rule_engine/RULE_ENGINE_CHECKLIST.md`

---

## I. Tóm tắt công việc đã làm

### 1.1 Thiết kế Rule Engine chính
- ✅ Kiến trúc tổng thể (các thành phần, luồng xử lý).
- ✅ Decision Flow tuần tự 10 bước (Trend → Structure → Breakout → Pullback → Volume → R/R → SL → Portfolio → Score → Signal).
- ✅ Hệ thống chấm điểm 100 điểm (10 rule với điểm max khác nhau).
- ✅ Điều kiện reject cứng (6 điều kiện không thương lượng).
- ✅ Thứ bậc ưu tiên rule khi xung đột (Priority ranking rõ ràng).

### 1.2 Thiết kế 10 Rule
- ✅ RULE_001_TREND.md — Xu hướng (HH/HL, LH/LL).
- ✅ RULE_002_MARKET_STRUCTURE.md — Cấu trúc thị trường hợp lệ.
- ✅ RULE_003_BREAKOUT.md — Breakout TRUE/WEAK/NO (body ratio, close vượt).
- ✅ RULE_004_PULLBACK.md — Pullback VALID/WAITING/FALSE_BREAK.
- ✅ RULE_005_VOLUME.md — Volume xác nhận (STRONG/NORMAL/WEAK/POOR).
- ✅ RULE_006_RSI.md — RSI bias (BULLISH/NEUTRAL/BEARISH).
- ✅ RULE_007_EMA.md — EMA bias (UP/NEUTRAL/DOWN).
- ✅ RULE_008_RISK.md — Risk/Reward (ACCEPTABLE/FAIR/UNACCEPTABLE).
- ✅ RULE_009_LIQUIDITY.md — Thanh khoản (GOOD/FAIR/POOR).
- ✅ RULE_010_EXIT.md — Exit rules (SL hit, False break, Structure break, Trail, Hold, Take profit).

### 1.3 Hỗ trợ tài liệu
- ✅ RULE_CONFLICTS.md — 11 tình huống xung đột + giải pháp.
- ✅ RULE_ENGINE_CHECKLIST.md — QA checklist 11 mục + 10 section.
- ✅ Cập nhật CURRENT_STATUS.md (Rule Engine Phase).
- ✅ Cập nhật DECISIONS.md (Quyết định Rule Engine + tham số chưa chốt).

---

## II. Kiểm tra Tính toàn vẹn Rule Engine

### 2.1 Decision Flow Logic
**Status: ✅ OK**

- ✅ 10 bước tuần tự, mỗi bước có reject/wait/pass condition rõ ràng.
- ✅ Các điều kiện reject cứng không mập mờ.
- ✅ Flow có thể được lập trình thành code (không có phần chủ quan).
- ⚠️ **Nhận xét:** Flow phụ thuộc nhiều vào tham số (body ratio 60%, volume 150% SMA, v.v.) — tất cả cần được chốt cụ thể trước backtest.

### 2.2 Scoring System
**Status: ⚠️ Cần chú ý**

**Tốt:**
- ✅ Thang điểm rõ ràng 0-100, 10 rule có điểm max khác nhau (hợp lý).
- ✅ Ngưỡng vào lệnh >= 80 là đề xuất có cơ sở (không quá cao, không quá thấp).
- ✅ Các bảng điểm chi tiết cho từng rule (25 cho Trend, 20 cho Structure, v.v.).

**Cần cải tiến:**
- ⚠️ **Ngưỡng 80 là giả thuyết, chưa kiểm chứng bằng backtest.**
  - Nếu backtest cho thấy 80 quá cao → sẽ bỏ lỡ nhiều setup tốt.
  - Nếu backtest cho thấy 80 quá thấp → sẽ vào quá nhiều setup yếu.
  - **Cần backtest 1-2 năm dữ liệu để xác nhận ngưỡng này.** Có thể phải điều chỉnh tới 75, 85, hay thậm chí 70.

- ⚠️ **Sự chênh lệch điểm giữa các rule có hợp lý không?**
  - Ví dụ: Trend 25 điểm, Volume 10 điểm, RSI 5 điểm → tỷ lệ hợp lý không?
  - Backtest có thể cho thấy Volume nên cao hơn hay thấp hơn.

- ⚠️ **Cách tính điểm mỗi rule có consistent không?**
  - Ví dụ: Breakout 15 điểm (TRUE), nhưng nếu body 50% (weak) thì giảm xuống 10 điểm.
  - Điều này hợp lý, nhưng cần backtest verify.

### 2.3 10 Rule — Tính khách quan
**Status: ✅ Phần lớn OK**

| Rule | Khách quan | Ghi chú |
|---|---|---|
| RULE_001 Trend | 95% ✅ | HH/HL so sánh mộc mạc, rõ ràng. |
| RULE_002 Structure | 95% ✅ | Swing high/low định nghĩa clear, không mơ hồ. |
| RULE_003 Breakout | 85% ⚠️ | Body ratio 60% là tham số, cần backtest xác nhận. |
| RULE_004 Pullback | 80% ⚠️ | Định nghĩa "hôi quá sâu" bao nhiêu % có phần chủ quan. |
| RULE_005 Volume | 95% ✅ | SMA so sánh là mộc mạc, tuy nhiên SMA period (20?) cần chốt. |
| RULE_006 RSI | 90% ✅ | RSI standard, nhưng phân kỳ khó định nghĩa chính xác (10% chủ quan). |
| RULE_007 EMA | 95% ✅ | So sánh giá vs EMA rõ ràng, nhưng EMA period chưa chốt. |
| RULE_008 Risk | 98% ✅ | R/R tính toán mộc mạc, nhưng R/R min 1.5 chưa chốt. |
| RULE_009 Liquidity | 85% ⚠️ | Spread/depth threshold (2 pip, 5 pip) là quy ước, có phần tùy thị trường. |
| RULE_010 Exit | 80% ⚠️ | Trailing SL, False Break detection có phần cần diễn giải, tham số chưa chốt. |

**Kết luận:** Phần lớn rule khách quan (80-98%). Các rule yếu là RULE_004, RULE_010, và một số tham số chưa chốt.

### 2.4 Rule Conflicts — Giải quyết xung đột
**Status: ✅ Toàn diện**

- ✅ Liệt kê 11 tình huống xung đột tiềm năng.
- ✅ Mỗi xung đột có priority rank rõ ràng (Price Action > Risk > Volume > Indicators).
- ✅ Hành động giải quyết cụ thể (reject vs giảm điểm).
- ✅ Không có xung đột "bất khả giải" — tất cả có hướng giải quyết.

**Nhận xét:**
- ✅ Priority ranking (Price Action/Structure > Risk > Volume > Indicators) phù hợp với triết lý Trend Following.
- ✅ Quy tắc "giảm điểm thay vì reject cứng khi chỉ báo không hỗ trợ" cân bằng tốt.

### 2.5 Checklist QA
**Status: ✅ Toàn diện**

- ✅ 11 mục bắt buộc cho mỗi rule (Tên, Mục đích, Input/Output, Điều kiện, v.v.).
- ✅ 10 section kiểm tra (Cấu trúc, Logic, Dependency, Khách quan, v.v.).
- ✅ Quy trình QA chi tiết (7 bước từ đọc file tới phê duyệt).
- ✅ Mẫu báo cáo QA chuẩn.

**Nhận xét:** Checklist rất chi tiết, có thể serve từng rule hiệu quả.

---

## III. Những vấn đề tìm được

### 3.1 Những lỗi tiềm ẩn / Thiếu sót

#### A. Tham số chưa chốt — ảnh hưởng lớn đến hiệu suất

**Severity: HIGH** ⚠️

| Tham số | File | Tình trạng | Tác động |
|---|---|---|---|
| Body ratio breakout | RULE_003 | Đề xuất 60%, chưa chốt | Ảnh hưởng reject/accept breakout |
| SMA period volume | RULE_005 | Đề xuất 20, chưa chốt | Ảnh hưởng xác nhận volume |
| EMA period | RULE_007 | Không chốt | Ảnh hưởng bias filter |
| R/R minimum | RULE_008 | Đề xuất 1.5, chưa chốt | Ảnh hưởng accept/reject risk |
| Scoring threshold | RULE_ENGINE.md | Đề xuất 80, chưa chốt | Ảnh hưởng accept/reject setup |
| Swing period (N) | RULE_001, 002 | Không chốt | Ảnh hưởng xác định HH/HL |
| % rủi ro/lệnh | risk/RISK_POLICY.md | Chưa chốt | Ảnh hưởng khối lượng lệnh |

**Hành động:** Tất cả tham số này PHẢI được Project Owner xác nhận trước khi chạy backtest, không thể để giả định được hết.

---

#### B. Rule không thể backtest chính xác — do thiếu dữ liệu hoặc định nghĩa mơ hồ

**Severity: MEDIUM** ⚠️

| Rule | Vấn đề | Hành động |
|---|---|---|
| RULE_004 Pullback | Định nghĩa "hôi quá sâu" bao nhiêu % là mờ | Cần lập trình cụ thể (ví dụ: close < 50% breakout distance) |
| RULE_006 RSI | Phân kỳ khó detect tự động | Cần define rõ công thức phân kỳ (ví dụ: giá HH nhưng RSI HL) |
| RULE_010 Exit | Trailing SL theo "structure mới" mơ hồ | Cần code rõ: trailing = swing low/high mới + ATR offset |
| RULE_009 Liquidity | Spread/depth threshold tùy thị trường | Cần define per-pair/per-market, không chung chung |

**Hành động:** Sau khi Project Owner chốt tham số, cần bổ sung công thức/pseudocode cụ thể cho các rule này.

---

#### C. Phụ thuộc dữ liệu chưa định nghĩa

**Severity: MEDIUM** ⚠️

| Rule | Dữ liệu cần | Tình trạng |
|---|---|---|
| RULE_005 Volume | Volume tại từng timeframe, nguồn dữ liệu | Chưa xác định (crypto có nhiều sàn, dữ liệu khác) |
| RULE_009 Liquidity | Spread, order book depth | Chỉ có khi connected tới broker real-time; backtest khó |
| RULE_010 Exit | Intra-bar price (high tick-by-tick) | Backtest chỉ có OHLC, khó detect SL chính xác |

**Hành động:** Cần xác định:
1. Dữ liệu sẽ lấy từ nguồn nào (sàn gì, broker nào).
2. Khi backtest, thay thế dữ liệu nào (ví dụ: assume spread = 2 pip).

---

#### D. Không có rule cho ... (Thiếu rule)

**Severity: LOW** 🟢

Kiểm tra xem có khoảng trống logic nào không:

- ✅ Trend detection: Có (RULE_001).
- ✅ Structure validation: Có (RULE_002).
- ✅ Breakout check: Có (RULE_003).
- ✅ Pullback follow: Có (RULE_004).
- ✅ Volume confirm: Có (RULE_005).
- ✅ Overbought/oversold: Có (RULE_006 RSI).
- ✅ Trend bias filter: Có (RULE_007 EMA).
- ✅ Risk management: Có (RULE_008).
- ✅ Liquidity: Có (RULE_009).
- ✅ Exit signals: Có (RULE_010).

**Kết luận:** Không thiếu rule chính nào. Rule Engine cover được hành trình vào-giữ-thoát lệnh.

---

#### E. Rule trùng lặp hoặc overlap

**Severity: LOW** 🟢

Kiểm tra: Có rule nào thực chất làm việc tương tự không?

- RULE_005 Volume + RULE_003 Breakout: Không trùng, Volume là xác nhận của Breakout.
- RULE_006 RSI + RULE_007 EMA: Khác nhau (RSI là oscillator, EMA là trend filter).
- RULE_008 Risk + RULE_004 Pullback: Khác nhau (Risk là risk/reward, Pullback là cấu trúc).

**Kết luận:** Không có rule nào trùng lặp.

---

### 3.2 Những điểm dễ gây Overfitting

**Severity: MEDIUM-HIGH** ⚠️

| Vấn đề | Nơi | Cách tránh |
|---|---|---|
| **Body ratio breakout (60%)** | RULE_003 | Chốt từ backtest 1-2 năm, lock cứng, không điều chỉnh |
| **Volume threshold (150% SMA20)** | RULE_005 | Chốt từ backtest, không flex per-pair |
| **R/R minimum (1.5)** | RULE_008 | Chốt từ backtest, không nới lỏng nếu score thấp |
| **Scoring threshold (80)** | RULE_ENGINE.md | Chốt từ backtest, không chỉnh sau 1-2 lệnh thua |
| **Trailing SL offset (ATR multiplier)** | RULE_010 | Chốt từ backtest, không thay đổi tuỳ lệnh |
| **EMA period** | RULE_007 | Chốt 1 period, dùng cho tất cả pair (không lạc vào "best-fit" per pair) |
| **Pullback depth threshold** | RULE_004 | Nếu dùng %, lock %, không thay đổi |

**Kết luận:** Overfitting risk là MEDIUM-HIGH. Cần kỷ luật chặt khi backtest — không được chốt tham số "đẹp nhất" cho 1 pair, rồi apply cho tất cả.

---

## IV. Đề xuất Cải tiến

### 4.1 Ngay lập tức (Trước khi viết code)

1. **Chốt tất cả tham số** — Tạo file `rule_engine/PARAMETERS_FINAL.md` sau khi Project Owner confirm:
   - Body ratio, SMA period, EMA period, R/R min, Score threshold, Swing period, Risk %.
   - Ghi rõ "Chốt lần cuối ngày XX/XX/2026, locked, không được thay đổi".

2. **Bổ sung công thức pseudocode cho các rule mơ hồ:**
   - RULE_004: `if close < (entry + (entry - SL) * 0.5): false_break()`
   - RULE_006: `if price_HH but RSI_HL: divergence_bearish()`
   - RULE_010: `trail_SL = new_swing_low + ATR * 1.5`

3. **Tạo file mapping strategy ↔ rule:**
   - `rule_engine/STRATEGY_RULE_MAPPING.md`: Mỗi chiến lược (TF_001, TF_002) dùng rule nào, điều kiện entry/exit cụ thể nào.
   - Ví dụ: TF_001 dùng RULE_001-009, entry = Pullback + nến xác nhận, exit = Close phase ngược.

4. **Mock backtest 1 tuần:**
   - Chạy Rule Engine bằng tay trên 100 setup lịch sử (1 tuần dữ liệu).
   - Verify: Logic chạy đúng? Output hợp lý? Có bug?
   - Đây là "sanity check" trước khi code.

---

### 4.2 Khi viết code (Phase 3)

1. **Unit test cho từng rule:**
   - Test RULE_001 với 10 scenarios (trend UP/DOWN/NEUTRAL, yếu/mạnh).
   - Test RULE_003 với breakout TRUE/WEAK/NO.
   - Coverage target: 90%+.

2. **Integration test:**
   - Chạy full Decision Flow trên 1000 setup giả định.
   - Verify: Setup reject ở bước nào, score tính đúng không?

3. **Backtest standard:**
   - Tuân theo `backtests/BACKTEST_STANDARD.md`.
   - Chạy trên ≥ 1-2 năm dữ liệu, ≥ 100 setup.
   - Ghi kỹ: % setup TRADE vs WAIT/REJECT, win rate, R/R trung bình.

---

### 4.3 Khi backtest (Phase 3-4)

1. **Verify ngưỡng Scoring (80):**
   - Backtest với threshold 70, 75, 80, 85, 90.
   - Xem cái nào cho Sharpe ratio tốt nhất (balance setup quantity vs quality).
   - Adjust ngưỡng nếu cần.

2. **Verify tham số từng rule:**
   - Backtest body ratio 50%, 55%, 60%, 65%, 70%.
   - Volume SMA period 15, 20, 25, 30.
   - Xem tham số nào cho win rate + R/R tốt nhất (không phải "tight nhất").

3. **Walk-forward test:**
   - Train trên 1 năm, test trên 6 tháng tiếp.
   - Repeat 4 lần (2 năm dữ liệu, 4 windows).
   - Verify: Tham số có stable không, hay chỉ tốt ở 1 window?

---

### 4.4 Documentation cần bổ sung

1. **`rule_engine/PARAMETERS_FINAL.md`** — Tất cả tham số sau khi chốt (ngăn "chưa chốt").
2. **`rule_engine/STRATEGY_RULE_MAPPING.md`** — Mapping TF_001/TF_002 ↔ Rule, Entry/Exit cụ thể.
3. **`rule_engine/RULE_IMPLEMENTATION_GUIDE.md`** — Hướng dẫn code: pseudocode, edge cases, unit test examples.

---

## V. Trạng thái Khác

### V.1 Những gì CÓ tốt

✅ **Decision Flow rõ ràng** — 10 bước tuần tự, có thể code.
✅ **Scoring System hợp lý** — 0-100, 10 rule không trùng lặp.
✅ **Conflict resolution** — Priority rank rõ, không mơ hồ.
✅ **QA checklist toàn diện** — 11 mục + 10 section, có thể dùng cho QA thật.
✅ **Rule Engine tính toán 80-95%** — Phần lớn không chủ quan.
✅ **Cover full vòng đời lệnh** — Entry (RULE_001-009), Exit (RULE_010).
✅ **Tài liệu chi tiết** — Mỗi rule có input/output/ví dụ/overfitting risk.

### V.2 Những gì CẦN làm tiếp

⚠️ **Chốt tất cả tham số** — Điều kiện sine qua non trước code.
⚠️ **Mock backtest 1 tuần** — Sanity check trước code.
⚠️ **Code Phase 3** — Lập trình Rule Engine thực tế.
⚠️ **Backtest 1-2 năm** — Xác nhân threshold 80, tham số từng rule.
⚠️ **Walk-forward test** — Verify tham số stable.
⚠️ **Bổ sung tài liệu** — Parameters Final, Strategy-Rule Mapping, Implementation Guide.

---

## VI. Kết luận

**Tổng thể: ✅ Rule Engine Phase được thiết kế SOLID**

- Kiến trúc rõ ràng, phù hợp với Trend Following philosophy.
- 10 rule cover được vòng đời lệnh (vào-giữ-thoát).
- Logic khách quan 80-95%, có thể code được.
- Conflict resolution fair (priority rank dựa trên hiệu quả, không tùy tiện).
- QA checklist toàn diện.

**Nhưng:** Rule Engine này là **thiết kế giả thuyết**. Hiệu suất thực tế phụ thuộc:
1. **Tham số cụ thể** — Phải chốt + backtest.
2. **Implementation code** — Phải code đúng, không bug.
3. **Backtest kiểm chứng** — Phải verify threshold 80, tham số từng rule trên dữ liệu thật.

**Tiếp theo:** Phase 03 là code + backtest. Dự kiến 4-8 tuần (tuỳ độ phức tạp code, lượng dữ liệu, máy chạy).

**Risks chính:**
- Overfitting threshold/tham số khi backtest → cần discipline + walk-forward test.
- Implementation code có bug → cần unit test + integration test.
- Dữ liệu liquidity/spread khó simul exact → cần mock giả định hợp lý.

---

## VII. File Checklist — Kiểm tra toàn bộ Phase 02

- ✅ RULE_ENGINE.md (chính)
- ✅ rule_engine/RULE_001_TREND.md
- ✅ rule_engine/RULE_002_MARKET_STRUCTURE.md
- ✅ rule_engine/RULE_003_BREAKOUT.md
- ✅ rule_engine/RULE_004_PULLBACK.md
- ✅ rule_engine/RULE_005_VOLUME.md
- ✅ rule_engine/RULE_006_RSI.md
- ✅ rule_engine/RULE_007_EMA.md
- ✅ rule_engine/RULE_008_RISK.md
- ✅ rule_engine/RULE_009_LIQUIDITY.md
- ✅ rule_engine/RULE_010_EXIT.md
- ✅ rule_engine/RULE_CONFLICTS.md
- ✅ rule_engine/RULE_ENGINE_CHECKLIST.md
- ✅ CURRENT_STATUS.md (updated)
- ✅ DECISIONS.md (updated)
- ✅ reports/RULE_ENGINE_PHASE_REPORT.md (file này)

**Tất cả files:** 16 files, tất cả ✅.


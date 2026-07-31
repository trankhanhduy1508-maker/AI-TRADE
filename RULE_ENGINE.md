# Rule Engine — Kiến trúc, Quy tắc, và Hệ thống Chấm điểm

> **Tài liệu thiết kế Rule Engine của AI-TRADE.** Mô tả đầy đủ cách hệ thống đánh giá
> một setup giao dịch từ khi phát hiện cho đến khi phát hành tín hiệu vào lệnh.
> Tất cả quy tắc phải nhất quán với `DECISIONS.md` (Trend Following + Market Structure
> + Volume xác nhận) và `strategies/` (TF_001, TF_002).

---

## 1. Kiến trúc tổng thể

### 1.1 Các thành phần chính

Rule Engine bao gồm **10 thành phần quy tắc (rules) + 1 hệ thống chấm điểm (scoring)**:

| ID | Tên Rule | Vai trò | Input | Output |
|---|---|---|---|---|
| RULE_001 | Trend (Xu hướng) | Xác định xu hướng hợp lệ bằng cấu trúc HH/HL hoặc LH/LL | Cấu trúc giá lịch sử | Trend status: UP/DOWN/NEUTRAL |
| RULE_002 | Market Structure | Xác định cấu trúc thị trường hiện tại (BOS/CHoCH) | Swing high/low gần nhất | Structure status: VALID/INVALID |
| RULE_003 | Breakout | Xác định breakout hợp lệ ra khỏi vùng cấu trúc | Close price, Body ratio, Volume (xác nhận) | Breakout: YES/NO/WEAK |
| RULE_004 | Pullback | Xác định pullback hợp lệ sau breakout | Price action sau breakout, Volume | Pullback: VALID/INVALID/WAITING |
| RULE_005 | Volume | Đánh giá khối lượng xác nhận breakout/phản ứng | Volume hiện tại vs trung bình | Volume: STRONG/NORMAL/WEAK |
| RULE_006 | RSI | Đánh giá mức độ quá mua/quá bán, phân kỳ | RSI value (30-70 zone) | RSI: BULLISH/BEARISH/NEUTRAL |
| RULE_007 | EMA | Xác định bias xu hướng dài hạn | Price vs EMA period | EMA: UP_BIAS/DOWN_BIAS/NEUTRAL |
| RULE_008 | Risk | Xác định stop loss hợp lệ và tỷ lệ R/R | Entry, Stop, Target levels | Risk: ACCEPTABLE/UNACCEPTABLE |
| RULE_009 | Liquidity | Đánh giá thanh khoản tại vùng giá đang xét | Order book depth, Spread | Liquidity: GOOD/FAIR/POOR |
| RULE_010 | Exit | Xác định điều kiện thoát lệnh (áp dụng SAU khi vào lệnh) | Price, Structure, SL/TP | Exit signal: EXIT_NOW/HOLD/TRAIL_SL |
| SCORING | Setup Score | Tính tổng điểm từ 10 rule trên | Tất cả output từ RULE_001-009 | Score: 0-100, Decision: TRADE/WAIT/REJECT |

### 1.2 Luồng xử lý tổng quát

```
Phát hiện Setup (Trend + Structure + Breakout)
    ↓
Áp dụng 10 Rule tuần tự (có thể reject/giảm điểm ở từng bước)
    ↓
Tính Setup Score (0-100)
    ↓
Kiểm tra Reject Conditions (điều kiện loại bỏ cứng)
    ↓
Nếu Score >= Ngưỡng (80 đề xuất) → Phát hành Trade Signal
Nếu Score < Ngưỡng → WAIT hoặc REJECT
```

---

## 2. Luồng quyết định chi tiết (Decision Flow)

**Nguyên tắc chung:** Thứ tự dưới là tuần tự **yêu cầu**. Nếu bất kỳ bước nào reject,
setup bị loại bỏ. Nếu bước nào cho kết quả WEAK/WAITING, có thể giảm điểm thay vì
reject hẳn (xem thậm chí mục Scoring).

### Bước 1: Có xu hướng hợp lệ?

**Điều kiện:** Cấu trúc giá phải cho thấy tối thiểu 2 cặp (HH + HL) liên tiếp (xu hướng
tăng) hoặc (LH + LL) liên tiếp (xu hướng giảm).

**Nếu KHÔNG:**
- → **REJECT cứng.** Setup không có xu hướng rõ ràng, chỉ là đi ngang hoặc cấu trúc
  không rõ ràng.
- Điểm Trend = 0.

**Nếu CÓ:**
- → Ghi nhận: Trend = UP hoặc DOWN (tùy hướng HH/HL hoặc LH/LL).
- Điểm Trend = 25 (cao nhất), có thể giảm nếu chuỗi HH/HL yếu/ngắn (xem RULE_001).
- Tiếp tục Bước 2.

---

### Bước 2: Có Market Structure hợp lệ?

**Điều kiện:** Swing high/low gần nhất phải rõ ràng, và setup đang xét phải hướng
cùng chiều với xu hướng từ Bước 1 (không giao dịch ngược xu hướng).

**Nếu KHÔNG (cấu trúc không rõ, hoặc setup ngược xu hướng):**
- → **REJECT cứng.**
- Điểm Market Structure = 0.

**Nếu CÓ:**
- → Ghi nhận: Structure = VALID (phá vỡ hướng đúng, không ngược lại).
- Điểm Market Structure = 20 (cao nhất).
- Tiếp tục Bước 3.

---

### Bước 3: Có Breakout hợp lệ?

**Điều kiện:** Giá đóng cửa vượt hẳn swing high/low vừa định nghĩa ở Bước 2, có
thân nến rõ ràng (body ratio), không phải nến doji/indecision.

**Nếu KHÔNG (không có breakout, hoặc chỉ chạm bằng râu):**
- → **REJECT cứng hoặc WAIT.**
  - Nếu setup vừa phát hiện nhưng chưa breakout hẳn → WAIT (tiếp tục theo dõi).
  - Nếu setup đã lâu mà vẫn chưa breakout → REJECT (setup mất hiệu lực).
- Điểm Breakout = 0 (nếu reject) hoặc 5 (nếu wait, giảm điểm).

**Nếu CÓ Breakout rõ ràng:**
- → Tiếp tục Bước 4.
- Điểm Breakout = 15 (cao nhất).

---

### Bước 4: Breakout được Volume xác nhận?

**Điều kiện:** Nến breakout phải có volume cao hơn rõ rệt so với trung bình gần đây
(tham chiếu `knowledge/VOLUME_RESEARCH.md`).

**Nếu KHÔNG (volume thấp/bình thường):**
- → **REJECT hoặc Giảm điểm tuỳ mức độ:**
  - Volume quá thấp (< 50% SMA) → REJECT cứng.
  - Volume bình thường (50-80% SMA) → Giảm điểm, từ 15 xuống 10 (Breakout từ 15 → 10,
    Volume từ 10 → 5).
  - Volume tạm ổn (80-100% SMA) → Giảm điểm nhẹ (Breakout vẫn 15, Volume từ 10 → 7).

**Nếu CÓ (volume rõ rệt cao):**
- → Tiếp tục Bước 5.
- Điểm Volume = 10 (cao nhất).

---

### Bước 5: Có Pullback hợp lệ?

**Điều kiện:** Sau breakout ở Bước 3-4, giá phải hồi lại gần vùng vừa phá vỡ mà
không phá ngược lại sâu bên trong vùng cũ (không phá hỏng breakout).

**Nếu KHÔNG (giá tiếp tục theo hướng breakout mà không hồi, hoặc hồi quá sâu):**
- → **WAIT, không reject hẳn.** Setup vẫn hợp lệ, chỉ chưa đủ điều kiện vào lệnh.
  - Nếu giá tiếp tục theo xu hướng → có thể vào lệnh tại breakout (rủi ro cao hơn).
  - Nếu hồi quá sâu (phá cấu trúc ngược) → REJECT (false break).
- Điểm Pullback = 0 (nếu reject false break) hoặc 8-12 (nếu wait, phụ thuộc tình huống).

**Nếu CÓ Pullback rõ ràng:**
- → Tiếp tục Bước 6.
- Điểm Pullback = 15 (cao nhất).

---

### Bước 6: Risk/Reward đạt tối thiểu?

**Điều kiện:** Tỷ lệ lời/lỗ tiềm năng phải >= Ngưỡng được định nghĩa trong
`risk/RISK_POLICY.md`. **Hiện chưa chốt số cụ thể, phần này ghi "Chưa chốt ngưỡng,
tham chiếu RISK_POLICY.md".**

**Nếu không chốt ngưỡng chính thức:**
- → Điểm Risk = 0 (chưa đánh giá được), nhưng không reject cứng.
- Ghi chú: "Cần chốt R/R min trong RISK_POLICY.md trước khi backtest."

**Nếu chốt được (giả định: R/R min = 1.5, tức lời ít nhất gấp 1.5 lần lỗ):**
- R/R >= 1.5 → Điểm Risk = 5 (cao nhất).
- R/R 1.0-1.5 → Giảm điểm: 3.
- R/R < 1.0 → REJECT cứng.

---

### Bước 7: Stop Loss xác định hợp lệ?

**Điều kiện:** Stop loss phải tuân theo quy tắc chiến lược hiện tại (TF_001 hoặc
TF_002) và không quá xa entry (tránh rủi ro quá lớn).

**Nếu KHÔNG (SL mơ hồ hoặc quá xa):**
- → **REJECT cứng.** Không thể quản lý rủi ro.
- Điểm Risk = 0.

**Nếu CÓ:**
- → SL hợp lệ.
- Điểm Risk = 5 (cao nhất, được tính ở Bước 6 và 7).
- Tiếp tục Bước 8.

---

### Bước 8: Tổng rủi ro danh mục còn đủ hạn mức?

**Điều kiện:** Tổng rủi ro của tất cả lệnh mở hiện tại + rủi ro setup mới phải <=
Giới hạn danh mục được định nghĩa trong `risk/RISK_POLICY.md`.

**Nếu KHÔNG (vượt giới hạn):**
- → **REJECT.** Setup bị loại tạm thời cho tới khi có lệnh đóng.
- Điểm Risk = 0 (đã bị reject tại Bước 6-7 hoặc tại bước này).

**Nếu CÓ:**
- → Có đủ hạn mức.
- Tiếp tục Bước 9.

---

### Bước 9: Setup Score đạt ngưỡng tối thiểu?

**Điều kiện:** Tổng điểm từ 9 rule ở trên (sau khi cộng/trừ theo các bước) phải >=
Ngưỡng tối thiểu đề xuất là **80 điểm** (xem mục 3 Scoring System).

**Nếu KHÔNG (Score < 80):**
- → **REJECT hoặc WAIT (tùy Score):**
  - Score 60-79 → WAIT: Setup còn tốt, chưa đủ điểm để vào ngay, có thể vào nếu
    có thêm xác nhận.
  - Score < 60 → REJECT: Setup quá yếu.

**Nếu CÓ (Score >= 80):**
- → Tiếp tục Bước 10.

---

### Bước 10: Phát hành Trade Signal

**Điều kiện:** Setup đã vượt qua tất cả 9 bước ở trên, Score >= 80, và không có
kill switch kích hoạt.

**Output cuối cùng:**
- → **TRADE SIGNAL**: Phát hành tín hiệu vào lệnh (entry, stop loss, target level).

**Thông tin tín hiệu bao gồm:**
- Chiến lược: TF_001 hoặc TF_002.
- Hướng: LONG hoặc SHORT.
- Entry price.
- Stop Loss.
- Target (nếu có).
- Risk amount (% vốn, tham chiếu RISK_POLICY.md).
- Setup Score (để audit sau).

---

## 3. Hệ thống chấm điểm (Scoring System)

### 3.1 Cấu trúc thang điểm 100

| Thành phần | Điểm max | Mô tả | Ghi chú |
|---|---|---|---|
| **RULE_001: Trend** | 25 | Xu hướng rõ ràng (chuỗi HH/HL dài) → 25; yếu hơn → giảm dần | Tham chiếu RULE_001 |
| **RULE_002: Market Structure** | 20 | Cấu trúc hợp lệ: 20; hơi yếu → 15; không rõ → 0 | Tham chiếu RULE_002 |
| **RULE_003: Breakout** | 15 | Breakout rõ ràng: 15; weak → 10; không có → 0 | Tham chiếu RULE_003 |
| **RULE_004: Pullback** | 15 | Pullback hợp lệ: 15; đang chờ → 8-12; không → 0 | Tham chiếu RULE_004 |
| **RULE_005: Volume** | 10 | Volume xác nhận rõ → 10; bình thường → 5-7; thấp → 0 | Tham chiếu RULE_005 |
| **RULE_006: RSI** | 5 | RSI không ngược signal (không quá mua/bán nhất thiết) → 5; trung lập → 3; ngược → 0 | Tham chiếu RULE_006 |
| **RULE_007: EMA** | 5 | Giá trên/dưới EMA đúng hướng → 5; trung lập → 3; sai hướng → 0 | Tham chiếu RULE_007 |
| **RULE_008: Risk** | 5 | R/R >= 1.5 → 5; 1.0-1.5 → 3; < 1.0 → 0 | Tham chiếu RULE_008 |
| **RULE_009: Liquidity** | 5 | Thanh khoản tốt → 5; tạm ổn → 3; kém → 0 | Tham chiếu RULE_009 |
| **TỔNG** | **100** | Tối đa 100 điểm | |

### 3.2 Cách tính điểm chi tiết

#### RULE_001 (Trend): 0-25

- **25 điểm**: 3+ cặp HH/HL (xu hướng tăng) hoặc LH/LL (xu hướng giảm) liên tiếp rõ ràng.
- **20 điểm**: 2 cặp rõ ràng, hoặc 3+ cặp nhưng yếu hơn (khoảng cách nhỏ).
- **15 điểm**: 2 cặp, nhưng 1 cặp hơi mập mờ.
- **0 điểm**: Không đủ 2 cặp, hoặc cấu trúc không rõ (đi ngang).

#### RULE_002 (Market Structure): 0-20

- **20 điểm**: Swing high/low rõ ràng, setup phá vỡ theo đúng xu hướng, không ngược lại.
- **15 điểm**: Cấu trúc còn ổn, nhưng swing high/low hơi mập mờ.
- **0 điểm**: Cấu trúc không rõ, hoặc setup ngược xu hướng chính (cấm tuyệt đối).

#### RULE_003 (Breakout): 0-15

- **15 điểm**: Giá đóng cửa vượt hẳn swing level, body ratio > 60%, không phải doji.
- **10 điểm**: Breakout rõ nhưng thân nến yếu (body 40-60%), hoặc chưa break hẳn.
- **5 điểm**: Chỉ chạm bằng bóng nến, chưa break, hoặc weak breakout.
- **0 điểm**: Không có breakout.

#### RULE_004 (Pullback): 0-15

- **15 điểm**: Pullback rõ ràng về gần swing level vừa phá, volume giảm, không phá ngược.
- **12 điểm**: Pullback ổn, nhưng hơi sâu (gần phá ngược).
- **8 điểm**: Chưa có pullback rõ ràng, giá tiếp tục theo breakout (chưa hồi) → có thể vào
  tại breakout nhưng rủi ro cao.
- **0 điểm**: Hồi quá sâu (phá ngược, false break), hoặc setup mất hợp lệ.

#### RULE_005 (Volume): 0-10

- **10 điểm**: Volume breakout > 150% SMA 20 nến, rõ rệt cao.
- **7 điểm**: Volume 100-150% SMA 20, ổn.
- **5 điểm**: Volume 80-100% SMA 20, bình thường.
- **0 điểm**: Volume < 80% SMA 20, thấp (có thể trigger reject ở Bước 4).

#### RULE_006 (RSI): 0-5

- **5 điểm**: RSI không ở vùng quá mua (> 70) hoặc quá bán (< 30) ngược signal, hoặc có phân kỳ
  dương (giá xuống, RSI lên — bullish).
- **3 điểm**: RSI trung lập (30-70), không cho tín hiệu rõ.
- **0 điểm**: RSI quá mua/bán ngược chiều signal, hoặc phân kỳ âm (giá lên, RSI xuống — bearish).

#### RULE_007 (EMA): 0-5

- **5 điểm**: Giá rõ ràng trên EMA (setup long) hoặc dưới EMA (setup short), trend bias rõ.
- **3 điểm**: Giá gần EMA (trong 2-3% giá), bias trung lập.
- **0 điểm**: Giá ngược lại bias của EMA (setup long nhưng giá dưới EMA), hoặc không xác định được
  bias.

#### RULE_008 (Risk): 0-5

- **5 điểm**: R/R >= 1.5, hoặc R/R >= 2.0 (tốt nhất).
- **3 điểm**: R/R 1.0-1.5, chấp nhận được.
- **0 điểm**: R/R < 1.0, hoặc không thể tính R/R (SL quá xa) → REJECT cứng ở Bước 6-7.

#### RULE_009 (Liquidity): 0-5

- **5 điểm**: Vùng giá có thanh khoản tốt (spread < 2 pip, depth tốt), không lo trượt giá.
- **3 điểm**: Thanh khoản ổn (spread 2-5 pip, depth trung bình).
- **0 điểm**: Thanh khoản kém (spread > 5 pip, depth sâu, dễ trượt) → có thể reject tạm hoặc chờ
  thanh khoản tốt hơn.

### 3.3 Ngưỡng quyết định

| Score | Quyết định | Hành động |
|---|---|---|
| >= 80 | TRADE | Phát hành Trade Signal, vào lệnh |
| 60-79 | WAIT | Setup còn tốt, chưa đủ điểm, chờ xác nhận thêm hoặc theo dõi |
| < 60 | REJECT | Setup quá yếu, bỏ qua |

**Ghi chú:**
- Ngưỡng 80 là **đề xuất thiết kế**, chưa được backtest kiểm chứng. Cần chạy backtest để xác nhận
  ngưỡng này có hợp lý hay cần điều chỉnh (ví dụ: 75 hoặc 85).
- Các setup REJECT không được tính lại — phải reset setup và chờ cấu trúc giá thay đổi để phát hiện
  setup mới.
- Các setup WAIT được tính lại mỗi nến/bar mới, có thể chuyển sang TRADE hoặc REJECT tuỳ điều kiện
  tiếp theo.

---

## 4. Điều kiện Reject cứng (Hard Stops)

Setup sẽ bị **REJECT ngay lập tức** nếu xảy ra bất kỳ điều kiện nào sau:

1. **Không có xu hướng rõ ràng** (Bước 1) → Thị trường đi ngang.
2. **Setup ngược xu hướng chính** (Bước 2) → Không giao dịch ngược xu hướng.
3. **Không có breakout** (Bước 3) → Setup không hình thành.
4. **False break** (Bước 5) → Hồi quá sâu, phá cấu trúc ngược, không phải pullback.
5. **Risk/Reward < 1.0** (Bước 6) → Lỗ nhiều hơn lời, không chấp nhận.
6. **Không xác định được Stop Loss** (Bước 7) → Không thể quản lý rủi ro.
7. **Vượt giới hạn danh mục** (Bước 8) → Tổng rủi ro quá cao.
8. **Kill Switch kích hoạt** → Dừng tất cả tín hiệu mới (xem `risk/KILL_SWITCH_RULES.md`).

---

## 5. Mối quan hệ giữa Decision Flow, Scoring, và Reject Conditions

```
┌─ Decision Flow (Bước 1-10)
│   ├─ Reject Conditions (Hard stops)
│   ├─ Wait/Weak Signal (Scoring giảm)
│   └─ Valid Signal (Scoring cao)
│
├─ Scoring System (0-100)
│   ├─ Tính điểm từ 10 rule
│   ├─ So sánh với Ngưỡng (80)
│   └─ Output: TRADE / WAIT / REJECT
│
└─ Trade Signal Output
    ├─ Chiến lược (TF_001 / TF_002)
    ├─ Entry, Stop Loss, Target
    ├─ Risk amount
    └─ Setup Score (audit)
```

---

## 6. Thứ tự đánh giá tín hiệu (Priority)

Thứ tự đánh giá và ưu tiên như sau (**không thay đổi**):

1. **Trend + Market Structure** (RULE_001 + RULE_002) → **Bắt buộc**, là nền tảng.
2. **Breakout** (RULE_003) → **Bắt buộc**, xác định setup vào lệnh hay không.
3. **Pullback** (RULE_004) → **Bắt buộc** (hoặc WAIT nếu chưa có).
4. **Volume** (RULE_005) → **Xác nhận**, có thể giảm điểm hoặc reject nếu quá yếu.
5. **Risk** (RULE_008) → **Bắt buộc**, không giao dịch nếu R/R xấu.
6. **RSI + EMA** (RULE_006 + RULE_007) → **Xác nhận phụ**, 5 điểm mỗi cái, không quyết định vào lệnh
   một mình.
7. **Liquidity** (RULE_009) → **Xác nhận phụ**, tránh trượt giá, 5 điểm.

**Nhớ:** Price Action/Market Structure là **chính**, chỉ báo là **phụ**. Không bao giờ vào lệnh chỉ vì
RSI hoặc EMA, dù "nhìn đẹp" — bắt buộc phải có cấu trúc giá rõ ràng trước.

---

## 7. Các file chi tiết

Mỗi rule có file riêng trong `rule_engine/` với 11 mục bắt buộc (xem
`rule_engine/RULE_ENGINE_CHECKLIST.md`):

- `rule_engine/RULE_001_TREND.md`
- `rule_engine/RULE_002_MARKET_STRUCTURE.md`
- `rule_engine/RULE_003_BREAKOUT.md`
- `rule_engine/RULE_004_PULLBACK.md`
- `rule_engine/RULE_005_VOLUME.md`
- `rule_engine/RULE_006_RSI.md`
- `rule_engine/RULE_007_EMA.md`
- `rule_engine/RULE_008_RISK.md`
- `rule_engine/RULE_009_LIQUIDITY.md`
- `rule_engine/RULE_010_EXIT.md`

Xung đột giữa rule: `rule_engine/RULE_CONFLICTS.md`

Checklist QA: `rule_engine/RULE_ENGINE_CHECKLIST.md`

---

## 8. Liên hệ với các file khác

- **`DECISIONS.md`** → Quyết định kiến trúc đã chốt (Trend Following, Market Structure, Volume xác
  nhận).
- **`strategies/TF_001_BREAKOUT_PULLBACK.md`** → Chi tiết chiến lược breakout/pullback.
- **`strategies/TF_002_TRENDLINE_REACTION.md`** → Chi tiết chiến lược trendline.
- **`risk/RISK_POLICY.md`** → Giới hạn rủi ro (hiện chưa chốt số).
- **`risk/POSITION_SIZING.md`** → Công thức tính khối lượng lệnh.
- **`risk/KILL_SWITCH_RULES.md`** → Quy tắc dừng khẩn cấp.
- **`knowledge/PRICE_ACTION_AND_MARKET_STRUCTURE.md`** → Định nghĩa swing high/low, BOS, CHoCH.
- **`knowledge/VOLUME_RESEARCH.md`** → Cách đánh giá volume.
- **`knowledge/TREND_FOLLOWING.md`** → Nguyên tắc trend following.
- **`backtests/BACKTEST_STANDARD.md`** → Chuẩn backtest để kiểm chứng rule engine này.

---

## 9. Trạng thái và ghi chú

- **Thiết kế:** Đã chốt kiến trúc, luồng quyết định, hệ thống chấm điểm.
- **Cần backtest:** Ngưỡng điểm 80, các tham số SMA volume, RSI/EMA thresholds.
- **Chưa chốt:** Các con số cụ thể trong `risk/RISK_POLICY.md` (% rủi ro/lệnh, R/R min, etc).
- **Tiếp theo:** Viết 10 file rule chi tiết, audit xung đột, chạy backtest để xác nhận ngưỡng.


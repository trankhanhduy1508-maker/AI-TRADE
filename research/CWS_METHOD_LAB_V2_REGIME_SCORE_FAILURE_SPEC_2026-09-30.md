# CWS METHOD LAB V2 — Regime + Signal Score + Failure Learning + Adaptive Management

**Ngày:** 2026-09-30  
**Repository:** `trankhanhduy1508-maker/AI-TRADE`  
**Nhánh duy nhất:** `codex/p0-covel-knowledge-audit`  
**Parent HEAD:** `0eba40c91ced5c14d8b012e409432192935a06f1`  
**Trạng thái:** PRE-IMPLEMENTATION, RESEARCH_ONLY, EDGE_UNPROVEN.

## 1. Mục tiêu

Cải thiện **chất lượng phương pháp** chứ không tối ưu số backtest. V2 kế thừa các bất biến an toàn của V1: chỉ dùng nến đã đóng, next-open, một vị thế/symbol, gap xấu hơn, stop không nới, không LIVE/DEMO-send, không scheduler, không phí/net-PnL claim. R0/R1/R2/R2b/V1 không sửa.

V2 bổ sung bốn năng lực:
1. nhận diện **trạng thái thị trường** từ quá khứ;
2. chấm **điểm chất lượng tín hiệu** thay vì TRUE/FALSE duy nhất;
3. học từ **lỗi giao dịch đã đóng** bằng taxonomy cố định;
4. quản lý vị thế thích nghi theo regime hiện tại nhưng **không bao giờ nới stop**.

Không dùng kết quả R2b đã biết để chọn ngưỡng thắng. Các ngưỡng dưới đây được khóa **trước** khi chạy empirical V2.

## 2. Regime Engine

Chỉ dùng dữ liệu đến close t.

Indicator cố định:
- ATR20 Wilder;
- SMA50;
- SMA200;
- SMA200 slope = SMA200(t) − SMA200(t−20);
- ATR ratio = ATR20(t) / median(100 ATR20 trước t);
- trend separation = |SMA50−SMA200| / ATR20(t).

Phân loại thứ tự ưu tiên:
- `VOLATILITY_SHOCK`: ATR ratio > 2.0.
- `TREND_STRONG_UP`: SMA50>SMA200, SMA200 slope>0, separation >= 1.0.
- `TREND_STRONG_DOWN`: đối xứng.
- `TREND_WEAK_UP`: SMA50>SMA200 và SMA200 slope>0 nhưng separation <1.0.
- `TREND_WEAK_DOWN`: đối xứng.
- `COMPRESSION`: ATR ratio <0.70 và không thuộc strong trend.
- còn lại `RANGE_OR_TRANSITION`.

Nếu thiếu 220 close hoặc 101 ATR observation: `UNKNOWN`.

## 3. Signal Score

Điểm nằm trong [0,100], cấu thành **cố định**, không học trọng số từ history đã mở.

LONG:
- +25: close vượt prior 55-bar high + 0.25ATR;
- +15: close>SMA200;
- +15: SMA200 slope>0;
- +10: SMA50>SMA200;
- +10: candle body >=0.50ATR;
- +10: close-location >=0.75;
- +10: regime = TREND_STRONG_UP; +5 nếu TREND_WEAK_UP;
- +5: ATR ratio trong [0.70,1.50].
SHORT đối xứng và chỉ được xét nếu short vehicle đã xác thực.

Decision:
- `TRADE` nếu score >=80, không shock, không quarantine/cooldown, source valid;
- `WATCH` nếu 60<=score<80;
- `ABSTAIN` nếu <60 hoặc regime UNKNOWN/SHOCK.
Không scale position/risk theo score trong V2; score chỉ quyết định chất lượng tín hiệu.

## 4. Failure Learning từ lệnh đã đóng

Mỗi lệnh đóng được tag **sau exit**, chỉ dựa thông tin đã biết lúc đó:
- `FAST_STOP`: stop trong <=5 bar sau entry và gross R<0.
- `FAILED_BREAKOUT`: gross R<0 và close tại exit đã quay lại bên trong channel 55 trước exit.
- `REGIME_REVERSAL`: regime direction tại exit đối nghịch direction entry.
- `VOL_SHOCK_EXIT`: exit regime = VOLATILITY_SHOCK.
- `NORMAL_LOSS`: lỗ không thuộc nhóm trên.
- `WIN`: gross R>0.
- `FLAT`: gross R==0.

Feedback không thay hyperparameter. Nó chỉ điều chỉnh **gating**:
- giữ 8 closed tags gần nhất;
- nếu >=4 `FAILED_BREAKOUT` hoặc `FAST_STOP` trong 8 lệnh: `QUALITY_QUARANTINE` 20 bar;
- nếu >=3 `REGIME_REVERSAL` trong 8 lệnh: chỉ cho `WATCH`, không TRADE, trong 20 bar;
- WIN không xóa lịch sử; deque tự trượt.

## 5. Adaptive Position Management

Initial stop vẫn 2.5ATR từ signal close như V1. Candidate không đổi sau entry.

Trailing stop LONG:
- strong up: prior 30-bar low;
- weak up: prior 20-bar low;
- range/transition/compression: prior 10-bar low;
- shock: prior 5-bar low.
SHORT đối xứng.

Stop mới = max(stop cũ, candidate trail) cho LONG / min cho SHORT. **Không nới stop**. Regime dùng cho trailing phải được tính từ dữ liệu đã đóng trước bar đang xử lý stop; current bar không được dùng để kéo stop trước khi kiểm tra gap/touch.

Nếu regime UNKNOWN: giữ stop cũ, không tạo trail mới.

## 6. Causality và anti-overfit

- Mọi feature tại t dùng `bars[:t+1]`; channel/trail phải loại current bar khi quy tắc yêu cầu prior.
- Suffix tương lai thay đổi không được làm thay decision/snapshot của prefix.
- Không dùng realized outcome để sửa score weights, regime thresholds, trail windows hoặc ATR multiplier trong V2.
- R2b/V1 đã mở chỉ dùng bugfix, không được gọi independent validation.
- V2 empirical cần dataset/window mới đăng ký trước kết quả. Synthetic QA chỉ chứng minh logic.

## 7. QA bắt buộc

Smoke:
- exact thresholds/version;
- regime strong/weak/compression/shock;
- score 0–100; TRADE/WATCH/ABSTAIN;
- orders_sent=0, account PnL None, edge UNPROVEN.

Runtime:
- next-open;
- persistent position;
- adaptive trailing strong 30 / weak 20 / range 10 / shock 5;
- stop monotonic;
- failure tags và 8-trade feedback;
- 1.000+ bar deterministic stream;
- prefix immunity.

Fault:
- malformed OHLC, NaN, duplicate/out-of-order, future/unclosed, string boolean;
- gap chưa audit;
- short không verified;
- current/future candle không được leak vào prior channel/trail;
- no cost/broker imports/action;
- invalid regime inputs fail closed.

**Không nghiên cứu chi phí trong V2.** `cost_status=NOT_EVALUATED` là bắt buộc; không suy ra net profitability.

# CWS METHOD LAB V2 — Implementation + QA Checkpoint

**Ngày:** 2026-09-30  
**Repo:** `trankhanhduy1508-maker/AI-TRADE`  
**Nhánh duy nhất:** `codex/p0-covel-knowledge-audit`  
**Parent trước V2:** `0eba40c91ced5c14d8b012e409432192935a06f1`  
**HEAD trước checkpoint:** `acf57ccf4ffd48b15ba5bc9fd09a08ac2c79d0e9`  
**Trạng thái:** RESEARCH_ONLY, EDGE_UNPROVEN, ORDERS_SENT=0.

## 1. Spec khóa trước code

`research/CWS_METHOD_LAB_V2_REGIME_SCORE_FAILURE_SPEC_2026-09-30.md` commit `2509ad559a69fd54aba04a27da4a6b3d7baa53b6`.

Founder directive: tập trung cải thiện **phương pháp**, không chỉ backtest; bỏ nghiên cứu chi phí khỏi nhiệm vụ V2. Chi phí vì thế chỉ mang `NOT_EVALUATED`, không đồng nghĩa 0 phí hoặc net profit.

V2 bổ sung bốn khối:
- Regime Engine: TREND_STRONG/WEAK UP/DOWN, COMPRESSION, RANGE_OR_TRANSITION, VOLATILITY_SHOCK, UNKNOWN.
- Signal Score 0–100 với TRADE >=80, WATCH 60–79, ABSTAIN <60 hoặc UNKNOWN/SHOCK.
- Failure Learning chỉ từ closed trades: FAST_STOP, FAILED_BREAKOUT, REGIME_REVERSAL, VOL_SHOCK_EXIT, NORMAL_LOSS, WIN, FLAT.
- Adaptive trailing chỉ **siết** stop: 30 bar strong trend, 20 weak, 10 range/compression/opposite, 5 shock; UNKNOWN giữ stop cũ.

Không tăng position sizing theo score, không dùng outcome để tự sửa weight/threshold, không reset position theo fold.

## 2. Implementation

`src/research/method_lab_v2.py` Git blob SHA:
`44a63bdde0715b4d5fd926cd221eaa797879f280`

Các bất biến:
- chỉ closed bar đã xác nhận;
- signal tại close, hypothetical entry ở next open;
- one position/symbol;
- adverse gap stop tại open;
- current bar không được dùng để kéo stop trước khi kiểm tra stop trên chính bar đó;
- source/session/audit flags fail-closed và phải là boolean thật;
- short disabled nếu chưa xác thực vehicle;
- no HTTP/socket/subprocess/broker/MT5 imports;
- output luôn `orders_sent=0`, `independent_forward_trades=0`, `account_currency_pnl=None`, `cost_status=NOT_EVALUATED`, `edge_status=UNPROVEN`.

Test file `tests/research/test_method_lab_v2.py` Git blob SHA:
`e094840c0f1cca75d51416be87315ded403389ca`.

Local cloud test bytes được đối chiếu bằng `git hash-object` và trùng chính xác hai blob GitHub ở trên.

## 3. Hai lỗi thật đã bắt và sửa

### FAIL 1 — ATR state không khởi tạo
Runtime lần đầu:
- 7 test methods;
- 5 ERROR;
- nguyên nhân: nhánh code yêu cầu `len(self.bars)<=20` đồng thời `len(self.bars)==21`, điều kiện bất khả thi. Từ bar 21 engine rơi vào `ATR_STATE_CORRUPT`.
- fix tối thiểu commit `574871507935adbdbbd9b50f3aaa00843a32d2fb`: nếu chưa có ATR và đủ 21 bars thì tính đúng 20 true ranges đầu, sau đó Wilder update bình thường.
- Runtime chạy lại 7/7 PASS.

### BUG 2 — feedback đếm tag thay vì giao dịch
Audit spec/code phát hiện một closed trade có cả FAST_STOP + FAILED_BREAKOUT bị tính là 2 failure. Như vậy chỉ 2–3 giao dịch xấu có thể đạt ngưỡng “4/8 trades”.
- fix commit `350f8c321789414b4560b9980f3663925a655076`;
- mỗi closed trade giờ chỉ đóng góp tối đa 1 lần vào quality-failure count, dù có nhiều failure tags;
- test commit `acf57ccf4ffd48b15ba5bc9fd09a08ac2c79d0e9` xác nhận 3 bad trades không quarantine, bad trade thứ 4 mới kích hoạt.

## 4. QA cuối cùng trên đúng GitHub bytes

Môi trường: Python 3.13.5 cloud container, không dùng Founder PC.

```
python -m unittest tests.research.test_method_lab_v2.Smoke -q
python -m unittest tests.research.test_method_lab_v2.Runtime -q
python -m unittest tests.research.test_method_lab_v2.Fault -q
python -m compileall -q src tests
```

Kết quả cuối:
- Smoke **4/4 PASS**
- Runtime synthetic **7/7 PASS**
- Fault **6/6 PASS**
- Tổng **17/17 PASS**
- compileall PASS
- imports duy nhất: `__future__, collections, dataclasses, math, statistics, time`.

Runtime có deterministic 1.200-bar regime stream; prefix immunity; next-open; persistent position; monotonic stop. Fault có malformed OHLC/NaN/future/unclosed/duplicate, string boolean, unaudited calendar gap, future-suffix mutation, 100 randomized score bounds và AST import audit.

## 5. Điều V2 CHƯA chứng minh

17 synthetic tests chứng minh **logic/invariants**, không chứng minh lợi nhuận. V2 chưa chạy empirical trên dataset/window mới, chưa paper-forward độc lập, chưa có venue/timezone audit và không nghiên cứu phí theo directive hiện tại.

Kết quả R0/R2/R2b/V1 đã xem không thể “quên” để trở thành holdout mới. V2 không được gọi tốt hơn V1 về expectancy cho đến khi có dataset/window mới khóa trước kết quả. Nếu chạy historical cũ để debug/ablation thì phải ghi HISTORICAL_REUSED, không OOS độc lập.

## 6. Bước kỹ thuật kế tiếp

Trước khi empirical V2:
1. xây **ablation harness** giữ cùng input để tách đóng góp Regime / Score / Failure Feedback / Adaptive Trail;
2. metric phải gồm số TRADE/WATCH/ABSTAIN, failure taxonomy, stop distance evolution, false-break proxy và missed-trend proxy, không chỉ PnL;
3. đăng ký một dataset/window chưa dùng cho selection trước khi đọc kết quả;
4. so V1 vs V2 bằng cùng source/same causal timestamps; giữ tất cả âm/dương;
5. không tự tăng risk và không gửi order.

**Kết luận:** METHOD LAB V2 đã được implement và test như một engine nghiên cứu nhân-quả. Hai lỗi logic đã được phát hiện và sửa trước checkpoint. Profitability vẫn UNPROVEN.

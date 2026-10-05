# AI AUTO TRADE — MASTER GOAL

> Canonical North Star cho nhánh Auto Trade của AI-TRADE.

## 1. Goal

Xây hệ thống **auto trade Trend Following kết nối MetaTrader 5**, vận hành tự động 24/7. Founder dùng **Android** để theo dõi và điều khiển, không phải ngồi đặt lệnh thủ công.

Kiến trúc mục tiêu:

`Android control/dashboard -> secure service -> Windows/VPS -> MT5 -> execution engine -> broker`

Android là control plane. Trading engine không được phụ thuộc vào việc điện thoại đang mở.

## 2. Knowledge First — bắt buộc

Trước khi tối ưu chiến lược hoặc mở rộng MT5, ưu tiên số 1 là xây **canonical knowledge base theo Practitioner First**.

Nguồn ưu tiên:
1. Sách/tài liệu do trader hoặc investor trực tiếp thành công viết, với track record có thể kiểm tra.
2. Bản sách hợp pháp do Founder cung cấp, nếu có.
3. Tài liệu chính thức của practitioner/quỹ/tổ chức và publisher metadata.
4. Primary research/papers để kiểm chứng giả thuyết.
5. Secondary interview/synthesis chỉ dùng để dẫn tới primary source và cross-check.

Peter Lynch — *One Up on Wall Street* / *Beating the Street* là core corpus về tư duy nghiên cứu và kỷ luật đầu tư. Larry Hite, William J. O'Neil, Mark Minervini và các practitioner khác được ingest theo mức bằng chứng track record. Michael Covel và các sách tổng hợp/phỏng vấn vẫn hữu ích, nhưng thuộc lớp **secondary synthesis**, không còn là nguồn practitioner duy nhất hoặc tối cao.

Không được giả vờ đã học toàn bộ sách nếu chưa có full lawful source. Không dùng bản sách lậu. Không chép dài nguyên văn nội dung có bản quyền; chỉ tổng hợp bằng ngôn ngữ riêng.

Mọi kiến thức quan trọng phải có cả **source provenance** và **track-record provenance**:
- `VERIFIED_PRACTITIONER_RECORD`
- `VERIFIED_FROM_PRACTITIONER_BOOK`
- `PRACTITIONER_RECORD_PARTIAL`
- `SECONDARY_SYNTHESIS`
- `VERIFIED_FROM_PRIMARY_RESEARCH`
- `IMPLEMENTATION_DERIVATION`
- `UNVERIFIED`

Canonical rules nằm tại:
- `knowledge/KNOWLEDGE_INGESTION_POLICY.md`
- `knowledge/PRACTITIONER_BOOK_CORPUS.md`

Phải phân biệt rõ **kiến thức nguồn** với **tham số do engineering/backtest lựa chọn**. Không được bê nguyên rule từ cổ phiếu sang FX/MT5 nếu chưa có backtest riêng.

Knowledge cần bao phủ tối thiểu:
- reaction vs prediction
- trend/price-driven decision making
- entry/exit philosophy
- stop loss / take profit / trailing exit
- let winners run
- pyramiding winners vs martingale/averaging down
- position sizing
- volatility/leverage
- drawdown
- correlation/diversification
- portfolio construction
- long/short
- behavioral bias/discipline
- statistical/scientific thinking
- performance evaluation

Canonical output chính đặt trong `knowledge/` và phải có khả năng truy nguồn.

## 3. Strategy principle

Bot không có nhiệm vụ đoán ngày mai giá tăng hay giảm.

Nó phải phản ứng với dữ liệu đã xảy ra theo rule deterministic:

`market data -> trend qualification -> signal -> independent risk gate -> execution`

Signal engine **không được tự quyết risk**.

Nếu signal nói BUY/SELL nhưng Risk Engine không cho phép, lệnh không được mở.

## 4. Portfolio first

Không hard-code một symbol duy nhất. Thiết kế để có thể nghiên cứu nhiều instrument MT5 phù hợp, đánh giá ở cấp portfolio, correlation, volatility và total exposure.

## 5. Validation ladder

Không nhảy thẳng từ ý tưởng sang tiền thật.

Thứ tự:
1. Knowledge provenance audit.
2. Machine-readable strategy specification.
3. Historical backtest.
4. Out-of-sample / walk-forward khi phù hợp.
5. Cost realism: spread, commission, swap, slippage.
6. Paper trading.
7. MT5 demo forward trading.
8. Crash/restart/reconnect/reconciliation tests.
9. 24/7 VPS deployment + Android monitoring.
10. Live-ready gate.

**Giai đoạn hiện tại vẫn tuân `PROJECT_CONTEXT.md`: chưa kết nối tài khoản thật và chưa gửi lệnh tiền thật.** Live trading chỉ được mở khóa khi Project Owner xác nhận rõ ràng ở một giai đoạn sau.

## 6. MT5 engineering direction

Nghiên cứu cả hai hướng:
- MQL5 Expert Advisor native.
- Python + MetaTrader 5 integration.

Không chọn công nghệ theo sở thích. So sánh reliability, recovery, state persistence, testing, deployability và khả năng vận hành 24/7.

Có thể dùng Python cho research/backtest và MQL5 cho production nếu evidence cho thấy đó là kiến trúc tốt hơn.

## 7. Android-first Founder workflow

Founder chủ yếu thao tác từ Android.

Coder/agent phải tự tìm workflow phù hợp để:
- development có thể điều khiển qua GitHub/Codex/cloud tooling;
- runtime Windows/MT5 chạy ở VPS/host riêng;
- Founder không phải ngồi trước PC để hệ thống hoạt động.

Dashboard tương lai cần tối thiểu:
- online/offline + heartbeat
- MT5 connection
- account mode DEMO/LIVE
- equity/balance/drawdown
- open positions/exposure/current risk
- recent trades/errors
- pause new trades
- kill switch

## 8. Safety and capital protection

Risk Engine là lớp độc lập, hard-rule, không phải quyết định tùy hứng của LLM.

Phải fail-safe khi:
- mất kết nối MT5
- dữ liệu stale
- spread bất thường
- order lỗi lặp lại
- state không chắc chắn
- risk/drawdown vượt policy

Nguyên tắc mặc định:

`UNKNOWN STATE -> DO NOT OPEN NEW RISK`

Không commit credentials, broker password, API secrets hoặc private keys.

Không tối ưu chỉ để tạo equity curve đẹp. Phải chống overfitting, look-ahead bias, data snooping, survivorship bias và unrealistic fills.

## 9. Agent autonomy

Agent được trao quyền tự xử lý routine technical decisions để tiến đến Goal.

Tự research, thiết kế, code, test, debug, refactor có mục tiêu, cập nhật docs/status và xử lý blocker thông thường.

Không hỏi Founder các quyết định kỹ thuật nhỏ đã có thể suy ra từ repo/evidence.

Nhưng không được tự thay đổi các hard risk limits hoặc tự unlock live-money trading.

## 10. Execution order

Ưu tiên hiện tại:
1. Practitioner-first knowledge ingestion + provenance audit.
2. Map claim thành hypothesis có thể test.
3. Strategy spec.
4. Backtesting + OOS/walk-forward.
5. Paper/demo execution.
6. MT5 full position lifecycle: entry + SL/TP + trailing + partial + winner pyramiding + reconciliation.
7. VPS 24/7 + Android control.
8. Live-ready validation.

Live-money không được tự mở khóa.

## 11. Definition of Done

Không coi là DONE chỉ vì EA đặt được một lệnh.

Hệ thống hoàn chỉnh phải có:
- traceable knowledge provenance
- deterministic strategy rules
- reproducible realistic backtests
- independent risk engine
- out-of-sample evidence
- paper/demo forward validation
- persistent state
- no duplicate orders
- MT5 reconnect/recovery
- broker reconciliation
- audit logs
- secure secrets
- Android monitoring/control
- kill switch
- 24/7 autonomous operation

North Star cuối cùng: **Founder có thể đóng điện thoại và hệ thống vẫn vận hành đúng rule; mở điện thoại lại vẫn thấy đầy đủ trạng thái và có thể dừng hệ thống ngay lập tức.**

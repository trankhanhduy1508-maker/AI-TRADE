# Provenance — Trend Following theo Michael W. Covel

> Trạng thái audit: **P0 / 2026-08-22**
>
> Tài liệu này là sổ đăng ký nguồn và phạm vi claim cho knowledge base. Nó không
> phải bản sao của sách, không thay thế sách, và không khẳng định repo đã ingest
> toàn bộ `Trend Following, Fifth Edition`.

## 1. Quy ước provenance

| Nhãn | Ý nghĩa trong repo |
|---|---|
| `VERIFIED_FROM_BOOK` | Claim đã được đối chiếu trực tiếp với bản sách hợp pháp mà repo/Founder có quyền sử dụng. Hiện P0 chưa gắn nhãn này cho claim nội dung nào. |
| `VERIFIED_FROM_AUTHOR` | Claim xuất hiện trong tài liệu công khai do Michael Covel phát hành hoặc trên kênh chính thức của ông; đây là author material, không tự động đồng nghĩa với toàn bộ nội dung Fifth Edition. |
| `VERIFIED_FROM_PRIMARY_RESEARCH` | Kết quả từ paper/working paper gốc của nhóm tác giả nghiên cứu; đây là bằng chứng độc lập, không gán ngược cho Covel. |
| `IMPLEMENTATION_DERIVATION` | Lựa chọn thiết kế của AI-TRADE để biến triết lý thành rule có thể kiểm thử; không phải tham số được Covel xác nhận. |
| `UNVERIFIED` | Claim chưa có nguồn đủ mạnh hoặc chưa được kiểm chứng bằng backtest; không được dùng làm fact hay quảng cáo hiệu quả. |

## 2. Sổ đăng ký nguồn

| ID | Nguồn | Loại | Phạm vi được phép dùng |
|---|---|---|---|
| `SRC-COVEL-BOOKS` | [Covel books/catalog](https://www.trendfollowing.com/translations/) | `VERIFIED_FROM_AUTHOR` cho metadata | Xác nhận Covel liệt kê `Trend Following, 5th Edition`, Wiley, ISBN-13 `978-1119371878`, phát hành 2017. Không dùng trang catalog để suy ra nội dung chi tiết của sách. |
| `SRC-COVEL-PREFACE` | [Official Fifth Edition preview](https://www.trendfollowing.com/pdfs/trend_following_michael_covel_2017.pdf) | `VERIFIED_FROM_AUTHOR` / preview | Xác nhận danh mục/ấn bản và phần preview công khai. Không coi preview 22 trang là full lawful copy. |
| `SRC-COVEL-TEN-TENETS` | [Ten Tenets of a Trend Follower](https://www.trendfollowing.com/wp-content/uploads/2017/10/covel-interview-2.pdf) | `VERIFIED_FROM_AUTHOR` | Price as primary observable input; cut losses/let profits run; buy higher highs/sell lower lows; react rather than predict; reduce discretion; adapt to change. Chỉ dùng diễn giải ngắn, không sao chép đoạn dài. |
| `SRC-COVEL-THEORY` | [Trend Following Theory](https://www.trendfollowing.com/trend/) | `VERIFIED_FROM_AUTHOR` | Reactive rules, price data, exit/risk/position-size concepts, discipline, portfolio breadth, and stated limitations. Các claim hiệu quả vẫn phải tách khỏi bằng chứng backtest của repo. |
| `SRC-COVEL-RESEARCH` | [Covel research process](https://www.trendfollowing.com/research/) | `VERIFIED_FROM_AUTHOR` | Covel's public framing of no-prediction, price-focused research, money management, and probability thinking. Đây là author position, không phải peer-reviewed validation. |
| `SRC-TSMOM-2012` | [Moskowitz, Ooi & Pedersen, Time Series Momentum](https://pages.stern.nyu.edu/~lpederse/papers/TimeSeriesMomentum.pdf) | `VERIFIED_FROM_PRIMARY_RESEARCH` | Nghiên cứu 58 liquid futures/forwards; persistence 1–12 months, partial longer-horizon reversal, and diversified cross-asset results in the stated sample. Không biến lookback 12 tháng thành tham số mặc định của AI-TRADE. |
| `SRC-CENTURY-2014` | [Hurst, Ooi & Pedersen, A Century of Evidence](https://www.trendfollowing.com/whitepaper/Century_Evidence_Trend_Following.pdf) | `VERIFIED_FROM_PRIMARY_RESEARCH` | Bằng chứng lịch sử mở rộng tới 1880, positive returns/low correlation trong nghiên cứu và diversification trong equity bear markets theo phạm vi paper. Không xem đây là guarantee tương lai. |

## 3. Claim matrix cho P0

| Claim ID | Nội dung diễn giải | Provenance | Dùng trong repo |
|---|---|---|---|
| `TF-COV-001` | Giá là dữ liệu quan sát chính; không cần dựng câu chuyện fundamentals để tạo một tín hiệu phản ứng. | `VERIFIED_FROM_AUTHOR` (`SRC-COVEL-TEN-TENETS`, `SRC-COVEL-THEORY`) | Nền tảng cho `TREND_FOLLOWING.md`; không cấm mọi dữ liệu phụ trong mọi nghiên cứu. |
| `TF-COV-002` | Trend following phản ứng sau khi điều kiện giá xuất hiện, không tuyên bố biết trước điểm bắt đầu/kết thúc. | `VERIFIED_FROM_AUTHOR` (`SRC-COVEL-TEN-TENETS`, `SRC-COVEL-RESEARCH`) | Nguyên tắc reaction; mọi entry cụ thể của repo vẫn là implementation derivation. |
| `TF-COV-003` | Giữ tổn thất nhỏ theo rule và để vị thế thắng có cơ hội tiếp diễn; không gắn một profit target cố định vào triết lý này nếu chưa có kiểm chứng riêng. | `VERIFIED_FROM_AUTHOR` (`SRC-COVEL-TEN-TENETS`, `SRC-COVEL-THEORY`) | Tách stop/exit trong strategy docs; không tự sinh % stop hay target. |
| `TF-COV-004` | Một hệ thống phải mô tả được thị trường, khối lượng, điều kiện vào, cách thoát lệnh thua và cách thoát lệnh thắng. | `VERIFIED_FROM_AUTHOR` (`SRC-COVEL-THEORY`) | Checklist thiết kế; chưa phải chiến lược đã chứng minh. |
| `TF-COV-005` | Sau khi chọn hệ thống/portfolio/risk policy, quyết định giao dịch nên được cơ giới hóa và giảm override cảm tính. | `VERIFIED_FROM_AUTHOR` (`SRC-COVEL-TEN-TENETS`) | Hỗ trợ deterministic rule engine; không biến LLM thành risk authority. |
| `TF-PR-001` | Time-series momentum có bằng chứng trong nghiên cứu trên nhiều asset class và horizon, nhưng kết luận bị giới hạn bởi universe, sample, costs và phương pháp paper. | `VERIFIED_FROM_PRIMARY_RESEARCH` (`SRC-TSMOM-2012`) | Dùng làm giả thuyết/đối chứng nghiên cứu, không phải kết quả backtest của AI-TRADE. |
| `TF-PR-002` | Nghiên cứu lịch sử dài cho thấy trend following có return/correlation properties trong sample đã nêu. | `VERIFIED_FROM_PRIMARY_RESEARCH` (`SRC-CENTURY-2014`) | Dùng để thiết kế validation portfolio/multi-market; không quảng cáo lợi nhuận tương lai. |
| `TF-ENG-001` | HH/HL/LH/LL, BOS/CHoCH, swing window và breakout/pullback definition là cách AI-TRADE operationalize price action. | `IMPLEMENTATION_DERIVATION` | Chỉ có hiệu lực khi strategy/backtest định nghĩa và kiểm chứng rõ. Không gắn nhãn Covel. |
| `TF-ENG-002` | EMA, volume, RSI, trendline touch và scoring threshold là lớp xác nhận/engineering choices của repo. | `IMPLEMENTATION_DERIVATION` hoặc `UNVERIFIED` tùy claim | Không được trình bày như rule nguyên bản của Covel; tham số phải được backtest riêng. |
| `TF-ENG-003` | Một chiến lược có thể áp dụng nguyên xi cho mọi symbol/timeframe hoặc luôn có win rate thấp/cao. | `UNVERIFIED` | Không dùng làm fact; phải ghi phạm vi dữ liệu và KPI thực tế. |

## 4. Coverage theo yêu cầu MASTER_GOAL

| Miền kiến thức | P0 state | Nguồn/việc còn lại |
|---|---|---|
| Systematic vs discretionary | Có author material về giảm discretion sau khi chọn system; chưa có full book | `SRC-COVEL-TEN-TENETS`; bổ sung sách hợp pháp nếu Founder cung cấp. |
| Reaction, price-driven decisions | Có author material | `TF-COV-001`, `TF-COV-002` |
| Entry/exit philosophy | Có author material ở mức nguyên tắc, chưa có tham số chiến lược cụ thể | `TF-COV-003`, `TF-COV-004`; strategy/backtest phải kiểm chứng. |
| Cut losses / let profits run | Có author material | `TF-COV-003`; không suy ra % stop/target. |
| Position sizing / volatility / leverage | Có author framing về size/risk/volatility; số cụ thể của repo chưa được nguồn | `SRC-COVEL-THEORY`; mọi con số là engineering/risk policy. |
| Drawdown / correlation / diversification / portfolio | Có author framing và primary research hỗ trợ một phần | `SRC-COVEL-THEORY`, `SRC-CENTURY-2014`; cần portfolio backtest có cost. |
| Long/short | Có author material và primary research có long/short futures framing | Không mặc định broker/MT5 semantics; cần strategy spec. |
| Behavior / discipline | Có author material | `SRC-COVEL-TEN-TENETS`; chuyển thành audit/log rules của repo là derivation. |
| Statistical/scientific thinking | Có author framing; evidence định lượng nằm ở primary research | `SRC-COVEL-RESEARCH`, `SRC-TSMOM-2012`, `SRC-CENTURY-2014` |
| Compounding / crisis / black swan | Có author framing về large winners/crisis, nhưng outcome phụ thuộc implementation | Cần stress/cost/portfolio tests; không claim guarantee. |
| Performance evaluation | Có checklist author; chưa có AI-TRADE result | `TF-COV-004`; KPI phải đến từ reproducible backtest/paper evidence. |

## 5. Boundary bắt buộc

- `Trend Following, Fifth Edition` là nguồn triết lý ưu tiên theo `MASTER_GOAL`,
  nhưng P0 **không được tuyên bố đã học toàn bộ sách** khi chưa có full lawful
  copy trong workspace.
- Không có claim nào trong tài liệu này được dùng để mở live-money trading, thay
  hard risk limits, hoặc coi author marketing/performance statement là bằng chứng
  thực nghiệm của AI-TRADE.
- Không gắn tên Covel vào `EMA 200`, `SMA 20`, `80/100`, `60% body ratio`, swing
  `N`, R/R hoặc các con số khác nếu chưa có provenance riêng.
- Tất cả kết quả của AI-TRADE phải được ghi là `UNVERIFIED`, `CODE VERIFIED`,
  `SIMULATION VERIFIED`, hoặc level phù hợp; không nâng lên production/live claim.

## 6. Cập nhật provenance

Khi Founder cung cấp bản sách hợp pháp hoặc khi một paper/backtest mới được kiểm
chứng, cập nhật registry và claim matrix trước khi sửa strategy/risk/MT5. Mọi
claim mới phải có một ID, một provenance label, một nguồn hoặc lý do `UNVERIFIED`,
và phạm vi áp dụng rõ ràng.

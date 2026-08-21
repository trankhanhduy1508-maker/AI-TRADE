# Trend Following — Kiến thức canonical

> Đây là bản tóm tắt khái niệm của AI-TRADE, không phải bản sao của sách. Claim
> có mã provenance trong `knowledge/COVEL_TREND_FOLLOWING_PROVENANCE.md`.
> Workspace chưa có full lawful copy của `Trend Following, Fifth Edition`, nên
> tài liệu này không tuyên bố đã ingest toàn bộ sách.

## 1. Phạm vi và nguồn

Trend Following trong AI-TRADE được dùng như một khung phản ứng với dữ liệu giá,
không phải lời hứa dự đoán hay bảo đảm lợi nhuận.

- `VERIFIED_FROM_AUTHOR`: các nguyên tắc công khai của Michael Covel về price,
  reaction, loss/profit asymmetry, rule discipline và portfolio/risk framing.
- `VERIFIED_FROM_PRIMARY_RESEARCH`: các kết quả nghiên cứu time-series momentum
  và trend-following trong universe, sample, horizon, cost assumptions của từng
  paper; không gán các kết quả đó ngược cho Covel.
- `IMPLEMENTATION_DERIVATION`: cách AI-TRADE định nghĩa HH/HL/LH/LL, BOS/CHoCH,
  breakout/pullback, EMA, volume, timeframe hay score để có thể kiểm thử.
- `UNVERIFIED`: claim chưa có nguồn hoặc chưa có backtest của AI-TRADE.

Registry nguồn đầy đủ: `knowledge/COVEL_TREND_FOLLOWING_PROVENANCE.md`.

## 2. Price và reaction

Theo `VERIFIED_FROM_AUTHOR` (`TF-COV-001`, `TF-COV-002`), giá là dữ liệu quan sát
chính để tạo quyết định; hệ thống không cần dựng một câu chuyện fundamentals để
biện minh cho một lệnh. “Reaction” nghĩa là chờ điều kiện giá đã xảy ra theo rule
định nghĩa trước, thay vì đoán điểm bắt đầu/kết thúc hoặc cố bắt đúng đáy/đỉnh.

Điều này không có nghĩa mọi dữ liệu phụ đều bị cấm. Trong AI-TRADE, price action
và cấu trúc là lớp quyết định chính; volume/EMA/RSI chỉ là xác nhận theo quyết
định repo, không phải kết luận nguyên bản của Covel.

## 3. Trend là khái niệm, rule là implementation

Ở mức khái niệm, một thị trường có thể tăng, giảm hoặc đi ngang. Mô tả HH/HL cho
xu hướng tăng và LH/LL cho xu hướng giảm là cách AI-TRADE operationalize khái niệm
đó (`IMPLEMENTATION_DERIVATION`, `TF-ENG-001`), không phải một tham số đã được
Covel chốt cho repo.

Việc xác định swing, độ dài lookback, BOS/CHoCH, breakout hợp lệ, pullback và
ngưỡng false-break phải được viết thành rule có input/output rõ ràng. Nếu chưa có
backtest cho một symbol/timeframe cụ thể, trạng thái vẫn là `UNVERIFIED`.

## 4. Entry, exit và bất đối xứng lãi/lỗ

Author material của Covel (`VERIFIED_FROM_AUTHOR`, `TF-COV-003`, `TF-COV-004`)
nhấn mạnh hai việc: kiểm soát lỗ theo rule và không cắt ngắn một vị thế thắng chỉ
vì muốn chốt một mức lợi nhuận cố định. Một hệ thống tối thiểu phải trả lời được:

1. Giao dịch market/instrument nào?
2. Kích thước vị thế được tính thế nào?
3. Điều kiện vào lệnh là gì?
4. Khi nào thoát vị thế thua?
5. Khi nào thoát vị thế thắng?

Các câu trả lời cụ thể của AI-TRADE thuộc strategy spec và risk policy. Không được
tự suy ra phần trăm stop, target, R/R hoặc win rate từ tên “Covel”.

Stop loss và exit theo xu hướng là hai khái niệm cần tách trong strategy docs:
stop bảo vệ khi giả thuyết sai; exit/trailing rule quyết định khi nào không còn
giữ vị thế thắng. Việc dùng tham số nào chỉ được coi là có giá trị sau khi kiểm
chứng trên dữ liệu phù hợp.

## 5. Systematic và kỷ luật

`VERIFIED_FROM_AUTHOR` (`TF-COV-005`) ủng hộ giảm discretionary override sau khi
đã chọn system, portfolio và risk policy. Đây là lý do AI-TRADE cần deterministic
rules, audit log và risk gateway độc lập. LLM có thể phân tích hoặc phản biện,
nhưng không được tự quyết định hard risk limit hay bỏ qua kill switch.

Mục tiêu kiểm thử không phải tạo equity curve đẹp bằng cách sửa rule sau mỗi kết
quả. Phải tách hypothesis, rule, test condition và backtest result; mọi con số
chưa qua kiểm chứng là `UNVERIFIED` hoặc `IMPLEMENTATION_DERIVATION`.

## 6. Bằng chứng độc lập và giới hạn diễn giải

Các nghiên cứu primary research được giữ riêng với author philosophy:

- `VERIFIED_FROM_PRIMARY_RESEARCH` (`TF-PR-001`): Moskowitz, Ooi và Pedersen
  báo cáo time-series momentum trong nhiều asset class/horizon trong sample của
  họ, cùng các đặc tính reversal dài hạn được nêu trong paper.
- `VERIFIED_FROM_PRIMARY_RESEARCH` (`TF-PR-002`): Hurst, Ooi và Pedersen báo cáo
  kết quả lịch sử dài về returns/correlation/diversification trong sample nghiên
  cứu của họ.

Hai kết quả trên không chứng minh chiến lược AI-TRADE, không chốt lookback 12
tháng, không thay risk policy, và không bảo đảm kết quả tương lai. AI-TRADE phải
kiểm chứng riêng theo market, timeframe, data quality, spread, commission, swap,
slippage, position sizing và portfolio correlation.

## 7. Điều không được khẳng định

- Trend Following không được trình bày là luôn sinh lời, luôn thắng, hoặc miễn
  nhiễm drawdown/black-swan.
- Không suy diễn một kết quả từ symbol/timeframe này sang symbol/timeframe khác.
- Không coi “thắng nhiều” là mục tiêu đủ; expectancy, drawdown, tail behavior,
  cost realism và khả năng tái lập mới là các mục tiêu kiểm chứng.
- Không gắn Covel với EMA period, SMA period, volume threshold, body ratio, swing
  window, score threshold, R/R hay phần trăm risk do repo tự chọn.
- Không mở MT5/live-money trading ở P0.

## 8. Pipeline conceptual để backtest sau P0

Pipeline chỉ là mapping kỹ thuật của repo (`IMPLEMENTATION_DERIVATION`), không phải
trích dẫn từ sách:

`market data -> trend qualification -> signal -> independent risk gate -> execution simulation -> evaluation`

Signal engine không được tự quyết risk. Khi risk gate reject, execution simulator
không tạo lệnh. Khi chưa đủ dữ liệu hoặc state không chắc chắn, trạng thái phải
được ghi nhận và không được biến thành claim hiệu quả.

## 9. Trạng thái P0

Đã hoàn thành audit provenance và chuẩn hóa canonical boundary trong báo cáo
`reports/P0_COVEL_TREND_FOLLOWING_AUDIT_2026-08-22.md`. Strategy spec và backtest
reproducible là bước sau, không được đánh dấu hoàn tất trong tài liệu này.

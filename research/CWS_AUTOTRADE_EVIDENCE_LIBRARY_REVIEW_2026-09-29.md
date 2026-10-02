# CWS AutoTrade — Tổng hợp bằng chứng có thể truy cập (2026-09-29)

**Mục tiêu:** phân biệt kết quả nghiên cứu gốc, hướng dẫn phương pháp, giới hạn truy cập và điều đã thực sự kiểm chứng trong R0. Tất cả dữ kiện dưới đây được kiểm tra từ abstract bài báo/tài liệu giới thiệu hoặc mục lục do đơn vị xuất bản cung cấp; KHÔNG giả nhận đã đọc trọn những chương sách bị giới hạn quyền truy cập.

| Nguồn | Phạm vi thực sự kiểm tra | Điều được nguồn hỗ trợ | Điều nguồn KHÔNG chứng minh cho CWS |
|---|---|---|---|
| Moskowitz, Ooi, Pedersen (2012), Time series momentum, *JFE* | Abstract bài nghiên cứu, trang Elsevier open access, https://doi.org/10.1016/j.jfineco.2011.11.003 | Bài báo trình bày kết quả momentum chuỗi thời gian trên **58** hợp đồng futures thanh khoản ở nhóm chỉ số, tiền tệ, hàng hóa và trái phiếu; quan sát động lượng 1–12 tháng | Không xác nhận breakout 55 nến H4/D1, Yahoo CFD giả định, hoặc hiệu quả sau phí của CWS năm 2026. Đây là động cơ thử nghiệm, không phải kết quả CWS |
| Bailey, Borwein, López de Prado, Zhu (2017), The Probability of Backtest Overfitting | Abstract từ kho lưu trữ học thuật UC, https://escholarship.org/uc/item/4w1110bb ; DOI https://doi.org/10.21314/jcf.2016.322 | Đề xuất đo xác suất backtest overfitting (PBO), sử dụng combinatorially symmetric cross-validation; chỉ holdout thông thường có thể không đủ khi sàng lọc chiến lược | Không được tính PBO từ vài lệnh rồi tuyên bố chắc chắn, không khắc phục được holdout từng bị xem qua |
| Harvey, Liu, Zhu (2016), ...and the Cross-Section of Expected Returns | Abstract Oxford RFS, https://doi.org/10.1093/rfs/hhv059 | Bài báo khảo sát nhiều yếu tố dự báo lợi nhuận được công bố, làm nổi bật vấn đề kiểm định nhiều giả thuyết | Không tự cung cấp mức t tối ưu hay ngưỡng lợi nhuận cho 28 thị trường CWS |
| Aronson (2006/2007), *Evidence-Based Technical Analysis* | Giới thiệu, mục lục và abstract chương 1/6 của Wiley, https://onlinelibrary.wiley.com/doi/book/10.1002/9781118268315 | Quy tắc giao dịch khách quan, so với benchmark, kiểm soát look-ahead, chi phí và sai lệch do khai thác dữ liệu là chủ đề phương pháp trọng tâm | Không công nhận bất kỳ chỉ báo kỹ thuật nào là luôn sinh lời; chương đầy đủ ngoài phần xem trước chưa được đọc |
| Robert Carver (2015), *Systematic Trading* | Trang nhà xuất bản, mô tả và mục lục https://harriman.house/books/systematic-trading/ | Đề cập volatility targeting, position sizing, danh mục, chi phí giao dịch, giới hạn của việc phức tạp hóa mô hình | Không thể suy ra giới hạn vốn thực thi từ chỉ số R khi CWS chưa có contract size/multiplier và chuyển đổi tiền tệ |
| Larry Harris (2002), *Trading and Exchanges* | Oxford publisher abstract và mục lục https://academic.oup.com/book/52292 , abstract chương transaction costs https://academic.oup.com/book/52292/chapter-abstract/421090015 | Nghiên cứu cấu trúc thị trường, loại lệnh, bid/ask và đo chi phí thực thi; chi phí có thể quyết định kết quả chiến lược giao dịch thường xuyên | Không phải bảng spread broker CWS; phần chương đầy đủ yêu cầu truy cập nên chưa đọc |
| Ernest P. Chan (2009), *Quantitative Trading* | Wiley giới thiệu và metadata https://onlinelibrary.wiley.com/doi/book/10.1002/9781119203377 | Sách bàn về xây dựng hoạt động giao dịch định lượng trên thực tế | Chưa có quyền đọc đầy đủ để khẳng định một công thức hoặc tham số riêng của tác giả |
| Marcos López de Prado (2018), *Advances in Financial Machine Learning* | Wiley metadata, mô tả và mục lục https://www.wiley-vch.de/en?isbn=9781119482086&option=com_eshop&view=product | Mục lục có dữ liệu tài chính, cross-validation, bet sizing, nguy cơ backtesting, backtest statistics và rủi ro chiến lược | Không dùng sách làm bằng chứng ML của CWS đã được huấn luyện, không tự áp dụng kỹ thuật được nhắc tên từ chương chưa đọc |

## Bài học áp dụng được vào quy trình, không phải khai thác holdout
1. Ghi **chính xác giả thuyết, tham số, phiên bản mã và split trước khi đánh giá**, như đã làm với commit prereg R0 `9041d3de3122abfb41ef8ab2f0fca12f114307cf`.
2. Khi R0 đã xem historical OOS, coi dữ liệu đó đã bị lộ vĩnh viễn. Không chọn “17/30 ô có expectancy dương” làm danh sách giao dịch triển khai: 17 con số đó xuất hiện sau khi mở holdout, mỗi ô đều chưa đạt 30 giao dịch.
3. Đánh giá kết quả trong **đúng thị trường, đúng sản phẩm và đúng chu kỳ**. Momentum futures hàng tháng trong JFE không suy ra cho breakout H4 của thị trường spot, chỉ số tiền mặt hay CFD.
4. Báo cáo cả thua lỗ, trường hợp không có dữ liệu, số lần thử tham số, trạng thái giới hạn chi phí, sai lệch và phí swap. Không lấy mã giả lập có lãi rồi gọi là after-cost broker.
5. Kiểm tra portfolio risk theo contract multiplier, lot step, mức ký quỹ, chuyển đổi tiền tệ *point-in-time*, chi phí và nguồn thực. Nếu thiếu, fail-closed và chỉ trình bày đơn vị giá/R.
6. Chỉ forward thật bắt đầu từ một mốc đã khóa **trước khi có sự kiện mới** mới có thể góp bằng chứng độc lập; bộ test sử dụng synthetic future timestamp của R1 chỉ kiểm tra mã, không phải forward.

## Trạng thái nguyên lý được kiểm định tại CWS
| Nguyên lý | Thực nghiệm R0 | Bằng chứng độc lập | Quyết định |
|---|---|---|---|
| Breakout + SMA200 + ATR/trailing không RR cố định | 30 ô đã đánh giá, 26 H4 thiếu dữ liệu | Không có; 0/30 đủ 30 lệnh OOS | `UNPROVEN`, giữ R0 để audit, không promotion |
| Next-bar-open + adverse-gap stop | Smoke/Runtime/Fault synthetic tests 14 bài × 3 vòng PASS | Chứng minh hợp đồng logic của simulator, KHÔNG chứng minh giá khớp thực | Giữ kiểm thử; cần dữ liệu bid/ask/tick thực |
| Chi phí thực thi/portfolio 0.25%/1% | 25 gross, 5 giả định; không có quy đổi tài khoản | Không có fee/multiplier broker đủ | `BLOCK_ACCOUNT_PNL` |
| Kỷ luật holdout, nguồn, forward | Manifest committed trước R0 historical OOS; R1 độc lập đăng ký trước mốc 2026-09-30 | R0 lịch sử có khả năng chồng nghiên cứu cũ; forward chưa bắt đầu | Không tuyên bố lợi thế thực |
| R1 nguồn forward | 18 bài synthetic × 3 vòng PASS, SHA chain và quarantine | Chưa có một bar mới nào được audit | `SOURCE_NOT_VERIFIED`; không tạo lệnh |

**Quy tắc trích dẫn:** chỉ dùng nguồn chính thống nêu trên, không sao chép chương sách hoặc báo cáo vượt quyền truy cập, không áp đặt sách là chân lý. Khi bổ sung tài liệu phải ghi URL, người viết, ngày, đoạn được phép truy cập, giả thuyết cụ thể, dataset phù hợp và kết quả test độc lập.

# CWS AutoTrade R1 — Đăng ký trước nguồn M1 → H4, KHÔNG phải H4 gốc (2026-09-29)

**Trạng thái: SOURCE_FEASIBILITY_ONLY.** Đây là nghiên cứu nguồn dữ liệu để giảm lệ thuộc OANDA token, không thay thế các ô `DATA_UNAVAILABLE_NATIVE_H4` của R0, không đánh giá lợi nhuận hoặc mở lại holdout đã xem. Đặc tả R0 `9041d3de3122abfb41ef8ab2f0fca12f114307cf` và mọi kết quả đã công bố giữ nguyên.

## Nguồn chính thống và ranh giới
HistData giới thiệu tải miễn phí dữ liệu M1 và tick, không cung cấp H4 gốc, và mô tả Generic ASCII M1 dưới dạng sáu trường `YYYYMMDD HHMMSS;open;high;low;close;volume`. OHLC dựa trên giá BID; múi giờ cố định EST (UTC−05:00), **không áp dụng daylight savings**. Ghi nhận dữ liệu hiện sẵn cho 13 cặp FX trong nghiên cứu, vàng/bạc, WTI/Brent và proxy SPX/USD, NSX/USD (tổng 19 loại nếu URL/tệp thực tế hợp lệ). Không thấy xác nhận nguồn cho Dow Jones và 6 cổ phiếu trong danh sách này. Trang công khai có thông báo cũ, **không** coi đó là bằng chứng dữ liệu luôn cập nhật tới tháng 9/2026.

Nguồn: https://www.histdata.com/download-free-forex-data/ ; https://www.histdata.com/f-a-q/data-files-detailed-specification/ ; https://www.histdata.com/f-a-q/ . Dịch vụ FTP/SFTP nhanh tính phí, **không sử dụng**: https://www.histdata.com/download-by-ftp/ .

Tệp nguồn chỉ nhận từ trang tải miễn phí sau khi xác minh điều khoản cho nghiên cứu; ghi URL tải, phiên bản, số byte và SHA-256 nguyên gốc; không tải hàng loạt bằng cách đoán endpoint; không đăng raw dữ liệu lên repo công khai. Nếu tệp/giấy phép không xác minh, `DATA_UNAVAILABLE`.

## Quy tắc chuyển đổi được khóa trước khi xem bất kỳ kết quả hiệu quả
1. Mỗi dòng M1 có chính xác timestamp EST cố định UTC−05:00, không chuyển thành America/New_York (có DST). Chuyển timestamp sang UTC bằng cộng 5 giờ, bất biến trong năm.
2. Parse 6 trường ASCII phân tách `;`, yêu cầu timestamp phút giây 00, OHLC hữu hạn/dương/nhất quán; cấm duplicate và dữ liệu lộn thứ tự. Volume nguồn 0 nghĩa là **không có thông tin volume**, không tự tạo thanh khoản.
3. Tạo H4 `DERIVED_H4_BID_ONLY` từ đúng 240 nến M1 liên tục với các timestamp cách nhau 60 giây. Căn ranh giới tại 17:00 **EST cố định** (tức 22:00 UTC), lặp mỗi 4 giờ. Open=giá bid M1 đầu tiên; high=max bid highs; low=min bid lows; close=bid close phút cuối. Không forward-fill hoặc tự dựng phút vắng.
4. Nếu thiếu một phút, thiếu đầu/cuối block, duplicate, nến chưa đóng, hoặc qua đứt phiên: loại **toàn bộ** block và ghi cụ thể `GAP_OR_INCOMPLETE_H4`; không giữ H4 giả. Chỉ xuất H4 khi có đúng 240 phút hợp lệ.
5. Ghi `derived_from=HISTDATA_GENERIC_ASCII_M1_BID`, `is_native_h4=false`, `is_mt5_broker=false`, `ask_available=false`, `actual_spread_available=false`, `execution_costs_verified=false`, hash raw/normalized và số block loại.
6. HistData instrument SPX/USD, NSX/USD và dầu là **sản phẩm/feed nguồn riêng**; không đồng nhất với S&P500/Nasdaq100 cash, Yahoo front month hay CFD trên MT5. Chỉ có thể kiểm tra hiệu quả `GROSS_ONLY`, không đánh giá lợi nhuận tiền thật.

## Hạn chế khoa học
Các ngày từng dùng TF-004/TF-014/R0 được xếp `HISTORICAL_REUSED`; không phải holdout độc lập dù tệp giá mới tải về. Bản nghiên cứu từ HistData nếu thực hiện phải tạo manifest cố định trước khi xem kết quả: nguồn+instrument+UTC+quyền sử dụng+hash+train/validation/holdout theo thời gian. Giữ nguyên R0 55/20/ATR2.5, không tối ưu từ OOS. Nếu chỉ dùng để thẩm định importer, không chạy backtest. Việc mua dữ liệu, FTP hoặc token không nằm trong nhiệm vụ.

## Forward
Giá open khôi phục từ file M1 đã tải sau khi sự kiện diễn ra là `HISTORICAL_REPLAY`, không phải timestamped forward paper. Dữ liệu đủ điều kiện forward cần quan sát theo thời gian thực sau `2026-09-30T00:00:00Z`, chi phí bid/ask/fees được chứng thực và kho raw được phép lưu. Bộ chuyển đổi M1 này **không** giải quyết được rào cản forward/broker-cost.

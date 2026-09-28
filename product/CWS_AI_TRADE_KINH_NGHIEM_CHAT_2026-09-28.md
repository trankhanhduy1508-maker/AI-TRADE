# CWS AI Trade — Kinh nghiệm đúc kết từ phiên 2026-09-28

## 1. UI giao dịch phải ưu tiên dữ liệu thật hơn vẻ đẹp

Founder yêu cầu mỗi cặp chỉ hiện một dòng tổng hợp:
- symbol/cặp;
- BUY/SELL;
- tổng Lot của các vị thế thuộc cặp;
- tổng P/L của các vị thế thuộc cặp;
- bên trên có tổng P/L toàn bộ vị thế.

Quy tắc trung thực:
- không biến `synthetic_volume` thành Lot thật;
- không biến `floatingR` hay `unrealizedR` thành P/L USD;
- thiếu dữ liệu thật thì hiện `—`;
- nếu một cặp có nhiều vị thế, tổng Lot/P&L chỉ được tính khi dữ liệu cần thiết của tất cả vị thế trong nhóm đều hợp lệ.

## 2. Training Arena khác broker position

Ảnh Founder kiểm tra cho thấy khu vực đang hiển thị là Training Arena paper, không phải MT5/broker position.

Nguồn Arena có:
- symbol;
- side/direction;
- entry/stop/current mark;
- unrealized R.

Nguồn Arena không có broker Lot thật hoặc broker P/L USD.

Giải pháp đúng:
- ghi rõ `Paper Lot` cho simulation lot;
- P/L Arena hiển thị bằng đơn vị `R`;
- tổng Arena cũng tổng theo `R`;
- broker/live/demo position mới dùng Lot + P/L tiền thật khi API cung cấp.

Không được dùng số paper/synthetic để làm người dùng tưởng là broker volume.

## 3. Aggregate position theo symbol

Founder không muốn thấy nhiều dòng EURUSD chỉ để tự cộng bằng mắt.

Ví dụ:
- EURUSD position A: 1 lot
- EURUSD position B: 2 lot

UI mong muốn:
- EURUSD: 3.00 lot, một dòng duy nhất.

P/L cũng aggregate theo symbol.

Nếu cùng một symbol đồng thời có BUY và SELL, UI phải thể hiện trạng thái mixed/hedged thay vì tự chọn một side và che mất sự thật.

## 4. Backtest: bài học quan trọng hơn con số headline

E-book không nên là dump log/report. Phải chắt lọc kinh nghiệm có evidence.

Các nguyên tắc đã đưa vào sách:
- phản ứng với thị trường thay vì dự đoán;
- win rate không đủ để đánh giá strategy;
- phải đọc expectancy, payoff, drawdown, cost và concentration cùng nhau;
- OOS và walk-forward quan trọng để giảm tự lừa bởi in-sample fit;
- spread/commission/slippage có thể xóa edge;
- execution assumption close-price quá đẹp có thể sụp khi chuyển next-open/gap-aware;
- một vài winner rất lớn có thể làm headline return nhìn khỏe trong khi hệ thống mong manh;
- diversification chỉ có ý nghĩa nếu lợi nhuận không phụ thuộc vài market;
- pyramiding phải test, không được mặc định là tốt.

## 5. Ví dụ concentration risk đáng nhớ

Gold từng có headline OOS rất cao nhưng phần lớn lợi nhuận đến từ một winner cực lớn.

Bài học:
- luôn kiểm tra top-trade contribution;
- chạy leave-one-out / remove-top-N winners;
- nếu bỏ một winner mà expectancy hoặc net R sụp mạnh thì edge chưa robust;
- headline return không phải bằng chứng đủ để promote strategy.

## 6. Thành công và thất bại đều phải vào tài liệu

Founder muốn học kinh nghiệm, không chỉ xem chiến thắng.

E-book phải có chương riêng:
`Những gì AI thử và thất bại`.

Các loại thất bại cần giữ:
- strategy âm ở holdout;
- walk-forward không ổn định;
- cost stress làm đảo dấu lợi nhuận;
- market concentration;
- parameter sensitivity;
- pyramiding làm kết quả xấu hơn;
- execution realism làm strategy từ dương thành âm;
- data/coverage không đủ để kết luận.

## 7. Quy tắc chứng cứ cho sách

- claim có số phải truy về report/database artifact thật;
- nếu không đủ evidence thì ghi inference hoặc bỏ;
- không marketing kiểu “AI thắng thị trường”;
- không hứa lợi nhuận;
- phân biệt rõ Research / Paper / Demo / Live;
- minh họa khái niệm phải ghi là minh họa, không giả thành backtest thật.

## 8. EPUB: lỗi font không nhất thiết là font

Bản EPUB đầu tiên hiển thị tiêu đề kiểu:
`CWS AI Trade ���`

Root cause thực tế là ký tự replacement `U+FFFD` đã nằm trong metadata/title XHTML sau bước convert, không chỉ là thiếu font.

Bài học:
- trước khi đổi font, scan toàn EPUB cho ký tự `�`;
- kiểm tra `content.opf`, `toc.ncx`, `nav.xhtml`, title page và cover XHTML;
- sửa encoding/source text trước;
- không chữa lỗi dữ liệu bằng cách nhúng thêm font.

## 9. EPUB TOC phải là navigation thật

Founder yêu cầu mục lục bấm vào chương phải nhảy tới đúng chương.

Validation cuối:
- EPUB đóng gói với `mimetype` là file đầu tiên và STORED/uncompressed;
- navigation nội bộ được kiểm tra;
- bản FIXED có 69 internal href và 0 broken target;
- không còn ký tự replacement `�`.

Artifact local cuối phiên:
`CWS_AI_Trade_10_Nam_Backtest_Sai_Lam_Kinh_Nghiem_AI_FIXED.epub`

## 10. Quy trình tạo EPUB nên chuẩn hóa

Pipeline nên là:
1. dùng DOCX/source có Unicode chuẩn làm nguồn;
2. tạo EPUB;
3. unpack;
4. scan Unicode replacement chars;
5. kiểm tra metadata/title/toc/nav;
6. kiểm tra mọi internal href;
7. repack với mimetype đúng quy chuẩn;
8. mở trên mobile reader và desktop reader nếu có;
9. chỉ phát hành sau khi TOC navigation và tiếng Việt PASS.

Không convert trực tiếp PDF thành EPUB nếu còn DOCX/source reflowable tốt hơn.

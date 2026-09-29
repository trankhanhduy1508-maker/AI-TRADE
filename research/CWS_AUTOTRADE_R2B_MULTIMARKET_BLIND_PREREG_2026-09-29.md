# R2b — mở rộng backtest quá khứ nhiều thị trường (chốt TRƯỚC KHI đọc kết quả của nguồn mới)
**Ngày:** 2026-09-29; **repo:** trankhanhduy1508-maker/AI-TRADE; **nhánh duy nhất:** codex/p0-covel-knowledge-audit; **HEAD gốc kiểm tra:** c6bcb7132f9313ae5bdf1d7b768377fd2821a522.

## Bài toán và chống thiên lệch
- Không thể "quên" kết quả R0/R2 đã mở. Các file thị trường từ nguồn mới vẫn mang `HISTORICAL_REUSED_EXPLORATORY` ở cấp người nghiên cứu; không bao giờ được gắn nhãn independent OOS dù lựa chọn trong máy không dùng giá tương lai.
- Tiếp tục **giữ nguyên R2 precommit** `6934a383b145369bb2447da29b3232e7ef04ab4d`: 3 ứng viên R0_REFERENCE=55/20/2.5, FAST=40/15/2, SLOW=80/30/3, SMA200/ATR20, mỗi 250 nến, huấn luyện tối đa 1.000 nến chỉ trước T, >=5 lệnh train, điểm `mean_closed_R - 0.01 * max_marked_DD_R`, chọn mã từ điển khi bằng nhau; không đủ dữ liệu thì FLAT. Tín hiệu khi nến t đã đóng, vào ở OPEN nến t+1, gap stop ở OPEN xấu hơn; short chỉ khi có vehicle kiểm toán, nên **tạm chỉ LONG**.
- Thêm **đối chứng prereg** `R2_POSITIVE_TRAIN_GATE`: dùng cùng điểm/cùng ứng viên và cửa sổ của R2, nhưng nếu điểm train của ứng viên đứng đầu không **dương nghiêm ngặt**, giữ FLAT cho 250 nến kế; không đọc giá đoạn test để chọn. Chạy cả R2 chuẩn và gated **trên mọi nguồn**; không chọn phương án thắng theo dữ liệu test rồi tuyên bố holdout độc lập.
- Kết quả so sánh gốc: số fold, chọn/FLAT, số lệnh đóng, mean R đóng, tổng realized R của từng fold *không phải ROI*, tổng unrealized R đánh dấu riêng, marked R=realized+unrealized mỗi fold, DD, tỉ lệ fold âm/dương, gap losses, số lượng mẫu. Không gộp giá, R hoặc %-đầu-tư giữa thị trường thành tài khoản tiền nếu không có sizing/FX/contract. Không dùng lợi nhuận âm của fold để xóa fold đó. Không ép RR cố định.
- Vì R2 gốc reset vị thế tại ranh giới mỗi fold mà không thực hiện thanh lý, mọi fold có vị thế mở được báo riêng: báo realized và unrealized, *không* tự cộng thành PnL đã chốt, không giả định có thể chuyển sang fold khác. Kết luận chiến lược tradeable hoặc vốn thực bị chặn.
- Phí chưa được xác nhận từ đúng venue; chạy **GROSS_ONLY** làm đường cơ sở; các stress 10/20/30 bps của notional chỉ là kịch bản **MODELED** (nếu engine R2 cố định không hỗ trợ tỷ lệ phí động thì không phát minh kết quả sau phí, phải báo `COST_STRESS_NOT_RUN` và thực hiện mô-đun version riêng kèm QA).
- So sánh với FLAT=0 R mặc định và phương pháp R0_REFERENCE cố định cùng source, cùng range và cùng fill semantics. So sánh với passive buy-and-hold chỉ nếu có vehicle hợp lệ/adjusted corporate actions và đơn vị so sánh phù hợp; không kết luận lợi nhuận tuyệt đối từ cash-index proxy.

## Nguồn chốt trước kết quả
Nhóm A: `ejtraderLabs/historical-data` commit `fbd29b3cd85c0eea4f6e8b81c053f98fb3de22fd`, các file `SYMBOL/SYMBOLd1.csv` cho AUDJPY, AUDUSD, EURCHF, EURGBP, EURJPY, EURUSD, GBPJPY, GBPUSD, USDCAD, USDCHF, USDJPY, XAUUSD. Đầu nguồn khoảng cuối 2012, cuối nguồn đầu 2022 (xác định CHÍNH XÁC qua kiểm toán từng file). Giá trong **point-scale thô**, không diễn dịch số 130583 thành giá USD nếu chưa có thông số tick/digits. Forex là quote feed không phải MT5 account execution; XAUUSD cũng không tự tương đương GLD. H4 vẫn riêng, không dán nhãn source-native trước khi kiểm toán.

Nhóm B: `vivek-v-rao/OHLC-Vol`, commit `c46f69d94faacf389378a07d540b3c38fe182d33`, `prices_ohlc.csv` GH blob `81d478f4bb4a89804060a4957782bb9e054b2085` bao gồm SPY, QQQ, GLD, USO (và HYG không thuộc protocol này). Quan sát trước nghiên cứu: khoảng 2010-01-04→2026-04-15, **kiểm toán đủ mỗi ticker trước khi chạy**. ETF SPY != cash SPX, QQQ != cash NDX, GLD != XAUUSD, USO != WTI/Brent; giá có thể điều chỉnh split, `Adj Close` khác OHLC vì dividend; vintage lịch sử chưa được kiểm toán.

Nhóm C: `OStochastic/Daily-SPY-data-from-2000-2025` commit `3b9362c58409e89b8a184bf427410079c574b468`, `spy_data.csv` GH blob `fd424789a7547730397e755c417de34caf9cedac`, ngày tháng/giá sau 3 dòng header. Dùng làm **source-integrity cross-check** có cùng SPY và cửa sổ overlap; không đếm 2 nguồn SPY là 2 lần kiểm thử độc lập hoặc tự dùng nguồn thắng để tuyển phương pháp. Nếu adjusted-OHLC không đồng nhất với nguồn nhóm B thì ghi `ADJUSTMENT_MISMATCH`, không nối/pha giá âm thầm.

**Cổng nguồn:** mỗi file phải được chụp source commit+Git blob, exact symbol/header/dates, ngày trùng, OHLC bất hợp lý, nonfinite, zero, flat-OHLC bất thường, weekend/calendar gaps, raw hash, split/roll/adjustment và dạng quote. Ghi reject nếu chất lượng không đạt; không dùng native-date-only thành timestamp thực đã kiểm toán. Apache/MIT license của repository tác giả **không tự xác nhận** quyền phân phối giá thị trường gốc. Chỉ xử lý trong phiên read-only, không đẩy raw lên repo/Drive.

## Thứ tự và tiêu chí thực thi
1. Commit văn bản này **trước** khi xem kết quả từ các file nói trên; không xem output thử rồi đổi tiêu chí tuyển chọn.
2. QA simulator: parity trên synthetic và tái hiện R2 SPX 34-fold cũ trước khi gọi nguồn mới; nếu thất bại khóa `ENGINE_PARITY_BLOCKED`.
3. Kiểm toán nguồn, đóng băng exact SHA/row coverage trước chạy. Mọi giá bị loại có reason; không "giả" dữ liệu sớm hơn lúc có.
4. Chạy **tất cả** ô nguồn đủ D1, R2 tiêu chuẩn và R2_POSITIVE_TRAIN_GATE đã chốt; không skip fold thua; lưu dữ liệu tóm tắt và thất bại, không raw chưa có quyền.
5. Smoke→Runtime→Fault, xác thực deterministic future-suffix immunity, cost flags, loss/open position. Nếu FAIL sửa minimal diff, ghi fail và test lại.
6. Cần source feed mới và window chốt độc lập để biết cải tiến thực, không thể nâng `UNPROVEN` chỉ vì lịch sử đẹp. Không chạy ngầm/scheduler, LIVE/DEMO-send.

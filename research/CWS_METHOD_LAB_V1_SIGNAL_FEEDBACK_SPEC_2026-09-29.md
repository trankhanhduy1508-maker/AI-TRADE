# CWS METHOD LAB V1 — chốt giả thuyết cải tiến phương pháp, không nghiên cứu chi phí

**Ngày:** 2026-09-29. **Repo:** `trankhanhduy1508-maker/AI-TRADE`. **Nhánh duy nhất:** `codex/p0-covel-knowledge-audit`. **HEAD nguồn:** `1415bb02afaa8a4e1fd723d65231ca580fb9b094`.

## Phạm vi và lý do

Founder đổi ưu tiên: tập trung cải tiến logic ra quyết định **không chỉ backtest**, tạm **bỏ nghiên cứu chi phí**. Không đổi R0/R1/R2/R2b, không viết lại prereg R3 vốn đã khóa một quy tắc chọn mô hình có phí riêng. METHOD LAB V1 là **giả thuyết mới**, mã thử nghiệm chỉ vận hành nghiên cứu giấy, không gửi lệnh, không báo lợi nhuận ròng, không bật DEMO/LIVE, không tạo branch/môi trường đắt tiền, không sử dụng PC Founder. R2b historical results đều đã mở, chỉ được dùng để nêu **vấn đề cần điều tra**, không dùng để hiệu chỉnh tham số rồi tuyên bố đã thắng trên lịch sử đó.

Vấn đề kỹ thuật đã thấy: R2b H4 D1 mâu thuẫn; thích nghi theo mean-R quá khứ không bảo đảm hiệu quả; R2 tự đặt flat ở mỗi ranh giới 250 nến nhưng không thực thanh lý, gây kết quả không phản ánh một vị thế liên tục; H4 feed chưa xác minh session/timezone; kill-switch/cờ boolean đã từng bị kiểu dữ liệu không đúng vượt qua. Chi phí chưa kiểm toán phải tiếp tục được gắn `UNKNOWN`, **không** được biến thành 0 phí hay bỏ gate giao dịch thật.

## Giả thuyết và tham số kỹ thuật khóa trước thử nghiệm

1. **Tín hiệu phá vỡ có xác nhận**: giữ channel trước 55 bar, SMA200, ATR20; LONG chỉ khi close bar t > max(high của 55 bar **trước t**) + **0,25×ATR20(t)**, close > SMA200(t), SMA200(t) > SMA200(t−20), thân nến (close−open) >= **0,50×ATR20(t)** và close thuộc 25% trên của biên high/low tại t. SHORT chỉ nếu có short vehicle được kiểm toán, với điều kiện đối xứng. Mục đích cơ học: không lấy một cú chạm râu nến hay breakout yếu làm lệnh; **chưa chứng minh có lợi nhuận**.
2. **Cổng sốc biến động**: khi ATR20(t) > **2×median** của **100 ATR20 trước t**, không tạo lệnh mới. Không dùng high/low hay ATR từ bar tương lai. Không đủ indicator → `ABSTAIN`.
3. **Tự điều chỉnh theo lỗi ĐÃ ĐÓNG**: giữ tối đa 5 kết quả vị thế nghiên cứu vừa **đóng** (gross initial-risk units). Nếu >=3/5 lệnh đóng âm, đặt `QUARANTINE` trong **20 bar đầy đủ** sau thời điểm nhận đủ kết quả. Không lấy unrealized đánh đồng lệnh đóng; không sửa chiến lược hoặc xóa lệnh thua. Mục đích ngăn giao dịch dồn khi thị trường không phù hợp, có thể bỏ lỡ cơ hội và **chưa có lợi ích được kiểm chứng**. Sau một stop, nghỉ thêm 5 bar đầy đủ. Thời gian học là lúc có sự kiện đã hoàn thành, không phải ngày giao dịch cũ chép vào lịch sử.
4. **Một vị thế liên tục**: tín hiệu tại close t → pending và xem xét mở giả định ở OPEN t+1; gapped invalid initial stop → không vào. Dùng initial stop = close(t)−2,5ATR(t) cho LONG (đối xứng SHORT). Trailing theo 20 bar đã đóng **trước bar đang xét**, không được nới stop, gap stop thoát ở OPEN xấu hơn, stop chạm entry bar xử lý bảo thủ. KHÔNG reset trạng thái ở mốc 250 nến hoặc ngày; chỉ có 1 vị thế / mã, không tự tạo thanh lý khi hết mẫu.
5. **Fail-closed nguồn và phiên**: input phải có OHLC dương hợp lệ, thời gian tăng đơn điệu, nến đã đóng, thời điểm thu thập không sớm hơn bar close. Nếu gap khác khoảng chuẩn phải có session-calendar evidence đã được kiểm tra ở bên ngoài; các cờ kiểm tra phải là boolean `True` thật. Không suy diễn FX/H4 clock thành UTC-native chỉ vì nguồn ghi yyyy-mm-dd hh:mm. Cờ do test tự đặt True **không** tương đương kiểm toán nguồn độc lập.
6. **Không tự nâng cấp từ bài kiểm thử**: fixture synthetic/regime/adversarial dùng để chứng minh causality, giới hạn hành vi và state carry, **không** kết luận tăng expectancy. Khi triển khai dữ liệu market mới: đăng ký dataset/window mới, khóa SHA code+nguồn trước xem kết quả; so fixed R0/reference và V1 với tất cả âm/dương, sau đó paper forward độc lập. Không tối ưu tham số bằng R0/R2b đã mở.

## QA ba vòng và tiêu chí dừng

- Smoke: biểu thức tín hiệu dùng đúng prior channel, SMA slope quá khứ, body, close-location, shock, gating; `orders_sent=0` bất biến.
- Runtime SYNTHETIC: stream có breakout thật, breakout râu nến không hợp lệ, volatility spike, pending next-open, stop trailing/gap xấu hơn, carry qua 250 nến, tự cách ly sau 3/5 lệnh đóng âm; quyết định từ prefix bất biến nếu suffix bị sửa.
- Fault: duplicate/missing/unclosed/future bar, malformed OHLC/float NaN, cờ string `"true"`, historical gap không chứng thực, không có short authorization, nến chưa chốt, reset/sao chép trạng thái không được đưa lệnh giả. Tạo test FAIL → sửa tối thiểu → chạy lại, giữ bằng chứng.
- Không nghiên cứu phí/không gọi nguồn phí. V1 **không** tuyên bố net PnL, không bỏ existing real-trading fee/risk guard vì task chỉ là phương pháp RESEARCH_ONLY.

**Tham khảo động cơ, không phải bằng chứng V1 có lợi thế:** Moskowitz–Ooi–Pedersen (2012), Time Series Momentum, JFE 104:228–250, DOI 10.1016/j.jfineco.2011.11.003; Bailey et al. (2017), Probability of Backtest Overfitting, DOI 10.21314/JCF.2016.322. Hai công trình không chứng thực các ngưỡng 0,25ATR/0,50ATR/5bar/20bar của giả thuyết này.

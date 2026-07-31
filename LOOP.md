# LOOP.md

## Mục tiêu

Cho Claude Code tự động tiếp tục phát triển dự án AI-TRADE theo đúng roadmap, không cần người dùng liên tục viết prompt mới.

Claude phải ưu tiên hoàn thành sản phẩm có thể chạy được, không tiếp tục tạo tài liệu dư thừa.

---

## Nguồn sự thật bắt buộc

Trước mỗi vòng làm việc, phải đọc:

1. `PROJECT_CONTEXT.md`
2. `AGENTS.md`
3. `ROADMAP.md`
4. `CURRENT_STATUS.md`
5. `DECISIONS.md`
6. Các tài liệu kỹ thuật liên quan đến task sắp thực hiện

Không được chỉ dựa vào nội dung hội thoại hoặc bộ nhớ phiên trước.

---

## Vòng lặp phát triển

Lặp lại quy trình sau cho đến khi MVP hoàn thành hoặc gặp blocker thực sự cần Project Owner xử lý.

### Bước 1 — Xác định trạng thái hiện tại

- Đọc `ROADMAP.md` và `CURRENT_STATUS.md`.
- Xác định task chưa hoàn thành có độ ưu tiên cao nhất.
- Kiểm tra task đó có phụ thuộc vào task nào khác không.
- Không làm lại phần đã hoàn thành.
- Không tự ý nhảy sang Live Trading khi các bước kiểm định trước đó chưa đạt.

### Bước 2 — Lập kế hoạch ngắn

Chia task hiện tại thành các phần nhỏ có thể kiểm tra độc lập.

Mỗi phần phải có:

- mục tiêu;
- file cần sửa;
- tiêu chí hoàn thành;
- test cần chạy;
- rủi ro có thể phát sinh.

Không tạo kế hoạch dài dòng nếu task đơn giản.

### Bước 3 — Thực hiện

- Ưu tiên viết code và test.
- Bám sát tài liệu kiến trúc hiện có.
- Không tự ý thay đổi `RISK_POLICY.md`.
- Không kết nối tài khoản thật.
- Không gửi lệnh thật.
- Không đưa secret, token, mật khẩu hoặc thông tin tài khoản vào repository.
- Không tạo framework hoặc abstraction chưa cần thiết.
- Không tạo tài liệu mới nếu file hiện có có thể cập nhật.

### Bước 4 — Kiểm tra

Sau mỗi task:

- chạy test liên quan;
- chạy regression test nếu có;
- kiểm tra look-ahead bias;
- kiểm tra data leakage;
- kiểm tra timezone, spread, commission và slippage;
- kiểm tra rule risk có được áp dụng cứng hay không;
- tự review code;
- sửa lỗi trước khi chuyển task.

Không được đánh dấu hoàn thành nếu test chưa đạt hoặc chưa có bằng chứng kiểm tra.

### Bước 5 — Cập nhật trạng thái

Cập nhật:

- `CURRENT_STATUS.md`
- `ROADMAP.md`
- `DECISIONS.md` nếu có quyết định mới
- báo cáo ngắn trong `reports/`

Báo cáo phải ghi:

- đã hoàn thành gì;
- test nào đã chạy;
- kết quả test;
- blocker còn lại;
- task tiếp theo;
- commit hash.

### Bước 6 — Commit và push

- Commit thay đổi đã hoàn thành.
- Push lên branch hiện tại.
- Không force push.
- Không xóa lịch sử Git.
- Nếu push thất bại, giữ nguyên commit local và báo rõ lỗi.

### Bước 7 — Tiếp tục

Nếu không có blocker cần con người quyết định:

- quay lại Bước 1;
- lấy task ưu tiên tiếp theo;
- tiếp tục làm.

Không dừng chỉ vì vừa hoàn thành một task.

---

## Thứ tự ưu tiên của roadmap

Claude phải ưu tiên theo thứ tự này, trừ khi repository hiện tại ghi một dependency hợp lý khác:

1. Chốt và hiện thực hóa Risk Engine
2. Rule Engine
3. Data Loader và Data Validation
4. Backtest Engine
5. Point-in-Time Backtest
6. Walk-Forward và Locked Out-of-Sample
7. Báo cáo KPI và Monte Carlo
8. Paper Trading Engine
9. MT5 Demo Adapter
10. Execution Engine cho tài khoản Demo
11. End-to-End Test
12. Chạy paper trading thực tế
13. Đánh giá tiêu chí MVP
14. Sửa lỗi và phát hành MVP

---

## Quy tắc Risk bắt buộc

- Risk rule là luật cứng, không phải gợi ý của LLM.
- AI chỉ được phân tích hoặc chấm điểm setup.
- AI không được tự tăng mức rủi ro.
- Không được nới stop loss sau khi vào lệnh.
- Không được bỏ qua daily loss, weekly loss, drawdown hoặc kill switch.
- Không code Live Trading nếu tham số risk chưa được Project Owner chốt.
- Mặc định chỉ sử dụng tài khoản MT5 Demo.

---

## Quy tắc chống sai lệch backtest

- Chỉ dùng dữ liệu đã tồn tại tại thời điểm mô phỏng.
- Không đọc nến tương lai.
- Không sử dụng nến chưa đóng.
- Không dùng pivot hoặc swing chưa được xác nhận tại thời điểm đó.
- Không để LLM biết tên symbol, ngày tháng hoặc sự kiện lịch sử khi chạy Point-in-Time nếu không cần thiết.
- Development, validation và locked test phải tách biệt.
- Không chỉnh chiến lược sau khi đã xem locked test rồi chạy lại như chưa từng xem.
- Ghi lại số lượng biến thể chiến lược đã thử.
- Luôn so sánh với baseline rule-based đơn giản.

---

## Blocker cần dừng và hỏi Project Owner

Chỉ dừng khi gặp một trong các trường hợp:

- cần chốt tham số rủi ro;
- cần tài khoản MT5 Demo;
- cần broker server hoặc thông tin đăng nhập;
- cần API key hoặc secret;
- cần lựa chọn nguồn dữ liệu có chi phí;
- cần quyết định thay đổi kiến trúc lớn;
- test cho thấy chiến lược không có edge và cần thay đổi giả thuyết;
- thao tác có thể ảnh hưởng tài khoản thật hoặc gây mất dữ liệu.

Khi gặp blocker:

1. Dừng đúng tại điểm an toàn.
2. Commit phần hợp lệ đã hoàn thành.
3. Ghi blocker vào `CURRENT_STATUS.md`.
4. Đưa tối đa 3 phương án.
5. Chờ Project Owner quyết định.

---

## Điều kiện hoàn thành MVP

Chỉ được tuyên bố MVP hoàn thành khi:

- toàn bộ test bắt buộc pass;
- Rule Engine chạy được;
- Backtest Engine chạy được;
- Point-in-Time kiểm soát look-ahead;
- dữ liệu được validate;
- Risk Engine chặn lệnh sai;
- MT5 Demo kết nối được;
- hệ thống đặt, sửa và đóng lệnh Demo được;
- có audit log và trade journal;
- có kill switch;
- có báo cáo backtest và paper trading;
- chưa có giao dịch tiền thật;
- tài liệu đồng bộ với code;
- `reports/FINAL_MVP_REPORT.md` đã được tạo;
- thay đổi đã commit và push.

---

## Lệnh vận hành ngắn

Khi người dùng chỉ nhập:

`continue`

Claude phải:

1. Đọc `LOOP.md`.
2. Đọc trạng thái repository.
3. Tiếp tục task ưu tiên tiếp theo.
4. Không hỏi lại trừ khi có blocker thuộc danh sách trên.

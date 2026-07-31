# Kill Switch Rules — Cơ chế dừng khẩn cấp

## Nguyên tắc

Phải luôn tồn tại một cơ chế **dừng toàn bộ hoạt động giao dịch/tín hiệu ngay lập
tức**, có thể kích hoạt bất kỳ lúc nào, **không phụ thuộc vào việc AI có đồng ý
hay không**. Đây là yêu cầu bắt buộc theo `PROJECT_CONTEXT.md`.

## Các mức kích hoạt

### 1. Kill switch thủ công (Manual)

- Project Owner có thể dừng toàn bộ hệ thống bất kỳ lúc nào, không cần lý do,
  không cần AI xác nhận trước.
- Đây là mức ưu tiên cao nhất, ghi đè lên mọi tín hiệu/setup đang chờ xử lý.

### 2. Kill switch tự động theo hiệu suất

Kích hoạt tự động khi xảy ra một trong các điều kiện sau (ngưỡng số cụ thể lấy từ
`risk/RISK_POLICY.md`, hiện **chưa chốt số** — mục này định nghĩa **loại** điều
kiện, không phải giá trị cuối cùng):

- Số lệnh thua liên tiếp vượt ngưỡng đã định nghĩa.
- Drawdown vượt ngưỡng % vốn đã định nghĩa.
- Tổng rủi ro danh mục đang mở vượt giới hạn (xem `risk/RISK_POLICY.md`).

### 3. Kill switch theo bất thường hệ thống (khi có code thật)

Áp dụng khi hệ thống có phần code thực thi (hiện `src/` còn rỗng — mục này là
**thiết kế trước**, chưa có code triển khai):

- Mất kết nối dữ liệu giá kéo dài quá X phút.
- Phát hiện dữ liệu đầu vào bất thường (giá nhảy cóc phi lý, dữ liệu thiếu...).
- Lỗi lặp lại nhiều lần liên tiếp trong quá trình xử lý tín hiệu.

## Hành vi khi kill switch được kích hoạt

1. Dừng ngay việc sinh tín hiệu/setup mới.
2. **Không tự động đóng các lệnh đang mở** (nếu có ở giai đoạn tương lai có kết
   nối thật) trừ khi được quyết định rõ ràng riêng — kill switch chặn giao dịch
   MỚI, việc xử lý lệnh đang mở là quyết định riêng của Project Owner tại thời
   điểm đó.
3. Ghi log rõ lý do kích hoạt vào `research/FAILURE_CASES.md` nếu là kill switch
   tự động do hiệu suất/bất thường.
4. Yêu cầu xác nhận rõ ràng của Project Owner trước khi mở lại — không tự động
   khôi phục sau một khoảng thời gian.

## Điều AI không được làm

- Không được tự ý bỏ qua hoặc "tạm hoãn" kill switch để "chờ thêm 1 lệnh nữa".
- Không được tự động mở lại hệ thống sau khi kill switch kích hoạt.
- Không được đề xuất nới lỏng ngưỡng kích hoạt kill switch trong lúc đang phân
  tích một lệnh cụ thể — thay đổi ngưỡng chỉ thực hiện qua sửa
  `risk/RISK_POLICY.md` một cách có ý thức, tách biệt khỏi quyết định giao dịch.

## Trạng thái hiện tại

Đây là **thiết kế quy tắc**, chưa có cơ chế kỹ thuật thực thi (chưa có code, chưa
kết nối dữ liệu thật, chưa có tài khoản thật — xem `PROJECT_CONTEXT.md`). Việc
triển khai kỹ thuật của kill switch sẽ được thiết kế khi hệ thống bắt đầu có
phần thực thi thật trong `src/`.

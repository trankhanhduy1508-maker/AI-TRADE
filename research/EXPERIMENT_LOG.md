# Nhật ký thử nghiệm

> Ghi lại **mọi lần chạy backtest/thử nghiệm thật**, kể cả khi kết quả xấu. Không
> xóa thử nghiệm thất bại — đây chính là dữ liệu quan trọng để tránh lặp lại sai
> lầm (xem thêm `research/FAILURE_CASES.md` cho các ca thất bại điển hình).

## Cách dùng file này

Mỗi thử nghiệm ghi: ngày, chiến lược/giả thuyết được test, dữ liệu dùng, thay đổi
so với lần trước (nếu có), link kết quả trong `backtests/`, nhận xét ngắn.

---

## Chưa có thử nghiệm nào được chạy thật

Tính đến thời điểm tạo tài liệu này, hệ thống mới ở giai đoạn xây dựng nền tảng
tài liệu và giả thuyết — **chưa kết nối dữ liệu giá thật, chưa chạy backtest
nào**. Mục này sẽ được cập nhật ngay khi thử nghiệm đầu tiên hoàn tất (xem
`CURRENT_STATUS.md` mục Next Task).

### Template cho mỗi lần thử nghiệm (copy khi có thử nghiệm thật)

```
### [YYYY-MM-DD] — [Mã chiến lược] trên [thị trường/timeframe]

- Dữ liệu: [nguồn, khoảng thời gian]
- Thay đổi so với lần trước: [nếu có]
- Kết quả: xem backtests/[tên file kết quả].md
- Nhận xét: [ngắn gọn, khách quan — không diễn giải quá mức từ 1 lần chạy]
```

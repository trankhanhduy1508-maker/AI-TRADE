# Các ca thất bại (Failure Cases)

> Mục đích: ghi lại **cụ thể** những lần một giả thuyết/chiến lược thất bại —
> không phải để đổ lỗi, mà để tránh lặp lại cùng một sai lầm logic. Đây là tài
> liệu **sống**, cập nhật liên tục khi có bằng chứng thật, không phải danh sách
> lý thuyết viết một lần.

## Cách dùng file này

Mỗi ca ghi: mô tả thất bại, nguyên nhân gốc (không chỉ triệu chứng), giả
thuyết/chiến lược liên quan, hành động khắc phục đã áp dụng.

---

## Chưa có ca thất bại thật nào được ghi nhận

Hệ thống chưa chạy backtest hay giao dịch thật nào (xem
`research/EXPERIMENT_LOG.md`), nên chưa có dữ liệu thất bại thực tế để ghi vào
đây. Mục này sẽ được cập nhật ngay khi phát sinh ca đầu tiên — dù là từ backtest,
paper trade, hay quan sát thủ công.

## Các loại lỗi chủ quan đã biết trước (từ `knowledge/`, chưa phải "ca thất bại"
thật, chỉ là điều cần cảnh giác)

Tham khảo mục "Lỗi thường gặp" trong từng file `strategies/*.md` — đây là dự đoán
trước các lỗi có thể xảy ra dựa trên kinh nghiệm chung, **không thay thế** việc
ghi lại ca thất bại thật khi nó xảy ra.

### Template cho mỗi ca thất bại thật (copy khi có ca thật)

```
### [YYYY-MM-DD] — [Mô tả ngắn]

- Chiến lược/giả thuyết liên quan: [link]
- Mô tả: [chuyện gì đã xảy ra]
- Nguyên nhân gốc: [không chỉ triệu chứng — vì sao nó xảy ra]
- Hành động khắc phục: [đã sửa gì trong strategies/risk/knowledge]
```

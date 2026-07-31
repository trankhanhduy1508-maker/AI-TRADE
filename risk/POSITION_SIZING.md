# Position Sizing — Cách tính khối lượng lệnh

> Công thức, không phải phán đoán. LLM chỉ được áp dụng công thức dưới đây, không
> được tự điều chỉnh kết quả.

## Công thức chuẩn

```
Khối lượng lệnh = (Vốn x % rủi ro cho phép mỗi lệnh) / (Khoảng cách Entry → Stop Loss)
```

Trong đó:

- **Vốn**: số vốn được phân bổ cho hệ thống này (không nhất thiết là toàn bộ tài
  khoản) — xác định bởi Project Owner, không phải giả định của AI.
- **% rủi ro cho phép mỗi lệnh**: lấy từ `risk/RISK_POLICY.md` — hiện **chưa
  chốt số**, nên công thức này hiện chỉ áp dụng được ở dạng mô phỏng/backtest
  (giả định 1 con số cụ thể để thử nghiệm, ghi rõ trong từng lần backtest, không
  coi là giá trị chính thức).
- **Khoảng cách Entry → Stop Loss**: lấy trực tiếp từ quy tắc stop loss của từng
  chiến lược trong `strategies/` cho setup cụ thể đang xét — không phải số cố
  định chung cho mọi lệnh.

## Nguyên tắc bắt buộc

- Không vào lệnh nếu không tính được khoảng cách Entry → Stop Loss **trước** khi
  vào lệnh.
- Không tăng khối lượng lệnh sau khi đã vào lệnh để "gỡ" một lệnh đang thua
  (không có khái niệm nhồi lệnh/martingale trong hệ thống này).
- Không tính khối lượng lệnh dựa trên "cảm giác tự tin" vào setup — mọi setup dù
  được đánh giá "đẹp" đến đâu vẫn dùng cùng % rủi ro như nhau, trừ khi
  `risk/RISK_POLICY.md` định nghĩa rõ hệ thống phân hạng mức độ tin cậy setup
  (nếu có trong tương lai, phải là công thức rõ ràng, không phải cảm tính).

## Đòn bẩy (Leverage)

Chưa xác định chính sách cụ thể — thị trường có đòn bẩy (forex, crypto futures)
cần chính sách riêng, sẽ bổ sung khi Project Owner xác nhận thị trường mục tiêu
cụ thể. Cho tới khi đó: **không giả định bất kỳ mức đòn bẩy nào**.

## Ví dụ minh họa (chỉ để hiểu công thức, KHÔNG phải số chính thức)

Giả sử (chỉ để minh họa, không phải giá trị đã chốt): Vốn = 10,000, % rủi ro/lệnh
= 1%, Entry = 100, Stop Loss = 98 (khoảng cách = 2).

```
Khối lượng lệnh = (10,000 x 1%) / 2 = 100 / 2 = 50 đơn vị
```

Con số 1% ở trên là ví dụ minh họa cho công thức, **không phải giá trị chính thức
của hệ thống** — giá trị chính thức chờ chốt tại `risk/RISK_POLICY.md`.

## Liên hệ với backtest

Khi backtest ở giai đoạn giả thuyết (chưa chốt % rủi ro chính thức), báo cáo kết
quả trong `backtests/RESULTS_TEMPLATE.md` phải **ghi rõ % rủi ro giả định đã
dùng** để không nhầm là con số chính thức đã được duyệt.

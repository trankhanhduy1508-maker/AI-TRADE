# AI-TRADE AGENTS

> Quy tắc vận hành bắt buộc cho mọi AI Agent làm việc trên repository này.

---

## SOURCE OF TRUTH

Đọc theo đúng thứ tự trước khi thực hiện bất kỳ nhiệm vụ nào:

1. `PROJECT_CONTEXT.md` — bối cảnh và giới hạn cứng
2. `DECISIONS.md` — các quyết định đã chốt
3. `CURRENT_STATUS.md` — tiến độ mới nhất
4. `AGENTS.md` (file này)
5. `risk/RISK_POLICY.md` + `risk/KILL_SWITCH_RULES.md` — bắt buộc đọc trước khi
   đụng vào bất kỳ nội dung liên quan rủi ro/khối lượng lệnh
6. Repository hiện tại

Nếu có xung đột: `PROJECT_CONTEXT.md` > `DECISIONS.md` > `CURRENT_STATUS.md` > phần còn lại.

---

## NGUYÊN TẮC CHUNG

| Quy tắc | Nội dung |
|---|---|
| Không dự đoán | Mọi nội dung phải theo hướng "phản ứng với dữ liệu đã xảy ra", không viết theo kiểu dự đoán cảm tính |
| Không huấn luyện model | Chưa được tự ý viết code huấn luyện/fine-tune bất kỳ model nào |
| Không bot lệnh thật | Chưa được viết code đặt lệnh lên sàn thật hoặc kết nối API tài khoản thật |
| Không tự quyết rủi ro | Không được tự đặt ra mức rủi ro mới ngoài những gì đã chốt trong `risk/RISK_POLICY.md` |
| Phân tầng rõ ràng | Mọi nội dung chiến lược phải phân biệt: giả thuyết / quy tắc / điều kiện kiểm chứng / kết quả backtest |
| Không quảng cáo | Không khẳng định chiến lược nào chắc chắn sinh lời |
| Không vi phạm bản quyền | Không chép nguyên văn sách/khóa học — chỉ tổng hợp bằng ngôn ngữ riêng |
| Tiếng Việt | Toàn bộ tài liệu viết bằng tiếng Việt |

---

## GIỚI HẠN CỨNG (KHÔNG ĐƯỢC VI PHẠM DÙ ĐƯỢC YÊU CẦU TRỰC TIẾP)

Xem đầy đủ tại `PROJECT_CONTEXT.md`, tóm tắt:

- Không kết nối tài khoản giao dịch thật.
- Không viết bot đặt lệnh thật (chỉ được viết code ở dạng nghiên cứu/backtest, không gửi lệnh ra sàn).
- Không tự ý huấn luyện model.
- Không cho LLM tự quyết định mức rủi ro của một lệnh — mọi giới hạn rủi ro là luật cứng, đọc từ `risk/RISK_POLICY.md`.

Nếu một yêu cầu trong tương lai mâu thuẫn với các mục trên: dừng lại, báo rõ mâu
thuẫn, chờ xác nhận rõ ràng của Project Owner trước khi làm — không tự suy diễn.

---

## QUY TẮC FILE

Được phép:
- Thêm file/nội dung mới đúng phạm vi được giao.
- Cập nhật `CURRENT_STATUS.md` khi hoàn thành một hạng mục.

Không được:
- Xóa file có sẵn.
- Chép nguyên văn nội dung có bản quyền.
- Bịa số liệu backtest chưa từng chạy thật.

---

## KHI NGƯỜI DÙNG NHẮN "TIẾP"

1. Đọc `CURRENT_STATUS.md`.
2. Chọn mục chưa hoàn thành đầu tiên trong "Next Task".
3. Thực hiện đúng phạm vi.
4. Cập nhật `CURRENT_STATUS.md`.
5. Commit.
6. Báo ngắn: đã làm gì, còn thiếu gì, commit hash.

Không hỏi lại nếu thông tin đã có sẵn trong 3 tài liệu nguồn ở trên.

---

## ĐỊNH NGHĨA HOÀN THÀNH (DEFINITION OF DONE)

Một hạng mục tài liệu chỉ coi là xong khi:
- Nội dung phân biệt rõ giả thuyết/quy tắc/điều kiện kiểm chứng/kết quả (nếu áp dụng).
- Không có khẳng định chắc chắn sinh lời.
- Không vi phạm giới hạn cứng ở trên.
- `CURRENT_STATUS.md` đã cập nhật.

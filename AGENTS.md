# AI-TRADE AGENTS

> Quy tắc vận hành bắt buộc cho mọi AI Agent làm việc trên repository này.

---

## SOURCE OF TRUTH

Đọc theo đúng thứ tự trước khi thực hiện nhiệm vụ Auto Trade:

1. `PROJECT_CONTEXT.md` — bối cảnh và giới hạn cứng
2. `DECISIONS.md` — các quyết định đã chốt
3. `CURRENT_STATUS.md` — tiến độ mới nhất
4. `auto_trade/MASTER_GOAL.md` — North Star Auto Trade/MT5
5. `AGENTS.md` (file này)
6. `risk/RISK_POLICY.md` + `risk/KILL_SWITCH_RULES.md` — bắt buộc đọc trước khi đụng vào bất kỳ nội dung liên quan rủi ro/khối lượng lệnh
7. Các file code/knowledge/evidence liên quan trực tiếp task hiện tại

Không ground toàn repo nếu task chỉ liên quan một phần nhỏ.

Nếu có xung đột: `PROJECT_CONTEXT.md` > `DECISIONS.md` > `CURRENT_STATUS.md` > `auto_trade/MASTER_GOAL.md` > phần còn lại.

---

## SUPERPOWERS / SKILL DISCIPLINE

Nếu môi trường có Superpowers hoặc skills tương đương, phải kiểm tra và dùng skill liên quan **trước khi hành động**.

Tối thiểu:

- `using-superpowers`: kiểm tra skill trước công việc.
- `brainstorming`: trước feature/architecture/thay đổi behavior mới.
- `writing-plans`: cho implementation nhiều bước sau khi design đã rõ.
- `test-driven-development`: trước code feature/bugfix khi phù hợp.
- `systematic-debugging`: khi có bug/test failure/unexpected behavior.
- `verification-before-completion`: trước khi tuyên bố DONE/fixed/pass.

Không dùng skill như nghi thức hình thức. Phải thực sự làm theo workflow/checklist của skill.

User/Founder instructions và governance trong repo vẫn có ưu tiên cao hơn skill nếu có xung đột.

Nguyên tắc kỹ thuật mặc định:

**STABLE FIRST -> MINIMUM CHANGE -> VERIFY -> REWRITE LAST.**

---

## NGUYÊN TẮC CHUNG

| Quy tắc | Nội dung |
|---|---|
| Knowledge First | Với Auto Trade, ưu tiên audit/nâng cấp kiến thức Trend Following theo `auto_trade/MASTER_GOAL.md` trước khi tối ưu chiến lược/MT5 |
| Không dự đoán | Mọi nội dung phải theo hướng "phản ứng với dữ liệu đã xảy ra", không viết theo kiểu dự đoán cảm tính |
| Không huấn luyện model | Chưa được tự ý viết code huấn luyện/fine-tune bất kỳ model nào |
| Không bot lệnh thật | Giai đoạn hiện tại chưa được gửi lệnh tiền thật; demo/paper/research phải tuân governance hiện hành |
| Không tự quyết rủi ro | Không được tự đặt ra mức rủi ro mới ngoài những gì đã chốt trong `risk/RISK_POLICY.md` |
| Phân tầng rõ ràng | Mọi nội dung chiến lược phải phân biệt: giả thuyết / quy tắc / điều kiện kiểm chứng / kết quả backtest |
| Không quảng cáo | Không khẳng định chiến lược nào chắc chắn sinh lời |
| Không vi phạm bản quyền | Không chép nguyên văn sách/khóa học; chỉ tổng hợp bằng ngôn ngữ riêng và ghi provenance |
| Tiếng Việt | Toàn bộ tài liệu viết bằng tiếng Việt |

---

## GIỚI HẠN CỨNG

Xem đầy đủ tại `PROJECT_CONTEXT.md`, tóm tắt:

- Giai đoạn hiện tại chưa kết nối tài khoản giao dịch thật.
- Chưa gửi lệnh tiền thật ra broker.
- Không tự ý huấn luyện model.
- Không cho LLM tự quyết định mức rủi ro của một lệnh; mọi giới hạn rủi ro là luật cứng, đọc từ `risk/RISK_POLICY.md`.

`auto_trade/MASTER_GOAL.md` mô tả đích dài hạn là autonomous MT5. Điều đó **không tự động mở khóa live-money trading**. Live chỉ được bật khi Project Owner xác nhận rõ ràng ở giai đoạn sau.

---

## AUTONOMY

Agent được trao quyền tự xử lý routine technical decisions để tiến tới Goal:

- tự research, thiết kế, code, test, debug và verify;
- tự xử lý blocker thông thường;
- không hỏi Founder những gì có thể suy ra từ repo/evidence;
- không bắt Founder làm thao tác kỹ thuật nhỏ thay cho agent nếu agent/tool có thể tự làm.

Nhưng agent không được tự:

- thay đổi hard risk limits;
- unlock live-money trading;
- đưa credential/secrets vào repo;
- bịa kết quả test/backtest/evidence.

---

## QUY TẮC FILE

Được phép:
- Thêm file/nội dung mới đúng phạm vi được giao.
- Cập nhật `CURRENT_STATUS.md` khi hoàn thành một hạng mục.

Không được:
- Xóa file có sẵn nếu không có lý do/evidence bắt buộc.
- Chép nguyên văn nội dung có bản quyền.
- Bịa số liệu backtest chưa từng chạy thật.

---

## KHI NGƯỜI DÙNG NHẮN "TIẾP"

1. Đọc `auto_trade/BOOTSTRAP.md`.
2. Đọc `CURRENT_STATUS.md`.
3. Chọn mục ưu tiên chưa hoàn thành đầu tiên phù hợp `auto_trade/MASTER_GOAL.md`.
4. Dùng skill/workflow liên quan.
5. Thực hiện đúng phạm vi.
6. Test/verify.
7. Cập nhật `CURRENT_STATUS.md`.
8. Commit.
9. Báo ngắn: đã làm gì, evidence, còn thiếu gì, commit hash.

Không hỏi lại nếu thông tin đã có sẵn trong source of truth.

---

## ĐỊNH NGHĨA HOÀN THÀNH

Một hạng mục chỉ coi là xong khi:
- Nội dung phân biệt rõ giả thuyết/quy tắc/điều kiện kiểm chứng/kết quả nếu áp dụng.
- Không có khẳng định chắc chắn sinh lời.
- Không vi phạm giới hạn cứng.
- Có test/verification evidence tương ứng với loại task.
- `CURRENT_STATUS.md` đã cập nhật khi task làm thay đổi trạng thái dự án.

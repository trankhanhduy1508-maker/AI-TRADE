# Knowledge Ingestion Policy — Practitioner First

Ngày hiệu lực: 2026-09-26

## Founder intent

AI-TRADE ưu tiên kiến thức do **người đã trực tiếp đầu tư/giao dịch thành công và có bằng chứng thành tích có thể kiểm tra** viết ra. Không dùng danh tiếng "guru", số follower, khóa học, quảng cáo hay lời tự nhận làm bằng chứng.

Mục tiêu không phải sưu tầm thật nhiều sách. Mục tiêu là tạo một knowledge base có provenance đủ rõ để biến thành giả thuyết kiểm chứng được.

## Phân tầng nguồn

### Tier A — PRIMARY PRACTITIONER

Tác giả trực tiếp quản lý vốn/giao dịch và có track record được tổ chức, quỹ, cuộc thi, nhà xuất bản uy tín hoặc nguồn độc lập ghi nhận.

Nhãn provenance:
- `VERIFIED_PRACTITIONER_RECORD`
- `VERIFIED_FROM_PRACTITIONER_BOOK`

Được dùng để hình thành nguyên tắc nghiên cứu, nhưng **không tự động trở thành rule giao dịch**.

### Tier B — PRACTITIONER, RECORD PARTIAL

Tác giả là trader/investor thực tế nhưng thành tích chỉ được mô tả một phần, tự công bố, hoặc khó audit độc lập.

Nhãn:
- `PRACTITIONER_RECORD_PARTIAL`
- `AUTHOR_REPORTED`

Được dùng làm hypothesis/cross-check, không được biến thành hard rule nếu chưa có backtest/evidence riêng.

### Tier C — SECONDARY / INTERVIEW / SYNTHESIS

Tác giả tổng hợp hoặc phỏng vấn trader khác, nhưng không phải nguồn gốc trực tiếp của track record được mô tả.

Ví dụ: sách phỏng vấn, sách tổng hợp trường phái, tài liệu giáo dục.

Nhãn:
- `SECONDARY_SYNTHESIS`
- `SECONDARY_INTERVIEW_SOURCE`

Chỉ dùng để tìm primary source, đối chiếu và mở rộng câu hỏi nghiên cứu.

### Tier D — UNVERIFIED GURU CONTENT

Khóa học, video, bài viết, sách hoặc lời khuyên không chứng minh được tác giả có thành tích giao dịch thực tế.

Nhãn:
- `UNVERIFIED_GURU_SOURCE`

Không được dùng làm canonical knowledge.

## Quy tắc bắt buộc khi ingest

Mỗi claim phải có:
1. Claim ID.
2. Tác giả + sách/nguồn.
3. Track-record tier của tác giả.
4. Provenance label.
5. Phạm vi thị trường của nguồn gốc: stocks / futures / FX / multi-asset...
6. Loại claim: philosophy / setup / risk / sizing / exit / psychology.
7. Mức độ có thể chuyển sang AI-TRADE.
8. Trạng thái: `SOURCE_ONLY`, `HYPOTHESIS`, `BACKTESTED`, `DEMO_VERIFIED`.
9. Không chép dài nội dung có bản quyền; chỉ tổng hợp bằng ngôn ngữ riêng.

## Quy tắc portability

Kiến thức từ một thị trường không được bê nguyên sang thị trường khác.

Ví dụ:
- Peter Lynch chủ yếu là quản lý quỹ cổ phiếu. Kiến thức của ông rất hữu ích cho quy trình nghiên cứu, kiên nhẫn, chất lượng luận điểm và chống nhiễu, nhưng **không phải** rule vào lệnh Forex H1.
- CAN SLIM/O'Neil và SEPA/Minervini sinh ra chủ yếu cho cổ phiếu. Price/volume concepts có thể trở thành hypothesis, không phải rule MT5 mặc định.
- Hite/systematic trend following gần với mục tiêu futures/FX hơn, nhưng mọi tham số vẫn phải được AI-TRADE kiểm chứng riêng.

## Quy tắc chống "AI học rồi tự tin"

LLM không được:
- tự gắn tên trader vào một con số mà nguồn không nói;
- trộn nhiều tác giả thành một chiến lược rồi tuyên bố đó là phương pháp của một người;
- dùng performance lịch sử của tác giả để suy ra chiến lược AI-TRADE sẽ sinh lời;
- tự thay hard risk limits;
- tự unlock live-money.

Pipeline canonical:

`source -> provenance -> distilled principle -> hypothesis -> deterministic spec -> backtest -> OOS/walk-forward -> paper -> MT5 demo -> live-ready gate`

## Bản quyền

Repo chỉ lưu metadata, claim ngắn, tóm tắt và mapping kỹ thuật. Không lưu bản sao sách có bản quyền nếu không có quyền phù hợp.

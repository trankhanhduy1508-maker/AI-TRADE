# CWS Trading Masterbook V3 — Handoff cho chat mới

Ngày: 2026-09-28

## Nhiệm vụ

TIẾP TỤC CWS TRADING MASTERBOOK từ checkpoint hiện tại.

Đây là chat mới.

KHÔNG làm lại từ đầu.
KHÔNG biến ebook thành bản dump backtest.
KHÔNG sao chép dài sách có bản quyền.
KHÔNG tuyên bố lợi nhuận tương lai.
KHÔNG thay đổi live-money gate, broker execution, risk gate hoặc The5ers gate.
KHÔNG gọi GROSS_ONLY là broker-net profitable.
KHÔNG fake PASS khi artifact chưa render/kiểm tra.

## Repo / branch

Repo:
`trankhanhduy1508-maker/AI-TRADE`

Branch:
`codex/p0-covel-knowledge-audit`

Ground tối thiểu:
1. `knowledge/CWS_TRADING_MASTERBOOK_V3_DISTILLED_2026-09-28.md`
2. `knowledge/PRACTITIONER_BOOK_CORPUS.md`
3. `knowledge/PRACTITIONER_DISTILLED_V1.md`
4. `reports/MULTIASSET_10Y_BACKTEST_2026-09-27.md`
5. `reports/TF004_MAXIMUM_ROBUSTNESS_VALIDATION_2026-09-27.md`

Không ground toàn repo nếu chưa cần.

## Founder intent

Tên sách:
**CWS TRADING MASTERBOOK**

Subtitle:
**Bài học thực chiến từ trader vô địch, sách kinh điển và backtest CWS**

Đầu sách phải ghi:
**Duy Trần - Founder CWS**

Founder muốn học để tự giao dịch tốt hơn, vì vậy mỗi chương phải trả lời:
- Tôi học được gì?
- Tôi nhìn chart thế nào?
- Tôi làm gì trước entry?
- Tôi quản lý risk thế nào?
- Tôi thoát thế nào?
- Tôi luyện bài học này ra sao?

Không viết chương chỉ có lý thuyết.

## Cấu trúc evidence

Ba lớp:
1. practitioner / competition record / long-term record;
2. books + interviews + research;
3. CWS evidence: backtest, OOS, walk-forward, cost/execution stress, paper evidence.

Mọi claim có tính thành tích phải có provenance.
Nếu không verify được thì ghi rõ mức bằng chứng hoặc bỏ.

## Book scope

Masterbook hiện đã có:
- bản đồ 75+ đầu sách/tác phẩm;
- 18 nguồn lõi được đúc kết sâu;
- 12 nguyên tắc lặp lại của trader giỏi;
- breakout/pullback playbooks;
- risk/sizing;
- exits;
- psychology;
- journal;
- backtesting;
- CWS failures;
- 90-day curriculum;
- pre-trade checklist;
- 100-trade curriculum;
- 27 hình/biểu đồ.

Khi mở rộng, ưu tiên **chiều sâu bài học** hơn tăng số tên sách.

## Những lesson bắt buộc giữ

- expectancy > win rate riêng lẻ;
- risk first;
- setup + trigger + invalidation;
- loser nhỏ, winner có không gian chạy;
- no martingale / no emotional averaging down;
- pyramiding winner chỉ là hypothesis, tổng risk phải khóa;
- regime matters;
- OOS/WF trước promotion;
- cost/slippage/gap/next-open matters;
- winner concentration;
- journal theo process;
- good loss ≠ bad trade;
- system versioning;
- survival > một giai đoạn lợi nhuận lớn.

## CWS examples bắt buộc giữ

Gold:
- baseline historical có headline lớn nhưng phụ thuộc winner cực lớn;
- best trade concentration;
- conservative execution làm kết quả đảo dấu.

BTC:
- winner concentration rõ;
- trend following cần asymmetric payoff nhưng phải stress outlier.

US30/NAS100:
- OOS và walk-forward có thể mâu thuẫn.

Cost:
- GROSS_ONLY không phải broker-net evidence.

## Artifact requirements

Xuất đủ:
1. EPUB3
2. PDF
3. DOCX editable

EPUB:
- UTF-8 tiếng Việt sạch;
- không có U+FFFD;
- mục lục bấm được và nhảy đúng chương;
- cover/metadata có `Duy Trần - Founder CWS`.

DOCX:
- A4;
- font Unicode chuẩn;
- “Mục lục”, không dùng heading tiếng Anh;
- render toàn bộ trang bằng DOCX skill;
- inspect mọi trang trước khi PASS.

PDF:
- convert từ DOCX đã PASS;
- render lại bằng PDF skill;
- không glyph lỗi, clip, overlap;
- kiểm tra outline/link nếu có.

## Quality gate

Không được báo hoàn tất chỉ vì file tạo được.

PASS cần:
- source build thành công;
- EPUB zip integrity PASS;
- EPUB internal TOC hrefs không missing;
- DOCX render đủ tất cả trang;
- PDF render đủ tất cả trang;
- không lỗi font Việt;
- author metadata đúng;
- ít nhất một vòng visual QA toàn bộ trang sau meaningful edit cuối.

## Khi nghiên cứu thêm sách

Ưu tiên:
- official author/publisher;
- competition organizer;
- university/institutional profile;
- reputable interviews;
- primary research papers.

Không cần ingest bản full có copyright để rút bài học.
Dùng lawful public material và paraphrase.

## Cách viết

Mỗi principle/chapter nên có:
1. Ý tưởng cốt lõi.
2. Tại sao nó quan trọng.
3. Ví dụ số.
4. Biểu đồ/minh họa.
5. Sai lầm thường gặp.
6. Bài tập Founder.
7. “Bài học rút ra”.
8. Nếu liên quan, đối chiếu evidence CWS.

## Quy tắc thao tác

Tự làm liên tục.
Test FAIL → tìm nguyên nhân thật → sửa minimal diff → test lại.
Không dừng giữa chừng chỉ để báo cáo.
Không fake evidence.
Chỉ checkpoint khi có artifact/evidence thật.

## Checkpoint hiện tại

Bản V3 đã hoàn thành nội dung lớn và artifact publishing.
Nếu chỉ tiếp tục chỉnh nội dung, giữ nguyên canonical byline:
**Duy Trần - Founder CWS**

Không quay lại bản ebook cũ quá nặng về backtest.


## Final artifact QA checkpoint

Current final publishing state:
- DOCX/PDF: 49 pages.
- All 49 DOCX-render pages visually inspected after final TOC edit.
- PDF re-exported from final DOCX.
- Visible DOCX/PDF `Mục lục`: 29 internal links.
- PDF: 59 annotations, 201 outline items.
- EPUB: 147 TOC/internal links; 0 broken targets; UTF-8 Vietnamese PASS.
- Author/byline: `Duy Trần - Founder CWS`.

Do not regress the visible TOC back to an empty Word field or the earlier `Table of Contents` heading.

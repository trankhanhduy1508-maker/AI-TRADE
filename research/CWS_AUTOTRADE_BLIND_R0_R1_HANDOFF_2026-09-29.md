# CWS AutoTrade — BLIND R0 / R1 FORWARD CHECKPOINT (2026-09-29)

**Nhánh duy nhất:** `codex/p0-covel-knowledge-audit`.
**HEAD trước khi ghi checkpoint:** `018585f464e5d426d082c69047293abf582e6bbc`.
**Không sửa Main/Production. Không tạo nhánh mới. Không dùng máy Founder. Không bật LIVE hoặc DEMO-send.**
**Trạng thái khoa học cuối:** `UNPROVEN`. Không có bằng chứng lợi thế giao dịch độc lập, tái lập, sau chi phí broker.

## Đọc tối thiểu phiên sau, KHÔNG nghiên cứu lại toàn repository
1. `research/CWS_AUTOTRADE_BLIND_R0_PREREG_2026-09-29.md` (commit `9041d3de3122abfb41ef8ab2f0fca12f114307cf`).
2. `research/manifests/CWS_BLIND_R0_2026-09-29.json` (commit `3d071818bdda0ea575eced6bed3a1185e384e0ab`).
3. `research/results/CWS_BLIND_R0_2026-09-29.json` (commit `a7a8855d84371faf3ce93ae394e80c32b800c0f4`).
4. `research/CWS_BLIND_R0_REPORT_AND_FAILURE_JOURNAL_2026-09-29.md` (commit `926fc42ad230ab04b735c8872326e0ea82b50b2a`, bảng kết quả 30 thị trường/khung, 26 trường hợp thiếu H4, lỗi, kết luận).
5. `research/CWS_AUTOTRADE_FORWARD_R1_PREREG_2026-09-29.md` (commit `debf1bd2f95080e0ddd1d94f97763eb3abe327f8`).
6. Khi cần sửa mã: `src/backtest/blind_r0.py`, `scripts/run_blind_r0.py`, `tests/backtest/test_blind_r0.py`, `src/paper/blind_r1_event_ledger.py`, `tests/paper/test_blind_r1_event_ledger.py` và hai workflow `cws-blind-r0-once.yml`, `cws-blind-r1-qa-once.yml`.

## Chuỗi bằng chứng R0, đã hoàn thành một lần
- HEAD gốc xác minh: `29548aae06c7d068d0c0aed37a8ae0ddb978271d`.
- Commit đặc tả R0 *trước khi đọc kết quả TF-004 / TF-014*: `9041d3de3122abfb41ef8ab2f0fca12f114307cf`.
- Chốt chương trình kiểm thử cloud tại commit `08febee552c905cbd96dc21943c81cf9167dee0a`.
- Workflow GitHub: https://github.com/trankhanhduy1508-maker/AI-TRADE/actions/runs/36566712493 . **SUCCESS**; Smoke 14/14, Runtime 14/14, Fault 14/14; thật sự có 42 lượt test đạt. Ghi nhận từ job `109400311700`.
- Manifest nguồn dữ liệu, hash raw/normalized, 56 split cố định được **commit thành công trước khi mở historical OOS** tại `3d071818bdda0ea575eced6bed3a1185e384e0ab`, kiểm tra ref từ remote thành công.
- Đã chạy nominal historical OOS đúng một lần sau commit manifest. Kết quả máy-readable commit `a7a8855d84371faf3ce93ae394e80c32b800c0f4`, báo cáo diễn giải commit `926fc42ad230ab04b735c8872326e0ea82b50b2a`.
- Tất cả 56 ô có trạng thái rõ: 28 D1 Yahoo/Bitstamp + 2 H4 Bitstamp đánh giá `EXPLORATORY_HISTORICAL_REUSED_UNPROVEN`; 26 ô H4 Yahoo `DATA_UNAVAILABLE_NATIVE_H4`. Không gán proxy Yahoo cho dữ liệu MT5 broker.
- Cộng tất cả 30 ô có 307 giao dịch đóng trong historical OOS (có tương quan chéo thị trường; không phải 307 quan sát độc lập). 17 ô expectancy R dương, 13 âm. **0/30** ô có >=30 lệnh OOS; **0/30** ô chi phí broker thực chứng; 25 ô `GROSS_ONLY`, 5 ô chi phí giả định nghiên cứu. **0** ô có dữ liệu forward mới. Không có kết luận lợi thế nào được xác nhận.
- RR quan sát có tính từ tỷ lệ R lời trung bình/R lỗ trung bình, không ép RR cố định. Bất kỳ lợi nhuận `net_pnl_price` nào cũng ở đơn vị giá riêng từng thị trường, không phải USD và không được cộng thành tổng danh mục.

## R1 đã được khóa trước khi có dữ liệu forward
- R1 giữ nguyên tín hiệu R0; giả thuyết mới là tính khả thi/quản trị rủi ro và hiệu quả *độc lập* sau phí thực chứng của phương pháp không đổi trên forward thật; không chọn tham số từ holdout đã mở.
- Gate dữ liệu forward từ `2026-09-30T00:00:00Z`. Các bar cũ chỉ làm warm-up, không được tính là forward lợi nhuận/lệnh. Khi xây *trading* forward pipeline phải đòi **bar signal hoàn toàn thuộc cửa sổ mới** (`open_ts >= FORWARD_START_UTC`) để không tính lợi nhuận một phần quá khứ.
- `src/paper/blind_r1_event_ledger.py` hiện mới là cổng metadata provenance + JSONL append-only SHA-256 chain. Mọi nguồn ngoài đều bị gắn `UNVERIFIED_EXTERNAL_SOURCE`, không có broker import/order-send và không tạo tín hiệu/lệnh. Đây **KHÔNG** phải hệ thống forward paper chạy thực tế hoặc dữ liệu được kiểm chứng. Thiếu nguồn audit vẫn `NOT_VERIFIED`.
- Workflow QA R1: https://github.com/trankhanhduy1508-maker/AI-TRADE/actions/runs/36567548186 ; **SUCCESS** tại commit `018585f464e5d426d082c69047293abf582e6bbc`. Smoke 18/18; Runtime 18/18; Fault 18/18 (54 lượt test fixture). Job `109403120308`. Bộ kiểm thử dùng đồng hồ/dữ liệu tổng hợp có đánh dấu rõ ràng; **không** chứng minh có dữ liệu thị trường forward thật.

## Các cổng chưa hoàn thành (FAIL-CLOSED, không báo PASS)
1. **Forward**: thời điểm nghiên cứu 2026-09-29; chưa có dữ liệu mới sau mốc đủ điều kiện. Không tuyên bố theo dõi nền hoặc lịch chạy.
2. **26 H4 thiếu nguồn**: xác minh feed H4 thực, quyền sử dụng, session, độ phủ. Nếu chỉ có 1h thì phải có đăng ký giả thuyết phiên mới và mô tả rõ aggregation; không tự đổi dữ liệu Yahoo thành MT5-native.
3. **Phí, kích thước hợp đồng và chuyển đổi tiền tệ**: cần nguồn thực từ chính venue và effective timestamp, spread/commission/slippage/financing/swap, lot step, leverage/margin, contract multiplier, corporate-action/roll. Không thể công nhận lợi nhuận tài khoản hoặc điều kiện tổng stop-risk <=1% khi thiếu input.
4. **Risk/paper engine**: chưa nối ledger R1 vào engine giao dịch giấy với kiểm tra stop-risk 0.25%/position, 1% aggregate, next-open, stale-source/auth/kill-switch, accounting vốn mark-to-market, trượt giá, chứng thực execution. Tuyệt đối không bật order-send.
5. **Tái lập dài hạn**: `manifest` có URL/hash, nhưng raw giá hợp pháp chưa được lưu bền vững; workflow R0 raw artifact retention **1 ngày**. Đây là giới hạn thực, không được nói đã có nguyên vẹn dataset lâu dài. Phải xác minh quyền lưu và kho riêng phù hợp trước khi tái lập.
6. **Tính độc lập**: historical OOS được xem là `HISTORICAL_REUSED` do có thể chồng lấn TF nghiên cứu cũ. Không được dùng lại như tập mới, đổi tham số rồi tính lại, hay coi là test độc lập. R0 cố định; nếu muốn đổi mô hình, prereg phiên R2 với cửa sổ forward mới khác.
7. **Promotion**: cần >=90 ngày forward thật, >=100 lệnh đóng tổng không đếm trùng, >=30 lệnh nếu kết luận cho một thị trường, positive net sau phí đã chứng thực kể cả 2x stress, dữ liệu hợp lệ, đối chứng, kiểm tra bootstrap/outlier và audit giới hạn rủi ro. Chưa đạt bất kỳ gate forward nào.

## Nguồn kết nối / thao tác đã xác minh
- GitHub connector có quyền đọc/ghi repo; nhánh thực tế đã cập nhật trên GitHub. Ưu tiên connector → API → cloud.
- Supabase connector hiện trả về 2 project tên `cws-render-e2e`, `cws-render-beta`. Không thấy project AutoTrade được chứng thực, nên không tự ghi dữ liệu nghiên cứu sang project render; **không thay đổi Supabase**.
- Google Drive có folder `CWS AI TRADE`, với `QA` và `Private Knowledge` đang không có file được liệt kê. Không tự coi đó là kho dữ liệu thị trường đã kiểm chứng; **không thay đổi Drive**.
- Không dùng máy Founder, không tạo nhánh, không đụng Main/Production, không phát sinh tài nguyên trả phí, không có lệnh trade nào.

## Thứ tự thực hiện phiên tiếp
A. Xác minh HEAD của nhánh hiện tại, đọc 5 file tối thiểu phía trên và log R0/R1. Không lặp lại backtest R0 historical OOS.
B. Giữ R0 nguyên vẹn; tăng cường cổng provenance source/data retention và ghi nhật ký thất bại. Mọi sửa kỹ thuật dùng fixture hoặc TRAIN+VALIDATION, đảm bảo khác biệt được version hóa.
C. Khảo sát nguồn *được phép*, thực cho 26 H4 và fee schedule từ venue tương ứng; thiếu thì công khai `DATA_UNAVAILABLE` / `GROSS_ONLY`.
D. Tách chức năng forward paper R1 ra khỏi broker/order-send; chỉ sau khi chứng thực source/cost/risk/market-time mới đưa bar/lệnh giấy mới sau 2026-09-30 vào append-only ledger.
E. QA Smoke → Runtime → Fault, lưu lệnh chạy + exit code + log + SHA; khi lỗi sửa minimal diff, test lại, không fake PASS.
F. Báo cáo mọi thị trường/tất cả lỗi. Nếu không thấy edge, giữ `UNPROVEN` và lưu cả chiến lược thất bại.

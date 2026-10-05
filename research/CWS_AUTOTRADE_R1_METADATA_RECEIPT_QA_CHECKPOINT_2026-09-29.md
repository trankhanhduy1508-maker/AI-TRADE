# CWS AutoTrade R1 — checkpoint nguồn miễn phí và nhật ký metadata, 2026-09-29

**Nhánh duy nhất:** `codex/p0-covel-knowledge-audit`. **HEAD trước thay đổi:** `a468ec34f9790ab7366078dba1399247ace34d57`.  
**Trạng thái:** `SOURCE_ONLY_UNVERIFIED`, `EDGE=UNPROVEN`, `FORWARD_TRADES=0`, `ORDERS_SENT=0`.

## 1. Tìm cách không phát sinh chi phí

Không tạo project Supabase trùng hai project render. Dùng nhật ký JSONL trong không gian riêng của runner, chỉ lưu metadata, SHA-256, thời điểm runner ghi nhận, loại H4 và số nến đạt/bị loại. File raw được xử lý trong bộ nhớ và không đưa vào nhật ký; khi không có quyền lưu raw, **không** đăng ZIP/CSV/quote lên GitHub hoặc Google Drive.

Tài liệu Kraken REST xác nhận `interval=240` và `assetVersion=1`; nến cuối luôn đang mở, tối đa 720 bản ghi gần đây, không dùng `since` để lấy cũ hơn 720: https://docs.kraken.com/api-reference/market-data/get-ohlc-data . Kraken yêu cầu xin phép trước cho một số trường hợp dùng dữ liệu công khai vào mục đích thương mại phi cá nhân: https://docs-legacy.kraken.com/api/docs/guides/global-intro/ . Bitstamp có public OHLC `step=14400` và nêu thỏa thuận giấy phép đối với việc sử dụng dữ liệu sàn cho mục đích thương mại: https://www.bitstamp.net/api/ . Dukascopy công bố Historical Data Export miễn phí, nhưng tài liệu XML data licence riêng có điều kiện phi thương mại; **không tự áp giấy phép XML sang CSV**, chưa xác nhận quyền lưu và khai thác thương mại cho feed mong muốn: https://www.dukascopy.com/swiss/english/marketwatch/historical/ ; https://www.dukascopy.com/plugins/cont.php?ref_id=1273 .

Đây là nguồn có thể **khảo sát ở chế độ read-only**, không phải sự cho phép dùng dữ liệu trong sản phẩm thương mại. Không truy cập API bằng cách lách auth/quota; không giả danh H4 spot là H4 MT5 broker. Chưa có nguồn FX broker có entitlement và chi phí tài khoản thật trong phiên này.

## 2. Kết quả thực hiện

- `src/paper/r1_source_receipt.py`: thêm receipt store độc lập, chỉ lưu metadata + hash thô, chuỗi SHA-256 liên kết, lock ghi và fsync; bắt buộc cặp provider-symbol-type khớp với HistData EURUSD H4 derived và Kraken/Bitstamp BTC/ETH native spot. Nến H4 native phải đúng ranh giới UTC. Lỗi trùng, ngược thời gian, future bar, sai schema, sửa chuỗi hash, khai khống license/fee đều bị chặn.
- `tests/paper/test_r1_source_receipt.py`: fixture hoàn toàn tổng hợp. Không chứa dữ liệu thị trường, token, HTTP, broker client hoặc lệnh gửi.
- Module **không tự đọc thị trường**, không khởi động lịch, không gửi lệnh, không cấp nhãn provider verified hoặc forward eligible. Trường `captured_at_utc` chỉ là đồng hồ runner, **không** đủ bằng chứng độc lập về đồng hồ nguồn. SHA chain chỉ phát hiện sửa đổi so với head đã neo độc lập; không phải bảo vệ trước người có quyền ghi và tái tính toàn bộ file.
- File metadata riêng cần nơi lưu bền vững đã được cho phép; cloud container của phiên chat không phải kho lưu liên tục. Chính sách quyền lưu raw vẫn còn blocker.

## 3. QA thật trên cloud container, không dùng máy Founder

Container Python 3.13.5; repo không clone được do DNS không phân giải github.com. Hai file được chạy tại workspace cloud cô lập, sau đó ghi qua GitHub connector và **đối chiếu SHA Git blob bằng GitHub fetch_file**:
- `src/paper/r1_source_receipt.py`: `01ee27ea79b6080a4fde12f37fbc75eb4f20621f`
- `tests/paper/test_r1_source_receipt.py`: `99758188c877baf993b29cb66bb06c6f4655be02`

Lệnh chạy, từng lệnh exit 0:
```bash
python -m unittest tests.paper.test_r1_source_receipt.Smoke -v
python -m unittest tests.paper.test_r1_source_receipt.Runtime -v
python -m unittest tests.paper.test_r1_source_receipt.Fault -v
```
Kết quả chính xác: **Smoke 2/2 PASS; Runtime synthetic 2/2 PASS; Fault 9/9 PASS**. AST kiểm tra module mới không có import HTTP, socket, subprocess, broker. Chưa chạy full repository regression hoặc real Kraken response, không được ghi thành runtime feed real.

**Bằng chứng thất bại và minimal fix:** Lần Fault đầu FAIL 1/9 vì fixture `test_broken_hash_chain_blocks_append` dùng `last_close_ts` lớn hơn đồng hồ test, nên cổng thời gian chặn trước khi vào cổng hash. Sửa duy nhất fixture cho timestamp hợp lệ, test lại Smoke→Runtime→Fault đều PASS. Không sửa cổng thời gian hoặc bỏ chặn để làm đẹp kết quả.

## 4. Không thay đổi các gate khoa học

- R0 và historical OOS đã mở giữ nguyên; không chỉnh 55/20/2.5, không chọn cặp từ kết quả đã xem.
- HistData 30.496 M1 thực -> 93 H4 derived BID-only, 35 block loại từ run trước; không tăng coverage nếu chưa quan sát file mới thật. Kraken parser và receipt mới vẫn synthetic-only. 26 native H4 thiếu ở R0 vẫn thiếu.
- Cần feed mới **sau** `2026-09-30T00:00:00Z`, quote bid/ask next-open ghi nhận đương thời, giấy phép nguồn/kho lưu, phí/contract/margin/FX account verified và full risk/kill-switch trước khi ghi nhận paper fill. Dữ liệu hồi cứu dù tải sau cutoff vẫn `HISTORICAL_REPLAY`.
- `UNPROVEN` cho tới khi đủ 90 ngày và 100 lệnh forward đóng thực sự, mẫu từng ô, baseline, stress sau phí và kiểm tra outlier.

**Bước tiếp theo trong phiên được ủy quyền có nguồn:** nối parser đã kiểm toán với receipt và R1 provenance ledger; snapshot tại thời điểm capture, kiểm toán quote/fee đúng tài khoản, rồi chạy paper-only sau cutoff. Không giả lập rằng công việc tiếp tục ngầm sau phiên chat.

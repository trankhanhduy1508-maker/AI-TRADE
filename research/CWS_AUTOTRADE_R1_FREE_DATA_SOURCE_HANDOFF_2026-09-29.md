# CWS AutoTrade — checkpoint R1 free data, nguồn thực và kiểm toán 2026-09-29

**Nhánh duy nhất:** `codex/p0-covel-knowledge-audit`.
**HEAD đã xác minh trước checkpoint:** `737e9de9fa989dde755f9bc4905adbd2026891e5`.
**Trạng thái khoa học:** `UNPROVEN`; 0 giao dịch forward độc lập, 0 nguồn chi phí broker đã được xác nhận, 26 ô H4 gốc vẫn thiếu.
**Tuyệt đối không** mở lại holdout R0; không LIVE/DEMO-send, không thay Main/Production, không dùng máy Founder, không tăng chi phí.

## Đọc tối thiểu phiên sau
1. `research/CWS_AUTOTRADE_BLIND_R0_R1_HANDOFF_2026-09-29.md`: chuỗi bằng chứng R0 bất biến và R1 forward.
2. `research/CWS_AUTOTRADE_R1_SOURCE_RISK_HANDOFF_2026-09-29.md`: OANDA parser và risk preflight.
3. `research/CWS_AUTOTRADE_R1_M1_DERIVED_H4_SOURCE_REGISTRATION_2026-09-29.md`: đặc tả H4 tổng hợp **khác** H4 gốc.
4. `reports/CWS_AUTOTRADE_R1_PUBLIC_SOURCE_PROBE_2026-09-29.json`: bằng chứng nguồn công khai Bitstamp truy vấn thật, metadata/hash, không gồm raw price.
5. Khi sửa: `src/data_loader/histdata_m1_h4.py`, `tests/data_loader/test_histdata_m1_h4.py`, `scripts/probe_blind_r1_public_sources.py`, `src/paper/blind_r1_event_ledger.py`, `tests/paper/test_blind_r1_event_ledger.py`, `src/data_loader/oanda_h4_adapter.py` và hai test file liên quan.

## H4 thay thế miễn phí và giới hạn thực tế
- Xác minh trang HistData chính thức: `https://www.histdata.com/download-free-forex-data/`; Generic ASCII chỉ cung cấp M1 (bid-only), timestamp **EST cố định UTC−05:00 không DST**: `https://www.histdata.com/f-a-q/data-files-detailed-specification/`.
- Trang danh sách công khai `https://www.histdata.com/download-free-forex-historical-data/?/ascii/1-minute-bar-quotes/EURUSD` hiển thị tháng 9/2026 và năm trước; trang `https://www.histdata.com/download-free-forex-historical-data/?/ascii/1-minute-bar-quotes/eurusd/2026/9` có nhãn tệp `HISTDATA_COM_ASCII_EURUSD_M1_202609.zip`. **Chỉ nhìn thấy nhãn và danh sách, chưa tải hoặc đọc byte ZIP**, không xác nhận nội dung, sự đầy đủ hay license lưu trữ.
- 19 ứng viên nếu các tệp thực sự có sẵn: 13 FX + XAU/XAG + WTI/Brent + SPX/USD/NSX/USD. 6 cổ phiếu Mỹ và Dow Jones không có nguồn HistData được xác nhận. Các chỉ số/hàng hóa này là feed/proxy nguồn riêng, không đồng nhất Yahoo cash/futures hoặc MT5 CFD.
- Commit đặc tả nguồn trước khi đánh giá: `3f860f001c6f1b6672a76bf28bb5c71425045e4e`.
- Importer `src/data_loader/histdata_m1_h4.py` tại commit `67fea7c8cbb1bef94f5131a9926478af41b3a305` yêu cầu đúng 240 phút thực liên tục, căn 17:00 EST cố định, loại cả block thiếu một phút, phát hiện duplicate/future/giá bất hợp lệ, SHA raw; kết quả luôn `DERIVED_H4_BID_ONLY_EXPLORATORY`, `ask_or_spread_available=false`.
- QA workflow `https://github.com/trankhanhduy1508-maker/AI-TRADE/actions/runs/36574965444`, tested SHA `14b4968950b80ffcd32e6d2abfe2f5a8bc34e035`: Smoke 19/19, Runtime 19/19, Fault 19/19 = **57 lượt PASS, toàn bộ SYNTHETIC**. Không có tệp HistData thật được xử lý và không có lợi nhuận/holdout được tính. Không sử dụng FTP/SFTP trả phí; không đưa dữ liệu thô lên GitHub.

## Bằng chứng nguồn thật: Bitstamp (KHÔNG phải chiến lược forward)
- Chạy cloud GET công khai chỉ đọc: `https://github.com/trankhanhduy1508-maker/AI-TRADE/actions/runs/36575325302`, tested SHA `4f092ab9c33203fe85558d9b19d6c4ee85ed4c62`.
- BTCUSD H4, BTCUSD D1, ETHUSD H4, ETHUSD D1: 4/4 responses đạt kiểm tra cấu trúc OHLC; 8 bar đã đóng/ô, tổng 32 bar; trong từng đoạn 8 bar không có gap/duplicate và timestamp không vượt thời điểm lấy dữ liệu. Nguồn công khai không yêu cầu token; **không** xác nhận fee account/venue.
- Báo cáo đầy đủ của lần GET, SHA256 raw mỗi response, URL và timestamp đã lưu thành **metadata-only** tại `reports/CWS_AUTOTRADE_R1_PUBLIC_SOURCE_PROBE_2026-09-29.json`, commit `737e9de9fa989dde755f9bc4905adbd2026891e5`. Không lưu raw OHLC do chưa kết luận chính sách lưu dữ liệu lâu dài.
- Probe diễn ra 2026-09-29 UTC, **trước mốc forward 2026-09-30T00:00:00Z**. Đây là kiểm tra kết nối nguồn và hợp lệ cấu trúc, không phải 32 lệnh hoặc 32 mẫu kiểm định lợi thế độc lập. Các BTC/ETH H4 đã là 2 ô H4 từng được đánh giá ở R0; không “giải quyết” 26 ô thiếu H4.

## Củng cố fail-closed / lỗi có bằng chứng
- OANDA H4 parser được bổ sung gate DST: các H4 vượt chuyển DST New York không suy đoán close = open +14400 khi offset thay đổi; đánh dấu `DST_H4_CLOSE_BOUNDARY_UNVERIFIED` đến khi có response gốc chứng minh boundary. Bổ sung kiểm thử synthetic xuân/thu; nguồn OANDA thực chưa được kết nối.
- Workflow source/risk rerun `https://github.com/trankhanhduy1508-maker/AI-TRADE/actions/runs/36575517798`, tested SHA `4c8f399be52efb313c77baf9440027f5bf98fa93`: 21 adapter tests + 19 risk tests = Smoke 40/40, Runtime 40/40, Fault 40/40, **120 lượt PASS** trên fixture. Không có nguồn OANDA thật.
- Ledger R1 bổ sung gate ràng buộc URL Bitstamp vào đúng market BTCUSD/ETHUSD, đúng step H4/D1, limit 1–1000, exclude_current_candle=true; không chấp nhận URL của thị trường khác, nến chưa hoàn thành hoặc query khác. Không có broker/order imports.
- Trong quá trình thay đổi ledger: các workflow trung gian `36575725815` và `36575746424` FAIL do source/test chưa đồng bộ; rerun `36575772806` FAIL do kiểm tra AST chặn cả `urllib.parse` thuần (nhầm import parser URL với HTTP network). Đã sửa tối thiểu audit để chỉ cấm `urllib.request`, `urllib.error` và sửa fixture đúng truy vấn. **Không tính các lần FAIL là PASS.**
- Rerun hoàn chỉnh `https://github.com/trankhanhduy1508-maker/AI-TRADE/actions/runs/36575830111`, tested SHA `97b67ac77cd31035cd5107712393c70aaafa1d55`: 21 test Smoke, 21 Runtime, 21 Fault, **63/63 lượt PASS**. Các test dùng timestamp synthetic, không có forward trades.
- Chỉ GitHub connector ghi file, GitHub public-repo standard hosted runner cho QA/read-only GET; GitHub chính thức ghi nhận standard runner cho public repo miễn phí, không dùng larger runner/paid artifact. Không dùng PC Founder hoặc tạo nhánh.

## R0 bất biến được kiểm chứng lại sau thay đổi
`research/CWS_AUTOTRADE_BLIND_R0_PREREG_2026-09-29.md` blob `c24865edfc76f9f21614de1f35451143eb0f927b`.
`research/manifests/CWS_BLIND_R0_2026-09-29.json` blob `57c4075587ff9f97b27f8480ddffb1061f264fc4`.
`research/results/CWS_BLIND_R0_2026-09-29.json` blob `56647bef016efcd1e2eb2d8b03028cdc060652e6`.
`src/backtest/blind_r0.py` blob `304ef89ee0a93f9b8ddfa08e7817cf6e320bed39`.

Không chạy lại historical OOS sau khi lộ kết quả. Không dùng “17 ô positive” để tối ưu hoặc chọn ứng viên rồi công nhận hiệu quả.

## Cổng còn thiếu / công việc phiên kế tiếp
1. Muốn có thêm H4 **thật**, tìm nguồn gốc broker native H4 có entitlement/chi phí/giấy phép rõ ràng; OANDA fxPractice cần kết nối do người dùng ủy quyền. HistData M1-derived H4 chỉ là nghiên cứu riêng và không lấp `DATA_UNAVAILABLE_NATIVE_H4`.
2. Muốn chạy pipeline HistData miễn phí, chỉ sử dụng liên kết ZIP người dùng đã được phép truy cập từ chính trang tải, kiểm tra tệp ZIP thực tế và điều kiện sử dụng trước khi lưu raw dài hạn. Không đoán hay vượt cơ chế download/auth. Sau đó test importer trên file thật, ghi SHA và số block đủ 240 M1; không đánh giá lợi nhuận trước khi commit dataset manifest.
3. Có thể tiếp tục read-only Bitstamp theo phiên có chủ đích **sau** mốc 2026-09-30T00:00Z. Nhưng close-bar OHLC tải hồi cứu sau khi nến kết thúc không cung cấp quote next-open quan sát đồng thời; không gọi đó là forward paper execution. Muốn forward cần ghi sự kiện quote thực cùng thời gian, nguồn và phí trước quyết định giả lập; chỉ sau khi cổng nguồn/fee/risk pass mới tạo lệnh GIẤY, không gọi broker order-send.
4. Cần >=90 ngày quan sát forward mới + >=100 giao dịch đóng tổng thật sự độc lập, nguồn và chi phí thực, baseline, gap/Monte Carlo/outlier và portfolio accounting đạt gate theo R1 prereg. **Không thể tuyên bố đủ điều kiện ngay 2026-09-29.**
5. Chưa có backend AutoTrade trên Supabase được chứng thực; tránh ghi dự án render. Không upload raw có quyền lưu chưa rõ lên Drive hay GitHub. Không có tác vụ giám sát nền được thiết lập.

**Nhãn khoa học cuối:** `UNPROVEN; PAPER_PIPELINE_PARTIAL; REAL_SOURCE_CONNECTIVITY_VERIFIED_ON_BITSTAMP_ONLY; NO_VERIFIED_BROKER_EXECUTION; NO_INDEPENDENT_FORWARD_TRADES`.

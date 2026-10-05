# AutoTrade — replay liên tục và regression execution, 05/10/2026

## Kết quả và giới hạn

Bot MT5 autonomous chưa hoàn thiện. Phiên này sửa data integrity Python và triển khai replay nghiên cứu giữ vị thế qua ranh giới fold; không đổi TF-013A runtime, không bật lệnh DEMO/live, không tạo provider/cloud có phí, không dùng máy Founder. Không triển khai MCP hoặc fine-tune model.

## Code thực
- `src/execution/mt5_runtime.py`: từ chối giá NaN/zero, OHLC sai, volume âm, timestamp không nguyên/dương; từ chối phí/P&L không hữu hạn và freshness limit vô hạn/không hợp lệ. Snapshot mặc định không phê duyệt risk; caller phải cấp explicit approval. Regression đã fail trước khi sửa, rồi đạt sau sửa.
- `src/research/continuous_replay.py`: giữ vị thế và pending entry qua lần chọn lại, giữ candidate khi vào cho trailing/exit, stop gap dùng adverse open, không có TP/RR cố định, không API broker. R units không phải tiền tài khoản.
- `continuous_walkforward.py`: reuse selections past-only R2; đối chiếu adaptive, R0 fixed và FLAT, stress phí không rerank bằng kết quả test. Không thay engine R2 đã đóng băng. Đây KHÔNG là full R3: nested FIT/VALIDATE và cổng risk mô hình R3 chưa triển khai.
- `pinned_continuous.py` và CLI: xác minh exact Git blob SHA trước đọc CSV, chỉ trả metadata/metrics; giữ các source reject; không lưu raw giá vào repo/output. Nguồn read-only research không có quyền redisplay đã xác minh.
- Cập nhật test web/Android đúng hợp đồng mới: session-client nằm trong gói build nhưng không được native WebView allowlist mở; cache content hash phải thay khi asset thay; Founder dùng password được cung cấp để broker verify; frozen bundle v11 đối chiếu hash riêng, không ép bằng canonical đang phát triển.

## Chạy thực dữ liệu đã khóa

Nguồn: hai manifest R2b ngày 29/09 trong repo, exact provider commits/blob. Chạy native Python từ raw snapshot qua GitHub connector; không phải JS port. 15 series D1 (10 FX + XAUUSD + SPY/QQQ/GLD/USO ETF) và 11 H4 (10 FX + XAUUSD). EURCHF D1/H4 giữ REJECTED_SOURCE_GAP, không nội suy.

Report: `research/results/CWS_CONTINUOUS_26_SERIES_REPLAY_2026-10-05.json`. Tổng 26 series, 1473 lệnh mô phỏng đóng với adaptive continuous replay; không là giao dịch độc lập hoặc portfolio có thể cộng R. Số series tổng realized R dương ở base modeled cost: D1 8/15, H4 3/11. Giữ tất cả kết quả âm. Không chọn thị trường dương hậu nghiệm để promote.

Cost mới là **constant price unit = 0.1% median close của 500 bar đầu**, stress 0/1x/2x/3x; đã xác định trong code trước mở kết quả. Selection dùng cùng constant cost trong past training. KHÔNG phải cost R2b theo trung bình entry/exit mỗi trade, không so ngang số dương với báo cáo cũ để claim cải thiện. KHÔNG là spread/commission/swap/financing broker thực. Giữ cùng lifecycle/count trong stress; realized và unrealized R giảm hoặc bằng khi tăng phí đã kiểm tra mọi lane/series.

Provider naive dates được giả UTC chỉ để xếp thứ tự; calendar/DST/vintage/corporate actions/rights chưa audit. ETFs không tương đương sản phẩm CFD MT5. Tất cả HISTORICAL_REUSED, UNPROVEN, promotion NOT_APPROVED, LLM calls 0, broker orders 0. Không tính account ROI/CAGR hoặc vốn thật.

## Verification

- Full Python pytest với tất cả test source/fixture trên nhánh: **799 passed, 1 skipped**. Skip: Java/Python release-manifest cross-language contract vì thiếu JDK; không gọi toàn bộ runtime/device PASS.
- Full Node web + forward tests hiện có: **36/36** đạt.
- Static PWA build exit 0. Không publish lại UI vì thay đổi phiên này là Python research/data boundary và tests.
- Smoke: source/hash + schema + data rejection. Runtime: native replay đủ 26 series, baseline và cost sensitivity. Fault: future mutation, gap stop, pending/carry, invalid prices/fees, source mismatch.
- Chưa browser E2E/reload/mobile cho web mới, chưa APK device E2E, chưa broker order check/fill/trailing/close/restart/reconcile 24/7. Không gọi bot DONE từ unit tests.

## Blocker thực còn lại

1. `runtime_config`: TF_004, enabled=false, demo_send_enabled=false, risk_profile_approved=false, max_total_volume_demo=NULL. Execution legacy `ai-trade-tick` v6 còn ghép THE5ERS readiness (BLOCKED_APPROVAL); tài khoản MetaQuotes-Demo thường phải có execution lane riêng, không giả approval quỹ để vượt gate. METAAPI provider trước đó chưa ready; không có official MT5 terminal execution host trong cloud này.
2. `risk/RISK_POLICY.md` chưa chốt % mỗi lệnh, tổng risk, số thua liên tiếp và DD; agent không được tự định nghĩa hard limits. Login/password hoạt động không đủ mở execution.
3. 7 forward states cũ mất direction/giá/stop (undefined/null) vẫn bị chặn bởi forward v2. Không bịa field, không reset để che lịch sử. 7 state còn giá trị vẫn legacy JSON string và decoder hỗ trợ đọc.
4. BTC, US30, WTI/Brent và US500 CFD chưa có raw snapshot mới đủ nguồn/phí trong cloud này. Thử truy cập public Yahoo/Bitstamp bằng HTTP bị URLError; chỉ dùng 26 snapshot GitHub có pin. SPY/USO chỉ là proxy nghiên cứu, không được ghi là đã hoàn tất toàn thị trường.

## Bước tiếp

Hoàn thiện ordinary-DEMO execution lane tái sử dụng TF-013A và risk/kill/recovery đã có, cung cấp execution host/provider khả dụng, chốt hard risk bằng Founder, rồi kiểm chứng broker lifecycle thật trên DEMO. Cải tiến research chỉ được promote qua cổng đã chốt; không tự cập nhật bot dựa trên lịch sử đã xem. Full R3 và independent forward vẫn chưa hoàn thành.

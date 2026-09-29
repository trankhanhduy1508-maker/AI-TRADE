# CWS AutoTrade R1 — checkpoint nguồn HistData thật, 2026-09-29

**Branch:** `codex/p0-covel-knowledge-audit`. **HEAD trước checkpoint:** `a31b0d011d9227526cd9c9137e8f405002c30b20`. **Trạng thái nghiên cứu:** `UNPROVEN`. Không chỉnh sửa Main, Production, R0 hoặc mở lại historical OOS. Không có lệnh LIVE/DEMO-send, không dùng Founder PC, không phát sinh phí.

## Đọc tối thiểu (không ground lại cả repo)
1. `research/CWS_AUTOTRADE_BLIND_R0_R1_HANDOFF_2026-09-29.md` và `research/CWS_AUTOTRADE_R1_SOURCE_RISK_HANDOFF_2026-09-29.md`.
2. `research/CWS_AUTOTRADE_R1_FREE_DATA_SOURCE_HANDOFF_2026-09-29.md`.
3. `research/CWS_AUTOTRADE_R1_M1_DERIVED_H4_SOURCE_REGISTRATION_2026-09-29.md` (đăng ký nguồn trước quan sát, commit `3f860f001c6f1b6672a76bf28bb5c71425045e4e`).
4. `reports/CWS_AUTOTRADE_R1_HISTDATA_EURUSD_202608_SOURCE_INTEGRITY.json` (commit `a2d1e09eea0bfcef64947d203ea19ef52ceec95d`).
5. `reports/CWS_AUTOTRADE_R1_56_CELL_SOURCE_COVERAGE_2026-09-29.json` (commit `a31b0d011d9227526cd9c9137e8f405002c30b20`).
6. Khi sửa mã: `src/data_loader/histdata_m1_h4.py`, `tests/data_loader/test_histdata_m1_h4.py`, `scripts/inspect_histdata_public_zip_once.py`, `.github/workflows/cws-r1-histdata-public-zip-probe-once.yml`.

## Kết quả có bằng chứng thật
- Chính HistData công bố ASCII BID M1, timestamp EST cố định UTC−05:00 (không DST), và giao diện tải ZIP công khai thông qua form `POST /get.php`; không dùng FTP trả phí, PayPal form hay endpoint đoán. Trang gốc: https://www.histdata.com/download-free-forex-historical-data/?/ascii/1-minute-bar-quotes/eurusd/2026/8 .
- Tệp EURUSD tháng **2026-08** thực qua quy trình tải miễn phí bình thường: `DAT_ASCII_EURUSD_M1_202608.csv` 1,646,784 bytes và `DAT_ASCII_EURUSD_M1_202608.txt` status sidecar 16,793 bytes. ZIP SHA-256 `65c7c5d0f170abf4a60b86908723ef5068ccec7aa3c76baefbe8542f87eed5b3`; CSV SHA-256 `3060c51484d3f6882fb4c2fd468673e827a07657cd3708ee31bae08f83226991`; TXT SHA-256 `96f6ca517c2ff0d612496aed7352e126b47f6a72075a14b2dc7e09f038ab1a53`.
- Kết quả parser **trên dữ liệu thực**, đọc OHLC BID: **30,496 nến M1** → **93 H4 tổng hợp**, loại **35** block không đủ đúng 240 phút liên tục. Không tạo phút giá thiếu, không claim native H4, không bid/ask execution. GitHub workflow: https://github.com/trankhanhduy1508-maker/AI-TRADE/actions/runs/36576897674 ; job `109434728440`; tested SHA `b54b3ef660839fc3e7e8b8122ac331b713fc88d2`. Smoke 19 fixture tests PASS, Runtime real file parsing `REAL_FILE_DERIVED_H4_INTEGRITY_ONLY`, Fault 19 fixture tests PASS. 0 chiến lược/holdout/lệnh được mở.
- Các attempt trung gian: workflow `36576207638` xác minh chỉ form (không ZIP anchor); `36576409190` đọc cấu trúc form; `36576585821` lấy ZIP nhưng script ban đầu từ chối vì chỉ mong 1 CSV; `36576689345` xác minh có đúng CSV+TXT; sau đó sửa tối thiểu allowlist hai file và QA đạt `36576897674`. Workflow `success` không tự động đồng nghĩa provider data pass; chỉ run cuối có trạng thái `REAL_FILE_DERIVED_H4_INTEGRITY_ONLY`.
- Parser HistData 19 synthetic tests ×3 QA: https://github.com/trankhanhduy1508-maker/AI-TRADE/actions/runs/36574965444 . Bitstamp public GET BTC/ETH H4/D1 4/4 ô, 8 nến đóng/ô, 32 nến source-only: https://github.com/trankhanhduy1508-maker/AI-TRADE/actions/runs/36575325302 ; metadata file `reports/CWS_AUTOTRADE_R1_PUBLIC_SOURCE_PROBE_2026-09-29.json`. OANDA parser/risk QA 120/120 synthetic: run `36575517798`; R1 ledger QA 63/63 synthetic: run `36575830111`.
- Coverage **56 ô**: R0 30 ô lịch sử khám phá, thiếu 26 H4 **gốc**; 19 ô có ứng viên HistData derived theo danh sách symbol, chỉ **1 ô EURUSD_H4 được quan sát bằng file thật**; các ô khác không tự nhận đã truy xuất. 0 broker cost verified, 0 independent forward trades.
- R0 bất biến, blob hashes lần trước: prereg `c24865edfc76f9f21614de1f35451143eb0f927b`; manifest `57c4075587ff9f97b27f8480ddffb1061f264fc4`; results `56647bef016efcd1e2eb2d8b03028cdc060652e6`; engine `304ef89ee0a93f9b8ddfa08e7817cf6e320bed39`. Không chạy lại historical OOS đã mở.

## Cổng chưa đạt, không được fake PASS
1. HistData bid-only M1-derived H4 **không giải quyết 26 H4 native** và là proxy khác sản phẩm/venue. 93 H4 chưa đủ SMA200, không phải mẫu để công nhận backtest. 35 block bị loại theo rule 240 M1, phải ghi lỗi chứ không lấp.
2. Chính sách quyền lưu trữ dài hạn/commercial và redistributing tệp raw HistData chưa xác minh; không upload ZIP/CSV lên GitHub/Drive. Chỉ lưu SHA-256/metadata; không thể khẳng định reproducibility nguyên bản dài hạn.
3. Chưa kết nối broker/OANDA practice read-only được ủy quyền, phí spread/commission/swap/slippage thực, contract size, FX conversion và actual next-bar-open quote. Cấm suy ra USD account returns từ price units/R.
4. Forward R1 cutoff `2026-09-30T00:00:00Z` chưa đến thời điểm thực hiện phiên này. CSV/ohlc tải hồi cứu không được gọi là contemporaneous forward-paper fill. Chưa có 90 ngày forward/100 lệnh mới, do đó `UNPROVEN`.
5. Không bật scheduler ngầm, không gọi broker order-send; user quy định Smoke→Runtime→Fault có log SHA và fix tối thiểu khi FAIL.

## Tiếp tục
- Xác minh read-only broker native H4/điều khoản lưu dữ liệu khi có kết nối hợp pháp và miễn phí. Không dùng OANDA token cá nhân qua public GitHub.
- Nếu chỉ nghiên cứu chất lượng nguồn: kiểm tra thêm tháng/cặp bằng chính free form công khai, không hiển thị raw giá hay tính hiệu suất trên R0 holdout. Mọi nghiên cứu performance mới phải prereg manifest và dataset split **trước** holdout riêng.
- Xây event-time, phí venue và risk audit cho R1 forward paper bằng chứng mới, chỉ sau cutoff, vẫn không kết nối LIVE/DEMO-send.
- Lưu đầy đủ cả kết quả thua lỗ, trường hợp nguồn lỗi và giao dịch chưa đóng; không công nhận edge khi thiếu bằng chứng độc lập.

# CWS AutoTrade R2 — checkpoint backtest dài hạn và kiểm toán dữ liệu (2026-09-29)

**Repository:** `trankhanhduy1508-maker/AI-TRADE`  
**Nhánh duy nhất:** `codex/p0-covel-knowledge-audit`  
**HEAD đầu phiên:** `99c4a53c9fb6797040a65e97e697474dc8b4e7a1`  
**HEAD trước checkpoint:** `e84116fc52bee51197c530db15025f4a0b716ea1`  
**Trạng thái:** `UNPROVEN`; 0 lệnh LIVE/DEMO-send, 0 lệnh forward độc lập. **Không sửa R0/Main/Production; không dùng máy Founder hoặc phát sinh chi phí.**

## 1. Mục tiêu đã đăng ký trước, không dùng thông tin tương lai

R2 là protocol **mới**, tách với R0 đã đóng băng. Đã commit prereg `research/CWS_AUTOTRADE_R2_WALK_FORWARD_PREREG_2026-09-29.md` tại `6934a383b145369bb2447da29b3232e7ef04ab4d` trước khi quan sát hiệu suất thực trong phiên. Các ứng viên cố định R0_REFERENCE 55/20/ATR2.5; R2_FAST 40/15/ATR2.0; R2_SLOW 80/30/ATR3.0; SMA200, ATR20. Mỗi bước 250 nến, học chỉ từ `bars[:T]` với cửa sổ tối đa 1.000 nến, tối thiểu 5 lệnh train, chọn theo `expectancy_R - 0.01 × DD_R`; không đủ mẫu thì FLAT. Test lịch sử đánh giá 250 nến tiếp theo; dữ liệu đoạn này chỉ được bổ sung cho những lần chọn sau, không sửa lại kết quả cũ.

Các giai đoạn lịch sử trước đây R0/TF-004/TF-014 đã được xem **vẫn là `HISTORICAL_REUSED`** bất kể walk-forward thực thi không đọc nến tương lai. Không gọi là holdout mới. Không đổi tham số R0 theo kết quả này; thay đổi R2 trong tương lai cần đăng ký lại giao thức và kiểm chứng trên cửa sổ khác, không tái dùng cùng holdout.

**Mã đã ghi đúng nhánh:** `src/research/r2_walkforward.py`, `r2_csv.py`, `r2_batch.py`, `scripts/run_r2_offline.py`; test `tests/research/test_r2_walkforward.py`, `test_r2_csv.py`, `test_r2_batch.py`. Mã yêu cầu normalized UTC OHLC và trạng thái quyền nghiên cứu. File nguyên bản không có quyền lưu được kiểm toán **không upload** vào GitHub/Drive. Mỗi kết quả vẫn `edge_status=UNPROVEN`; phí giả định gắn `MODELED_ONLY`, không diễn giải thành net đã kiểm chứng. Tiến hành bằng GitHub connector + cloud sandbox, không dùng GitHub Actions.

## 2. Coverage 56 ô: không fake hoàn thành

Manifest cố định toàn bộ 28 thị trường × H4/D1: `research/manifests/CWS_AUTOTRADE_R2_LONG_HORIZON_INPUT_CATALOG_2026-09-29.json` (commit `facbd20e133daeabd22c8e749e1e1443aa213d56`). Trước đó R0 đã khám phá 30 ô, thiếu 26 ô native H4; R0 OOS mở rồi, không chạy lại. Trong phiên này **chỉ một ô S&P 500 D1** có nguồn giá lịch sử thực đủ chất lượng để replay; 55 ô **chưa** backtest thực trong phiên này. Kiểm toán đầy đủ `reports/CWS_AUTOTRADE_R2_56_CELL_SESSION_COVERAGE_2026-09-29.json` commit `e84116fc52bee51197c530db15025f4a0b716ea1`.

Không có file giá đầy đủ cho FX, vàng, bạc, WTI, Brent, crypto, chứng khoán, native H4 trong cloud/Drive hiện tại. Ứng viên nguồn công khai chưa có file, xác thực quyền sử dụng, hoặc OHLC hợp lệ thì phải ghi `DATA_UNAVAILABLE` chứ không suy diễn lợi nhuận. Dữ liệu đã khám phá R0 không được đếm là backtest mới.

## 3. Kiểm toán nguồn gần 100 năm của S&P 500, chốt trước khi mở hiệu suất

Nguồn GitHub read-only `fja05680/dow-sp500-100-years`, source commit `52a1ddd481fc947e511f709896d4f2b3fb49fb0e`, `SP500.csv`, Git blob `9f52b84ad69c7f4b19b30f9db4efd10635d342a7`, 23.104 dòng 1927-12-30→2019-12-23, raw SHA256 `6836bc88f522e1e204c1c703baff5667ea2b3586c8711052deb689c52e2c6d17`. Nguồn tự mô tả dẫn dữ liệu từ Yahoo; **tệp retrospective chưa chứng thực vintage giá như biết tại ngày lịch sử**, chưa xác minh quyền raw redistribution/commercial. README/LICENSE MIT của repo tác giả không được coi là giấy phép bản quyền giá thị trường gốc. Không đưa raw lên GitHub/Drive.

**Lỗi nguồn nghiêm trọng:** 8.509 dòng trước năm 1962 chứa bốn giá OHLC bằng nhau; có thêm 38 ngày sau 1962, kể cả chuỗi nhiều ngày năm 1967 và 1971, mang OHLC bằng nhau dù có volume dương. Kho lưu khác (`Vaibhav/Stock-Analysis`) có cùng 38 ngày lỗi, không phải kiểm chứng độc lập. **Trước khi tính performance**, đã commit source prereg `research/manifests/CWS_AUTOTRADE_R2_SP500_D1_SOURCE_1983_2019_2026-09-29.json` commit `2567c7cdb0ea745696e5c05dab2703e5a40a100b`: chỉ nhận đoạn sau 1983-07-01 đã qua gate; không điền OHLC thiếu.

Sau kiểm toán: **9.197 D1 OHLC** 1983-07-01→2019-12-23, 0 invalid, 0 OHLC all-equal, 0 duplicate; normalized SHA256 `bfe505bb20133a29ecab00262f8d635a393c37c82836585ebfcdcc3e95bf96ce`. Ngày nguồn chỉ là session label, được mã hóa UTC midnight cho xếp thứ tự, **không** phải dấu thời gian actual market-open hoặc giá được xuất bản ở quá khứ. S&P 500 là **cash index không giao dịch trực tiếp**, không quy đổi kết quả sang tài khoản MT5.

## 4. Kết quả thực, đã lưu nhưng không phải chứng minh edge

**Bằng chứng:** `research/results/CWS_AUTOTRADE_R2_SP500_D1_1983_2019_WALKFORWARD_2026-09-29.json` commit `ae495664e133c6ea46e0976c2a6abf12659473c6`, report blob `3c59574a233a099fdf5876295be2e13d34c26d19`.

Replay trên giá lịch sử thực qua **JS reference port** của Python R2 logic, giá được đọc bằng GitHub connector (không upload raw). **Trước khi mở giá thực**, kiểm tra parity Python↔JS trên 5 synthetic folds: cùng candidate, số trade, R/DD và trạng thái open trong ngưỡng 1e−7. Chưa chạy native Python production engine trên đầy đủ 9.197 giá thực; cần kiểm tra chéo độc lập trên chính tệp nếu có quyền/lưu bytes. Không fake loại kiểm thử này thành bản production.

**34** giai đoạn 250 nến, bắt đầu đánh giá khoảng 1985-06-24 và hết giai đoạn cuối 2019-03-14; những nến cuối không đủ 250 bỏ qua theo prereg. **85** lệnh mô phỏng đã đóng, gross-only, mean closed-trade `+0.1311917354686225 R`, tổng isolated fold realized `+11.151297514832914 R` **không là equity portfolio**. Còn **11** giai đoạn kết thúc có vị thế mở (không giả thanh lý hay bỏ khỏi báo cáo), 1 gap stop, lựa chọn FLAT 1 / R0_REFERENCE 11 / FAST 7 / SLOW 15. Không được chuyển tổng R thành % vốn/USD vì vị thế reset sau từng episode, nguồn không tradeable, thiếu multiplier/FX, phí và công thức capital carry.

Phân tích không chọn lọc:

| Giai đoạn bắt đầu | Số fold | Lệnh đóng | Realized R tổng các fold độc lập | Vị thế còn mở cuối fold |
|---|---:|---:|---:|---:|
| 1980s | 5 | 15 | -3.4346276896 | 2 |
| 1990s | 10 | 21 | +6.5896270062 | 3 |
| 2000s | 10 | 22 | +0.3456437912 | 2 |
| 2010s | 9 | 27 | +7.6506544070 | 4 |

**17 fold âm**, 13 dương, 4 fold realized bằng 0. Tổng R *chưa thực hiện* tại cuối 11 fold mở là +24.4312009325 R, **không gộp với lợi nhuận đã đóng** và không dùng làm danh mục tái đầu tư. Đây là dấu hiệu kết quả phụ thuộc đáng kể vào đánh dấu vị thế mở và các thời kỳ. Đặc biệt fold bắt đầu 1989-06-08 có 7 lệnh đóng, realized -4.30368 R và vị thế mở +2.26157 R. Kết quả khả quan gross trung bình không đủ để kết luận edge.

## 5. Dow Jones từ 1885: tìm được giá, từ chối fake OHLC

Cùng nguồn, `DJA.csv` blob `0141e90a628ddb77804648e8eca7f03d6f9334dd`: **36.863** dòng 1885-05-02→2019-12-24, **36.863/36.863 dòng OHLC đều bằng nhau và volume 0**. `DJA-orig.csv` blob `677738099fb24d2495a73dad42f38fcb50ad4e6f` là chuỗi single-close MeasuringWorth, gồm giai đoạn chỉ số tiền thân và điều chỉnh nối dữ liệu. Không chạy hệ thống ATR/channel H4/D1 như thể có giá high/low/open thật. Chỉ có thể dùng cho nghiên cứu close-only ở protocol riêng *đăng ký trước khi mở kết quả*. Trạng thái `CLOSE_ONLY_REJECTED_FOR_R2_OHLC_ATR`.

## 6. QA thật, lỗi, giới hạn và thứ tự kế tiếp

Trước kết quả giá thật: kiểm thử container Python 3.13.5 trên cloud không phải Founder PC; Smoke 12/12, Runtime synthetic 17/17, Fault 60/60 (**89/89 PASS**, từng vòng exit 0), compileall PASS. 1 thử nghiệm gap-stop ban đầu FAIL do fixture không tạo tín hiệu đúng, chỉ sửa fixture rồi chạy lại. Test 14.610 nến synthetic → 56 fold hoàn tất trong 1,481s, không phải 40 năm giá thị trường. 7 file R2 code/tests/script đã đối chiếu Git blob SHA trùng byte. Các mã test có gate không để nến tương lai thay đổi lựa chọn trước, reject malformed OHLC/gap, quote tương lai, close-only nhầm OHLC, duplicate, thiếu rights, no orders. Khi thêm cost-stress 2x/3x và batch clock gate, đã chạy lại 29 test R2 theo 3 vòng PASS (tổng 89 bao gồm 60 R1). Lệnh bản R2: `python -m unittest tests.research.test_r2_walkforward tests.research.test_r2_csv tests.research.test_r2_batch` và per-class Smoke/Runtime/Fault.

**Những gì KHÔNG đạt:** chưa có chuỗi OHLC được chứng thực dài gần trăm năm cho S&P, chưa có dữ liệu sau 2019 từ nguồn này đến ngày 2026-09-29; 55 ô thị trường chưa backtest dữ liệu thật trong phiên; chưa có raw archive/rights verified để tái lập; chưa có kết quả cross-check native Python trên raw SPX; chưa có phí tài khoản thực, index không phải executable vehicle, benchmark passive cùng venue, bootstrap/outlier kiểm toán và forward mới. Không có việc tiếp tục ngầm sau phiên.

**Thứ tự nghiên cứu tiếp:** xác nhận quyền nghiên cứu/lưu của nguồn S&P và thị trường khác; tải đúng khoảng sớm nhất **thực sự có OHLC**, hash và đăng ký từng dataset trước performance, bổ sung năm 2020–2026 mà không đổi các kỳ trước; chạy native Python và so sánh reference port trên cùng bytes; thực hiện cùng R2 protocol 56 ô có dữ liệu, ghi mọi skip/âm/dương và 2x/3x modeled stress nếu có profile phí có căn cứ. Với 1885 Dow chỉ nghiên cứu close-only bằng prereg khác; không biến close-only thành OHLC. Mọi khả năng thích nghi mới từ kết quả R2 vừa mở phải mang version/window mới, không mô tả là kiểm chứng out-of-sample độc lập.

**Cổng bất biến:** 0 lệnh LIVE/DEMO-send, 0 lệnh độc lập, `UNPROVEN`, không sửa R0/OOS đã mở, không đụng Main/Production, không bật lịch, không tốn phí.

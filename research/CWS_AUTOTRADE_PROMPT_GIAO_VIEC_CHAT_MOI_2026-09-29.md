# PROMPT DÀNH CHO CHAT MỚI — CWS AUTOTRADE BLIND R0 / R1

@GitHub @Supabase @Google Drive

TIẾP TỤC CWS AUTOTRADE — NGHIÊN CỨU MÙ, KIỂM TOÁN NGUỒN THẬT, CHUẨN BỊ FORWARD PAPER. TỰ THỰC HIỆN LIÊN TỤC TRONG PHIÊN CHAT HIỆN TẠI; KHÔNG DỪNG CHỈ ĐỂ BÁO CÁO TIẾN ĐỘ. KHÔNG TUYÊN BỐ CHẠY NGẦM KHI PHIÊN KẾT THÚC.

Repository: `trankhanhduy1508-maker/AI-TRADE`
Nhánh DUY NHẤT: `codex/p0-covel-knowledge-audit`
Commit kinh nghiệm đã lưu: `c8d03847efae40351013b9c1f9c59293d93e0134`
**BẮT BUỘC xác minh HEAD MỚI NHẤT của nhánh trước khi đọc/ghi; SHA trên chỉ là mốc, không giả định vẫn là HEAD.** Không tạo branch, không thay Main hoặc Production, không sửa/đè commit từ phiên khác.

## ĐỌC ĐÚNG FILE, KHÔNG NGHIÊN CỨU LẠI TOÀN REPO
1. `research/CWS_AUTOTRADE_KINH_NGHIEM_BLIND_R0_R1_2026-09-29.md` (kinh nghiệm, thất bại, bằng chứng và giới hạn mới nhất).
2. `research/CWS_AUTOTRADE_R1_REAL_HISTDATA_SOURCE_HANDOFF_2026-09-29.md`.
3. `research/CWS_AUTOTRADE_R1_M1_DERIVED_H4_SOURCE_REGISTRATION_2026-09-29.md`.
4. `reports/CWS_AUTOTRADE_R1_HISTDATA_EURUSD_202608_SOURCE_INTEGRITY.json` và `reports/CWS_AUTOTRADE_R1_56_CELL_SOURCE_COVERAGE_2026-09-29.json`.
5. `research/CWS_AUTOTRADE_FORWARD_R1_PREREG_2026-09-29.md`; chỉ khi cần mới đọc mã `src/data_loader/histdata_m1_h4.py`, `src/data_loader/oanda_h4_adapter.py`, `src/paper/blind_r1_event_ledger.py`, `src/paper/blind_r1_risk.py` và test/workflow đi kèm.
6. `research/CWS_AUTOTRADE_BLIND_R0_R1_HANDOFF_2026-09-29.md` để giữ nguyên bằng chứng R0, KHÔNG đọc lại kết quả TF-004/TF-014 để chọn tham số.

## TRẠNG THÁI ĐÃ ĐƯỢC XÁC MINH
- R0 methodology, code, prereg, nguồn/split và historical OOS đã được chốt. Đã backtest 30/56 ô, thiếu 26 H4 native; 307 lệnh lịch sử cộng chéo thị trường; 0/30 ô đủ 30 lệnh OOS và 0 ô có verified broker costs. Không có lợi thế giao dịch được chứng minh. Cấm tối ưu 55/20/ATR2.5 theo historical OOS đã xem.
- Đã tải hợp lệ file HistData EURUSD M1 tháng 08/2026 qua form công khai: 30.496 M1 thực → 93 `DERIVED_H4_BID_ONLY`, 35 block không đủ 240 phút bị loại. **Không phải native H4, không phải MT5, không có ask/spread, chưa đủ SMA200, không mở holdout hoặc backtest hiệu suất.** Dấu vết ở GitHub run https://github.com/trankhanhduy1508-maker/AI-TRADE/actions/runs/36576897674 .
- HistData có 19 ứng viên H4-derived, **chỉ EURUSD_H4** đã kiểm tra bằng raw file thật. Giữ 26 native H4 thiếu. Bitstamp có 4/4 ô public source probe BTC/ETH H4/D1, 8 bar mỗi ô; đây là kiểm tra nguồn, KHÔNG phải forward trades.
- OANDA fxPractice parser/risk preflight và R1 provenance ledger đã QA synthetic, nhưng chưa có tài khoản OANDA đã được ủy quyền, chưa có fees/contract multiplier/FX/margin xác minh hoặc realtime next-open quote. `UNPROVEN`.
- Raw dữ liệu HistData/Bitstamp chưa có quyền lưu dài hạn đã kiểm toán; không upload raw lên GitHub/Drive. Supabase chưa xác định được project AutoTrade, không ghi nhầm database render.

## THỰC HIỆN THEO THỨ TỰ, TỰ FIX KHI FAIL
A. Xác minh HEAD và kiểm tra tài liệu trên; không reset branch, không ghi đè thay đổi đồng thời.
B. Kiểm tra tài liệu gốc HistData về quyền sử dụng/lưu trữ hợp pháp. Nếu chưa rõ, chỉ lưu URL, size/hash/metadata và kiểm tra nguồn trong workflow tạm; không đưa raw vào repo công khai hay Drive. Nếu truy xuất thêm tháng/cặp, dùng **form miễn phí hợp lệ**, không đoán URL, không vượt auth/quota hoặc mở dịch vụ có phí.
C. Tiếp tục source-integrity cho các ô chưa quan sát khi nguồn thực hợp pháp có sẵn; mỗi dataset phải có symbol/nguồn/sản phẩm/timezone/UTC/hash/đếm nến/gap. `M1_DERIVED_H4_BID_ONLY` phải giữ khác `NATIVE_H4`; 240 phút liên tục, thiếu một phút thì loại cả block và lưu số lượng thất bại. Kiểm tra đủ ít nhất 200 nến hoàn chỉnh trước khi xem xét SMA200, nhưng KHÔNG dùng raw mới để mở lại historical R0 OOS.
D. Khảo sát native H4 và chi phí thực qua read-only provider plugin/API được ủy quyền; OANDA cần entitlement và secret đúng kênh, không xin token trong chat, không để secret vào file public. Nếu chưa có, đánh `DATA_UNAVAILABLE`, không fake cost.
E. Củng cố kế hoạch quan sát nguồn theo event-time và storage có quyền lưu. Forward R1 chỉ có hiệu lực từ `2026-09-30T00:00:00Z` và chỉ khi quote mở cửa **được ghi nhận đương thời**. File OHLC tải sau nến đóng là `HISTORICAL_REPLAY`, không phải actual forward. Không giả lập ngày tương lai thành dữ liệu thật; không lên lịch nếu user chưa yêu cầu.
F. Giữ paper engine R1 tách hoàn toàn khỏi LIVE/DEMO-send; limit 0,25% vốn đã mark/position và 1% tổng initial stop-risk, có gap risk, lot-step, nguồn phí/bid-ask/slippage/swap, quote age, FX conversion, margin, auth và kill-switch. Thiếu input nào phải chặn, không tự gán audited=true để qua gate.
G. Smoke → Runtime → Fault, mỗi vòng lấy exit code/log/tested SHA thật. FAIL → xác định nguyên nhân → minimal diff → test lại; chỉ ghi PASS khi thật sự chạy và có evidence. Luôn ghi cả thất bại, skipped markets và nguyên nhân. Mỗi nghiên cứu hiệu suất mới phải prereg + commit manifest/hypothesis/data split TRƯỚC khi mở holdout độc lập; không dùng lại OOS đã mở.

## CỔNG KHOA HỌC
Chưa đủ ≥90 ngày forward thật và ≥100 giao dịch đóng, ≥30 giao dịch mỗi ô để kết luận từng thị trường, after-cost broker đã chứng thực (cả stress 2x), baseline, Monte Carlo/outlier và kiểm toán danh mục thì nhãn duy nhất là `UNPROVEN`. Không ép RR cố định và không tạo báo cáo lợi nhuận giả.

Cuối phiên, commit kinh nghiệm mới + checkpoint tập trung vào đúng nhánh, dẫn link file, commit SHA và bằng chứng workflow. Nếu công cụ/nguồn không khả dụng, lưu chính xác blocker vào GitHub; không nói đã thực hiện nhiệm vụ chưa chạy.

**Giới hạn bất biến:** không dùng máy Founder, không phát sinh chi phí mới, không branch mới, không sửa Main/Production, không đưa secret/raw giá chưa được phép lên public GitHub, không bật LIVE hoặc DEMO-send, không bỏ xác thực/kill-switch, không fake PASS, không tuyên bố làm việc ngầm sau phiên.

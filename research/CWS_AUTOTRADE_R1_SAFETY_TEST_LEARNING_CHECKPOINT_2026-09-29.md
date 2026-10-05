# CWS AutoTrade R1 — Kiểm thử, sửa lỗi an toàn và kinh nghiệm, 2026-09-29

**Repository:** `trankhanhduy1508-maker/AI-TRADE`  
**Nhánh duy nhất:** `codex/p0-covel-knowledge-audit`  
**HEAD đầu phiên:** `e762b6477e5b43cbb73627accdd10f0b7024b01e`  
**HEAD trước checkpoint:** `9ca81219e1e25b293333e16d2555f0d22dca4f92`  
**Nhãn khoa học:** `UNPROVEN`; nghiên cứu này **không** đo/đánh giá lợi nhuận, không mở lại historical OOS của R0, không có giao dịch LIVE/DEMO-send.

## 1. Phát hiện có thể tái hiện

`src/paper/blind_r1_risk.py` dùng `all((...))` kiểm tra tính đúng/sai của 8 cổng audit và kill-switch; Python coi chuỗi `"false"` và số nguyên `1` là truthy. Nhánh SHORT trước đây dùng `not value.short_allowed`, nên một chuỗi `"false"` cũng có thể vượt kiểm tra cho phép bán khống trong **synthetic paper preflight**. Đây là lỗi fail-closed của bộ tính toán mô phỏng, **không** phải bằng chứng đã gửi lệnh thực.

Kiểm thử hồi quy được viết trước khi sửa. Lần đầu chạy `tests.paper.test_r1_boolean_safety.Fault`: exit code **1**, 9 test methods, **11 lỗi** (8 subtests cổng audit và 3 trường hợp quyền short/kiểu dữ liệu), vì phản hồi đã đi qua cổng thay vì bị từ chối. Không bỏ test lỗi.

## 2. Minimal diff đã commit

- `if value.direction=="SHORT" and not value.short_allowed` → `value.short_allowed is not True`.
- `all((flag1, ...))` → `all(flag is True for flag in (...))`.
- Giữ nguyên mode `RESEARCH_PAPER_ONLY`, 0,25% mỗi vị thế, 1% tổng initial-stop risk, cơ chế round-down, phí/trượt giá/swap giả lập, `orders_sent=0`. Không sửa tín hiệu, tham số hoặc engine R0.
- Mã cập nhật: `src/paper/blind_r1_risk.py`, blob SHA `81556bd5c92a1e8afd44105f36890ed70ce69ead`.
- Test mới: `tests/paper/test_r1_boolean_safety.py`, blob SHA `74602b52c8367deb92d71195af85a2e4fa83872b`; `tests/paper/test_r1_risk_properties.py`, blob SHA `5388e30566e696937b59f3545e8cc4521e080dc3`.

## 3. Smoke → Runtime → Fault, bằng chứng chạy thật

**Môi trường:** Python 3.13.5 trên container cloud của phiên, **không** dùng máy Founder. Workspace là bộ file đích được chép từ GitHub/phiên hiện tại; không phải checkout toàn bộ repository vì container không phân giải được github.com. Sau khi ghi mã qua GitHub connector, đã so sánh **Git blob SHA trùng tuyệt đối cho cả 9 file nguồn/test đã chạy**. `compileall` trên `src/paper`, `tests/paper`, `tests/data_loader` exit 0.

Lệnh dùng ở từng vòng:
```bash
for tier in Smoke Runtime Fault; do
  python -m unittest \
    tests.paper.test_r1_boolean_safety.$tier \
    tests.paper.test_r1_risk_properties.$tier \
    tests.paper.test_r1_source_receipt.$tier \
    tests.paper.test_r1_forward_readiness.$tier \
    tests.data_loader.test_kraken_native_h4.$tier -q
done
```
**Sau fix và đối chiếu SHA:** Smoke **8/8 PASS**, Runtime tổng hợp **11/11 PASS**, Fault **41/41 PASS**, tổng **60/60**; mỗi vòng exit 0. Risk property runner dùng seed `20260929` và **1.000** cấu hình giả lập để kiểm tra risk fraction, total initial risk, lot-step, margin và `orders_sent=0`. Fault kiểm tra chuỗi `"true"/"false"`, số nguyên, `None`, danh sách trên các cổng kiểm toán, kill-switch và quyền short. Không nhận PASS chỉ vì test được tạo/commit.

Các nguồn khác giữ nguyên byte so với GitHub:
- `src/paper/r1_source_receipt.py` `01ee27ea79b6080a4fde12f37fbc75eb4f20621f`;
- `tests/paper/test_r1_source_receipt.py` `99758188c877baf993b29cb66bb06c6f4655be02`;
- `src/paper/r1_forward_readiness.py` `bf0cd399ea15681d6a59bc8b2bac778fd9963f58`;
- `tests/paper/test_r1_forward_readiness.py` `7c35cd67eae012cc44dfce21b55b39dcda82db13`;
- `src/data_loader/kraken_native_h4.py` `0fb9d3242c15b25324403e9f88be3e4ceff92f39`;
- `tests/data_loader/test_kraken_native_h4.py` `9633f0f130078ef7014bf136a108a37ced51940e`.

## 4. Quy trình tự cải tiến mà không overfit

1. **Phát hiện:** ghi lại một lỗi cụ thể, tạo bài test có thể tái hiện FAIL trước khi sửa.
2. **Sửa:** sửa tối thiểu, không chỉnh thông số giao dịch theo historical holdout đã mở.
3. **Kiểm chứng:** chạy 3 vòng và các thuộc tính bất biến trên fixture, giữ kết quả lỗi và SHA.
4. **Phân loại:** `SAFETY_FIX_VALIDATED_SYNTHETIC` khác `STRATEGY_EDGE_UNPROVEN`. Bản vá không chứng minh cải tiến expectancy hoặc tỷ lệ lãi/lỗ.
5. **Đánh giá chiến lược mới khi có dữ liệu:** prereg R2 riêng và split TRAIN→VALIDATION→forward mới **trước** quan sát; không chọn tham số dựa vào R0 historical OOS đã mở. Kiểm thử mô phỏng không cần broker; chi phí giả định phải gắn `MODELED`, chưa coi là chi phí thực của tài khoản.

## 5. Giới hạn và blocker trung thực

- Chưa chạy toàn bộ regression của repo, chỉ **9 file** risk/source/forward/ledger phụ trợ trong phiên này; chưa gọi API broker, chưa tải real market feed từ container do DNS/network không khả dụng.
- Chưa đánh giá bất kỳ chiến lược nào bằng dữ liệu mới. R0 và historical OOS giữ nguyên; forward R1 cutoff `2026-09-30T00:00:00Z` chưa tự khởi chạy; **0 lệnh forward độc lập** trong checkpoint này.
- Không thay đổi Main/Production, không tạo branch, không ghi Supabase render, không tải raw feed thiếu quyền lên Drive/GitHub, không phát sinh chi phí, không bật LIVE/DEMO-send, không lên lịch chạy ngầm.

**Bài học:** một boolean annotation trong Python không ép kiểu dữ liệu. Mọi cổng xác thực, kill-switch hoặc quyền short phải kiểm tra `is True` ở boundary. Đánh giá khả năng tự tiến bộ bằng test FAIL→fix→regression, không bằng lợi nhuận giả hoặc chọn lọc lịch sử.

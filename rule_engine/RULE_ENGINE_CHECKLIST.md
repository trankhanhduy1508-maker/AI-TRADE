# RULE_ENGINE_CHECKLIST — QA Checklist cho Rule Engine

Đây là checklist bắt buộc để kiểm tra một rule mới hoặc rule đã sửa trước khi đưa vào hệ thống
thực tế.

---

## A. Kiểm tra Cấu trúc Rule (11 mục bắt buộc)

Mỗi file `rule_engine/RULE_*.md` **PHẢI** có đủ 11 mục sau:

- [ ] **1. Tên Rule** — Tên ID rõ ràng (RULE_001, RULE_002, v.v.).
- [ ] **2. Mục đích** — Nêu rõ rule này dùng để làm gì, vì sao cần thiết.
- [ ] **3. Input** — Liệt kê tất cả dữ liệu đầu vào cần có (cụ thể, không mơ hồ).
- [ ] **4. Output** — Liệt kê tất cả kết quả có thể (cụ thể, có thể được code kiểm tra).
- [ ] **5. Điều kiện** — Công thức/logic rõ ràng để đánh giá (không chủ quan).
- [ ] **6. Ngoại lệ** — Mô tả các tình huống ngoài lệ, cách xử lý.
- [ ] **7. Ví dụ** — Ít nhất 1-2 ví dụ cụ thể với dữ liệu thực tế.
- [ ] **8. Dữ liệu cần** — Loại dữ liệu, format, nguồn (OHLCV, indicator, v.v.).
- [ ] **9. Khả năng Backtest** — Liệu rule này có thể backtest tự động được không? Có khó khăn gì?
- [ ] **10. Độ khách quan** — % mức độ khách quan (0-100%), có phần nào chủ quan cần lưu ý.
- [ ] **11. Điểm dễ gây Overfitting** — Tham số nào dễ gây overfit? Cách tránh.

---

## B. Kiểm tra Logic và Định nghĩa

### B1. Input/Output rõ ràng
- [ ] Input không mơ hồ: "giá cao" → cụ thể "close price", không dùng "some price".
- [ ] Output có thể được code kiểm tra: không dùng "cảm giác tốt" → phải có con số (>80%, <5 pip).
- [ ] Output phải có ít nhất 3 kết quả có thể (ví dụ: TRUE/FALSE/WEAK).

### B2. Điều kiện lô-gic
- [ ] Điều kiện phải rõ ràng, có thể viết thành code: `if condition: return result`.
- [ ] Không dùng từ mơ hồ như "khá", "ổn", "tạm được" → dùng con số.
- [ ] Nếu có ngưỡng (threshold), phải ghi cụ thể: "Volume > 150% SMA20" thay vì "volume tốt".

### B3. Dependency
- [ ] Rule này phụ thuộc rule nào khác? Ghi rõ (ví dụ: RULE_005 depends on RULE_003).
- [ ] Có rule nào bị conflict với rule này? Kiểm tra `RULE_CONFLICTS.md`.
- [ ] Liên hệ với chiến lược nào? Ghi rõ (`strategies/TF_001`, `TF_002`).

---

## C. Kiểm tra Tính khách quan

### C1. Công thức toán học
- [ ] Tất cả tính toán có công thức cụ thể không? (Body ratio = |Close-Open|/(High-Low), v.v.).
- [ ] Công thức có thể được lập trình tự động không?

### C2. Tham số Hardcoding
- [ ] Tất cả tham số (SMA period, ngưỡng volume, ATR multiplier, v.v.) có được **chốt cứng** trước
  không?
- [ ] Tham số đó có được **document rõ ràng** không (không để chỗ trống "chưa chốt")?
- [ ] Nếu tham số "chưa chốt", ghi rõ "Chưa chốt, cần Project Owner xác nhận" — không để mơ hồ.

### C3. Diễn giải tùy ý
- [ ] Có chỗ nào trong điều kiện để người phân tích "diễn giải tùy ý" không?
- [ ] Ví dụ "pullback hợp lệ" → phải rõ "hôi % bao nhiêu là hợp lệ", không dùng "nhìn có vẻ hợp lệ".

---

## D. Kiểm tra Backtest-ability

### D1. Dữ liệu
- [ ] Rule này cần loại dữ liệu nào? (OHLC, Volume, RSI, EMA, v.v.)
- [ ] Dữ liệu đó có sẵn hay cần tính toán trước?
- [ ] Có giới hạn lookback (bao nhiêu nến trước) không?

### D2. Backtest khác nhau
- [ ] Rule này có thể backtest on all timeframes không, hay chỉ một số timeframe?
- [ ] Có tham số phụ thuộc timeframe không? Ghi rõ.

### D3. Look-ahead bias
- [ ] Rule này có dùng dữ liệu "tương lai" không? (ví dụ: "nếu biết giá sẽ lên 10% sau")
- [ ] Khi backtest, có thể kiểm tra điều kiện rule này **ngay** khi bar close không, hay phải chờ bar
  tiếp theo?

---

## E. Kiểm tra Tính toàn vẹn Rule Engine

### E1. Thứ tự trong Decision Flow
- [ ] Rule này ở vị trí nào trong Decision Flow (Bước 1-10)? Có hợp lý không?
- [ ] Nếu điều kiện ở bước này fail, có reject/wait đúng không?

### E2. Scoring
- [ ] Rule này có điểm max bao nhiêu? Có trong bảng scoring không?
- [ ] Khi nào được điểm max, khi nào giảm, khi nào 0? Rõ ràng không?

### E3. Liên hệ chiến lược
- [ ] Rule này có được mention trong `strategies/TF_001` hoặc `TF_002` không?
- [ ] Nếu là rule xác định **stop loss hoặc entry**, có match chính xác với strategy không?

---

## F. Kiểm tra Ví dụ

### F1. Ví dụ đầy đủ
- [ ] Ví dụ có input cụ thể (con số thực, không biến số mơ hồ)?
- [ ] Ví dụ có output rõ ràng (TRUE/FALSE/WEAK, với điểm)?
- [ ] Ví dụ có logic giải thích (tại sao input dẫn đến output)?

### F2. Ví dụ đa dạng
- [ ] Có ví dụ cho **kết quả tốt nhất** (output max)?
- [ ] Có ví dụ cho **kết quả trung bình**?
- [ ] Có ví dụ cho **kết quả xấu** (reject hoặc 0 điểm)?

---

## G. Kiểm tra Ngoại lệ

### G1. Đã liệt kê ngoại lệ?
- [ ] Rule này có các tình huống đặc biệt cần handle không?
- [ ] Mỗi ngoại lệ có được mô tả và cách xử lý rõ ràng không?

### G2. Ngoại lệ và overlap
- [ ] Có ngoại lệ nào overlap với ngoại lệ khác không? (ví dụ: 2 cách xử lý cho cùng 1 tình huống)
- [ ] Nếu overlap, rule nào được ưu tiên?

---

## H. Kiểm tra Tài liệu

### H1. Ngôn ngữ
- [ ] Toàn bộ file viết bằng **tiếng Việt** không?
- [ ] Không có chữ Anh hỗn hợp mà không giải thích (trừ những terms standard như OHLC, EMA, v.v.)?

### H2. Tham chiếu
- [ ] Rule này có tham chiếu file khác không? Các tham chiếu có chính xác không?
- [ ] Ví dụ: "xem `risk/RISK_POLICY.md`" → file đó có tồn tại, và có nội dung liên quan không?

### H3. Không chép bản quyền
- [ ] Rule này có chép nguyên văn từ sách/khóa học không?
- [ ] Nếu dùng khái niệm từ nguồn khác, có ghi công nguồn không?

---

## I. Checklist Chung (tất cả rule)

- [ ] **Không có chép bản quyền** — toàn bộ nội dung được tổng hợp/diễn giải.
- [ ] **Không khẳng định sinh lời** — không viết "rule này chắc chắn sẽ thắng".
- [ ] **Ghi rõ trạng thái** — Nếu chưa chốt tham số, ghi "chưa chốt, cần Project Owner xác nhận".
- [ ] **Phân tầng rõ** — Giả thuyết ≠ quy tắc ≠ điều kiện kiểm chứng ≠ kết quả backtest.
- [ ] **Có thể lập trình** — Không có phần nào quá mơ hồ để dev implement không được.
- [ ] **Có thể backtest** — Không có input/output không khả thi backtest.

---

## J. Quy trình Kiểm tra (Step by step)

1. **Đọc toàn bộ file rule** 2 lần (một lần để hiểu, một lần để kiểm tra).
2. **Tích vào checklist từ A-I** — nếu thiếu, note lại và yêu cầu sửa.
3. **Kiểm tra logic rule:**
   - Viết lại điều kiện thành pseudocode (không phải code thật).
   - Chạy qua ví dụ → verify output có khớp logic không.
4. **Kiểm tra dependency:**
   - Liệt kê tất cả rule khác mà rule này phụ thuộc.
   - Kiểm tra xem các rule đó có tồn tại, đã hoàn thiện chưa.
5. **Kiểm tra xung đột:**
   - Xem rule này có xung đột nào trong `RULE_CONFLICTS.md` không.
   - Nếu có, xem xứ lý xung đột đó có hợp lý không.
6. **Cuối cùng:**
   - Nếu tất cả check ✓, rule được phê duyệt.
   - Nếu có ❌, liệt kê vấn đề và yêu cầu sửa.

---

## K. Mẫu Báo cáo Kiểm tra

```markdown
## QA Review — [RULE_ID]

**Reviewer:** [Tên]
**Date:** [Ngày]
**Status:** ✅ PASS / ❌ FAILED

### Kết quả

- Mục đích: ✓
- Input/Output: ✓
- Điều kiện: ✓
- ...
- Overall: ✅ PASS — Rule này được phê duyệt.

### Ghi chú (nếu có)

- [Nếu failed, liệt kê vấn đề cần sửa]

### Recommend

- [Những gợi ý cải tiến (optional)]
```

---

## L. Lưu ý cuối cùng

- Checklist này **bắt buộc thực hiện trước khi merge** rule vào hệ thống chính.
- Nếu không pass checklist, rule **không được dùng** cho tới khi được sửa.
- Checklist cũng được áp dụng cho bất kỳ **update/chỉnh sửa** rule hiện có.


# CWS AutoTrade — METHOD LAB V1: cải tiến phương pháp ngoài backtest
**Ngày:** 2026-09-29. **Repo:** `trankhanhduy1508-maker/AI-TRADE`. **Nhánh duy nhất:** `codex/p0-covel-knowledge-audit`. **HEAD đầu nhiệm vụ:** `1415bb02afaa8a4e1fd723d65231ca580fb9b094`. **HEAD trước checkpoint:** `e328964c6491e51551f0dc7fe925640c4d95fe5c`.

**Founder directive:** tập trung cải thiện **phương pháp**, không chỉ backtest; **bỏ nghiên cứu chi phí** trong nhiệm vụ này. Những gate chống giao dịch thật và nhãn phí chưa xác minh vẫn giữ nguyên, không thay bằng phí = 0 hay net đã kiểm chứng.

## 1. Nghiên cứu đã chốt trước viết mã

Spec bất biến `research/CWS_METHOD_LAB_V1_SIGNAL_FEEDBACK_SPEC_2026-09-29.md`, commit `750bb1a68c5b8fa90e116ae08feff5eb10f0d2d4`. Tách khỏi R3 đã prereg trước đây: R3 cũ có quy tắc lựa chọn gắn phí modeled, **không sửa hoặc tuyên bố implement R3**. Giữ nguyên R0/R1/R2/R2b và historical OOS đã mở. Các ngưỡng của METHOD LAB V1 là **giả thuyết kỹ thuật được khóa trước khi thấy bất kỳ kết quả empirical của V1**, không phải thông số đã có lợi nhuận được chứng minh.

- **Xác nhận breakout:** close vượt channel 55 prior highs/lows thêm 0,25×ATR20, nằm phía hợp lệ SMA200 với độ dốc SMA200 so 20 nến trước; thân nến >=0,50 ATR, close ở 25% cuối biên về phía phá vỡ. Không dùng râu nến một mình để chấp nhận.
- **Tránh sốc biến động:** ATR20 hiện tại lớn hơn 2×median 100 ATR20 **trước đó** ⇒ không tạo tín hiệu mới; không dùng ATR hiện tại trong reference median.
- **Phản hồi từ lệnh đã đóng:** 3/5 giao dịch nghiên cứu đã **đóng** lỗ theo gross initial-risk R ⇒ cách ly 20 nến đầy đủ; sau mỗi stop nghỉ ít nhất 5 nến đầy đủ. Không dùng unrealized làm giao dịch đã đóng; không tự thay tham số khi kết quả xấu.
- **Quản lý trạng thái liên tục:** một position/symbol trong bộ máy, signal ở close t, pending ở OPEN t+1, loại gap không hợp lệ, trailing stop từ 20 nến strict prior, stop không nới, gap-through xử lý OPEN bất lợi, entry-bar stop xử lý bảo thủ. **Không reset** position tại fold 250 như nghiên cứu R2.
- **Nguồn fail-closed:** chỉ tiếp nhận candle giá OHLC hợp lệ, đã đóng, timestamp/clock tăng đơn điệu, không nhận session gap chưa có chứng nhận bên ngoài. Cờ caller tự đặt True không là independent source audit. Short mặc định không cho phép nếu thiếu xác thực vehicle.
- **Giải thích quyết định:** ghi check bị từ chối riêng (`LONG_CHANNEL_BUFFER`, `LONG_STRONG_BODY`, `LONG_RISING_SMA`, v.v.), đếm các loại lỗi; phân tích phương pháp dựa vào lỗi đã quan sát thay vì sửa rule sau khi biết tương lai.

**Nguồn động cơ (không xác nhận chính các ngưỡng V1):** `https://doi.org/10.1016/j.jfineco.2011.11.003` và `https://doi.org/10.21314/JCF.2016.322`.

## 2. Mã thực thi, không gọi broker

- `src/research/method_lab_v1.py` — Git blob SHA **`76cd97d6f3bb5f13e6f1b3ef9ba663c4979fbca3`**. Gồm hàm thuần `signal_from_closed_history`, research state machine `ResearchMethod.on_bar`, giải thích lý do reject, persistent position/pending, trailing/gap/cooldown và feedback quarantine, audit snapshot. Không có HTTP, broker, order-send, timer/scheduler hay network import.
- `tests/research/test_method_lab_v1.py` — blob **`53cd3616ca1cb28c3f4ba640831b8f9a09bbdb80`**, 18 bài test.
- `tests/research/test_method_lab_properties.py` — blob **`449a3892cadab1a3d383c3815fc0b24453244f6e`**, 5 bài test bổ sung (H4, 1.000 nến seeded, 200 invalid mutation, unrealized không biến thành closed, session gap bị chặn).

**Đối chiếu GitHub:** `fetch_file` trên đúng nhánh xác nhận SHA ba file trùng chính xác `git hash-object` byte được chạy trong cloud container. Không dùng máy Founder, không dùng GitHub Actions, không tạo nhánh, không sửa Main/Production.

## 3. Bằng chứng kiểm thử thật

**Môi trường:** Python 3.13.5, cloud container cô lập, nguồn fixture **tổng hợp**, không fetch real prices để chạy V1. Lệnh:
```bash
python -m unittest tests.research.test_method_lab_v1.Smoke tests.research.test_method_lab_properties.Smoke -q
python -m unittest tests.research.test_method_lab_v1.Runtime tests.research.test_method_lab_properties.Runtime -q
python -m unittest tests.research.test_method_lab_v1.Fault tests.research.test_method_lab_properties.Fault -q
python -m compileall -q src tests
```

**Kết quả cuối sau khi chỉnh logic chặn tái tín hiệu trên bar gap-invalid và thêm diagnostics:** Smoke **4/4 PASS**, Runtime synthetic **8/8 PASS**, Fault **11/11 PASS**, tổng **23/23**, các lệnh exit 0. 1.000 nến sinh bằng seed 20260929, 200 dữ liệu đột biến bất hợp lệ bị chặn mà snapshot không bị thay. AST audit source import đúng `__future__`, `collections`, `dataclasses`, `math`, `statistics`, `time`; 0 import HTTP/socket/subprocess/broker/MetaTrader. `compileall` exit 0.

Đã kiểm: breakout đủ xác nhận ⇒ chỉ pending, không vào cùng nến; breakout chỉ bằng wick ⇒ từ chối kèm lý do; ATR shock ⇒ dừng tín hiệu; gap qua stop ⇒ thoát giả định ở OPEN xấu hơn; pending gap invalid ⇒ không vào và không re-signal cùng bar; vị thế giữ qua chỉ số nến 250/500; stop không nới khi vị thế tiếp diễn; nguồn clock/gap/unclosed/duplicate/NaN/future/string boolean bị từ chối; 3/5 lệnh **đã đóng** âm kích hoạt quarantine; vị thế còn mở không kích hoạt quarantine; prefix quyết định không thay khi suffix tương lai khác. `orders_sent=0`, `independent_forward_trades=0`.

**Ghi chép khắc phục:** ban đầu 18 bài test PASS cho bản core; sau audit thêm blocked-entry-bar tránh tái signal cùng nến gap-invalid, đồng thời thêm từng check thất bại để tra nguyên nhân. Chạy lại ba vòng và mở rộng lên 23 test; không giả một FAIL ban đầu đã không xảy ra.

## 4. Giới hạn, không fake hiệu quả

- Đây là **cải tiến kiến trúc quyết định và kiểm soát hành vi có bằng chứng synthetic**, **không có backtest lợi nhuận V1** và không có real forward paper run trong phiên này. Cổng ATR/breakout/quarantine có thể giảm false breakout **hoặc** bỏ lỡ trend và giảm lợi nhuận; chưa biết dấu/tác động thực nghiệm.
- Cờ source trong fixture do test cấp `True` **không** xác minh venue/market session ngoài đời; output luôn `data_source_independently_verified=False`. H4 cũ chưa được biến thành nguồn clock verified.
- Không nghiên cứu phí theo yêu cầu. Output `cost_status=NOT_EVALUATED`, `account_currency_pnl=None`, `edge_status=UNPROVEN`; gross R minh họa không thể thay net sau phí.
- Chưa chạy full repository regression hoặc nối live-feed/MT5; không chạm R0, R1 risk gates, main, production; không khởi chạy task background, không phát sinh phí.

**Hướng kiểm chứng khi có dữ liệu độc lập đã được cấp quyền:** ghi log mọi tín hiệu được nhận/từ chối và lý do từng check trên nến đóng ghi nhận đương thời; đo tỷ lệ false-break, stopout, số trend bị bỏ lỡ, thời gian quarantine và so sánh với reference R0 **trên cửa sổ đăng ký mới trước khi quan sát**, không dùng R2b đã thấy để tuyển V1. Không tự động tăng rủi ro hoặc gửi giao dịch.

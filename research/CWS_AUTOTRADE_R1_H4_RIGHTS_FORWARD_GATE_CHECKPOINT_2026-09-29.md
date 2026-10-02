# CWS AUTOTRADE — R1 H4 SOURCE RIGHTS + FORWARD SAFETY CHECKPOINT
**Ngày:** 2026-09-29 (Asia/Ho_Chi_Minh)  
**Repo:** trankhanhduy1508-maker/AI-TRADE  
**Nhánh DUY NHẤT:** `codex/p0-covel-knowledge-audit`  
**HEAD đầu phiên (đã xác minh):** `3efa9a189c51567b0a79baf9758bc9e9258d0838`  
**Trạng thái khoa học:** `UNPROVEN`. Không thay đổi R0, Main, Production hoặc historical OOS đã mở.

## 1. Phạm vi và nguồn chính thức đã kiểm tra
- HistData cho tải M1 miễn phí, giới thiệu dữ liệu để kiểm thử chiến lược; trang công khai không xác nhận rõ quyền **lưu bản thô dài hạn / khai thác thương mại / phân phối lại**. Vì vậy `HISTDATA_RAW_RETENTION_RIGHTS=NOT_VERIFIED`; **không** tải thêm hàng loạt hoặc đẩy ZIP, CSV, giá nguồn lên repo/Drive. Nguồn: https://www.histdata.com/about-us/ ; https://www.histdata.com/download-free-forex-data/ ; https://www.histdata.com/f-a-q/ .
- Kraken Spot REST công bố endpoint `GET /0/public/OHLC`, `interval=240` (H4 gốc theo **venue Kraken spot**) và `assetVersion=1` cho tên cặp hiển thị. **Dòng OHLC cuối luôn là nến chưa đóng**; API chỉ trả tối đa 720 nến gần nhất, không thể dùng `since` để lấy sâu hơn. Nguồn: https://docs.kraken.com/api/docs/rest-api/get-ohlc-data . Hướng dẫn Kraken yêu cầu xin phép trước cho một số trường hợp sử dụng dữ liệu công khai **thương mại, phi cá nhân**; `KRAKEN_COMMERCIAL_DATA_RIGHTS=PERMISSION_REQUIRED_OR_UNVERIFIED`. Nguồn: https://docs-legacy.kraken.com/api/docs/guides/global-intro/ . Phiên này **không truy xuất thành công payload Kraken thật**, không tăng số ô được xác minh.
- Bitstamp có native H4 `step=14400`, `exclude_current_candle=true`; trang API hướng dẫn bên sử dụng dữ liệu sàn cho mục đích thương mại liên hệ để ký giấy phép dữ liệu. Nguồn: https://www.bitstamp.net/api/ . 4 ô Bitstamp trước đó vẫn chỉ là source probe 8 nến đóng/ô, không phải kết quả giao dịch.
- OANDA v20 định nghĩa `H4` gốc, endpoint giá/candles theo tài khoản yêu cầu bearer token và account ID, có bid/ask khi được cấp quyền. Nguồn: https://developer.oanda.com/rest-live-v20/instrument-df/ ; https://developer.oanda.com/rest-live-v20/pricing-ep/ . Chưa có kết nối read-only được ủy quyền/entitlement/tài khoản phí; `BROKER_NATIVE_H4=DATA_UNAVAILABLE`.
- Biểu phí công khai Kraken thay đổi theo sản phẩm, maker/taker, khối lượng hoặc điều kiện tài khoản. Không thể suy ra phí **tài khoản AutoTrade** từ bảng tham khảo; `BROKER_COSTS_VERIFIED=0`. Nguồn: https://www.kraken.com/features/fee-schedule ; https://support.kraken.com/articles/201893638-how-trading-fees-work-on-kraken .

## 2. Phân loại và giới hạn nguồn
| Nguồn | Dạng H4 | Quan sát file/feed thật trong checkpoint này | Phí tài khoản chứng thực | Kết luận |
| --- | --- | --- | --- | --- |
| HistData EURUSD 08/2026 | M1 BID -> `DERIVED_H4_BID_ONLY` | Giữ nguyên 30.496 M1, 93 H4 đủ 240 phút, 35 block loại từ run trước | Không | `REAL_FILE_DERIVED_H4_INTEGRITY_ONLY` |
| Bitstamp BTCUSD/ETHUSD | `NATIVE_H4_BITSTAMP_SPOT` | Giữ nguyên source probe trước: 8 H4 đóng mỗi ô | Không | `SOURCE_PROBE_ONLY` |
| Kraken BTCUSD/ETHUSD | `NATIVE_H4_KRAKEN_SPOT` | 0 payload thật; parser **synthetic-only** | Không | `OFFLINE_PARSER_VALIDATED_SOURCE_NOT_OBSERVED` |
| OANDA fxPractice / broker | `NATIVE_H4_ACCOUNT_FEED` nếu có entitlement | 0 tài khoản đã xác minh | Không | `DATA_UNAVAILABLE` |

Không coi Kraken Spot là MT5 CFD/broker hay lấy dữ liệu lịch sử trùng giai đoạn làm holdout mới. 26 ô thiếu native H4 của R0 **không được chuyển thành PASS**. Coverage 56 ô, 19 ứng viên HistData derived và đúng 1 ô HistData đã quan sát thực giữ nguyên báo cáo trước.

## 3. Mã nguồn thực hiện, không phát sinh chi phí
- `src/data_loader/kraken_native_h4.py`: parser ngoại tuyến cho cặp BTC/USD và ETH/USD (`assetVersion=1`), kiểm tra envelope/cặp/cursor/kiểu Decimal/OHLC/VWAP, H4 UTC liên tiếp, chặn nến tương lai/gap/trùng timestamp, bỏ **vô điều kiện** nến cuối đang mở, SHA-256 raw. Tự gắn cờ quyền dữ liệu/phí/clock/forward chưa kiểm toán. Không có HTTP hoặc broker order API.
- `src/paper/r1_forward_readiness.py`: cổng ngoại tuyến kiểm tra event-time causal, cutoff `2026-09-30T00:00:00Z`, bid <= ask, quote <=30 giây từ close và tới decision; chặn nếu thiếu auth, phí, quyền dữ liệu hoặc kill-switch. Các flag do caller khai báo **không phải bằng chứng độc lập**; ngay cả trường hợp fixture hợp lệ chỉ xuất `TIMING_INTEGRITY_ONLY_AWAITING_INDEPENDENT_AUDIT`, `paper_fills_created=0`, `orders_sent=0`.
- Test: `tests/data_loader/test_kraken_native_h4.py` và `tests/paper/test_r1_forward_readiness.py`. Không chứa giá thị trường thật hoặc tài khoản/token.

## 4. Bằng chứng 3 vòng trên workspace cloud riêng, không phải máy Founder
Runner: `Python 3.13.5`, không clone được repo do DNS container; chỉ kiểm thử đúng **bốn file nguồn/test mới**, không được coi là toàn bộ regression suite repo. Sau khi ghi bằng GitHub connector, đối chiếu Git blob SHA của cả bốn file; local và GitHub **trùng tuyệt đối**:

- `src/data_loader/kraken_native_h4.py`: `0fb9d3242c15b25324403e9f88be3e4ceff92f39`
- `tests/data_loader/test_kraken_native_h4.py`: `9633f0f130078ef7014bf136a108a37ced51940e`
- `src/paper/r1_forward_readiness.py`: `bf0cd399ea15681d6a59bc8b2bac778fd9963f58`
- `tests/paper/test_r1_forward_readiness.py`: `7c35cd67eae012cc44dfce21b55b39dcda82db13`

Lệnh đã chạy, mỗi lệnh exit 0:
```bash
python -m unittest tests.data_loader.test_kraken_native_h4.Smoke tests.paper.test_r1_forward_readiness.Smoke -v
python -m unittest tests.data_loader.test_kraken_native_h4.Runtime tests.paper.test_r1_forward_readiness.Runtime -v
python -m unittest tests.data_loader.test_kraken_native_h4.Fault tests.paper.test_r1_forward_readiness.Fault -v
```
Kết quả: **Smoke 3/3; Runtime synthetic 4/4; Fault 21/21**. AST static check 2 module: không network/order imports hoặc calls được liệt kê. Đây là **synthetic validation của code**, KHÔNG phải runtime trên Kraken real response, không phải actual forward feed, không chứng thực lợi thế. Không dùng GitHub Actions, không reboot máy, không chạy ngầm.

## 5. Blocker, kinh nghiệm và cổng nghiên cứu
- **BLOCKED DATA RIGHTS:** chưa có giấy phép/kết luận quyền raw HistData và sử dụng thương mại dữ liệu Kraken/Bitstamp. Chỉ lưu metadata và code. Không chuyển tài liệu giới thiệu tải miễn phí thành giấy phép phân phối.
- **BLOCKED REAL SOURCE:** không có Kraken raw bytes quan sát được; không có broker-native H4 từ tài khoản được cấp quyền; không thể gọi test fixture là real feed.
- **BLOCKED COSTS:** thiếu phí/tier thực của đúng account, spread bid/ask contemporaneous, commission, swap/financing, contract multiplier, FX conversion và margin. Zero phí không được thay thế dữ liệu thiếu.
- **BLOCKED FORWARD:** trước cutoff, không có quote next-open được ghi nhận đương thời và nơi lưu được quyền; module mới kiểm tra tính nhân quả **khi có input hợp pháp**, không tự nhận là forward-paper engine hoàn chỉnh. Không DEMO-send/LIVE và không tạo lệnh paper giả.
- **BLOCKED DATABASE:** Supabase liệt kê hai project `cws-render-e2e` và `cws-render-beta`, không xác minh project AutoTrade; **không ghi sang render**. Drive thấy thư mục `CWS AI TRADE`, không lưu raw khi quyền chưa xác minh.
- **EDGE:** chưa có mẫu 90 ngày, 100 lệnh đóng, chi phí thực sau phí/stress, baseline, block bootstrap và outlier độc lập. Giữ `UNPROVEN`. Không tối ưu lại R0 55/20/ATR2.5 hay dùng lại historical OOS.

Kinh nghiệm: (1) native H4 của venue không suy ra tính tương đương MT5; (2) nến cuối Kraken là open bar, phải loại bất kể timestamp giả lập; (3) caller boolean/sha không thay được kiểm toán provider độc lập; (4) test synthetic PASS nhưng source và profitability vẫn UNPROVEN; (5) không khởi chạy job forward sớm hoặc tự gán quan sát giá hồi cứu.

**Tiếp tục sau checkpoint:** chỉ mở source capture thật khi có quyền, ingest forward đúng event-clock từ cutoff, ghép ledger hash-chain với quote snapshot đã kiểm toán, dùng risk preflight 0,25%/1% và bảo vệ kill-switch. Mọi đánh giá hiệu suất mới phải prereg nguồn/split và dùng quan sát độc lập. Không bật lịch ngầm tự động nếu chưa được yêu cầu.

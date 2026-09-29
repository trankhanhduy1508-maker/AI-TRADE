# CWS AutoTrade — R1 nguồn H4 và chặn rủi ro: checkpoint 2026-09-29

**Đây là bản bàn giao tiếp sau:** `research/CWS_AUTOTRADE_BLIND_R0_R1_HANDOFF_2026-09-29.md`.
**Nhánh duy nhất:** `codex/p0-covel-knowledge-audit`. **HEAD đã kiểm tra trước khi ghi:** `95350c7f1f67da347630c2b9f6059ccd3e6044ab`.
**Trạng thái độc lập cuối:** `UNPROVEN`, không có forward mới, không broker-verified costs, không có lệnh LIVE/DEMO-send hay khoản phí mới.

## Đọc trước, không đọc toàn repo
1. `research/CWS_AUTOTRADE_BLIND_R0_R1_HANDOFF_2026-09-29.md` — R0/R1 trước đó, R0 frozen.
2. `research/CWS_AUTOTRADE_R1_NATIVE_H4_SOURCE_FEASIBILITY_2026-09-29.md` — khả năng native H4 OANDA + giới hạn nguồn.
3. `src/data_loader/oanda_h4_adapter.py` và `tests/data_loader/test_oanda_h4_adapter.py`.
4. `src/paper/blind_r1_risk.py` và `tests/paper/test_blind_r1_risk.py`.
5. `.github/workflows/cws-r1-source-risk-qa-once.yml`; bằng chứng https://github.com/trankhanhduy1508-maker/AI-TRADE/actions/runs/36573015745

## Đã thực hiện trong phiên hiện tại
- HEAD ban đầu xác minh `1b54597685f3bfe3477dff52af581b2019344b45`. Không tạo nhánh, không sửa Main/Production, không chạm PC Founder.
- Rà soát nguồn tài liệu chính thống OANDA v20. `H4` có định nghĩa nến bốn giờ gốc, `D` có dailyAlignment. fxPractice đòi tài khoản và bearer token; OANDA nêu lịch sử base price group có thể khác live account pricing. Không có tài khoản/token/entitlement OANDA được xác thực ở phiên này; **26 ô H4 chưa bổ sung dữ liệu thực**.
- Tạo parser hoàn toàn ngoại tuyến `src/data_loader/oanda_h4_adapter.py`. Chỉ tạo URL GET **fxPractice** và xác thực bytes JSON đã được caller nhận hợp pháp; không cài HTTP client/token/POST/order. Bắt buộc M/B/A đồng bộ, native H4/D, complete flag, giờ NY, DST D, OHLC và bid<=mid<=ask, timestamp, SHA nguồn. Ghi rõ chưa kiểm toán nguồn/licence/chi phí broker. Không gọi API OANDA thật, không tải dữ liệu mới.
- Tạo `src/paper/blind_r1_risk.py`, pure function `risk_preflight` tính khối lượng **nghiên cứu giả lập** theo Decimal làm tròn xuống lot step. Cổng cố định 0.25% equity/position và 1% tổng stop-risk; bắt buộc snapshot fee, spread, 2 chiều adverse slippage, financing buffer, margin, multiplier, FX và quote <=30 giây. Từ chối sản phẩm nontradeable, short chưa chứng thực, sai SL, thiếu auth/kill-switch; mode khác `RESEARCH_PAPER_ONLY` bị chặn. Kết quả luôn `orders_sent=0`, `verified_real_world_inputs=False` bởi các audit flag do caller cung cấp **không** tự làm chứng thực venue. Chưa kết nối module với event-ledger hoặc tài khoản thật.
- Có tests synthetic hợp đồng API, DST, nguồn sai, timestamp tương lai, dữ liệu incomplete, chi phí/risk/margin, kill-switch và mode. Fixture không phải dữ liệu thị trường.
- **Lỗi thật:** workflow đầu tiên https://github.com/trankhanhduy1508-maker/AI-TRADE/actions/runs/36572916962 FAIL tại Smoke: fixture crossed ask.open = 1.1000 làm invalid ask OHLC trước khi chạm đến cross-spread. Sửa đúng một dòng fixture ask.open = 1.1901 để ask candle hợp lệ nhưng bid.open > ask.open; commit `407fd11ddbbfe10cd858664dfde2068ed1b3b322`.
- Rerun immutable tại commit `95350c7f1f67da347630c2b9f6059ccd3e6044ab`, workflow https://github.com/trankhanhduy1508-maker/AI-TRADE/actions/runs/36573015745 **SUCCESS**; job `109421431603`. 19 tests adapter + 19 tests risk = 38 mỗi vòng; Smoke 38/38, Runtime 38/38, Fault 38/38, tổng **114 lượt PASS trên fixture**; code compile/import audit PASS. Không fake PASS, không giấu thất bại ban đầu.
- Kiểm tra R0 immutable sau thay đổi: prereg blob `c24865edfc76f9f21614de1f35451143eb0f927b`; manifest blob `57c4075587ff9f97b27f8480ddffb1061f264fc4`; results blob `56647bef016efcd1e2eb2d8b03028cdc060652e6`; R0 simulator blob `304ef89ee0a93f9b8ddfa08e7817cf6e320bed39`. Không sửa code hay chạy lại historical OOS.

## Hiện chưa thể tuyên bố
- Không có 26 ô H4 nguồn mới, không có dữ liệu native OANDA truy xuất thực, không có giá/commission/swap thực từ broker.
- Risk module tính từ input giả định và audit flags chưa được kiểm chứng bên ngoài; không được nói đã quản lý được tiền/broker/portfolio thực.
- Không có forward paper trade thực, không có dữ liệu hoàn toàn mới sau mốc `2026-09-30T00:00:00Z` (mốc tương lai lúc làm checkpoint 2026-09-29).
- R0 cũ 30 ô exploratory (28 D1 + 2 H4 Bitstamp), 26 ô thiếu H4; tổng 307 lệnh đóng OOS trên nhiều thị trường, 0/30 đủ 30 lệnh/ô, 0/30 chi phí broker verified; hiệu quả độc lập `UNPROVEN`.
- Dữ liệu giá lịch sử gốc được giữ tạm 1 ngày trong artifact Actions, chưa chứng minh kho raw dài hạn được phép.
- OANDA v20 account mới, token cá nhân và quyền lưu data phải được xác nhận đúng nguồn. Không lấy token từ chat, không đưa token vào public repo.

## Thứ tự tiếp tục được phép và cổng cấm
1. Nếu có kết nối được ủy quyền với broker/OANDA practice: trước tiên kiểm tra **read-only** danh mục instrument thật, tính sẵn có H4/D, điều kiện tài khoản, quota, phí nguồn và điều khoản lưu trữ. Không tự yêu cầu user trả phí hoặc sử dụng máy Founder.
2. Khi chưa có nguồn đó, duy trì `DATA_UNAVAILABLE` cho 26 H4; không chuyển Yahoo/H1 aggregated thành OANDA/MT5 H4. Bitstamp crypto H4 hiện là dữ liệu spot lịch sử, không phải chứng thực CFD/MT5.
3. Tăng cường provenance bền vững và kế hoạch thu thập quote realtime đúng **next-bar-open**. Một giá mở cửa được đọc từ OHLC sau khi nến hoàn thành chỉ là hồi cứu, không phải giao dịch giấy triển khai theo thời gian thực.
4. Chỉ dữ liệu mới có `open_ts >= FORWARD_START_UTC` mới được tính là tín hiệu/lệnh forward; warm-up quá khứ không bao giờ được tính là lợi nhuận forward. Mọi bar phải `complete`, đúng phiên/zone, nguồn/bid-ask được kiểm toán và event clock có chứng cứ.
5. Kết nối paper module vào một ledger và cổng nguồn được kiểm toán, vẫn **không** kết nối order-send; fail closed nếu fee/multiplier/FX/margin/auth/kill-switch hoặc market-session không hợp lệ. Triple-check Smoke → Runtime → Fault, commit evidence cụ thể; không chấm lợi thế trước ngưỡng forward đã đăng ký.
6. R0 methodology, manifest, raw dataset identity và opened historical OOS **bất biến**; không re-optimize 55/20/2.5 hay dùng 17 positive-history cells để lựa chọn thị trường sau khi đã nhìn kết quả. Muốn nghiên cứu phương pháp mới phải prereg R2 với tập forward riêng hoàn toàn mới.

**Nguồn OANDA:** https://developer.oanda.com/rest-live-v20/instrument-df/ ; https://developer.oanda.com/rest-live-v20/introduction/ ; https://help.oanda.com/ca/en/faqs/rest-v20-api-troubleshooting-guide.htm .

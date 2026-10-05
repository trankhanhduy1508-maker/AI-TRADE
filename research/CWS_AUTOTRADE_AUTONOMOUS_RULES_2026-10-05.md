# CWS AutoTrade — kiến thức thành quy tắc, chạy không cần AI

## Goal Founder đã chốt
Bot tự giao dịch theo quy tắc đã được kiểm chứng, không phụ thuộc vào ChatGPT đang mở. AI hỗ trợ nghiên cứu/cải tiến; runtime đặt lệnh là code deterministic. Web/PWA là hướng chính hiện tại. Tự nghiên cứu và tự trade là hai tiến trình riêng.

## Đã triển khai
- Gói `knowledge/runtime/autonomous_rules_v1.json`: 12 nguyên tắc từ Masterbook V3 đã có; nguồn và heading có hash. Không tuyên bố đã đọc thêm toàn bộ sách.
- `src/research/knowledge_pipeline.py`: nạp gói, kiểm tra nguồn không thay đổi, chặn tự promote và broker-send, gọi lại bộ R2 walk-forward hiện có.
- `scripts/run_knowledge_research.py`: CSV + metadata có hash → chọn ứng viên bằng dữ liệu quá khứ → kiểm thử đoạn kế tiếp → cost stress → kết quả có version/hash, không gọi AI, không có broker orders.
- 5 nguyên tắc có mapping nghiên cứu: expectancy/drawdown, closed-bar/next-open, gap-aware stop, trailing exit không TP cố định, chronological WF/cost stress. 7 nguyên tắc còn lại được nạp để truy nguồn nhưng cần validation riêng; không giả vờ tất cả đã thành executable strategy.
- Source drift/manifest tự nâng thành DEMO_VERIFIED/enable broker bị từ chối.
- TF-013A active không bị thay bởi R2 lab.

## Cách chạy
`python3 scripts/run_knowledge_research.py --csv DATA.csv --metadata STUDY.json --as-of-utc UNIX_SECONDS --output RESULT.json`

CSV cần timestamp (UTC epoch giây), open, high, low, close. Metadata dùng đúng schema Study của R2: symbol, timeframe, source_kind, source_sha256, exposure, session, allow_short, assumed_round_trip_cost_price. Hash phải khớp file CSV. Chi phí chỉ MODELED_ONLY; nghiên cứu gross hoặc synthetic không trở thành broker-net profitability.

## Kết quả kiểm chứng
20 unit/integration test Python PASS: 16 existing WF + 4 knowledge pipeline. Kiểm thử sử dụng synthetic fixture, không phải lợi nhuận thị trường thật. Có deterministic replay, future-suffix isolation, cost stress, gap-aware stop, source tampering và promotion lock.

## Chưa hoàn thành
- Chưa chạy gói mới với dữ liệu broker-net thật; chưa chứng minh edge hoặc lợi nhuận dương.
- Chưa tích hợp pipeline mới vào lịch cloud; không tạo thêm cron trùng các cron nghiên cứu hiện có.
- Gói mới chưa được promotion vào production; không tự thay strategy sau từng lệnh thua.
- MT5 web login, broker execution bridge, risk approval và recovery còn các blocker trong checkpoint Web/MT5 cùng ngày.
- Forward paper còn 7 state hỏng chưa phục hồi từ evidence gốc. Không sử dụng chúng để phê duyệt strategy.
- Không gửi lệnh DEMO hoặc tiền thật trong hạng mục này.

## Tiêu chuẩn cuối cùng
Knowledge → deterministic rules → historical research → OOS/WF/cost stress → paper → broker DEMO + ticket/position readback → recovery → vận hành độc lập. Chỉ khi đủ bằng chứng mới gọi bot tự trade hoàn chỉnh. Không cam kết equity luôn tăng.

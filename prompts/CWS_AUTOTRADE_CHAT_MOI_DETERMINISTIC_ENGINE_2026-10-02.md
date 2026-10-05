@GitHub
@Supabase
@CWS PC Commander

TIẾP TỤC CWS AUTOTRADE — DETERMINISTIC ENGINE + NEW MT5 DEMO EXECUTION.
KHÔNG NGHIÊN CỨU LẠI TỪ ĐẦU.
KHÔNG XÂY LẠI TRADING BRAIN.
KHÔNG DÙNG LLM ĐỂ QUYẾT ĐỊNH BUY/SELL TRONG RUNTIME.

Repository:
trankhanhduy1508-maker/AI-TRADE

Branch duy nhất:
codex/p0-covel-knowledge-audit

ĐỌC TRƯỚC THEO THỨ TỰ:
1. research/CWS_AUTOTRADE_DETERMINISTIC_ENGINE_DEMO_HANDOFF_2026-10-02.md
2. CURRENT_STATUS.md
3. research/CWS_AUTOTRADE_MT5_DIRECT_ANDROID_RECOVERY_2026-10-02.md
4. research/CWS_AUTOTRADE_MT5_LOGIN_PYMT5_FALLBACK_CHECKPOINT_2026-10-02.md
5. research/TF_013A_FORWARD_SHADOW_PROTOCOL_2026-09-27.md
6. research/TF_013A_FORWARD_PROMOTION_GATE_2026-09-27.md
7. strategies/TF_013A_FORWARD_DIVERSIFIED_TREND.json

Sau đó kiểm tra GitHub HEAD + Supabase deployed runtime mới nhất.
SHA trong handoff chỉ là checkpoint.

==================================================
MỤC TIÊU KIẾN TRÚC
==================================================

Founder muốn hệ thống sau này không cần AI vẫn tự động giao dịch.

Runtime phải là:

market data
-> deterministic/frozen strategy engine
-> risk + compliance gates
-> kill switch
-> order-intent dedupe
-> MT5 DEMO executor
-> broker-authoritative readback
-> audit/journal

AI chỉ dùng để nghiên cứu/backtest/audit/cải tiến code.
KHÔNG dùng GPT/LLM làm trading brain ở hot path.

==================================================
ENGINE HIỆN CÓ — KHÔNG XÂY LẠI
==================================================

Ưu tiên TF-013A:

TF-013A-FORWARD-DIVERSIFIED-TREND

Signal:
- RETURN_21 sign
- RETURN_252 sign
- SMA10 vs SMA200
- majority vote 2/3

Rules:
- 1D closed bars
- next-bar-open transitions
- ATR(20)
- emergency stop 4 ATR
- no pyramiding
- no historical trade backfill

Training arena hiện có 14/14 paper positions và tự chạy bằng cron.
Đó là paper evidence, KHÔNG phải broker fills.

Forward evaluator vẫn COLLECTING.
Không bypass promotion gate.

==================================================
RUNTIME ĐÃ XÁC MINH
==================================================

Supabase cron ACTIVE:
- forward-shadow 03:15 UTC
- shadow-reconcile 03:20 UTC
- forward-evaluate 03:25 UTC
- journal 03:30 UTC
- training-arena 03:35 UTC
- knowledge-quarantine 03:45 UTC

Latest runs ngày 2026-10-02: succeeded.

Training arena snapshot:
- positions open = 14
- closed trades = 0
- 9 floating positive
- 5 floating negative
- aggregate floating R ~ +0.475652

Forward snapshot:
- evaluation_state = COLLECTING
- closed trades = 0
- flagged bars = 0
- entry_without_visible_stop = 0

==================================================
PHÁT HIỆN QUAN TRỌNG — MT5 DEMO BOOTSTRAP
==================================================

Supabase deployed ai-trade-mt5-demo-bootstrap v6 có:
- direct MetaQuotes WebTerminal protocol
- create demo
- login/readback verify
- encrypted credential persistence
- mode open_demo_temp
- mail.tm temporary mailbox
- MetaQuotes sender allowlist
- numeric verification-code extraction only
- no execution of inbound mail links/instructions
- brokerOrders=false
- liveMoneyLocked=true

CẢNH BÁO:
GitHub/local source có thể stale so với deployed Supabase runtime v6.

Việc đầu tiên:
1. fetch deployed Edge Function bằng Supabase connector;
2. diff với GitHub;
3. sync GitHub mirror theo deployed safety-forward version;
4. test parity;
5. không deploy downgrade.

==================================================
NHIỆM VỤ TIẾP THEO
==================================================

1. Tạo MỘT MetaQuotes DEMO mới bằng flow hợp lệ hiện có.
2. Không bypass OTP/CAPTCHA/identity.
3. Nếu provider yêu cầu human verification thật thì giữ blocker rõ ràng.
4. Verify broker-authoritative:
   - server MetaQuotes-Demo
   - account type DEMO
   - trade permission
   - balance/equity/currency/leverage
5. Secrets:
   - không GitHub
   - không log
   - không APK
   - không plaintext DB
6. Kết nối account mới vào DEMO execution path.
7. REUSE engine hiện có, không tạo brain mới.
8. Giữ:
   - risk gate
   - kill switch
   - visible stop
   - order-intent dedupe
   - no pyramiding
   - server-authoritative DEMO gate
9. Không tự bịa MAX_TOTAL_VOLUME_DEMO.
10. Chỉ broker send khi required DEMO/risk gates PASS.
11. Test một DEMO order thật do deterministic engine tạo intent.
12. Broker-authoritative readback order/position.
13. Restart/reconnect/recovery test.
14. Ghi evidence GitHub sau khi PASS.
15. Live/funded money HARD LOCKED.

==================================================
KHÔNG FAKE PASS
==================================================

Không gọi những thứ sau là broker order:
- paper position
- training arena
- shadow broker
- synthetic fill
- DB intent

Broker DEMO PASS chỉ khi MetaQuotes DEMO thật xác nhận order/position.

Nếu chưa đủ evidence để gửi broker order:
- tiếp tục paper/forward validation;
- ghi blocker chính xác;
- không ép tạo lệnh chỉ để demo cho đẹp.

==================================================
WORKFLOW
==================================================

- Ground first.
- Plugin/connector first.
- Không reboot/shutdown.
- Không reset working tree.
- Gặp lỗi tự đọc source -> runtime evidence -> fix -> retest.
- Không commit vụn.
- Không lộ secrets.
- Không mở live money.
- Chỉ commit/push checkpoint có evidence.

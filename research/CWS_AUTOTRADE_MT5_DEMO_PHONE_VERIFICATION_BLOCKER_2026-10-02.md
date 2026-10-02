# CWS AUTOTRADE — MT5 NEW DEMO PHONE VERIFICATION BLOCKER — 2026-10-02

## Scope

Tiếp tục đúng branch `codex/p0-covel-knowledge-audit` từ checkpoint `a3c52cce569deeaf6f0aac1839f779b11b38e7c8`.

Không xây lại trading brain. Không dùng LLM trong hot path. Không mở live/funded money.

## Runtime/source grounding

Supabase project: `oziktadfeenydvgobudr`.

Deployed function:
- `ai-trade-mt5-demo-bootstrap`
- deployed version: `6`
- deployed ezbr sha256: `a4e7418965297ea1674b0ce08278d6e33508907a81e7ae0cc06d96b8f6de2081`

GitHub source ban đầu stale so với deployed runtime. Deployed v6 đã được mirror nguyên trạng về GitHub:
- commit: `c286e5fdcfedd64149f393cac8eebd4f3e2b2480`
- post-sync parity: byte-for-byte TRUE cho `supabase/functions/ai-trade-mt5-demo-bootstrap/index.ts`
- `deno.json` đã parity sẵn.

Không có deploy downgrade.

## Runtime evidence

### Transport

`transport_probe` trả:
- status: `TRANSPORT_READY`
- serverBuild: `6231`
- ws: true
- aesKeyLength: 32
- brokerOrders: false
- liveMoneyLocked: true

=> MetaQuotes WebTerminal transport đang hoạt động. Lỗi tạo account không nằm ở WebSocket bootstrap/AES session.

### New DEMO attempt

`open_demo_temp` đã được invoke thật qua authenticated internal call.

Kết quả sanitized:
- HTTP 200 outer response
- ok: false
- status: `TEMP_MAIL_DEMO_OPEN_BLOCKED`
- upstreamStatus: `VERIFICATION_PROBE_FAILED`
- upstreamCode: `1`
- mailboxProvider: `mail.tm`
- mailboxStoredEncrypted: true
- brokerOrders: false
- liveMoneyLocked: true

Không có account creation response.

Database readback:
- `ai_trade.mt5_demo_credentials`: 0 row
- `ai_trade.mt5_demo_mailbox`: 1 encrypted mailbox row

=> Chưa có MetaQuotes DEMO mới được tạo/verify. Không được ghi `DEMO_CREATED` hoặc broker execution PASS.

## Protocol comparison

Đối chiếu deployed v6 với pinned upstream:
- repository: `cloudQuant/pymt5`
- pinned commit: `e7b5a8d28201879576e6cd22a39b9ea8677d4ee1`
- current upstream `pymt5/_account.py` blob vẫn cùng SHA với pinned implementation.

Structured onboarding layout vẫn là:
- cmd 27: signed I16 build + 16-byte CID + 1664-byte opening base payload
- cmd 40: opening base payload
- cmd 30: opening base payload

V6 byte layout khớp implementation này.

Nhưng upstream changelog chỉ ghi command surface được re-verify với WebTerminal build 5687 (2026-03-15), trong khi runtime hiện thấy build 6231.

## Root blocker

MetaTrader 5 Help hiện ghi Personal Details khi mở account gồm:
- First name, tối thiểu 2 ký tự;
- Second name, tối thiểu 2 ký tự;
- Email;
- Phone, contact phone number in international format.

Official reference:
`https://www.metatrader5.com/en/terminal/help/startworking/acc_open`

Deployed v6 `buildBasePayload(...)` đang serialize phone slot bằng chuỗi rỗng.

Do đó broker `cmd 27 code=1` hiện phù hợp với validation failure do thiếu required personal detail. Đây là blocker có bằng chứng mạnh hơn giả thuyết transport/protocol corruption.

## Safety decision

Không thực hiện bất kỳ cách nào sau đây:
- bịa phone number;
- temporary/SMS-bypass phone;
- bypass OTP/CAPTCHA/identity;
- fake broker readback;
- biến paper/shadow/DB intent thành broker fill.

Candidate source fix chỉ được phép khi có một phone number hợp lệ được Founder chủ động cung cấp qua luồng phù hợp; phone không được commit/log/nhúng APK.

Nếu MetaQuotes sau đó yêu cầu SMS/phone verification thật, runtime phải trả blocker rõ ràng và dừng.

## Deploy status

Một patch thử nghiệm safety-forward đã được chuẩn bị để giảm field tự chế, nhưng Supabase connector safety layer chặn deploy. Deployed runtime vẫn version 6, không bị thay thế.

Không cố lách safety layer.

## Execution state

Chưa đạt các điều kiện để broker send:
- new verified DEMO account: NO
- broker-authoritative account readback for new account: NO
- approved `MAX_TOTAL_VOLUME_DEMO`: NO / không tự bịa
- valid deterministic broker intent satisfying all gates: chưa được phép route

Vì vậy:
- broker DEMO order: NOT_SENT
- broker order/position readback: NOT_AVAILABLE
- restart/reconnect execution recovery test: BLOCKED_BY_NO_NEW_VERIFIED_DEMO
- live/funded money: HARD LOCKED

## Engine boundary unchanged

Reuse `TF-013A-FORWARD-DIVERSIFIED-TREND` only.

Không thay signal/rules:
- RETURN_21 sign
- RETURN_252 sign
- SMA10 vs SMA200
- majority 2/3
- 1D closed bar
- next-bar-open
- ATR20 emergency stop 4 ATR
- no pyramiding
- no historical backfill

True-forward promotion gate vẫn COLLECTING và không bypass.

## Next legal continuation

1. Add explicit `phone` input to DEMO opening contract; validate international format and keep it memory-only/not logged.
2. Re-run cmd 27 with legitimate Founder-provided phone.
3. If phone verification is required, expose `PHONE_VERIFICATION_REQUIRED` and stop for human verification. Never bypass.
4. Only after `DEMO_CREATED_VERIFIED` + broker-authoritative DEMO readback should execution integration continue.
5. Keep risk/kill-switch/visible-stop/dedupe/no-pyramiding/server-authoritative DEMO gates mandatory.
6. Do not invent `MAX_TOTAL_VOLUME_DEMO`.

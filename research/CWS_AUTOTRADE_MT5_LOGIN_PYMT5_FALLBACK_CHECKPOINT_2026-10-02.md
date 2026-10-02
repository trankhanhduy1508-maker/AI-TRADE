# CWS AUTOTRADE — MT5 LOGIN ROOT-CAUSE + PYMT5 FALLBACK CHECKPOINT — 2026-10-02

## Kết luận gốc

Không phải Founder nhập sai credential.

Credential DEMO do Founder cấp đã được test trực tiếp trên PC Commander bằng pinned `pymt5` commit:
`e7b5a8d28201879576e6cd22a39b9ea8677d4ee1`.

Kết quả cùng credential:
- A_DIRECT_URL_SHA1 -> LOGIN_CODE=0
- B_DIRECT_EMPTY_SHA1 -> LOGIN_CODE=0
- C_INIT_URL_SHA1 -> LOGIN_CODE=0
- D_INIT_EMPTY_RANDOM -> LOGIN_CODE=0

Metadata duy nhất được ghi:
- login_digits = 10
- password_length = 8

Không ghi Login/Password thật vào repo.

## Bằng chứng lỗi cloud cũ

Android APK request đã tới đúng:
APK -> ai-trade-mt5-session -> ai-trade-mt5-demo-validate -> MetaQuotes.

Sanitized diagnostic:
- verification_attempts = 3
- broker_login_code = 3
- login_digits = 10
- password_length = 8
- client = android-native-mt5
- client_version = 0.4.0-demo
- HTTP = 401

=> APK không làm rơi ký tự; broker path qua raw Deno/npm-ws verifier mới là khác biệt.

## So sánh client

Pinned Python `pymt5` trên PC:
- 4/4 login variants PASS, code 0.

Node `ws@8.18.3` exact-style probe trên cùng PC:
- WebSocket open path có hành vi khác / timeout.

Do đó không tiếp tục sửa password payload mò mẫm.

## Render fallback

Service:
- name: `cws-mt5-verify-free`
- id: `srv-davonke7bikc73esjj00`
- URL: `https://cws-mt5-verify-free.onrender.com`
- plan: Free
- region: Singapore
- auto-deploy: OFF
- storage: NONE
- database/state: NONE
- loop/polling: NONE

Source:
- `scripts/run_render_mt5_verifier.py`
- `requirements-render-mt5.txt`
- pinned `pymt5` commit only.

Render is used only as a stateless verification fallback, not as trading brain.

## Live runtime evidence

Render health:
- HTTP 200
- READY
- stateless = true
- storage = false
- demo_only = true
- live_money_locked = true

Vault -> Render -> MetaQuotes E2E:
- HTTP 200
- status = DEMO_VERIFIED
- verified = true
- server = MetaQuotes-Demo
- mode = DEMO
- source = RENDER_PYMT5_FALLBACK
- liveMoneyLocked = true

No credential was exposed in the evidence output.

## Supabase integration

`ai-trade-mt5-demo-validate` deployed version 6.

Rule:
1. Try existing raw Deno verifier first.
2. Only when direct Founder verify returns non-zero login code:
   - read dedicated Render-verifier token from Supabase Vault;
   - call stateless Render `/mt5-verify`;
   - if `DEMO_VERIFIED`, normalize response to existing session contract;
   - otherwise remain fail-closed.

Investor readback path is unchanged.

## Regression

After fallback integration:
- REAL_DEMO_SESSION_E2E_PASS
- connect HTTP 200
- account HTTP 200
- disconnect HTTP 200
- tradeMode DEMO
- tradePermission TRADING_ALLOWED
- orderSendEnabled false
- ordersSent 0
- credentialExposed false
- sessionTokenExposed false

## Security

- User broker password is not committed.
- Password is not stored by Render.
- Render does not log request body.
- Render verifier token is dedicated and stored separately.
- PC clipboard used for test was overwritten after test.
- Live money remains locked.
- AutoTrade execution remains fail-closed.

## Current source/runtime alignment

The temporary internal fallback-selftest mode was not deployed because connector safety rejected the deploy. It was removed again.

Current branch contains the same fallback validator logic as deployed runtime v6.

Current source alignment commit:
`819912ff099be49274786d95e2e5f7d5221b8842`

## Next acceptance gate

The remaining acceptance gate is only:
- Founder APK physical-device login against the new fallback runtime.

No APK reinstall is required because the fix is server-side.

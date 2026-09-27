# MT5 DEMO bootstrap worker

Cloud-only bootstrap for a MetaQuotes-Demo account using the public WebTerminal protocol through `pymt5`.

Safety invariants:
- DEMO only.
- No live/funded account creation.
- No order is sent by this worker.
- Password and investor password are never logged.
- Email verification is fail-closed.
- Phone verification is fail-closed.
- No CAPTCHA/OTP bypass.
- No fabricated identity.
- The worker verifies the resulting account through `get_account()` before declaring success.

Required environment variables:
- `MT5_FIRST_NAME`
- `MT5_SECOND_NAME`
- `MT5_EMAIL`
- `MT5_CLIENT_ID_HEX` (32 hex characters)

Optional:
- `MT5_EMAIL_CODE`
- `MT5_COUNTRY` (default VN)
- `MT5_DEMO_DEPOSIT` (default 100000 demo currency units)
- `MT5_DEMO_LEVERAGE` (default 100)
- `MT5_DEMO_GROUP`

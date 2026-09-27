# The5ers Bootcamp — Canonical Rules Snapshot 2026-09-27

Nguồn phải được re-check trước khi activation vì prop-firm rules có thể đổi.

Official references:
- https://the5ers.com/bootcamp/
- https://the5ers.com/faqs/how-does-the-bootcamp-program-work/
- https://the5ers.com/faqs/what-is-the-leverage-in-the-bootcamp-program/
- https://the5ers.com/faqs/can-i-use-an-ea-expert-advisor-can-i-set-a-stealth-mode-stop-loss/
- https://the5ers.com/faqs/prohibited-trading-practices/
- https://the5ers.com/terms-and-conditions/

## Re-check 2026-09-27

Official pages were re-checked on 2026-09-27 before any activation attempt.

Observed official-page update labels:
- English Terms & Conditions page: Last update – Aug. 3nd 2026.
- Bootcamp workflow FAQ: last update: September 6, 2026.
- EA FAQ: last update: July 22, 2026.
- Prohibited Trading Practices FAQ: last update: July 28, 2026.

The current Terms still require written notification and prior written approval before Automated Trading Software may be used. No written approval evidence has been verified for AI-TRADE. automation_approval_verified therefore remains false.

The Bootcamp FAQ confirms the three challenge phases are on demo accounts, evaluation time is unlimited, the 3% daily pause applies only to funded accounts, and inactivity beyond 30 consecutive days may close the account.

## Challenge phases

| Phase | Initial | Target | Max Loss | Target Balance | Absolute Floor |
|---|---:|---:|---:|---:|---:|
| 1 | $5,000 | 6% | 5% | $5,300 | $4,750 |
| 2 | $10,000 | 6% | 5% | $10,600 | $9,500 |
| 3 | $15,000 | 6% | 5% | $15,900 | $14,250 |

Challenge daily pause: none.

Time limit: unlimited.

Account inactivity: >30 consecutive days may close the account.

## Margin / leverage

Official FAQ currently lists:
- Forex: 1:30.
- Metals: 1:25.
- Indices: 1:25.
- Commodities: 1:1.5.
- Crypto: 1:0.60.

Execution must read broker symbol contract/margin; these values are rule context, not a substitute for broker metadata.

## Stop loss

Every automated trade must carry visible broker-side protective stop loss.

Stealth SL is prohibited.

## EA / automation

Current official FAQ allows owned EA subject to prohibited-practice restrictions.

Current official Terms re-checked 2026-09-27 additionally require:
- written notification;
- written approval before using Automated Trading Software.

Therefore AI-TRADE uses the stricter gate:
`AUTOMATION_APPROVAL_VERIFIED == true`
before any Bootcamp challenge order path may activate.

## Prohibited path

AI-TRADE Bootcamp mode must not implement:
- copy trades from other person's signals;
- tick scalping;
- latency arbitrage;
- reverse arbitrage;
- hedge arbitrage;
- HFT;
- emulators;
- third-party shared EA;
- stealth stop loss;
- anti-detection impersonation.

## Funded-stage separation

Bootcamp funded rules are NOT the same as challenge:
- funded max loss is shown as 4%;
- funded daily pause is 3%.

Do not silently carry challenge 5% rule into funded account.

Funded execution remains a different future gate.

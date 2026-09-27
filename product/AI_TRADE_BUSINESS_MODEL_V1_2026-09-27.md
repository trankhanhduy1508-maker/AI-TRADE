# CWS AI Trade — Business Model V1

Status: Founder idea -> structured product direction. Not a final legal or pricing approval.

## Product identity

CWS AI Trade is not pure copy-trading.

It is a hybrid:
- autonomous AI trading bot;
- explainable trading journal;
- paper/shadow learning arena;
- optional broker connectivity;
- optional performance-based pricing;
- partner-broker distribution.

The strategy engine must remain independent from billing and broker-referral economics.

## Revenue model

Potential revenue streams:
1. AI subscription / Pro tier.
2. AI Success Fee based on new net profit above a High-Water Mark.
3. Broker partner / IB / affiliate revenue where legally and contractually permitted.

Do not force all three fees on every customer.

Preferred product experiment:
- **Pro Fixed**: recurring subscription, 0% performance fee.
- **Pro Success**: low or zero fixed fee + performance fee.
- **Partner Broker Benefit**: partner revenue can partially subsidize AI fees or customer credits.

## Success fee principles

Founder starting idea: 10% of customer profit.

Recommended interpretation:
- do not charge per winning trade;
- use a continuous High-Water Mark;
- calculate only on new net profit above the prior HWM;
- prefer realized net P/L after broker costs;
- crystallize periodically, with monthly settlement as the current product hypothesis;
- if account recovers from a drawdown back to its old HWM, do not charge again for the recovered portion.

Example:
- start 1,000
- rise to 1,200 -> new profit base 200
- fall to 1,050
- recover to 1,200 -> no new success fee
- rise to 1,250 -> only 50 is new profit above HWM

## Free experience

Do not freeze the Founder’s first number (50 trades) as a permanent truth.

Current product hypothesis:
- generous initial free paper usage;
- continuing small recurring free quota so users can keep returning;
- free tier should be useful enough to build trust and product habit;
- quota should eventually be tested empirically, not chosen only by intuition.

Candidate experiment:
- first 100 paper trades free;
- then 20 paper trades/month;
- keep basic dashboard/chart/journal available.

This is a hypothesis to A/B test, not a final billing rule.

## Broker partnership model

CWS AI Trade may support:
- Connect Existing Broker; or
- Open With Partner Broker.

Never require a partner broker just to access the strategy.

If partner revenue is earned:
- keep it out of the strategy engine;
- strategy must never know IB/CPA/revenue-share rate;
- do not increase trade frequency to maximize broker revenue;
- disclose partner compensation clearly;
- consider sharing part of partner revenue with customers as AI credits or fee rebates.

Preferred architecture:
market data -> strategy -> risk -> execution
                           |
                           X no billing/referral input

trade result -> billing/partner accounting -> AI credit / revenue

## Trust model

CWS AI Trade should be unusually transparent for an automated bot.

Per position/trade expose:
- strategy id;
- symbol;
- direction;
- entry;
- current price;
- stop loss;
- take profit if applicable;
- lot/volume;
- floating P/L;
- realized P/L;
- risk used;
- reason for entry;
- reason for exit;
- chart context;
- post-trade lesson.

Do not market with unverifiable win-rate claims.
Do not guarantee returns.

## Product flywheel

Free users -> more usage -> more opt-in telemetry -> better research dataset ->
candidate strategies -> backtest -> walk-forward -> paper/shadow -> promotion gate ->
better product -> more users.

Critical rule:
production strategy must not self-modify directly from live user data.
All improvements must pass a separate research/promotion pipeline.

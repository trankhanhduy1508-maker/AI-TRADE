# CWS AutoTrade — R1 Native H4 source feasibility and provenance (2026-09-29)

**Scope:** source feasibility for the 26 H4 gaps identified by frozen R0. **This does not reopen R0 historical OOS, modify R0 strategy, make a new performance claim, or authorize any trade.** Checked against primary OANDA developer documentation and official Bitstamp public API behaviour. No OANDA account/token or OANDA historical data was available during this session.

## Native H4 candidate: OANDA v20 REST on fxPractice (not MT5)
- OANDA's primary definition explicitly lists `H4` as a native **4-hour candlestick with day alignment**, `D` as native daily, and candle fields `time`, `bid`, `ask`, `mid`, `volume`, `complete`. Documentation: https://developer.oanda.com/rest-live-v20/instrument-df/
- Authorized v20 practice endpoints, where eligible: `GET https://api-fxpractice.oanda.com/v3/instruments/{instrument}/candles?granularity=H4&price=MBA&count=5000&smooth=false`. The instrument must be looked up in **the user's actual practice account supported instruments**, not inferred from Yahoo symbols. OANDA documents 5,000 candles/page and price components M/B/A: https://developer.oanda.com/rest-live-v20/api-comparison/ ; https://github.com/oanda/v20-openapi/blob/master/yaml/separate/v20_instrument.yaml
- OANDA requires a v20 account and bearer API token. Availability differs by division; a free practice account is described but eligibility for this user/region and which 26 assets it exposes **have not been checked**. Documentation: https://developer.oanda.com/rest-live-v20/introduction/
- OANDA expressly warns that historical candles are base price-group data, while live account quotes can differ with the actual account's pricing group. Never promote H4 mid/bid/ask history to **verified actual execution costs**, nor claim OANDA CFD is MT5 symbol/venue. Primary support: https://help.oanda.com/ca/en/faqs/rest-v20-api-troubleshooting-guide.htm
- A bearer token may authorize more than reads. Never put token/account identifier into source code, Git history, logs, public Actions artifacts or chat. Code path in `src/data_loader/oanda_h4_adapter.py` is parser and **URL builder only**: no HTTP request, POST, trade/order endpoint, token handling or order-send. A separate authorized read-only executor would still need safe token handling and explicit user connection.
- Native OANDA provider timestamp/session is timezone-sensitive: `dailyAlignment=17`, `alignmentTimezone=America/New_York`, `weeklyAlignment=Friday` should be fixed and recorded. No future candle, smoothing or assumption that a 24-hour D1 is exactly 86,400 seconds during DST changes. A closed H4 bar spans 14,400 seconds while a weekend trading gap remains a genuine unavailable session interval.

## Coverage classification (frozen 28-market universe)
- 13 FX H4: **candidate** OANDA v20 practice account; each `EUR_USD` etc. requires actual instrument entitlement/availability check, actual native H4 retrieval and licence/retention verification.
- XAUUSD, XAGUSD H4: **candidate** OANDA METAL where that account supports instrument, not guaranteed.
- WTI, Brent, S&P 500, Nasdaq 100, Dow Jones H4: **candidate** OANDA CFD if present in the account's instrument listing. Product is distinct from Yahoo front-month futures or cash indexes, so brand-new study with separate instrument identity and split is required. Do not transfer R0 outcomes to new product.
- AAPL, MSFT, NVDA, AMZN, GOOGL, META H4: **NOT YET SOURCED**; an OANDA equity CFD if available would still be a different product with borrow, dividend adjustment and fee issues. Do not assume OANDA offers individual stock CFDs.
- BTCUSD/ETHUSD: existing R0 used Bitstamp native spot H4; this is *not* the gap. Bitstamp spot crypto is not identical to any broker CFD.

## Alternate no-new-cost research paths, not execution-equivalent
- An expressly registered research-only `H1_AGGREGATED_H4` study may be feasible from a legitimately obtainable H1 feed and documented exchange calendar. It requires *new* source/data preregistration because aggregate H4 is not source-native H4 and is not OANDA/MT5 H4 broker OHLC.
- Broker-terminal `copy_rates_range` requires an authorized running terminal and broker feed; user rules forbid running on Founder PC. No existing authorized, freely provisioned cloud MT5 terminal has been verified; status `NOT_CONFIGURED`.
- Free-access promotion cannot be claimed from advertising a free tier. Confirm zero marginal costs, account limits, instrument entitlement, licence and relevant spread/commission/swap before retrieving persistent data.

## Source gate for any new research
Before opening ANY new holdout: write new provider/account **nonsecret** identifiers, instrument type, request URL without bearer token, source interval and timestamp alignment, schema/version, count, source complete flags, missing-session calendar, raw-source and normalized SHA-256, bid/ask/mid conventions, data usage licence, chronology and frozen train/validation/holdout. Commit manifest first. R0 historical holdout is permanently exposed and never reclassified independent. If any source requirement fails, mark `DATA_UNAVAILABLE` or `PROXY_NONEXECUTABLE`, not green.

## Forward paper timing
A newly received *closed H4* candle cannot be treated as though its next OPEN was observed live unless a contemporaneous **new-bar quote event** was captured and independently timestamped. Batch historical candle open obtained after the bar closes is retrospective hypothetical execution, not forward paper. Future R1 orderless simulation must distinguish `HISTORICAL_OHLC_REPLAY` from `TIMESTAMPED_PAPER_OPEN` and quarantine both until source audit. Nothing in this feasibility note starts background collection.

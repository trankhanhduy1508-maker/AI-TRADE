# AI-TRADE Dashboard — Modular Architecture

## Founder intent

The dashboard is intentionally split into independent feature groups so one feature can be fixed or rolled back without reverting the whole monitor.

## Feature modules

| Group | Path | Responsibility | Safe rollback boundary |
|---|---|---|---|
| 01 Shell | `dashboard/index.html` | HTML shell + chart dependency | UI shell only |
| 02 Design tokens | `styles/tokens.css` | colors, radius, typography tokens | visual theme only |
| 03 Layout | `styles/layout.css` | responsive grids/sections | layout only |
| 04 Components | `styles/components.css` | cards, badges, tables, journal, chart styling | component styling only |
| 05 API | `js/api.js` | Supabase dashboard fetches | transport only |
| 06 Store | `js/store.js` | browser state | client state only |
| 07 Current Trade | `js/modules/current-trade.js` | live/open trade panel | current-trade UI only |
| 08 Progress | `js/modules/progress.js` | 50 trades / 120 days / 8 markets | progress UI only |
| 09 Pipeline | `js/modules/pipeline.js` | 03:15/03:20/03:25 cron cards | pipeline UI only |
| 10 Recent Trades | `js/modules/recent-trades.js` | latest forward trade list | history UI only |
| 11 Journal | `js/modules/journal.js` | post-trade learning notes | journal UI only |
| 12 Candlestick | `js/modules/candlestick.js` | H1 candle chart + EMA + Entry/SL/TP | chart only |
| 13 Performance | `js/modules/performance.js` | net R, expectancy, PF, DD | metrics UI only |
| 14 Safety | `js/modules/safety.js` | MT5 DEMO + The5ers/risk/live locks | safety UI only |
| 15 Orchestrator | `js/app.js` | load/render schedule | orchestration only |

## Data rule

The premium interface must never invent a trade.

- no current trade -> render an explicit empty state;
- no closed trades -> recent list is empty;
- no journal -> journal displays waiting state;
- chart may show real market candles even when there is no trade;
- mock/demo values from design images must never enter runtime data.

## Rollback rule

Prefer reverting the commit for the affected feature module only.

Examples:
- chart breaks -> revert Candlestick module commit;
- journal wording breaks -> revert Journal module commit;
- API schema changes -> revert API module + corresponding Edge Function commit;
- styling regression -> revert the specific CSS group.

Do not roll back `TF-013A`, forward journal, or safety gates merely to fix a UI defect.

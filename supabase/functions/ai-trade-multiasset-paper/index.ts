import postgres from "npm:postgres@3.4.9";

type Row = Record<string, any>;
type Direction = "UP" | "DOWN";
type AssetClass = "FOREX" | "METAL" | "CRYPTO" | "ENERGY" | "INDEX";
type CostMode = "RESEARCH_PROXY" | "GROSS_ONLY";

type Cost = {
  spread: number;
  commission: number;
  slippage: number;
  swapPerBar: number;
};

type Instrument = {
  key: string;
  label: string;
  assetClass: AssetClass;
  yahooSymbol: string;
  brokerAliases: string[];
  costMode: CostMode;
  cost: Cost;
};

type Bar = {
  timestamp: number;
  open: number;
  high: number;
  low: number;
  close: number;
};

type Position = {
  direction: Direction;
  entryBarTimestamp: number;
  entryPrice: number;
  stop: number;
  initialStop: number;
  holdingBars: number;
};

const ZERO_COST: Cost = {
  spread: 0,
  commission: 0,
  slippage: 0,
  swapPerBar: 0,
};

const UNIVERSE: Instrument[] = [
  {
    key: "EURUSD",
    label: "EUR/USD",
    assetClass: "FOREX",
    yahooSymbol: "EURUSD=X",
    brokerAliases: ["EURUSD"],
    costMode: "RESEARCH_PROXY",
    cost: { spread: 0.0002, commission: 0.00002, slippage: 0.00005, swapPerBar: 0.00001 },
  },
  {
    key: "GBPUSD",
    label: "GBP/USD",
    assetClass: "FOREX",
    yahooSymbol: "GBPUSD=X",
    brokerAliases: ["GBPUSD"],
    costMode: "RESEARCH_PROXY",
    cost: { spread: 0.0002, commission: 0.00002, slippage: 0.00005, swapPerBar: 0.00001 },
  },
  {
    key: "USDJPY",
    label: "USD/JPY",
    assetClass: "FOREX",
    yahooSymbol: "USDJPY=X",
    brokerAliases: ["USDJPY"],
    costMode: "RESEARCH_PROXY",
    cost: { spread: 0.02, commission: 0.002, slippage: 0.005, swapPerBar: 0.001 },
  },
  {
    key: "AUDUSD",
    label: "AUD/USD",
    assetClass: "FOREX",
    yahooSymbol: "AUDUSD=X",
    brokerAliases: ["AUDUSD"],
    costMode: "RESEARCH_PROXY",
    cost: { spread: 0.00025, commission: 0.000025, slippage: 0.00006, swapPerBar: 0.000012 },
  },
  {
    key: "USDCAD",
    label: "USD/CAD",
    assetClass: "FOREX",
    yahooSymbol: "CAD=X",
    brokerAliases: ["USDCAD"],
    costMode: "GROSS_ONLY",
    cost: ZERO_COST,
  },
  {
    key: "USDCHF",
    label: "USD/CHF",
    assetClass: "FOREX",
    yahooSymbol: "CHF=X",
    brokerAliases: ["USDCHF"],
    costMode: "GROSS_ONLY",
    cost: ZERO_COST,
  },
  {
    key: "NZDUSD",
    label: "NZD/USD",
    assetClass: "FOREX",
    yahooSymbol: "NZDUSD=X",
    brokerAliases: ["NZDUSD"],
    costMode: "GROSS_ONLY",
    cost: ZERO_COST,
  },
  {
    key: "XAUUSD",
    label: "Gold",
    assetClass: "METAL",
    yahooSymbol: "GC=F",
    brokerAliases: ["XAUUSD", "GOLD"],
    costMode: "RESEARCH_PROXY",
    cost: { spread: 0.5, commission: 0.1, slippage: 0.25, swapPerBar: 0.05 },
  },
  {
    key: "BTCUSD",
    label: "Bitcoin",
    assetClass: "CRYPTO",
    yahooSymbol: "BTC-USD",
    brokerAliases: ["BTCUSD", "BITCOIN"],
    costMode: "RESEARCH_PROXY",
    cost: { spread: 50, commission: 20, slippage: 25, swapPerBar: 0 },
  },
  {
    key: "USOIL",
    label: "WTI Oil",
    assetClass: "ENERGY",
    yahooSymbol: "CL=F",
    brokerAliases: ["USOIL", "WTI", "XTIUSD"],
    costMode: "RESEARCH_PROXY",
    cost: { spread: 0.05, commission: 0.02, slippage: 0.03, swapPerBar: 0.02 },
  },
  {
    key: "US30",
    label: "Dow Jones / US30",
    assetClass: "INDEX",
    yahooSymbol: "^DJI",
    brokerAliases: ["US30", "DJ30", "DJI", "DOW"],
    costMode: "GROSS_ONLY",
    cost: ZERO_COST,
  },
  {
    key: "NAS100",
    label: "Nasdaq 100",
    assetClass: "INDEX",
    yahooSymbol: "^NDX",
    brokerAliases: ["NAS100", "USTEC", "NDX", "NASDAQ"],
    costMode: "GROSS_ONLY",
    cost: ZERO_COST,
  },
  {
    key: "US500",
    label: "S&P 500",
    assetClass: "INDEX",
    yahooSymbol: "^GSPC",
    brokerAliases: ["US500", "SPX500", "SP500", "SPX"],
    costMode: "GROSS_ONLY",
    cost: ZERO_COST,
  },
];

const sql = postgres(Deno.env.get("SUPABASE_DB_URL")!, {
  prepare: false,
  max: 1,
  connect_timeout: 10,
  idle_timeout: 20,
});

const json = (body: unknown, status = 200) =>
  new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json; charset=utf-8" },
  });

async function authorized(req: Request) {
  const rows = await sql`select secret from ai_trade.cron_auth where id=1`;
  const expected = String(rows[0]?.secret ?? "");
  const supplied = req.headers.get("x-ai-trade-cron") ?? "";
  return Boolean(expected) && supplied === expected;
}

async function appendEvent(
  eventType: string,
  result: string,
  details: Row = {},
) {
  await sql`
    insert into ai_trade.events(event_type, result, details)
    values (${eventType}, ${result}, ${JSON.stringify(details)}::jsonb)
  `;
}

async function yahooBars(symbol: string): Promise<Bar[]> {
  const today = new Date();
  const period2 = Math.floor(
    Date.UTC(
      today.getUTCFullYear(),
      today.getUTCMonth(),
      today.getUTCDate(),
    ) / 1000,
  );
  const period1 = period2 - 400 * 86400;
  const url =
    "https://query1.finance.yahoo.com/v8/finance/chart/" +
    encodeURIComponent(symbol) +
    "?period1=" +
    period1 +
    "&period2=" +
    period2 +
    "&interval=1d&events=history&includeAdjustedClose=true";
  const response = await fetch(url, {
    headers: { "user-agent": "AI-TRADE-research/0.3" },
  });
  if (!response.ok) throw new Error("YAHOO_HTTP_" + response.status);
  const payload = await response.json();
  if (payload?.chart?.error) throw new Error("YAHOO_CHART_ERROR");
  const result = payload?.chart?.result?.[0];
  const timestamps: number[] = result?.timestamp ?? [];
  const quote = result?.indicators?.quote?.[0];
  if (!quote) throw new Error("YAHOO_NO_DATA");

  const bars: Bar[] = [];
  for (let i = 0; i < timestamps.length; i += 1) {
    const open = Number(quote.open?.[i]);
    const high = Number(quote.high?.[i]);
    const low = Number(quote.low?.[i]);
    const close = Number(quote.close?.[i]);
    if (
      timestamps[i] >= period2 ||
      !Number.isFinite(open) ||
      !Number.isFinite(high) ||
      !Number.isFinite(low) ||
      !Number.isFinite(close)
    ) continue;
    bars.push({ timestamp: timestamps[i], open, high, low, close });
  }
  bars.sort((a, b) => a.timestamp - b.timestamp);
  if (bars.length < 40) throw new Error("INSUFFICIENT_BARS");
  return bars;
}

async function loadState(instrument: Instrument) {
  const rows = await sql`
    select symbol, label, asset_class, yahoo_symbol, cost_mode,
           extract(epoch from last_processed)::bigint as last_processed_epoch,
           position
    from ai_trade.paper_state
    where symbol=${instrument.key}
  `;
  return rows[0] ?? null;
}

async function initialize(instrument: Instrument, latest: Bar) {
  await sql`
    insert into ai_trade.paper_state(
      symbol, label, asset_class, yahoo_symbol, cost_mode,
      last_processed, position, updated_at
    )
    values (
      ${instrument.key},
      ${instrument.label},
      ${instrument.assetClass},
      ${instrument.yahooSymbol},
      ${instrument.costMode},
      to_timestamp(${latest.timestamp}),
      null,
      now()
    )
    on conflict (symbol) do nothing
  `;
  await appendEvent("paper_warm", "WARMED", {
    symbol: instrument.key,
    yahooSymbol: instrument.yahooSymbol,
    costMode: instrument.costMode,
    detail: "Forward-only start; no historical trades backfilled",
  });
}

async function persistState(
  instrument: Instrument,
  lastProcessed: number,
  position: Position | null,
) {
  await sql`
    update ai_trade.paper_state
    set last_processed=to_timestamp(${lastProcessed}),
        position=${position ? JSON.stringify(position) : null}::jsonb,
        updated_at=now()
    where symbol=${instrument.key}
  `;
}

async function processInstrument(instrument: Instrument) {
  const bars = await yahooBars(instrument.yahooSymbol);
  const latest = bars[bars.length - 1];
  let state = await loadState(instrument);

  if (!state) {
    await initialize(instrument, latest);
    return {
      symbol: instrument.key,
      label: instrument.label,
      assetClass: instrument.assetClass,
      yahooSymbol: instrument.yahooSymbol,
      costMode: instrument.costMode,
      status: "WARMED",
      lastProcessed: latest.timestamp,
      position: null,
    };
  }

  const lastProcessed = Number(state.last_processed_epoch);
  if (!Number.isFinite(lastProcessed)) throw new Error("INVALID_CHECKPOINT");
  if (lastProcessed < bars[0].timestamp) {
    await appendEvent("paper_gap", "GAP_BLOCKED", {
      symbol: instrument.key,
      lastProcessed,
      firstAvailable: bars[0].timestamp,
    });
    return {
      symbol: instrument.key,
      status: "GAP_BLOCKED",
      lastProcessed,
    };
  }

  let position: Position | null = state.position
    ? {
        direction: String(state.position.direction) as Direction,
        entryBarTimestamp: Number(state.position.entryBarTimestamp),
        entryPrice: Number(state.position.entryPrice),
        stop: Number(state.position.stop),
        initialStop: Number(state.position.initialStop),
        holdingBars: Number(state.position.holdingBars ?? 0),
      }
    : null;

  const pendingIndexes = bars
    .map((bar, index) => ({ bar, index }))
    .filter((item) => item.bar.timestamp > lastProcessed)
    .map((item) => item.index);

  if (pendingIndexes.length === 0) {
    return {
      symbol: instrument.key,
      label: instrument.label,
      assetClass: instrument.assetClass,
      yahooSymbol: instrument.yahooSymbol,
      costMode: instrument.costMode,
      status: "NO_NEW_CLOSED_BAR",
      lastProcessed,
      position: position?.direction ?? null,
    };
  }

  let checkpoint = lastProcessed;
  let entries = 0;
  let exits = 0;

  for (const index of pendingIndexes) {
    const bar = bars[index];
    let exitedThisBar = false;

    if (position && index >= 20) {
      position.holdingBars += 1;
      const priorChannel = bars.slice(index - 20, index);
      if (position.direction === "UP") {
        position.stop = Math.max(
          position.stop,
          Math.min(...priorChannel.map((item) => item.low)),
        );
      } else {
        position.stop = Math.min(
          position.stop,
          Math.max(...priorChannel.map((item) => item.high)),
        );
      }

      const stopHit = position.direction === "UP"
        ? bar.low <= position.stop
        : bar.high >= position.stop;

      if (stopHit) {
        const exitPrice = position.direction === "UP"
          ? position.stop - instrument.cost.slippage
          : position.stop + instrument.cost.slippage;
        const executed = position.direction === "UP"
          ? exitPrice - position.entryPrice
          : position.entryPrice - exitPrice;
        const pnl =
          executed -
          instrument.cost.spread -
          instrument.cost.commission -
          instrument.cost.swapPerBar * position.holdingBars;
        const initialRisk = Math.abs(
          position.entryPrice - position.initialStop,
        );
        if (!(initialRisk > 0)) throw new Error("INVALID_INITIAL_RISK");
        const r = pnl / initialRisk;

        await sql`
          insert into ai_trade.paper_trades(
            symbol, direction, entry_ts, exit_ts, r, exit_reason, cost_mode
          )
          values (
            ${instrument.key},
            ${position.direction},
            to_timestamp(${position.entryBarTimestamp}),
            to_timestamp(${bar.timestamp}),
            ${r},
            'TRAILING_STOP',
            ${instrument.costMode}
          )
          on conflict (symbol, entry_ts, exit_ts) do nothing
        `;
        await appendEvent("paper_exit", "CLOSED", {
          symbol: instrument.key,
          direction: position.direction,
          r,
          costMode: instrument.costMode,
        });
        position = null;
        exits += 1;
        exitedThisBar = true;
      }
    }

    if (!position && !exitedThisBar && index > 20 && index > 5) {
      const reference = bars[index - 21].close;
      if (reference !== bar.close) {
        const direction: Direction = bar.close > reference ? "UP" : "DOWN";
        const prior = bars.slice(index - 5, index);
        const stop = direction === "UP"
          ? Math.min(...prior.map((item) => item.low))
          : Math.max(...prior.map((item) => item.high));
        const validStop = direction === "UP" ? stop < bar.close : stop > bar.close;
        if (validStop) {
          const entryPrice = direction === "UP"
            ? bar.close + instrument.cost.slippage
            : bar.close - instrument.cost.slippage;
          position = {
            direction,
            entryBarTimestamp: bar.timestamp,
            entryPrice,
            stop,
            initialStop: stop,
            holdingBars: 0,
          };
          await appendEvent("paper_entry", "OPEN", {
            symbol: instrument.key,
            direction,
            entryPrice,
            stop,
            costMode: instrument.costMode,
          });
          entries += 1;
        }
      }
    }

    checkpoint = bar.timestamp;
  }

  await persistState(instrument, checkpoint, position);
  return {
    symbol: instrument.key,
    label: instrument.label,
    assetClass: instrument.assetClass,
    yahooSymbol: instrument.yahooSymbol,
    brokerAliases: instrument.brokerAliases,
    costMode: instrument.costMode,
    status: "PROCESSED",
    processedBars: pendingIndexes.length,
    entries,
    exits,
    lastProcessed: checkpoint,
    position: position?.direction ?? null,
  };
}

async function metrics() {
  const rows = await sql`
    select
      s.symbol,
      s.label,
      s.asset_class,
      s.yahoo_symbol,
      s.cost_mode,
      s.last_processed,
      s.position,
      count(t.id)::int as trades,
      coalesce(sum(t.r), 0)::float8 as net_r,
      coalesce(avg(t.r), 0)::float8 as expectancy_r,
      coalesce(min(t.r), 0)::float8 as worst_trade_r
    from ai_trade.paper_state s
    left join ai_trade.paper_trades t on t.symbol=s.symbol
    group by s.symbol, s.label, s.asset_class, s.yahoo_symbol,
             s.cost_mode, s.last_processed, s.position
    order by s.asset_class, s.symbol
  `;
  return rows;
}

Deno.serve(async (req) => {
  try {
    if (!(await authorized(req))) {
      return json({ ok: false, status: "UNAUTHORIZED" }, 401);
    }

    const results = [];
    for (const instrument of UNIVERSE) {
      try {
        results.push(await processInstrument(instrument));
      } catch (error) {
        const message = error instanceof Error ? error.message : String(error);
        results.push({
          symbol: instrument.key,
          label: instrument.label,
          assetClass: instrument.assetClass,
          yahooSymbol: instrument.yahooSymbol,
          costMode: instrument.costMode,
          status: "ERROR",
          error: message,
        });
        await appendEvent("paper_error", "ERROR", {
          symbol: instrument.key,
          message,
        });
      }
      await new Promise((resolve) => setTimeout(resolve, 75));
    }

    return json({
      ok: true,
      mode: "PAPER_ONLY",
      brokerOrders: false,
      pyramiding: false,
      universeSize: UNIVERSE.length,
      universe: UNIVERSE.map((item) => ({
        key: item.key,
        label: item.label,
        assetClass: item.assetClass,
        yahooSymbol: item.yahooSymbol,
        brokerAliases: item.brokerAliases,
        costMode: item.costMode,
      })),
      results,
      metrics: await metrics(),
    });
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    return json({ ok: false, status: "ERROR", message }, 500);
  }
});

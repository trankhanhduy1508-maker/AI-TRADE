import postgres from "npm:postgres@3.4.9";

type Row = Record<string, any>;

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

async function appendEvent(
  eventType: string,
  result: string,
  details: Row = {},
  clientOrderId?: string,
) {
  await sql`
    insert into ai_trade.events(event_type, result, client_order_id, details)
    values (
      ${eventType},
      ${result},
      ${clientOrderId ?? null},
      ${JSON.stringify(details)}::jsonb
    )
  `;
}

async function sha256(value: string) {
  const digest = await crypto.subtle.digest(
    "SHA-256",
    new TextEncoder().encode(value),
  );
  return [...new Uint8Array(digest)]
    .map((x) => x.toString(16).padStart(2, "0"))
    .join("");
}

function num(value: unknown, fallback = 0) {
  const n = Number(value);
  return Number.isFinite(n) ? n : fallback;
}

function timeframeMs(value: string) {
  const map: Record<string, number> = {
    "1m": 60_000, "2m": 120_000, "3m": 180_000, "4m": 240_000,
    "5m": 300_000, "6m": 360_000, "10m": 600_000, "12m": 720_000,
    "15m": 900_000, "20m": 1_200_000, "30m": 1_800_000,
    "1h": 3_600_000, "2h": 7_200_000, "3h": 10_800_000,
    "4h": 14_400_000, "6h": 21_600_000, "8h": 28_800_000,
    "12h": 43_200_000, "1d": 86_400_000, "1w": 604_800_000,
  };
  if (!map[value]) throw new Error("UNSUPPORTED_TIMEFRAME");
  return map[value];
}

function normalizePartial(volume: number, fraction: number, spec: Row) {
  const min = num(spec.minVolume);
  const step = num(spec.volumeStep);
  if (!(fraction > 0 && fraction < 1) || min <= 0 || step <= 0) {
    throw new Error("PARTIAL_VOLUME_NOT_REPRESENTABLE");
  }
  let candidate = Math.floor((volume * fraction + 1e-12) / step) * step;
  if (candidate < min) candidate = min;
  if (volume - candidate > 1e-12 && volume - candidate < min) {
    candidate = volume - min;
  }
  const ratio = candidate / step;
  if (
    candidate <= 0 ||
    candidate >= volume ||
    candidate < min ||
    Math.abs(ratio - Math.round(ratio)) > 1e-8
  ) throw new Error("PARTIAL_VOLUME_NOT_REPRESENTABLE");
  return Number(candidate.toFixed(8));
}

function tradeDone(result: Row) {
  return result?.numericCode === 10009 ||
    result?.numericCode === 10010 ||
    result?.stringCode === "TRADE_RETCODE_DONE" ||
    result?.stringCode === "TRADE_RETCODE_DONE_PARTIAL";
}

async function reserveIntent(clientId: string) {
  const inserted = await sql`
    insert into ai_trade.order_intents(client_order_id, status)
    values (${clientId}, 'SUBMITTING')
    on conflict (client_order_id) do nothing
    returning client_order_id
  `;
  return inserted.length === 1;
}

async function finishIntent(clientId: string, result: Row) {
  const status = tradeDone(result)
    ? (result?.numericCode === 10010 ||
        result?.stringCode === "TRADE_RETCODE_DONE_PARTIAL" ? "PARTIAL" : "FILLED")
    : "REJECTED";
  const brokerId = String(result?.positionId ?? result?.orderId ?? "") || null;
  await sql`
    update ai_trade.order_intents
    set status=${status},
        broker_order_id=${brokerId},
        retcode=${result?.numericCode ?? null},
        updated_at=now()
    where client_order_id=${clientId}
  `;
  return status;
}

async function tradeIntent(
  clientId: string,
  fn: () => Promise<Row>,
) {
  if (!(await reserveIntent(clientId))) {
    return { status: "DUPLICATE_SUPPRESSED" };
  }
  try {
    const result = await fn();
    const status = await finishIntent(clientId, result);
    return { status, result };
  } catch (error) {
    await sql`
      update ai_trade.order_intents
      set status='AMBIGUOUS', updated_at=now()
      where client_order_id=${clientId}
    `;
    throw error;
  }
}

async function deterministicId(parts: string[]) {
  return "AI" + (await sha256(parts.join("|"))).slice(0, 20);
}

Deno.serve(async (req) => {
  try {
    const authRows = await sql`
      select secret from ai_trade.cron_auth where id=1
    `;
    const expectedSecret = String(authRows[0]?.secret ?? "");
    const suppliedSecret = req.headers.get("x-ai-trade-cron") ?? "";
    if (!expectedSecret || suppliedSecret !== expectedSecret) {
      return json({ ok: false, status: "UNAUTHORIZED" }, 401);
    }

    const configRows = await sql`
      select * from ai_trade.runtime_config where id=1
    `;
    const config = configRows[0];
    if (!config) {
      await appendEvent("tick", "CONFIG_ERROR");
      return json({ ok: false, status: "CONFIG_ERROR" }, 500);
    }

    if (!config.enabled) {
      await appendEvent("tick", "DISABLED", { symbol: config.symbol });
      return json({ ok: true, status: "DISABLED" });
    }

    const token = Deno.env.get("METAAPI_TOKEN")?.trim() ?? "";
    const accountId = Deno.env.get("METAAPI_ACCOUNT_ID")?.trim() ?? "";
    if (!token || !accountId) {
      const missing = [
        ...(token ? [] : ["METAAPI_TOKEN"]),
        ...(accountId ? [] : ["METAAPI_ACCOUNT_ID"]),
      ];
      await appendEvent("tick", "CONFIG_BLOCKED", { missing });
      return json({ ok: false, status: "CONFIG_BLOCKED", missing }, 503);
    }

    const module = await import("npm:metaapi.cloud-sdk@29.3.3/esm-node");
    const MetaApi = module.default;
    const api = new MetaApi(token);
    const account = await api.metatraderAccountApi.getAccount(accountId);

    if (String(account.platform).toLowerCase() !== "mt5") {
      throw new Error("MT5_REQUIRED");
    }
    if (!String(account.server ?? "").toLowerCase().includes("demo")) {
      throw new Error("DEMO_SERVER_REQUIRED");
    }
    if (String(account.state).toUpperCase() !== "DEPLOYED") await account.deploy();
    await account.waitConnected();

    const connection = account.getRPCConnection();
    await connection.connect();
    await connection.waitSynchronized();

    const symbol = String(config.symbol);
    const timeframe = String(config.timeframe);
    await connection.subscribeToMarketData(symbol);

    const startOfDay = new Date();
    startOfDay.setUTCHours(0, 0, 0, 0);

    const [positionsAll, spec, price, deals, candlesRaw] = await Promise.all([
      connection.getPositions(),
      connection.getSymbolSpecification(symbol),
      connection.getSymbolPrice(symbol),
      connection.getDealsByTimeRange(startOfDay, new Date()),
      account.getHistoricalCandles(
        symbol,
        timeframe,
        undefined,
        Math.min(
          1000,
          Math.max(
            80,
            Number(config.lookback_bars) +
              Number(config.trailing_lookback) +
              Number(config.stop_lookback_bars) +
              10,
          ),
        ),
      ),
    ]);

    if (!spec || !price || !candlesRaw?.length) {
      throw new Error("MARKET_DATA_UNAVAILABLE");
    }

    const now = Date.now();
    const barMs = timeframeMs(timeframe);
    const candles = candlesRaw
      .filter((c: Row) => new Date(c.time).getTime() + barMs <= now)
      .sort((a: Row, b: Row) =>
        new Date(a.time).getTime() - new Date(b.time).getTime()
      );

    const minimumBars = Math.max(
      Number(config.lookback_bars),
      Number(config.stop_lookback_bars),
      Number(config.trailing_lookback),
    ) + 2;
    if (candles.length < minimumBars) throw new Error("INSUFFICIENT_CLOSED_BARS");

    const bid = num(price.bid);
    const ask = num(price.ask);
    const point = num(spec.point);
    if (bid <= 0 || ask <= 0 || ask < bid || point <= 0) {
      throw new Error("INVALID_QUOTE");
    }
    const spreadPoints = (ask - bid) / point;
    if (spreadPoints > num(config.max_spread_points)) {
      await appendEvent("tick", "SPREAD_BLOCKED", { spreadPoints });
      return json({ ok: true, status: "SPREAD_BLOCKED", spreadPoints });
    }

    const dailyPnl = (deals ?? [])
      .filter((d: Row) => Number(d.magic ?? 0) === Number(config.magic))
      .reduce(
        (sum: number, d: Row) =>
          sum + num(d.profit) + num(d.commission) + num(d.swap) + num(d.fee),
        0,
      );
    if (dailyPnl <= -num(config.max_daily_loss_demo)) {
      await appendEvent("tick", "DAILY_LOSS_BLOCKED", { dailyPnl });
      return json({ ok: true, status: "DAILY_LOSS_BLOCKED", dailyPnl });
    }

    const ownPositions = (positionsAll ?? []).filter((p: Row) =>
      String(p.symbol) === symbol &&
      Number(p.magic ?? 0) === Number(config.magic)
    );
    const openIds = ownPositions.map((p: Row) => String(p.id));

    const localOpen = await sql`
      select position_id
      from ai_trade.managed_positions
      where strategy_id=${String(config.strategy_id)} and status='OPEN'
    `;
    for (const row of localOpen) {
      if (!openIds.includes(String(row.position_id))) {
        await sql`
          update ai_trade.managed_positions
          set status='CLOSED', updated_at=now()
          where position_id=${String(row.position_id)}
        `;
      }
    }
    for (const p of ownPositions) {
      await sql`
        insert into ai_trade.managed_positions(
          position_id, strategy_id, last_stop, status
        )
        values (
          ${String(p.id)},
          ${String(config.strategy_id)},
          ${p.stopLoss ?? null},
          'OPEN'
        )
        on conflict (position_id) do nothing
      `;
    }

    const current = candles[candles.length - 1];
    const barStamp = new Date(current.time).toISOString();

    if (ownPositions.length === 0) {
      const reference =
        candles[candles.length - 1 - Number(config.lookback_bars)];
      if (num(current.close) === num(reference.close)) {
        return json({ ok: true, status: "NO_SIGNAL" });
      }

      const direction =
        num(current.close) > num(reference.close) ? "UP" : "DOWN";
      const prior = candles.slice(
        candles.length - 1 - Number(config.stop_lookback_bars),
        candles.length - 1,
      );
      const stop = direction === "UP"
        ? Math.min(...prior.map((b: Row) => num(b.low)))
        : Math.max(...prior.map((b: Row) => num(b.high)));
      const entry = direction === "UP" ? ask : bid;

      if (
        (direction === "UP" && stop >= entry) ||
        (direction === "DOWN" && stop <= entry)
      ) throw new Error("INVALID_PROTECTIVE_STOP");

      let target: number | undefined;
      if (config.exit_mode !== "TRAILING_ONLY") {
        const risk = Math.abs(entry - stop);
        target = direction === "UP"
          ? entry + risk * num(config.reward_risk)
          : entry - risk * num(config.reward_risk);
      }

      const clientId = await deterministicId([
        String(config.strategy_id), symbol, "ENTRY", barStamp, direction,
      ]);

      if (!config.demo_send_enabled) {
        await appendEvent(
          "entry",
          "MONITOR_ONLY",
          { direction, entry, stop, target },
          clientId,
        );
        return json({
          ok: true, status: "MONITOR_ONLY", direction, entry, stop, target,
        });
      }

      const volume = num(config.demo_volume);
      if (volume <= 0 || volume > 0.01) throw new Error("DEMO_VOLUME_CAP");
      if (
        spreadPoints > num(config.max_spread_points) ||
        dailyPnl <= -num(config.max_daily_loss_demo)
      ) throw new Error("RISK_GATE_BLOCKED");

      const options = {
        comment: "AI-TRADE DEMO",
        clientId,
        magic: Number(config.magic),
      };
      const sent = await tradeIntent(
        clientId,
        () =>
          direction === "UP"
            ? connection.createMarketBuyOrder(
              symbol, volume, stop, target, options,
            )
            : connection.createMarketSellOrder(
              symbol, volume, stop, target, options,
            ),
      );
      await appendEvent(
        "entry",
        sent.status,
        { direction, entry, stop, target },
        clientId,
      );
      return json({ ok: true, status: sent.status, clientId });
    }

    if (ownPositions.length > 1) {
      await appendEvent(
        "manage",
        "MULTIPLE_OWN_POSITIONS",
        { count: ownPositions.length },
      );
      return json({ ok: false, status: "MULTIPLE_OWN_POSITIONS" }, 409);
    }

    const position = ownPositions[0];
    const positionId = String(position.id);
    const stateRows = await sql`
      select *
      from ai_trade.managed_positions
      where position_id=${positionId}
    `;
    const state = stateRows[0] ?? {};
    const isLong =
      String(position.type).toUpperCase() === "POSITION_TYPE_BUY";
    const stopLoss = num(position.stopLoss, 0);
    const takeProfit = num(position.takeProfit, 0);
    const targetHit = takeProfit > 0 &&
      (isLong
        ? num(current.high) >= takeProfit
        : num(current.low) <= takeProfit);

    if (
      targetHit &&
      config.exit_mode === "PARTIAL_THEN_TRAIL" &&
      !state.partial_done
    ) {
      const partialId = await deterministicId([
        String(config.strategy_id), symbol, "PARTIAL", barStamp, positionId,
      ]);
      let partialVolume: number | null = null;
      try {
        partialVolume = normalizePartial(num(position.volume), 0.5, spec);
      } catch {
        partialVolume = null;
      }

      if (partialVolume === null) {
        const fallbackId = await deterministicId([
          String(config.strategy_id),
          symbol,
          "PARTIAL_FALLBACK_TRAIL",
          barStamp,
          positionId,
        ]);
        if (!config.demo_send_enabled) {
          return json({
            ok: true,
            status: "MONITOR_ONLY",
            mode: "TRAILING_FALLBACK",
          });
        }
        if (stopLoss <= 0) throw new Error("PROTECTIVE_STOP_MISSING");
        const modified = await tradeIntent(
          fallbackId,
          () => connection.modifyPosition(positionId, stopLoss, 0),
        );
        if (modified.status === "FILLED" || modified.status === "PARTIAL") {
          await sql`
            update ai_trade.managed_positions
            set partial_done=true, updated_at=now()
            where position_id=${positionId}
          `;
        }
        await appendEvent(
          "partial_fallback",
          modified.status,
          {},
          fallbackId,
        );
        return json({
          ok: true,
          status: modified.status,
          mode: "TRAILING_FALLBACK",
        });
      }

      if (!config.demo_send_enabled) {
        return json({
          ok: true,
          status: "MONITOR_ONLY",
          action: "PARTIAL_CLOSE",
          partialVolume,
        });
      }

      const partial = await tradeIntent(
        partialId,
        () => connection.closePositionPartially(positionId, partialVolume!),
      );
      if (partial.status === "FILLED" || partial.status === "PARTIAL") {
        await sql`
          update ai_trade.managed_positions
          set partial_done=true, updated_at=now()
          where position_id=${positionId}
        `;
        const dropId = await deterministicId([
          String(config.strategy_id), symbol, "DROP_TP", barStamp, positionId,
        ]);
        await tradeIntent(
          dropId,
          () => connection.modifyPosition(positionId, stopLoss, 0),
        );
      }
      await appendEvent(
        "partial_close",
        partial.status,
        { partialVolume },
        partialId,
      );
      return json({
        ok: true,
        status: partial.status,
        action: "PARTIAL_CLOSE",
      });
    }

    if (
      config.exit_mode === "TRAILING_ONLY" ||
      config.exit_mode === "PARTIAL_THEN_TRAIL"
    ) {
      const lookback = Number(config.trailing_lookback);
      const trailBars = candles.slice(
        candles.length - 1 - lookback,
        candles.length - 1,
      );
      const candidate = isLong
        ? Math.min(...trailBars.map((b: Row) => num(b.low)))
        : Math.max(...trailBars.map((b: Row) => num(b.high)));
      const improves =
        stopLoss <= 0 || (isLong ? candidate > stopLoss : candidate < stopLoss);
      const marketSafe = isLong ? candidate < bid : candidate > ask;

      if (improves && marketSafe) {
        const trailId = await deterministicId([
          String(config.strategy_id), symbol, "TRAIL", barStamp, positionId,
        ]);
        if (!config.demo_send_enabled) {
          return json({
            ok: true,
            status: "MONITOR_ONLY",
            action: "TRAIL",
            candidate,
          });
        }
        const modified = await tradeIntent(
          trailId,
          () =>
            connection.modifyPosition(
              positionId,
              candidate,
              takeProfit > 0 ? takeProfit : 0,
            ),
        );
        if (modified.status === "FILLED" || modified.status === "PARTIAL") {
          await sql`
            update ai_trade.managed_positions
            set last_stop=${candidate}, updated_at=now()
            where position_id=${positionId}
          `;
        }
        await appendEvent(
          "trail_stop",
          modified.status,
          { candidate },
          trailId,
        );
        return json({
          ok: true,
          status: modified.status,
          action: "TRAIL",
        });
      }
    }

    return json({ ok: true, status: "HOLD" });
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    try {
      await appendEvent("tick", "ERROR", { message });
    } catch {
      // If DB itself is unavailable, preserve the original execution error.
    }
    return json({ ok: false, status: "ERROR", message }, 500);
  }
});

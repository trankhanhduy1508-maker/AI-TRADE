import { createClient } from "npm:@supabase/supabase-js@2.117.2";

type Row = Record<string, any>;

const json = (body: unknown, status = 200) =>
  new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json; charset=utf-8" },
  });

function adminClient() {
  const url = Deno.env.get("SUPABASE_URL");
  const modern = JSON.parse(Deno.env.get("SUPABASE_SECRET_KEYS") ?? "{}");
  const key = modern.default ?? Deno.env.get("SUPABASE_SERVICE_ROLE_KEY");
  if (!url || !key) throw new Error("SUPABASE_ADMIN_CONFIG_MISSING");
  return createClient(url, key, {
    auth: { persistSession: false, autoRefreshToken: false },
  });
}

async function appendEvent(
  db: ReturnType<typeof adminClient>,
  eventType: string,
  result: string,
  details: Row = {},
  clientOrderId?: string,
) {
  await db.schema("ai_trade").from("events").insert({
    event_type: eventType,
    result,
    client_order_id: clientOrderId ?? null,
    details,
  });
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

async function reserveIntent(
  db: ReturnType<typeof adminClient>,
  clientId: string,
) {
  const { data } = await db.schema("ai_trade").from("order_intents")
    .select("status,broker_order_id,retcode")
    .eq("client_order_id", clientId)
    .maybeSingle();
  if (data) return false;
  const { error } = await db.schema("ai_trade").from("order_intents").insert({
    client_order_id: clientId,
    status: "SUBMITTING",
  });
  if (error) {
    if (String(error.code) === "23505") return false;
    throw error;
  }
  return true;
}

async function finishIntent(
  db: ReturnType<typeof adminClient>,
  clientId: string,
  result: Row,
) {
  const status = tradeDone(result)
    ? (result?.numericCode === 10010 ||
        result?.stringCode === "TRADE_RETCODE_DONE_PARTIAL" ? "PARTIAL" : "FILLED")
    : "REJECTED";
  await db.schema("ai_trade").from("order_intents").update({
    status,
    broker_order_id: String(result?.positionId ?? result?.orderId ?? "") || null,
    retcode: result?.numericCode ?? null,
    updated_at: new Date().toISOString(),
  }).eq("client_order_id", clientId);
  return status;
}

async function tradeIntent(
  db: ReturnType<typeof adminClient>,
  clientId: string,
  fn: () => Promise<Row>,
) {
  if (!(await reserveIntent(db, clientId))) return { status: "DUPLICATE_SUPPRESSED" };
  try {
    const result = await fn();
    const status = await finishIntent(db, clientId, result);
    return { status, result };
  } catch (error) {
    await db.schema("ai_trade").from("order_intents").update({
      status: "AMBIGUOUS",
      updated_at: new Date().toISOString(),
    }).eq("client_order_id", clientId);
    throw error;
  }
}

async function deterministicId(parts: string[]) {
  return "AI" + (await sha256(parts.join("|"))).slice(0, 20);
}

Deno.serve(async (req) => {
  const db = adminClient();

  const suppliedCronSecret = req.headers.get("x-ai-trade-cron") ?? "";
  const { data: authRow, error: authError } = await db.schema("ai_trade")
    .from("cron_auth").select("secret").eq("id", 1).single();
  if (authError || !authRow || suppliedCronSecret !== authRow.secret) {
    return json({ ok: false, status: "UNAUTHORIZED" }, 401);
  }

  const { data: config, error: configError } = await db.schema("ai_trade")
    .from("runtime_config").select("*").eq("id", 1).single();
  if (configError || !config) {
    await appendEvent(db, "tick", "CONFIG_ERROR", { message: String(configError?.message ?? "") });
    return json({ ok: false, status: "CONFIG_ERROR" }, 500);
  }

  if (!config.enabled) {
    await appendEvent(db, "tick", "DISABLED", { symbol: config.symbol });
    return json({ ok: true, status: "DISABLED" });
  }

  const token = Deno.env.get("METAAPI_TOKEN")?.trim() ?? "";
  const accountId = Deno.env.get("METAAPI_ACCOUNT_ID")?.trim() ?? "";
  if (!token || !accountId) {
    await appendEvent(db, "tick", "CONFIG_BLOCKED", {
      missing: [
        ...(token ? [] : ["METAAPI_TOKEN"]),
        ...(accountId ? [] : ["METAAPI_ACCOUNT_ID"]),
      ],
    });
    return json({ ok: false, status: "CONFIG_BLOCKED" }, 503);
  }

  try {
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

    const [positionsAll, spec, price, deals, candlesRaw] = await Promise.all([
      connection.getPositions(),
      connection.getSymbolSpecification(symbol),
      connection.getSymbolPrice(symbol),
      connection.getDealsByTimeRange(
        new Date(new Date().setUTCHours(0, 0, 0, 0)),
        new Date(),
      ),
      account.getHistoricalCandles(
        symbol,
        timeframe,
        undefined,
        Math.min(1000, Math.max(80, Number(config.lookback_bars) + Number(config.trailing_lookback) + 10)),
      ),
    ]);

    if (!spec || !price || !candlesRaw?.length) throw new Error("MARKET_DATA_UNAVAILABLE");

    const now = Date.now();
    const barMs = timeframeMs(timeframe);
    const candles = candlesRaw
      .filter((c: Row) => new Date(c.time).getTime() + barMs <= now)
      .sort((a: Row, b: Row) => new Date(a.time).getTime() - new Date(b.time).getTime());
    if (candles.length <= Math.max(config.lookback_bars, config.stop_lookback_bars)) {
      throw new Error("INSUFFICIENT_CLOSED_BARS");
    }

    const bid = num(price.bid);
    const ask = num(price.ask);
    const point = num(spec.point);
    if (bid <= 0 || ask <= 0 || ask < bid || point <= 0) throw new Error("INVALID_QUOTE");
    const spreadPoints = (ask - bid) / point;
    if (spreadPoints > num(config.max_spread_points)) {
      await appendEvent(db, "tick", "SPREAD_BLOCKED", { spreadPoints });
      return json({ ok: true, status: "SPREAD_BLOCKED", spreadPoints });
    }

    const dailyPnl = (deals ?? [])
      .filter((d: Row) => Number(d.magic ?? 0) === Number(config.magic))
      .reduce((sum: number, d: Row) =>
        sum + num(d.profit) + num(d.commission) + num(d.swap) + num(d.fee), 0);
    if (dailyPnl <= -num(config.max_daily_loss_demo)) {
      await appendEvent(db, "tick", "DAILY_LOSS_BLOCKED", { dailyPnl });
      return json({ ok: true, status: "DAILY_LOSS_BLOCKED", dailyPnl });
    }

    const ownPositions = (positionsAll ?? []).filter((p: Row) =>
      String(p.symbol) === symbol && Number(p.magic ?? 0) === Number(config.magic)
    );

    const openIds = ownPositions.map((p: Row) => String(p.id));
    const { data: localOpen } = await db.schema("ai_trade").from("managed_positions")
      .select("position_id").eq("strategy_id", config.strategy_id).eq("status", "OPEN");
    for (const row of localOpen ?? []) {
      if (!openIds.includes(String(row.position_id))) {
        await db.schema("ai_trade").from("managed_positions").update({
          status: "CLOSED", updated_at: new Date().toISOString(),
        }).eq("position_id", row.position_id);
      }
    }
    for (const p of ownPositions) {
      await db.schema("ai_trade").from("managed_positions").upsert({
        position_id: String(p.id),
        strategy_id: config.strategy_id,
        last_stop: p.stopLoss ?? null,
        status: "OPEN",
        updated_at: new Date().toISOString(),
      }, { onConflict: "position_id", ignoreDuplicates: true });
    }

    const current = candles[candles.length - 1];
    const barStamp = new Date(current.time).toISOString();

    if (ownPositions.length === 0) {
      const reference = candles[candles.length - 1 - Number(config.lookback_bars)];
      if (num(current.close) === num(reference.close)) {
        return json({ ok: true, status: "NO_SIGNAL" });
      }
      const direction = num(current.close) > num(reference.close) ? "UP" : "DOWN";
      const prior = candles.slice(
        candles.length - 1 - Number(config.stop_lookback_bars),
        candles.length - 1,
      );
      const stop = direction === "UP"
        ? Math.min(...prior.map((b: Row) => num(b.low)))
        : Math.max(...prior.map((b: Row) => num(b.high)));
      const entry = direction === "UP" ? ask : bid;
      if ((direction === "UP" && stop >= entry) || (direction === "DOWN" && stop <= entry)) {
        throw new Error("INVALID_PROTECTIVE_STOP");
      }

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
        await appendEvent(db, "entry", "MONITOR_ONLY", { direction, entry, stop, target }, clientId);
        return json({ ok: true, status: "MONITOR_ONLY", direction, entry, stop, target });
      }

      const volume = num(config.demo_volume);
      if (volume <= 0 || volume > 0.01) throw new Error("DEMO_VOLUME_CAP");
      const options = { comment: "AI-TRADE DEMO", clientId, magic: Number(config.magic) };
      const sent = await tradeIntent(db, clientId, () =>
        direction === "UP"
          ? connection.createMarketBuyOrder(symbol, volume, stop, target, options)
          : connection.createMarketSellOrder(symbol, volume, stop, target, options)
      );
      await appendEvent(db, "entry", sent.status, { direction, entry, stop, target }, clientId);
      return json({ ok: true, status: sent.status, clientId });
    }

    if (ownPositions.length > 1) {
      await appendEvent(db, "manage", "MULTIPLE_OWN_POSITIONS", { count: ownPositions.length });
      return json({ ok: false, status: "MULTIPLE_OWN_POSITIONS" }, 409);
    }

    const position = ownPositions[0];
    const positionId = String(position.id);
    const { data: state } = await db.schema("ai_trade").from("managed_positions")
      .select("*").eq("position_id", positionId).single();

    const isLong = String(position.type).toUpperCase() === "POSITION_TYPE_BUY";
    const stopLoss = num(position.stopLoss, 0);
    const takeProfit = num(position.takeProfit, 0);
    const targetHit = takeProfit > 0 &&
      (isLong ? num(current.high) >= takeProfit : num(current.low) <= takeProfit);

    if (
      targetHit &&
      config.exit_mode === "PARTIAL_THEN_TRAIL" &&
      !state?.partial_done
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
          String(config.strategy_id), symbol, "PARTIAL_FALLBACK_TRAIL", barStamp, positionId,
        ]);
        if (config.demo_send_enabled) {
          const modified = await tradeIntent(db, fallbackId, () =>
            connection.modifyPosition(positionId, stopLoss, 0)
          );
          if (modified.status === "FILLED" || modified.status === "PARTIAL") {
            await db.schema("ai_trade").from("managed_positions").update({
              partial_done: true, updated_at: new Date().toISOString(),
            }).eq("position_id", positionId);
          }
          await appendEvent(db, "partial_fallback", modified.status, {}, fallbackId);
          return json({ ok: true, status: modified.status, mode: "TRAILING_FALLBACK" });
        }
        return json({ ok: true, status: "MONITOR_ONLY", mode: "TRAILING_FALLBACK" });
      }

      if (!config.demo_send_enabled) {
        return json({ ok: true, status: "MONITOR_ONLY", action: "PARTIAL_CLOSE", partialVolume });
      }
      const partial = await tradeIntent(db, partialId, () =>
        connection.closePositionPartially(positionId, partialVolume!)
      );
      if (partial.status === "FILLED" || partial.status === "PARTIAL") {
        await db.schema("ai_trade").from("managed_positions").update({
          partial_done: true, updated_at: new Date().toISOString(),
        }).eq("position_id", positionId);
        const dropId = await deterministicId([
          String(config.strategy_id), symbol, "DROP_TP", barStamp, positionId,
        ]);
        await tradeIntent(db, dropId, () => connection.modifyPosition(positionId, stopLoss, 0));
      }
      await appendEvent(db, "partial_close", partial.status, { partialVolume }, partialId);
      return json({ ok: true, status: partial.status, action: "PARTIAL_CLOSE" });
    }

    if (config.exit_mode === "TRAILING_ONLY" || config.exit_mode === "PARTIAL_THEN_TRAIL") {
      const lookback = Number(config.trailing_lookback);
      if (candles.length > lookback) {
        const trailBars = candles.slice(candles.length - 1 - lookback, candles.length - 1);
        const candidate = isLong
          ? Math.min(...trailBars.map((b: Row) => num(b.low)))
          : Math.max(...trailBars.map((b: Row) => num(b.high)));
        const improves = stopLoss <= 0 || (isLong ? candidate > stopLoss : candidate < stopLoss);
        const marketSafe = isLong ? candidate < bid : candidate > ask;
        if (improves && marketSafe) {
          const trailId = await deterministicId([
            String(config.strategy_id), symbol, "TRAIL", barStamp, positionId,
          ]);
          if (!config.demo_send_enabled) {
            return json({ ok: true, status: "MONITOR_ONLY", action: "TRAIL", candidate });
          }
          const modified = await tradeIntent(db, trailId, () =>
            connection.modifyPosition(positionId, candidate, takeProfit > 0 ? takeProfit : 0)
          );
          if (modified.status === "FILLED" || modified.status === "PARTIAL") {
            await db.schema("ai_trade").from("managed_positions").update({
              last_stop: candidate, updated_at: new Date().toISOString(),
            }).eq("position_id", positionId);
          }
          await appendEvent(db, "trail_stop", modified.status, { candidate }, trailId);
          return json({ ok: true, status: modified.status, action: "TRAIL" });
        }
      }
    }

    return json({ ok: true, status: "HOLD" });
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    await appendEvent(db, "tick", "ERROR", { message });
    return json({ ok: false, status: "ERROR", message }, 500);
  }
});

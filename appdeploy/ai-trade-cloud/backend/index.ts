import { router, json, db, secrets } from '@appdeploy/sdk';

type ExitMode = 'TRAILING_ONLY' | 'FIXED_TP' | 'PARTIAL_THEN_TRAIL';
type Intent = { id: string; status: string; at: string };
type EventItem = { at: string; result: string; detail?: string };
type Managed = { positionId: string; partialDone: boolean; lastStop?: number; pyramidAdds: number };

type RuntimeState = {
  key: 'singleton';
  accountId?: string;
  engineStatus: string;
  lastTick?: string;
  lastAction?: string;
  lastError?: string;
  brokerConnected: boolean;
  strategy: string;
  symbol: string;
  timeframe: string;
  exitMode: ExitMode;
  magic: number;
  demoVolume: number;
  maxPyramidAdds: number;
  managed?: Managed;
  intents: Intent[];
  events: EventItem[];
};

const DEFAULT_STATE: RuntimeState = {
  key: 'singleton',
  engineStatus: 'LOCKED',
  brokerConnected: false,
  strategy: 'TF-004 Time-Series Momentum + Channel Trailing',
  symbol: 'EURUSD',
  timeframe: '15m',
  exitMode: 'TRAILING_ONLY',
  magic: 260927,
  demoVolume: 0.01,
  maxPyramidAdds: 0,
  intents: [],
  events: [],
};

type StoredState = RuntimeState & { id: string };

async function loadState(): Promise<StoredState> {
  const { items } = await db.list<RuntimeState>('runtime', { limit: 10 });
  const existing = items.find(item => item.key === 'singleton');
  if (existing) {
    const state = existing as StoredState;
    if (!Number.isInteger(state.maxPyramidAdds) || state.maxPyramidAdds < 0) state.maxPyramidAdds = 0;
    if (state.managed && !Number.isInteger(state.managed.pyramidAdds)) state.managed = { ...state.managed, pyramidAdds: 0 };
    return state;
  }
  const [id] = await db.add('runtime', [DEFAULT_STATE]);
  if (!id) throw new Error('STATE_CREATE_FAILED');
  return { ...DEFAULT_STATE, id };
}

async function saveState(state: StoredState) {
  const { id, ...record } = state;
  const [ok] = await db.update('runtime', [{ id, record }]);
  if (!ok) throw new Error('STATE_UPDATE_FAILED');
}

function pushEvent(state: StoredState, result: string, detail?: string) {
  state.events = [
    ...state.events,
    { at: new Date().toISOString(), result, detail },
  ].slice(-40);
}

function configured(names: string[], required: string[]) {
  return Object.fromEntries(required.map(name => [name, names.includes(name)]));
}

function n(value: unknown, fallback = 0) {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : fallback;
}

async function makeId(parts: string[]) {
  const bytes = new TextEncoder().encode(parts.join('|'));
  const digest = await crypto.subtle.digest('SHA-256', bytes);
  const hex = [...new Uint8Array(digest)]
    .map(b => b.toString(16).padStart(2, '0'))
    .join('');
  return 'AI' + hex.slice(0, 20);
}

function hasIntent(state: StoredState, id: string) {
  return state.intents.some(intent => intent.id === id);
}

function recordIntent(state: StoredState, id: string, status: string) {
  state.intents = [
    ...state.intents.filter(intent => intent.id !== id),
    {
      id,
      status,
      at: new Date().toISOString(),
    },
  ].slice(-100);
}

function tradeDone(result: Record<string, unknown>) {
  return (
    result.numericCode === 10009 ||
    result.numericCode === 10010 ||
    result.stringCode === 'TRADE_RETCODE_DONE' ||
    result.stringCode === 'TRADE_RETCODE_DONE_PARTIAL'
  );
}

function normalizePartial(
  volume: number,
  fraction: number,
  spec: Record<string, unknown>
) {
  const min = n(spec.minVolume);
  const step = n(spec.volumeStep);
  if (!(fraction > 0 && fraction < 1) || min <= 0 || step <= 0) return null;
  let candidate = Math.floor((volume * fraction + 1e-12) / step) * step;
  if (candidate < min) candidate = min;
  if (volume - candidate > 1e-12 && volume - candidate < min)
    candidate = volume - min;
  const ratio = candidate / step;
  if (
    candidate <= 0 ||
    candidate >= volume ||
    candidate < min ||
    Math.abs(ratio - Math.round(ratio)) > 1e-8
  )
    return null;
  return Number(candidate.toFixed(8));
}

async function metaApiAccount(state: StoredState) {
  const names = await secrets.listSecretNames();
  const required = [
    'METAAPI_TOKEN',
    'MT5_DEMO_LOGIN',
    'MT5_DEMO_PASSWORD',
    'MT5_DEMO_SERVER',
    'AI_TRADE_DEMO_ENABLE',
  ];
  const flags = configured(names, required);
  if (required.some(name => !flags[name])) throw new Error('CONFIG_BLOCKED');

  const enabled = (await secrets.readSecret('AI_TRADE_DEMO_ENABLE'))
    .trim()
    .toUpperCase();
  if (enabled !== 'YES') throw new Error('DEMO_NOT_ARMED');

  const token = await secrets.readSecret('METAAPI_TOKEN');
  const login = (await secrets.readSecret('MT5_DEMO_LOGIN')).trim();
  const password = await secrets.readSecret('MT5_DEMO_PASSWORD');
  const server = (await secrets.readSecret('MT5_DEMO_SERVER')).trim();
  if (!server.toLowerCase().includes('demo'))
    throw new Error('DEMO_SERVER_REQUIRED');

  const module = await import('metaapi.cloud-sdk/esm-node');
  const MetaApi = module.default;
  const api = new MetaApi(token);

  let account;
  if (state.accountId) {
    try {
      account = await api.metatraderAccountApi.getAccount(state.accountId);
    } catch {
      state.accountId = undefined;
    }
  }
  if (!account) {
    const accounts =
      await api.metatraderAccountApi.getAccountsWithInfiniteScrollPagination();
    account = accounts.find(
      (item: { login?: string; server?: string; platform?: string }) =>
        String(item.login) === login &&
        String(item.server) === server &&
        String(item.platform).toLowerCase() === 'mt5'
    );
  }
  if (!account) {
    account = await api.metatraderAccountApi.createAccount({
      name: 'AI-TRADE DEMO',
      type: 'cloud',
      login,
      password,
      server,
      platform: 'mt5',
      application: 'MetaApi',
      magic: state.magic,
      reliability: 'regular',
    });
  }
  if (String(account.platform).toLowerCase() !== 'mt5')
    throw new Error('MT5_REQUIRED');
  if (
    !String(account.server ?? server)
      .toLowerCase()
      .includes('demo')
  )
    throw new Error('DEMO_SERVER_REQUIRED');
  state.accountId = account.id;
  if (String(account.state).toUpperCase() !== 'DEPLOYED')
    await account.deploy();
  await account.waitConnected();
  return account;
}

async function runTick() {
  const state = await loadState();
  state.lastTick = new Date().toISOString();
  state.lastError = undefined;

  try {
    const names = await secrets.listSecretNames();
    const required = [
      'METAAPI_TOKEN',
      'MT5_DEMO_LOGIN',
      'MT5_DEMO_PASSWORD',
      'MT5_DEMO_SERVER',
      'AI_TRADE_DEMO_ENABLE',
    ];
    if (required.some(name => !names.includes(name))) {
      state.engineStatus = 'CONFIG_BLOCKED';
      state.brokerConnected = false;
      pushEvent(state, 'CONFIG_BLOCKED');
      await saveState(state);
      return;
    }
    if (
      (await secrets.readSecret('AI_TRADE_DEMO_ENABLE'))
        .trim()
        .toUpperCase() !== 'YES'
    ) {
      state.engineStatus = 'LOCKED';
      state.brokerConnected = false;
      pushEvent(state, 'LOCKED');
      await saveState(state);
      return;
    }

    const account = await metaApiAccount(state);
    const connection = account.getRPCConnection();
    await connection.connect();
    await connection.waitSynchronized();
    state.brokerConnected = true;

    await connection.subscribeToMarketData(state.symbol);
    const start = new Date();
    start.setUTCHours(0, 0, 0, 0);

    const [positionsRaw, accountInfo, spec, price, deals, candlesRaw] = await Promise.all([
      connection.getPositions(),
      connection.getAccountInformation(),
      connection.getSymbolSpecification(state.symbol),
      connection.getSymbolPrice(state.symbol),
      connection.getDealsByTimeRange(start, new Date()),
      account.getHistoricalCandles(
        state.symbol,
        state.timeframe,
        undefined,
        100
      ),
    ]);
    if (!accountInfo || !spec || !price || !candlesRaw?.length)
      throw new Error('MARKET_DATA_UNAVAILABLE');
    if (String(accountInfo.type) !== 'ACCOUNT_TRADE_MODE_DEMO') throw new Error('DEMO_ACCOUNT_REQUIRED');
    if (accountInfo.tradeAllowed === false || accountInfo.investorMode === true) throw new Error('ACCOUNT_TRADING_DISABLED');

    const now = Date.now();
    const candleMs = 15 * 60 * 1000;
    const candles = candlesRaw
      .filter(
        (c: { time: Date | string }) =>
          new Date(c.time).getTime() + candleMs <= now
      )
      .sort(
        (a: { time: Date | string }, b: { time: Date | string }) =>
          new Date(a.time).getTime() - new Date(b.time).getTime()
      );
    if (candles.length < 25) throw new Error('INSUFFICIENT_CLOSED_BARS');

    const bid = n(price.bid);
    const ask = n(price.ask);
    const point = n(spec.point);
    if (bid <= 0 || ask <= 0 || ask < bid || point <= 0)
      throw new Error('INVALID_QUOTE');
    const spreadPoints = (ask - bid) / point;
    if (spreadPoints > 30) {
      state.engineStatus = 'SPREAD_BLOCKED';
      state.lastAction = 'No new risk';
      pushEvent(state, 'SPREAD_BLOCKED', spreadPoints.toFixed(2));
      await saveState(state);
      return;
    }

    const dailyPnl = (deals ?? [])
      .filter(
        (deal: { magic?: number }) => Number(deal.magic ?? 0) === state.magic
      )
      .reduce(
        (
          sum: number,
          deal: {
            profit?: number;
            commission?: number;
            swap?: number;
            fee?: number;
          }
        ) =>
          sum +
          n(deal.profit) +
          n(deal.commission) +
          n(deal.swap) +
          n(deal.fee),
        0
      );
    if (dailyPnl <= -10) {
      state.engineStatus = 'DAILY_LOSS_BLOCKED';
      state.lastAction = 'No new risk';
      pushEvent(state, 'DAILY_LOSS_BLOCKED');
      await saveState(state);
      return;
    }

    const positions = (positionsRaw ?? []).filter(
      (position: { symbol?: string; magic?: number }) =>
        String(position.symbol) === state.symbol &&
        Number(position.magic ?? 0) === state.magic
    );
    if (positions.length > 1) throw new Error('MULTIPLE_OWN_POSITIONS');
    const current = candles[candles.length - 1];
    const barStamp = new Date(current.time).toISOString();

    if (positions.length === 0) {
      state.managed = undefined;
      const reference = candles[candles.length - 21];
      if (n(current.close) === n(reference.close)) {
        state.engineStatus = 'NO_SIGNAL';
        state.lastAction = 'Hold cash';
        await saveState(state);
        return;
      }
      const direction = n(current.close) > n(reference.close) ? 'UP' : 'DOWN';
      const prior = candles.slice(candles.length - 6, candles.length - 1);
      const stop =
        direction === 'UP'
          ? Math.min(...prior.map((bar: { low?: number }) => n(bar.low)))
          : Math.max(...prior.map((bar: { high?: number }) => n(bar.high)));
      const entry = direction === 'UP' ? ask : bid;
      if (
        (direction === 'UP' && stop >= entry) ||
        (direction === 'DOWN' && stop <= entry)
      )
        throw new Error('INVALID_PROTECTIVE_STOP');

      let target: number | undefined;
      if (state.exitMode !== 'TRAILING_ONLY') {
        const risk = Math.abs(entry - stop);
        target = direction === 'UP' ? entry + risk * 1.5 : entry - risk * 1.5;
      }

      const clientId = await makeId([
        state.strategy,
        state.symbol,
        'ENTRY',
        barStamp,
        direction,
      ]);
      if (hasIntent(state, clientId)) {
        state.engineStatus = 'DUPLICATE_SUPPRESSED';
        await saveState(state);
        return;
      }
      recordIntent(state, clientId, 'SUBMITTING');
      await saveState(state);

      const options = {
        comment: 'AI-TRADE DEMO',
        clientId,
        magic: state.magic,
      };
      let result;
      try {
        result =
          direction === 'UP'
            ? await connection.createMarketBuyOrder(
                state.symbol,
                state.demoVolume,
                stop,
                target,
                options
              )
            : await connection.createMarketSellOrder(
                state.symbol,
                state.demoVolume,
                stop,
                target,
                options
              );
      } catch (cause) {
        recordIntent(state, clientId, 'AMBIGUOUS');
        state.engineStatus = 'AMBIGUOUS';
        state.lastError =
          cause instanceof Error ? cause.message : String(cause);
        pushEvent(state, 'AMBIGUOUS');
        await saveState(state);
        return;
      }
      const status = tradeDone(result as Record<string, unknown>)
        ? 'FILLED'
        : 'REJECTED';
      recordIntent(state, clientId, status);
      state.engineStatus = status;
      state.lastAction = direction === 'UP' ? 'BUY DEMO' : 'SELL DEMO';
      pushEvent(state, status, state.lastAction);
      await saveState(state);
      return;
    }

    const position = positions[0];
    const positionId = String(position.id);
    if (!state.managed || state.managed.positionId !== positionId) {
      state.managed = {
        positionId,
        partialDone: false,
        lastStop: n(position.stopLoss) || undefined,
        pyramidAdds: 0,
      };
    }

    const isLong = String(position.type).toUpperCase() === 'POSITION_TYPE_BUY';
    const stopLoss = n(position.stopLoss);
    const takeProfit = n(position.takeProfit);
    const targetHit =
      takeProfit > 0 &&
      (isLong ? n(current.high) >= takeProfit : n(current.low) <= takeProfit);

    if (
      state.exitMode === 'PARTIAL_THEN_TRAIL' &&
      targetHit &&
      !state.managed.partialDone
    ) {
      const volume = normalizePartial(
        n(position.volume),
        0.5,
        spec as Record<string, unknown>
      );
      const partialId = await makeId([
        state.strategy,
        state.symbol,
        'PARTIAL',
        barStamp,
        positionId,
      ]);
      if (!hasIntent(state, partialId)) {
        recordIntent(state, partialId, 'SUBMITTING');
        await saveState(state);
        let result;
        if (volume === null) {
          if (stopLoss <= 0) throw new Error('PROTECTIVE_STOP_MISSING');
          result = await connection.modifyPosition(positionId, stopLoss, 0);
          state.lastAction = 'Partial unavailable, trailing fallback';
        } else {
          result = await connection.closePositionPartially(positionId, volume);
          if (tradeDone(result as Record<string, unknown>))
            await connection.modifyPosition(positionId, stopLoss, 0);
          state.lastAction = 'Partial close then trail';
        }
        const status = tradeDone(result as Record<string, unknown>)
          ? 'FILLED'
          : 'REJECTED';
        recordIntent(state, partialId, status);
        if (status === 'FILLED') state.managed.partialDone = true;
        state.engineStatus = status;
        pushEvent(state, status, state.lastAction);
        await saveState(state);
        return;
      }
    }

    const sameDirectionSignal = n(current.close) !== n(candles[candles.length - 21].close) &&
      (n(current.close) > n(candles[candles.length - 21].close)) === isLong;
    const marketPrice = isLong ? bid : ask;
    const openPrice = n(position.openPrice);
    const winning = isLong ? marketPrice > openPrice : marketPrice < openPrice;
    const oldRiskProtected = stopLoss > 0 && (isLong ? stopLoss >= openPrice : stopLoss <= openPrice);
    const nettingAccount = String(accountInfo.marginMode) === 'ACCOUNT_MARGIN_MODE_RETAIL_NETTING';
    const pyramidLimit = Math.max(0, state.maxPyramidAdds);
    const totalVolumeCap = state.demoVolume * (1 + pyramidLimit);
    if (
      pyramidLimit > 0 &&
      nettingAccount &&
      sameDirectionSignal &&
      winning &&
      oldRiskProtected &&
      state.managed.pyramidAdds < pyramidLimit &&
      n(position.volume) + state.demoVolume <= totalVolumeCap + 1e-12
    ) {
      const pyramidId = await makeId([
        state.strategy,
        state.symbol,
        'PYRAMID',
        barStamp,
        String(state.managed.pyramidAdds + 1),
      ]);
      if (!hasIntent(state, pyramidId)) {
        recordIntent(state, pyramidId, 'SUBMITTING');
        await saveState(state);
        const options = { comment: 'AI-TRADE DEMO PYRAMID', clientId: pyramidId, magic: state.magic };
        let pyramidResult;
        try {
          pyramidResult = isLong
            ? await connection.createMarketBuyOrder(state.symbol, state.demoVolume, stopLoss, undefined, options)
            : await connection.createMarketSellOrder(state.symbol, state.demoVolume, stopLoss, undefined, options);
        } catch (cause) {
          recordIntent(state, pyramidId, 'AMBIGUOUS');
          state.engineStatus = 'AMBIGUOUS';
          state.lastError = cause instanceof Error ? cause.message : String(cause);
          pushEvent(state, 'AMBIGUOUS', 'Winner pyramid');
          await saveState(state);
          return;
        }
        const pyramidStatus = tradeDone(pyramidResult as Record<string, unknown>) ? 'FILLED' : 'REJECTED';
        recordIntent(state, pyramidId, pyramidStatus);
        if (pyramidStatus === 'FILLED') state.managed.pyramidAdds += 1;
        state.engineStatus = pyramidStatus;
        state.lastAction = pyramidStatus === 'FILLED' ? 'Winner pyramid DEMO' : 'Pyramid rejected';
        pushEvent(state, pyramidStatus, state.lastAction);
        await saveState(state);
        return;
      }
    }

    if (
      state.exitMode === 'TRAILING_ONLY' ||
      state.exitMode === 'PARTIAL_THEN_TRAIL'
    ) {
      const prior = candles.slice(candles.length - 21, candles.length - 1);
      const candidate = isLong
        ? Math.min(...prior.map((bar: { low?: number }) => n(bar.low)))
        : Math.max(...prior.map((bar: { high?: number }) => n(bar.high)));
      const improves =
        stopLoss <= 0 || (isLong ? candidate > stopLoss : candidate < stopLoss);
      const safe = isLong ? candidate < bid : candidate > ask;
      if (improves && safe) {
        const clientId = await makeId([
          state.strategy,
          state.symbol,
          'TRAIL',
          barStamp,
          positionId,
        ]);
        if (!hasIntent(state, clientId)) {
          recordIntent(state, clientId, 'SUBMITTING');
          await saveState(state);
          const result = await connection.modifyPosition(
            positionId,
            candidate,
            takeProfit > 0 ? takeProfit : 0
          );
          const status = tradeDone(result as Record<string, unknown>)
            ? 'FILLED'
            : 'REJECTED';
          recordIntent(state, clientId, status);
          if (status === 'FILLED') state.managed.lastStop = candidate;
          state.engineStatus = status;
          state.lastAction = 'Trail protective stop';
          pushEvent(state, status, state.lastAction);
          await saveState(state);
          return;
        }
      }
    }

    state.engineStatus = 'HOLD';
    state.lastAction = 'Let winner run';
    await saveState(state);
  } catch (cause) {
    const message = cause instanceof Error ? cause.message : String(cause);
    state.brokerConnected = false;
    state.engineStatus =
      message === 'CONFIG_BLOCKED' || message === 'DEMO_NOT_ARMED'
        ? message
        : 'ERROR';
    state.lastError = message;
    pushEvent(state, state.engineStatus, message);
    await saveState(state);
  }
}


type ResearchBar = {
  timestamp: number;
  open: number;
  high: number;
  low: number;
  close: number;
};

type ResearchCost = {
  spread: number;
  commission: number;
  slippage: number;
  swapPerBar: number;
};

type ResearchTrade = {
  r: number;
  exitDay: string;
};

function researchMetrics(trades: ResearchTrade[]) {
  let equity = 0;
  let peak = 0;
  let maxDrawdownR = 0;
  let lossStreak = 0;
  let maxLossStreak = 0;
  let grossWin = 0;
  let grossLoss = 0;
  let worstTradeR = 0;
  const byDay = new Map<string, number>();

  for (const trade of trades) {
    equity += trade.r;
    peak = Math.max(peak, equity);
    maxDrawdownR = Math.max(maxDrawdownR, peak - equity);
    worstTradeR = Math.min(worstTradeR, trade.r);
    if (trade.r < 0) {
      lossStreak += 1;
      maxLossStreak = Math.max(maxLossStreak, lossStreak);
      grossLoss += Math.abs(trade.r);
    } else {
      lossStreak = 0;
      grossWin += trade.r;
    }
    byDay.set(trade.exitDay, (byDay.get(trade.exitDay) ?? 0) + trade.r);
  }

  const dayValues = [...byDay.values()];
  return {
    trades: trades.length,
    netR: Number(equity.toFixed(3)),
    expectancyR: Number((trades.length ? equity / trades.length : 0).toFixed(3)),
    profitFactorR: grossLoss > 0 ? Number((grossWin / grossLoss).toFixed(3)) : null,
    maxDrawdownR: Number(maxDrawdownR.toFixed(3)),
    worstTradeR: Number(worstTradeR.toFixed(3)),
    maxLossStreak,
    worstRealizedDayR: Number((dayValues.length ? Math.min(...dayValues) : 0).toFixed(3)),
  };
}

function runTf004Research(
  bars: ResearchBar[],
  baseCost: ResearchCost,
  multiplier: number,
  signalStart = 0,
  signalEnd = bars.length
) {
  const cost = {
    spread: baseCost.spread * multiplier,
    commission: baseCost.commission * multiplier,
    slippage: baseCost.slippage * multiplier,
    swapPerBar: baseCost.swapPerBar * multiplier,
  };

  const trades: ResearchTrade[] = [];
  let position:
    | {
        direction: 'UP' | 'DOWN';
        entryIndex: number;
        referenceEntry: number;
        entryPrice: number;
        stop: number;
        initialStop: number;
      }
    | null = null;

  for (let index = 0; index < bars.length; index += 1) {
    const bar = bars[index];
    let exitedThisBar = false;

    if (position && index > position.entryIndex) {
      if (index >= 20) {
        const prior = bars.slice(index - 20, index);
        if (position.direction === 'UP') {
          const candidate = Math.min(...prior.map((item) => item.low));
          position.stop = Math.max(position.stop, candidate);
        } else {
          const candidate = Math.max(...prior.map((item) => item.high));
          position.stop = Math.min(position.stop, candidate);
        }
      }

      const stopHit =
        position.direction === 'UP'
          ? bar.low <= position.stop
          : bar.high >= position.stop;

      if (stopHit) {
        const theoreticalExit = position.stop;
        const exitPrice =
          position.direction === 'UP'
            ? theoreticalExit - cost.slippage
            : theoreticalExit + cost.slippage;
        const executedPnl =
          position.direction === 'UP'
            ? exitPrice - position.entryPrice
            : position.entryPrice - exitPrice;
        const holdingBars = index - position.entryIndex;
        const explicit =
          cost.spread + cost.commission + cost.swapPerBar * holdingBars;
        const pnl = executedPnl - explicit;
        const initialRisk = Math.abs(position.entryPrice - position.initialStop);
        if (initialRisk > 0) {
          trades.push({
            r: pnl / initialRisk,
            exitDay: new Date(bar.timestamp * 1000).toISOString().slice(0, 10),
          });
        }
        position = null;
        exitedThisBar = true;
      }
    }

    if (!position && !exitedThisBar) {
      if (index <= 20 || index <= 5 || index < signalStart || index >= signalEnd) {
        continue;
      }
      const reference = bars[index - 21].close;
      if (reference === bar.close) continue;
      const direction: 'UP' | 'DOWN' = bar.close > reference ? 'UP' : 'DOWN';
      const prior = bars.slice(index - 5, index);
      const stop =
        direction === 'UP'
          ? Math.min(...prior.map((item) => item.low))
          : Math.max(...prior.map((item) => item.high));
      if (
        (direction === 'UP' && stop >= bar.close) ||
        (direction === 'DOWN' && stop <= bar.close)
      ) {
        continue;
      }
      const entryPrice =
        direction === 'UP'
          ? bar.close + cost.slippage
          : bar.close - cost.slippage;
      position = {
        direction,
        entryIndex: index,
        referenceEntry: bar.close,
        entryPrice,
        stop,
        initialStop: stop,
      };
    }
  }

  return researchMetrics(trades);
}

async function yahooDailyBars(symbol: string): Promise<ResearchBar[]> {
  const start = 1451606400;
  const now = new Date();
  const end = Math.floor(
    Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate()) / 1000
  );
  const url =
    'https://query1.finance.yahoo.com/v8/finance/chart/' +
    encodeURIComponent(symbol) +
    '?period1=' +
    start +
    '&period2=' +
    end +
    '&interval=1d&events=history&includeAdjustedClose=true';
  const response = await fetch(url, {
    headers: { 'user-agent': 'AI-TRADE-research/0.2' },
  });
  if (!response.ok) {
    throw new Error('YAHOO_HTTP_' + response.status + '_' + symbol);
  }
  const payload = (await response.json()) as {
    chart?: {
      error?: unknown;
      result?: Array<{
        timestamp?: number[];
        indicators?: {
          quote?: Array<{
            open?: Array<number | null>;
            high?: Array<number | null>;
            low?: Array<number | null>;
            close?: Array<number | null>;
          }>;
        };
      }>;
    };
  };
  if (payload.chart?.error) throw new Error('YAHOO_CHART_' + symbol);
  const result = payload.chart?.result?.[0];
  const timestamps = result?.timestamp ?? [];
  const quote = result?.indicators?.quote?.[0];
  if (!quote) throw new Error('YAHOO_NO_DATA_' + symbol);

  const bars: ResearchBar[] = [];
  for (let i = 0; i < timestamps.length; i += 1) {
    const open = quote.open?.[i];
    const high = quote.high?.[i];
    const low = quote.low?.[i];
    const close = quote.close?.[i];
    if (
      timestamps[i] >= end ||
      open == null ||
      high == null ||
      low == null ||
      close == null ||
      !Number.isFinite(open) ||
      !Number.isFinite(high) ||
      !Number.isFinite(low) ||
      !Number.isFinite(close)
    ) {
      continue;
    }
    bars.push({ timestamp: timestamps[i], open, high, low, close });
  }
  bars.sort((a, b) => a.timestamp - b.timestamp);
  if (bars.length < 500) throw new Error('YAHOO_TOO_FEW_BARS_' + symbol);
  return bars;
}

function walkForwardResearch(
  bars: ResearchBar[],
  cost: ResearchCost,
  multiplier: number
) {
  const trainBars = Math.floor(bars.length * 0.5);
  const testBars = Math.max(1, Math.floor(bars.length * 0.1));
  const folds = [];
  let trainEnd = trainBars;
  while (trainEnd < bars.length) {
    const testEnd = Math.min(trainEnd + testBars, bars.length);
    const metrics = runTf004Research(
      bars.slice(0, testEnd),
      cost,
      multiplier,
      trainEnd,
      testEnd
    );
    folds.push(metrics);
    trainEnd = testEnd;
  }
  return {
    folds: folds.length,
    positiveFolds: folds.filter((fold) => fold.netR > 0).length,
    netRSum: Number(
      folds.reduce((sum, fold) => sum + fold.netR, 0).toFixed(3)
    ),
    worstFoldDrawdownR: Number(
      Math.max(...folds.map((fold) => fold.maxDrawdownR), 0).toFixed(3)
    ),
    trades: folds.reduce((sum, fold) => sum + fold.trades, 0),
  };
}

async function tf004RiskLab() {
  const definitions: Array<{
    symbol: string;
    cost: ResearchCost;
  }> = [
    {
      symbol: 'EURUSD=X',
      cost: {
        spread: 0.0002,
        commission: 0.00002,
        slippage: 0.00005,
        swapPerBar: 0.00001,
      },
    },
    {
      symbol: 'GBPUSD=X',
      cost: {
        spread: 0.0002,
        commission: 0.00002,
        slippage: 0.00005,
        swapPerBar: 0.00001,
      },
    },
    {
      symbol: 'USDJPY=X',
      cost: {
        spread: 0.02,
        commission: 0.002,
        slippage: 0.005,
        swapPerBar: 0.001,
      },
    },
  ];
  const multipliers = [0, 1, 1.5, 2];

  const results = await Promise.all(
    definitions.map(async ({ symbol, cost }) => {
      const bars = await yahooDailyBars(symbol);
      const split = Math.floor(bars.length * 0.7);
      const stress = multipliers.map((multiplier) => {
        const oos = runTf004Research(bars, cost, multiplier, split, bars.length);
        const walkForward = walkForwardResearch(bars, cost, multiplier);
        return { multiplier, oos, walkForward };
      });
      const baseline = stress.find((item) => item.multiplier === 1)!;
      const positiveStress = stress.filter(
        (item) => item.oos.netR > 0 && item.walkForward.netRSum > 0
      );
      return {
        symbol,
        bars: bars.length,
        firstBar: new Date(bars[0].timestamp * 1000).toISOString().slice(0, 10),
        lastBar: new Date(bars[bars.length - 1].timestamp * 1000)
          .toISOString()
          .slice(0, 10),
        baseline,
        stress,
        highestPositiveCostMultiplier:
          positiveStress.length > 0
            ? Math.max(...positiveStress.map((item) => item.multiplier))
            : null,
      };
    })
  );

  const baselineRobust = results.every(
    (item) =>
      item.baseline.oos.netR > 0 &&
      item.baseline.walkForward.netRSum > 0 &&
      item.baseline.walkForward.positiveFolds >=
        Math.ceil(item.baseline.walkForward.folds / 2)
  );

  return {
    generatedAt: new Date().toISOString(),
    strategy: 'TF-004-TIME-SERIES-CHANNEL',
    source: 'Yahoo chart daily research proxy',
    provenance: 'UNVERIFIED_RESEARCH_DATA_AND_COSTS',
    window: '2016-01-01 through last completed UTC day',
    parameters: {
      lookbackBars: 20,
      stopLookbackBars: 5,
      exitLookbackBars: 20,
      positionPolicy: 'ONE_OPEN',
      ambiguousBarPolicy: 'STOP_FIRST',
    },
    result: results,
    riskProfileCandidate: {
      status: baselineRobust ? 'RESEARCH_CANDIDATE_ONLY' : 'FAIL_CLOSED',
      maxSpreadPoints: null,
      maxDailyLossDemo: null,
      maxPyramidAdds: null,
      maxTotalVolumeDemo: null,
      reasons: [
        'Yahoo data is not broker execution data.',
        'Cost assumptions are unverified price-unit proxies.',
        'Backtest is normalized in R and does not size account capital.',
        'Pyramiding is not included in this fixed TF-004 historical engine.',
        baselineRobust
          ? 'Baseline passed the narrow research rule, but broker-aligned evidence is still required.'
          : 'Baseline did not pass the narrow cross-pair OOS/walk-forward robustness rule.',
      ],
    },
  };
}


function runTf004PyramidResearch(
  bars: ResearchBar[],
  baseCost: ResearchCost,
  multiplier: number,
  maxAdds: number,
  signalStart = 0,
  signalEnd = bars.length
) {
  const cost = {
    spread: baseCost.spread * multiplier,
    commission: baseCost.commission * multiplier,
    slippage: baseCost.slippage * multiplier,
    swapPerBar: baseCost.swapPerBar * multiplier,
  };
  const trades: ResearchTrade[] = [];
  let totalAdds = 0;
  let position:
    | {
        direction: 'UP' | 'DOWN';
        originalEntryIndex: number;
        originalEntryPrice: number;
        originalRisk: number;
        stop: number;
        legs: Array<{ entryIndex: number; entryPrice: number }>;
        adds: number;
      }
    | null = null;

  for (let index = 0; index < bars.length; index += 1) {
    const bar = bars[index];
    let exitedThisBar = false;

    if (position && index > position.originalEntryIndex) {
      if (index >= 20) {
        const prior = bars.slice(index - 20, index);
        if (position.direction === 'UP') {
          position.stop = Math.max(
            position.stop,
            Math.min(...prior.map((item) => item.low))
          );
        } else {
          position.stop = Math.min(
            position.stop,
            Math.max(...prior.map((item) => item.high))
          );
        }
      }

      const stopHit =
        position.direction === 'UP'
          ? bar.low <= position.stop
          : bar.high >= position.stop;

      if (stopHit) {
        const exitPrice =
          position.direction === 'UP'
            ? position.stop - cost.slippage
            : position.stop + cost.slippage;
        let totalPnl = 0;
        for (const leg of position.legs) {
          const executed =
            position.direction === 'UP'
              ? exitPrice - leg.entryPrice
              : leg.entryPrice - exitPrice;
          const holdingBars = index - leg.entryIndex;
          totalPnl +=
            executed -
            cost.spread -
            cost.commission -
            cost.swapPerBar * holdingBars;
        }
        if (position.originalRisk > 0) {
          trades.push({
            r: totalPnl / position.originalRisk,
            exitDay: new Date(bar.timestamp * 1000).toISOString().slice(0, 10),
          });
        }
        position = null;
        exitedThisBar = true;
      }
    }

    if (position && index > position.originalEntryIndex && position.adds < maxAdds) {
      const reference = index > 20 ? bars[index - 21].close : bar.close;
      const sameDirection =
        reference !== bar.close &&
        (bar.close > reference) === (position.direction === 'UP');
      const winning =
        position.direction === 'UP'
          ? bar.close > position.originalEntryPrice
          : bar.close < position.originalEntryPrice;
      const breakevenProtected =
        position.direction === 'UP'
          ? position.stop >= position.originalEntryPrice
          : position.stop <= position.originalEntryPrice;
      const stopStillProtective =
        position.direction === 'UP'
          ? position.stop < bar.close
          : position.stop > bar.close;

      if (
        sameDirection &&
        winning &&
        breakevenProtected &&
        stopStillProtective &&
        signalStart <= index &&
        index < signalEnd
      ) {
        const entryPrice =
          position.direction === 'UP'
            ? bar.close + cost.slippage
            : bar.close - cost.slippage;
        position.legs.push({ entryIndex: index, entryPrice });
        position.adds += 1;
        totalAdds += 1;
      }
    }

    if (!position && !exitedThisBar) {
      if (index <= 20 || index <= 5 || index < signalStart || index >= signalEnd) {
        continue;
      }
      const reference = bars[index - 21].close;
      if (reference === bar.close) continue;
      const direction: 'UP' | 'DOWN' = bar.close > reference ? 'UP' : 'DOWN';
      const prior = bars.slice(index - 5, index);
      const stop =
        direction === 'UP'
          ? Math.min(...prior.map((item) => item.low))
          : Math.max(...prior.map((item) => item.high));
      if (
        (direction === 'UP' && stop >= bar.close) ||
        (direction === 'DOWN' && stop <= bar.close)
      ) {
        continue;
      }
      const entryPrice =
        direction === 'UP'
          ? bar.close + cost.slippage
          : bar.close - cost.slippage;
      const originalRisk = Math.abs(entryPrice - stop);
      if (originalRisk <= 0) continue;
      position = {
        direction,
        originalEntryIndex: index,
        originalEntryPrice: entryPrice,
        originalRisk,
        stop,
        legs: [{ entryIndex: index, entryPrice }],
        adds: 0,
      };
    }
  }

  return { ...researchMetrics(trades), adds: totalAdds };
}

function walkForwardPyramidResearch(
  bars: ResearchBar[],
  cost: ResearchCost,
  multiplier: number,
  maxAdds: number
) {
  const trainBars = Math.floor(bars.length * 0.5);
  const testBars = Math.max(1, Math.floor(bars.length * 0.1));
  const folds = [];
  let trainEnd = trainBars;
  while (trainEnd < bars.length) {
    const testEnd = Math.min(trainEnd + testBars, bars.length);
    folds.push(
      runTf004PyramidResearch(
        bars.slice(0, testEnd),
        cost,
        multiplier,
        maxAdds,
        trainEnd,
        testEnd
      )
    );
    trainEnd = testEnd;
  }
  return {
    folds: folds.length,
    positiveFolds: folds.filter((fold) => fold.netR > 0).length,
    netRSum: Number(
      folds.reduce((sum, fold) => sum + fold.netR, 0).toFixed(3)
    ),
    worstFoldDrawdownR: Number(
      Math.max(...folds.map((fold) => fold.maxDrawdownR), 0).toFixed(3)
    ),
    trades: folds.reduce((sum, fold) => sum + fold.trades, 0),
    adds: folds.reduce((sum, fold) => sum + fold.adds, 0),
  };
}

async function tf004PyramidLab() {
  const definitions: Array<{ symbol: string; cost: ResearchCost }> = [
    {
      symbol: 'EURUSD=X',
      cost: {
        spread: 0.0002,
        commission: 0.00002,
        slippage: 0.00005,
        swapPerBar: 0.00001,
      },
    },
    {
      symbol: 'GBPUSD=X',
      cost: {
        spread: 0.0002,
        commission: 0.00002,
        slippage: 0.00005,
        swapPerBar: 0.00001,
      },
    },
    {
      symbol: 'USDJPY=X',
      cost: {
        spread: 0.02,
        commission: 0.002,
        slippage: 0.005,
        swapPerBar: 0.001,
      },
    },
  ];

  const result = await Promise.all(
    definitions.map(async ({ symbol, cost }) => {
      const bars = await yahooDailyBars(symbol);
      const split = Math.floor(bars.length * 0.7);
      const baseOos = runTf004PyramidResearch(
        bars,
        cost,
        1,
        0,
        split,
        bars.length
      );
      const addOos = runTf004PyramidResearch(
        bars,
        cost,
        1,
        1,
        split,
        bars.length
      );
      const baseWf = walkForwardPyramidResearch(bars, cost, 1, 0);
      const addWf = walkForwardPyramidResearch(bars, cost, 1, 1);
      return {
        symbol,
        base: { oos: baseOos, walkForward: baseWf },
        pyramid1: { oos: addOos, walkForward: addWf },
        delta: {
          oosNetR: Number((addOos.netR - baseOos.netR).toFixed(3)),
          oosMaxDrawdownR: Number(
            (addOos.maxDrawdownR - baseOos.maxDrawdownR).toFixed(3)
          ),
          wfNetR: Number((addWf.netRSum - baseWf.netRSum).toFixed(3)),
          wfWorstDrawdownR: Number(
            (addWf.worstFoldDrawdownR - baseWf.worstFoldDrawdownR).toFixed(3)
          ),
        },
      };
    })
  );

  const uniformlyImproved = result.every(
    (item) =>
      item.delta.oosNetR > 0 &&
      item.delta.wfNetR > 0 &&
      item.delta.oosMaxDrawdownR <= 0 &&
      item.delta.wfWorstDrawdownR <= 0
  );

  return {
    generatedAt: new Date().toISOString(),
    strategy: 'TF-004-TIME-SERIES-CHANNEL',
    experiment: 'winner-only one-add pyramiding',
    rule: {
      addOnlyWhenWinning: true,
      priorStopAtLeastBreakeven: true,
      sameDirectionMomentum: true,
      maxAdds: 1,
      normalization:
        'total leg PnL divided by original entry-to-stop risk; research metric only',
    },
    provenance: 'IMPLEMENTATION_DERIVATION_RESEARCH_ONLY',
    result,
    conclusion: uniformlyImproved
      ? 'RESEARCH_CANDIDATE_ONLY'
      : 'NO_PYRAMID_PROMOTION',
  };
}


type PaperForwardTrade = {
  direction: 'UP' | 'DOWN';
  entryTimestamp: number;
  exitTimestamp: number;
  r: number;
  exitReason: 'TRAILING_STOP';
};

type PaperForwardPosition = {
  direction: 'UP' | 'DOWN';
  entryBarTimestamp: number;
  entryPrice: number;
  stop: number;
  initialStop: number;
};

type PaperForwardRecord = {
  key: string;
  symbol: string;
  lastProcessed: number;
  position?: PaperForwardPosition;
  trades: PaperForwardTrade[];
  events: EventItem[];
};

type StoredPaperForwardRecord = PaperForwardRecord & { id: string };

function paperCost(symbol: string): ResearchCost {
  if (symbol === 'USDJPY=X') {
    return {
      spread: 0.02,
      commission: 0.002,
      slippage: 0.005,
      swapPerBar: 0.001,
    };
  }
  return {
    spread: 0.0002,
    commission: 0.00002,
    slippage: 0.00005,
    swapPerBar: 0.00001,
  };
}

async function listPaperStates() {
  const { items } = await db.list<PaperForwardRecord>('paper-forward', {
    limit: 10,
  });
  return items as StoredPaperForwardRecord[];
}

async function getPaperState(symbol: string) {
  const states = await listPaperStates();
  return states.find((item) => item.key === symbol);
}

async function createPaperState(
  symbol: string,
  lastProcessed: number
): Promise<StoredPaperForwardRecord> {
  const record: PaperForwardRecord = {
    key: symbol,
    symbol,
    lastProcessed,
    trades: [],
    events: [
      {
        at: new Date().toISOString(),
        result: 'WARMED',
        detail: 'Forward-only start; no historical trades backfilled',
      },
    ],
  };
  const [id] = await db.add('paper-forward', [record]);
  if (!id) throw new Error('PAPER_STATE_CREATE_FAILED_' + symbol);
  return { ...record, id };
}

async function savePaperState(state: StoredPaperForwardRecord) {
  const { id, ...record } = state;
  record.trades = record.trades.slice(-200);
  record.events = record.events.slice(-40);
  const [ok] = await db.update('paper-forward', [{ id, record }]);
  if (!ok) throw new Error('PAPER_STATE_UPDATE_FAILED_' + state.symbol);
}

function paperEvent(
  state: StoredPaperForwardRecord,
  result: string,
  detail?: string
) {
  state.events = [
    ...state.events,
    { at: new Date().toISOString(), result, detail },
  ].slice(-40);
}

function paperMetrics(state: StoredPaperForwardRecord) {
  return researchMetrics(
    state.trades.map((trade) => ({
      r: trade.r,
      exitDay: new Date(trade.exitTimestamp * 1000)
        .toISOString()
        .slice(0, 10),
    }))
  );
}

async function runPaperSymbol(symbol: string) {
  const bars = await yahooDailyBars(symbol);
  const latest = bars[bars.length - 1];
  let state = await getPaperState(symbol);
  if (!state) {
    state = await createPaperState(symbol, latest.timestamp);
    return {
      symbol,
      status: 'WARMED',
      lastProcessed: latest.timestamp,
      metrics: paperMetrics(state),
    };
  }

  const cost = paperCost(symbol);
  const pendingIndexes: number[] = [];
  for (let i = 0; i < bars.length; i += 1) {
    if (bars[i].timestamp > state.lastProcessed) pendingIndexes.push(i);
  }

  if (pendingIndexes.length === 0) {
    return {
      symbol,
      status: 'NO_NEW_CLOSED_BAR',
      lastProcessed: state.lastProcessed,
      position: state.position?.direction ?? null,
      metrics: paperMetrics(state),
    };
  }

  for (const index of pendingIndexes) {
    const bar = bars[index];
    let exitedThisBar = false;

    if (state.position && index > 20) {
      const priorChannel = bars.slice(index - 20, index);
      if (state.position.direction === 'UP') {
        state.position.stop = Math.max(
          state.position.stop,
          Math.min(...priorChannel.map((item) => item.low))
        );
      } else {
        state.position.stop = Math.min(
          state.position.stop,
          Math.max(...priorChannel.map((item) => item.high))
        );
      }

      const stopHit =
        state.position.direction === 'UP'
          ? bar.low <= state.position.stop
          : bar.high >= state.position.stop;
      if (stopHit) {
        const exitPrice =
          state.position.direction === 'UP'
            ? state.position.stop - cost.slippage
            : state.position.stop + cost.slippage;
        const executed =
          state.position.direction === 'UP'
            ? exitPrice - state.position.entryPrice
            : state.position.entryPrice - exitPrice;
        const entryIndex = bars.findIndex(
          (item) => item.timestamp === state.position!.entryBarTimestamp
        );
        const holdingBars =
          entryIndex >= 0 ? Math.max(0, index - entryIndex) : 0;
        const pnl =
          executed -
          cost.spread -
          cost.commission -
          cost.swapPerBar * holdingBars;
        const initialRisk = Math.abs(
          state.position.entryPrice - state.position.initialStop
        );
        const r = initialRisk > 0 ? pnl / initialRisk : 0;
        state.trades.push({
          direction: state.position.direction,
          entryTimestamp: state.position.entryBarTimestamp,
          exitTimestamp: bar.timestamp,
          r,
          exitReason: 'TRAILING_STOP',
        });
        paperEvent(
          state,
          'PAPER_EXIT',
          state.position.direction + ' ' + r.toFixed(3) + 'R'
        );
        state.position = undefined;
        exitedThisBar = true;
      }
    }

    if (!state.position && !exitedThisBar && index > 20 && index > 5) {
      const reference = bars[index - 21].close;
      if (reference !== bar.close) {
        const direction: 'UP' | 'DOWN' =
          bar.close > reference ? 'UP' : 'DOWN';
        const prior = bars.slice(index - 5, index);
        const stop =
          direction === 'UP'
            ? Math.min(...prior.map((item) => item.low))
            : Math.max(...prior.map((item) => item.high));
        const validStop =
          direction === 'UP' ? stop < bar.close : stop > bar.close;
        if (validStop) {
          const entryPrice =
            direction === 'UP'
              ? bar.close + cost.slippage
              : bar.close - cost.slippage;
          state.position = {
            direction,
            entryBarTimestamp: bar.timestamp,
            entryPrice,
            stop,
            initialStop: stop,
          };
          paperEvent(
            state,
            'PAPER_ENTRY',
            direction + ' @ ' + entryPrice.toFixed(6)
          );
        }
      }
    }

    state.lastProcessed = bar.timestamp;
  }

  await savePaperState(state);
  return {
    symbol,
    status: 'PROCESSED',
    processedBars: pendingIndexes.length,
    lastProcessed: state.lastProcessed,
    position: state.position?.direction ?? null,
    metrics: paperMetrics(state),
  };
}

async function runPaperForward() {
  const symbols = ['EURUSD=X', 'GBPUSD=X', 'USDJPY=X'];
  const results = [];
  for (const symbol of symbols) {
    try {
      results.push(await runPaperSymbol(symbol));
    } catch (cause) {
      results.push({
        symbol,
        status: 'ERROR',
        error: cause instanceof Error ? cause.message : String(cause),
      });
    }
  }
  return {
    generatedAt: new Date().toISOString(),
    mode: 'PAPER_ONLY',
    brokerOrders: false,
    pyramiding: false,
    results,
  };
}

async function paperForwardSnapshot() {
  const states = await listPaperStates();
  return {
    generatedAt: new Date().toISOString(),
    mode: 'PAPER_ONLY',
    brokerOrders: false,
    pyramiding: false,
    states: states.map((state) => ({
      symbol: state.symbol,
      lastProcessed: state.lastProcessed,
      lastProcessedIso: new Date(state.lastProcessed * 1000).toISOString(),
      position: state.position?.direction ?? null,
      metrics: paperMetrics(state),
      recentEvents: state.events.slice(-8).reverse(),
    })),
  };
}

export const paperForwardCronHandler = async () => {
  await runPaperForward();
  return { statusCode: 200 };
};

export const tradeCronHandler = async () => {
  await runTick();
  return { statusCode: 200 };
};

export const handler = router({
  'GET /api/_healthcheck': [
    async () => json({ ok: true, runtime: 'cloud', liveMoneyLocked: true }),
  ],
  'GET /api/research/tf004-risk': [
    async () => json(await tf004RiskLab()),
  ],
  'GET /api/research/tf004-pyramid': [
    async () => json(await tf004PyramidLab()),
  ],
  'GET /api/research/paper-forward': [
    async () => json(await paperForwardSnapshot()),
  ],
  'GET /api/research/paper-forward/run': [
    async () => {
      await runPaperForward();
      return json(await paperForwardSnapshot());
    },
  ],
  'GET /api/status': [
    async () => {
      const state = await loadState();
      const names = await secrets.listSecretNames();
      const required = [
        'METAAPI_TOKEN',
        'MT5_DEMO_LOGIN',
        'MT5_DEMO_PASSWORD',
        'MT5_DEMO_SERVER',
        'AI_TRADE_DEMO_ENABLE',
      ];
      return json({
        mode: 'DEMO_ONLY',
        liveMoneyLocked: true,
        strategy: state.strategy,
        symbol: state.symbol,
        timeframe: state.timeframe,
        exitMode: state.exitMode,
        engineStatus: state.engineStatus,
        brokerConnected: state.brokerConnected,
        lastTick: state.lastTick ?? null,
        lastAction: state.lastAction ?? null,
        lastError: state.lastError ?? null,
        credentials: configured(names, required),
        scheduler: 'Every 5 minutes',
        recentEvents: state.events.slice(-8).reverse(),
      });
    },
  ],
});

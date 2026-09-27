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
  maxPyramidAdds: 1,
  intents: [],
  events: [],
};

type StoredState = RuntimeState & { id: string };

async function loadState(): Promise<StoredState> {
  const { items } = await db.list<RuntimeState>('runtime', { limit: 10 });
  const existing = items.find(item => item.key === 'singleton');
  if (existing) {
    const state = existing as StoredState;
    if (!Number.isInteger(state.maxPyramidAdds) || state.maxPyramidAdds < 0) state.maxPyramidAdds = 1;
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

export const tradeCronHandler = async () => {
  await runTick();
  return { statusCode: 200 };
};

export const handler = router({
  'GET /api/_healthcheck': [
    async () => json({ ok: true, runtime: 'cloud', liveMoneyLocked: true }),
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

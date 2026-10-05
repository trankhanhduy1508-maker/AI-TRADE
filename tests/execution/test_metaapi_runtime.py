import asyncio
from datetime import datetime, timezone

from src.execution.metaapi_runtime import closed_bars, daily_pnl
from src.execution.metaapi_runtime import runtime_inputs_for_symbol
from types import SimpleNamespace


class Account:
    async def get_historical_candles(self, **kwargs):
        return [
            {
                "time": "2026-09-27T00:30:00+00:00",
                "open": 1.0,
                "high": 1.2,
                "low": .9,
                "close": 1.1,
                "tickVolume": 10,
            },
            {
                "time": "2026-09-27T00:45:00+00:00",
                "open": 1.1,
                "high": 1.3,
                "low": 1.0,
                "close": 1.2,
                "tickVolume": 12,
            },
            {
                "time": "2026-09-27T01:00:00+00:00",
                "open": 1.2,
                "high": 1.4,
                "low": 1.1,
                "close": 1.3,
                "tickVolume": 8,
            },
        ]


class Storage:
    def get_deals_by_time_range(self, start, end):
        return [
            {"magic": 260927, "profit": -4, "commission": -1, "swap": 0, "fee": 0},
            {"magic": 999, "profit": 100, "commission": 0, "swap": 0, "fee": 0},
        ]


class Connection:
    history_storage = Storage()


def test_metaapi_closed_bars_exclude_current_forming_candle():
    result = asyncio.run(
        closed_bars(
            Account(),
            symbol="EURUSD",
            timeframe="15m",
            count=3,
            now=datetime(2026, 9, 27, 1, 10, tzinfo=timezone.utc),
        )
    )
    assert len(result) == 2
    assert result[-1].timestamp.startswith("2026-09-27T00:45:00")


def test_metaapi_daily_pnl_only_counts_bot_magic():
    pnl = daily_pnl(
        Connection(),
        magic=260927,
        now=datetime(2026, 9, 27, 2, 0, tzinfo=timezone.utc),
    )
    assert pnl == -5


class QuoteAdapter:
    async def quote(self, symbol):
        return 1.1, 1.1001, '2026-10-05T10:00:00+00:00'

    async def symbol_contract(self, symbol):
        return SimpleNamespace(point=.00001)


def test_quote_does_not_prove_risk_approval_or_reconciliation():
    _, _, snapshot, _ = asyncio.run(runtime_inputs_for_symbol(
        QuoteAdapter(),symbol='EURUSD',own_open_positions=0,current_symbol_volume=0,
        daily_loss_value=0,max_tick_age_seconds=60,
        now=datetime(2026,10,5,10,0,tzinfo=timezone.utc)))
    assert snapshot.data_fresh
    assert not snapshot.risk_allowed
    assert not snapshot.reconciled
    assert not snapshot.state_known


def test_server_may_supply_independently_verified_control_state():
    _, _, snapshot, _ = asyncio.run(runtime_inputs_for_symbol(
        QuoteAdapter(),symbol='EURUSD',own_open_positions=0,current_symbol_volume=0,
        daily_loss_value=0,max_tick_age_seconds=60,risk_allowed=True,
        reconciled=True,state_known=True,
        now=datetime(2026,10,5,10,0,tzinfo=timezone.utc)))
    assert snapshot.risk_allowed and snapshot.reconciled and snapshot.state_known

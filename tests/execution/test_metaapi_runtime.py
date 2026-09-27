from pathlib import Path
from contextlib import contextmanager
import tempfile

from src.execution.metaapi_cloud import MetaApiCloudAdapter, MetaApiCloudConfig
from src.execution.metaapi_runtime import collect_metaapi_market_state
from tests.execution.test_metaapi_cloud import FakeTransport


@contextmanager
def ledger_path():
    handle = tempfile.NamedTemporaryFile(suffix=".sqlite", delete=False)
    path = Path(handle.name)
    handle.close()
    path.unlink(missing_ok=True)
    try:
        yield path
    finally:
        path.unlink(missing_ok=True)


def test_metaapi_runtime_builds_common_market_state():
    transport = FakeTransport()
    with ledger_path() as path:
        adapter = MetaApiCloudAdapter(
            MetaApiCloudConfig("account-1", "secret"),
            ledger_path=path,
            transport=transport,
        )
        market = collect_metaapi_market_state(
            adapter,
            symbol="EURUSD",
            timeframe="15m",
            count=10,
            magic=260926,
        )
        assert len(market.bars) == 1
        assert market.bid == 1.105
        assert round(market.spread_points, 6) == 2.0
        assert market.daily_pnl == -5.0
        adapter.close()

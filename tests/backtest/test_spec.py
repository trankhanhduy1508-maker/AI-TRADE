import json
import tempfile
from pathlib import Path

import pytest

from src.backtest.spec import load_strategy_spec, strategy_spec_from_dict


def test_strategy_spec_requires_signal_only_and_provenance():
    spec = strategy_spec_from_dict(
        {
            "strategy_id": "TF-001",
            "risk_mode": "SIGNAL_ONLY",
            "entry_timing": "CLOSE",
            "ambiguous_bar_policy": "STOP_FIRST",
            "provenance": {"hypothesis": "VERIFIED_FROM_AUTHOR"},
        }
    )

    assert spec.strategy_id == "TF-001"
    assert spec.risk_mode == "SIGNAL_ONLY"
    assert spec.provenance["hypothesis"] == "VERIFIED_FROM_AUTHOR"


def test_strategy_spec_rejects_capital_risk_or_missing_provenance():
    with pytest.raises(ValueError, match="SIGNAL_ONLY"):
        strategy_spec_from_dict(
            {"strategy_id": "bad", "risk_mode": "CAPITAL_RISK"}
        )

    with pytest.raises(ValueError, match="provenance"):
        strategy_spec_from_dict(
            {"strategy_id": "bad", "risk_mode": "SIGNAL_ONLY"}
        )


def test_strategy_spec_loads_json_file():
    path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", dir=".", delete=False, encoding="utf-8"
        ) as handle:
            path = Path(handle.name)
            json.dump(
                {
                    "strategy_id": "TF-001",
                    "risk_mode": "SIGNAL_ONLY",
                    "provenance": {"entry": "IMPLEMENTATION_DERIVATION"},
                },
                handle,
            )

        spec = load_strategy_spec(path)

        assert spec.entry_timing == "CLOSE"
        assert spec.score_threshold == 80.0
    finally:
        if path is not None:
            path.unlink(missing_ok=True)


def test_strategy_spec_supports_explicit_signal_model_and_lookback():
    spec = strategy_spec_from_dict(
        {
            "strategy_id": "TF-003",
            "risk_mode": "SIGNAL_ONLY",
            "signal_model": "TIME_SERIES_MOMENTUM",
            "lookback_bars": 20,
            "provenance": {"signal": "VERIFIED_FROM_PRIMARY_RESEARCH"},
        }
    )

    assert spec.signal_model == "TIME_SERIES_MOMENTUM"
    assert spec.lookback_bars == 20


def test_strategy_spec_supports_explicit_channel_trailing_exit():
    spec = strategy_spec_from_dict(
        {
            "strategy_id": "TF-004",
            "risk_mode": "SIGNAL_ONLY",
            "exit_model": "CHANNEL_TRAILING",
            "exit_lookback_bars": 20,
            "provenance": {"exit": "IMPLEMENTATION_DERIVATION"},
        }
    )

    assert spec.exit_model == "CHANNEL_TRAILING"
    assert spec.exit_lookback_bars == 20

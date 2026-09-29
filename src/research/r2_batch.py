"""Offline R2 batch runner. Metadata summaries only; no broker/network/order APIs.

Source rights are caller assertions, never independently verified by this code.
Do not copy licensed raw prices into output or public GitHub.
"""
from __future__ import annotations

from pathlib import Path
from .r2_csv import load_normalized_ohlc
from .r2_walkforward import Study, run_walkforward

MAX_CELLS = 56
FIELDS = frozenset({"cell", "symbol", "timeframe", "source_kind",
                    "csv_path", "research_rights_confirmed", "session",
                    "allow_short", "assumed_round_trip_cost_price"})


def run_batch(entries: list[dict], *, as_of_utc: int) -> dict:
    if not isinstance(entries, list) or not 1 <= len(entries) <= MAX_CELLS:
        raise ValueError('INVALID_CATALOG_SIZE')
    seen = set()
    report = {}
    for entry in entries:
        if not isinstance(entry, dict) or set(entry) != FIELDS:
            raise ValueError('INVALID_CATALOG_SCHEMA')
        cell = entry['cell']
        if not isinstance(cell, str) or not cell or cell in seen:
            raise ValueError('DUPLICATE_OR_EMPTY_CELL')
        seen.add(cell)
        result = dict(symbol=entry['symbol'], timeframe=entry['timeframe'],
                      source_kind=entry['source_kind'], edge_status='UNPROVEN',
                      orders_sent=0, independent_forward_trades=0)
        if entry['research_rights_confirmed'] is not True:
            result['status'] = 'RESEARCH_RIGHTS_NOT_CONFIRMED'
        elif not isinstance(entry['csv_path'], str) or not entry['csv_path']:
            result['status'] = 'DATA_UNAVAILABLE_NO_LOCAL_SOURCE'
        elif not Path(entry['csv_path']).is_file():
            result['status'] = 'DATA_UNAVAILABLE_FILE_NOT_FOUND'
        else:
            try:
                bars, raw_sha = load_normalized_ohlc(entry['csv_path'])
                study = Study(symbol=entry['symbol'], timeframe=entry['timeframe'],
                              source_kind=entry['source_kind'], source_sha256=raw_sha,
                              exposure='HISTORICAL_REUSED',
                              session=entry['session'], allow_short=entry['allow_short'],
                              assumed_round_trip_cost_price=entry['assumed_round_trip_cost_price'])
                research = run_walkforward(bars, study=study, as_of_utc=as_of_utc)
                eps = research.pop('episodes')
                total = sum(e['closed_trades'] for e in eps)
                sum_r = sum(e['realized_r'] for e in eps)
                research['episode_count'] = len(eps)
                research['closed_trades_in_isolated_episodes'] = total
                research['mean_closed_trade_r'] = sum_r/total if total else None
                research['episodes_with_open_position'] = sum(e['open_position_at_boundary'] for e in eps)
                research['episodes'] = eps
                result.update(research)
                result['status'] = 'HISTORICAL_REUSED_DESCRIPTIVE_ONLY'
                result['research_rights_independently_verified'] = False
                result['source_snapshot_durable'] = False
            except (ValueError, OSError) as exc:
                result['status'] = 'DATA_REJECTED_OR_INSUFFICIENT'
                result['reason'] = str(exc)
        report[cell] = result
    return {"status": "RESEARCH_ONLY_NO_INDEPENDENT_EDGE_CLAIM",
            "cell_count": len(report),
            "cells_with_historical_exploratory_results": sum(
                x['status'] == 'HISTORICAL_REUSED_DESCRIPTIVE_ONLY'
                for x in report.values()),
            "cells": report, "orders_sent": 0, "edge_status": "UNPROVEN"}

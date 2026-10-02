"""Strict local input for exploratory R2. Does not fetch or publish raw prices."""
from __future__ import annotations
import csv
import hashlib
import io
from pathlib import Path
from .r2_walkforward import Bar

COLUMNS = ('open_ts_utc', 'open', 'high', 'low', 'close')
MAX_CSV_BYTES = 50_000_000
MAX_ROWS = 200_000


def load_normalized_ohlc(path: str | Path) -> tuple[list[Bar], str]:
    raw = Path(path).read_bytes()
    if not 0 < len(raw) <= MAX_CSV_BYTES or b'\x00' in raw:
        raise ValueError('INVALID_RAW_CSV_SIZE_OR_BINARY')
    digest = hashlib.sha256(raw).hexdigest()
    try:
        text = raw.decode('utf-8-sig')
        reader = csv.DictReader(io.StringIO(text, newline=''), strict=True)
        if reader.fieldnames is None or tuple(reader.fieldnames) != COLUMNS:
            raise ValueError('REQUIRES_NORMALIZED_UTC_OHLC_COLUMNS')
        bars = []
        for i, line in enumerate(reader, 2):
            if i > MAX_ROWS + 1:
                raise ValueError('TOO_MANY_ROWS')
            if None in line or any(line[c] is None for c in COLUMNS):
                raise ValueError(f'UNEXPECTED_CSV_FIELD_LINE_{i}')
            t = line['open_ts_utc']
            if not t.isascii() or not t.isdecimal():
                raise ValueError(f'UTC_EPOCH_REQUIRED_LINE_{i}')
            bars.append(Bar(int(t), *(float(line[c]) for c in COLUMNS[1:])))
    except (UnicodeDecodeError, csv.Error, OverflowError) as e:
        raise ValueError('INVALID_CSV_ENCODING_OR_FORMAT') from e
    return bars, digest

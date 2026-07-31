"""CSV loader for OHLCV data.

Loads market data from CSV files (DATA_REQUIREMENTS.md section 1, BACKTEST_ENGINE.md step 1).
Accepts flexible header casing and returns list[Bar].
"""

import csv
from src.rule_engine.types import Bar


def load_csv(path: str) -> list[Bar]:
    """Load OHLCV data from CSV file and return list[Bar].

    CSV must have columns: timestamp, open, high, low, close, volume
    (column names are case-insensitive, normalized to lowercase).

    Args:
        path: Path to CSV file

    Returns:
        list[Bar]: List of closed bars (closed=True by default for historical data)

    Raises:
        ValueError: If file is empty, columns missing, or read error
    """
    bars = []
    required_cols = {"timestamp", "open", "high", "low", "close", "volume"}

    try:
        with open(path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)

            if reader.fieldnames is None:
                raise ValueError(f"CSV file {path} is empty or has no header")

            # Normalize header to lowercase
            normalized_header = {col.lower(): col for col in reader.fieldnames}

            # Check all required columns exist
            missing = required_cols - set(normalized_header.keys())
            if missing:
                raise ValueError(
                    f"CSV file {path} missing required columns: {missing}. "
                    f"Found: {set(normalized_header.keys())}"
                )

            # Read data rows
            for row_idx, row in enumerate(reader, start=2):  # start=2 (header is row 1)
                try:
                    # Get values using normalized column names
                    bar = Bar(
                        timestamp=row[normalized_header["timestamp"]].strip(),
                        open=float(row[normalized_header["open"]]),
                        high=float(row[normalized_header["high"]]),
                        low=float(row[normalized_header["low"]]),
                        close=float(row[normalized_header["close"]]),
                        volume=float(row[normalized_header["volume"]]),
                        closed=True  # Historical data is always closed
                    )
                    bars.append(bar)
                except (KeyError, ValueError) as e:
                    raise ValueError(
                        f"CSV file {path} row {row_idx}: "
                        f"Failed to parse. Error: {e}"
                    )

        if not bars:
            raise ValueError(f"CSV file {path} has no data rows (only header)")

        return bars

    except FileNotFoundError:
        raise ValueError(f"CSV file not found: {path}")
    except Exception as e:
        raise ValueError(f"Error reading CSV file {path}: {e}")

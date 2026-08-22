"""Explicit price-unit cost assumptions for research backtests."""

from dataclasses import dataclass


@dataclass(frozen=True)
class CostModel:
    """Non-capital cost proxy; values are in instrument price units."""

    profile_id: str
    spread_price: float
    commission_price: float
    slippage_price: float
    swap_price_per_bar: float

    def __post_init__(self) -> None:
        if not self.profile_id.strip():
            raise ValueError("cost profile_id is required")
        if any(
            value < 0
            for value in (
                self.spread_price,
                self.commission_price,
                self.slippage_price,
                self.swap_price_per_bar,
            )
        ):
            raise ValueError("cost assumptions cannot be negative")

    @classmethod
    def zero(cls) -> "CostModel":
        """Return a zero-cost fixture model for deterministic unit tests."""

        return cls("zero-test-costs", 0.0, 0.0, 0.0, 0.0)

    def total_explicit(self, holding_bars: int) -> float:
        if holding_bars < 0:
            raise ValueError("holding_bars cannot be negative")
        return (
            self.spread_price
            + self.commission_price
            + self.swap_price_per_bar * holding_bars
        )

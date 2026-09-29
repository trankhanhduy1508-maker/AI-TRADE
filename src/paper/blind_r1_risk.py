"""Research-only R1 portfolio-risk sizing preflight. No broker or order APIs.

This function computes hypothetical conservative lot caps from EXPLICIT input.
Boolean audit attestations are supplied by an external authorised reviewer;
a caller setting them True is NOT evidence of a real venue audit.
No function sends an order or changes a trading account.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from decimal import Decimal, ROUND_FLOOR


MAX_RISK_PER_POSITION = Decimal("0.0025")
MAX_COMBINED_INITIAL_RISK = Decimal("0.01")
MAX_QUOTE_AGE_SECONDS = 30


@dataclass(frozen=True)
class RiskInputs:
    symbol: str
    mode: str
    direction: str
    product_type: str
    current_equity_account: float
    existing_initial_risk_account: float
    entry_price: float
    stop_price: float
    contract_multiplier: float
    fx_quote_to_account: float
    lot_step: float
    min_lot: float
    max_lot: float
    round_trip_fee_per_lot_account: float
    adverse_slippage_price_one_side: float
    round_trip_spread_price: float
    financing_buffer_per_lot_account: float
    margin_per_lot_account: float
    available_margin_account: float
    quote_timestamp_utc: int
    decision_timestamp_utc: int
    provenance_id: str
    # These flags are untrusted caller statements until the source is audited.
    feed_audited: bool
    execution_costs_audited: bool
    contract_audited: bool
    fx_conversion_audited: bool
    margin_audited: bool
    authorization_verified: bool
    kill_switch_off: bool
    short_allowed: bool
    protective_stop_available: bool


def _d(v: float, label: str, *, allow_zero: bool = False) -> Decimal:
    if isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v):
        raise ValueError(label+"_INVALID")
    if v < 0 or (v == 0 and not allow_zero):
        raise ValueError(label+"_INVALID")
    return Decimal(str(v))


def risk_preflight(value: RiskInputs) -> dict:
    """Return a PAPER-ONLY proposal, fail closed on missing/unsafe inputs."""
    if not isinstance(value,RiskInputs):
        raise TypeError("RISK_INPUTS_REQUIRED")

    def reject(code: str) -> dict:
        return {"status":"REJECTED","reason":code,"units":0.0,
                "paper_only":True,"orders_sent":0,
                "verified_real_world_inputs":False}

    if value.mode != "RESEARCH_PAPER_ONLY":
        return reject("MODE_FORBIDDEN")
    if not isinstance(value.symbol,str) or not value.symbol.strip() or (
            not isinstance(value.provenance_id,str)
            or not value.provenance_id.strip()):
        return reject("MISSING_SYMBOL_OR_PROVENANCE")
    if value.direction not in ("LONG","SHORT"):
        return reject("INVALID_DIRECTION")
    if value.product_type in ("CASH_INDEX","NONEXECUTABLE_PROXY","INDICATIVE_FX"):
        return reject("PRODUCT_NOT_EXECUTABLE")
    if value.product_type not in ("SPOT","FX", "FUTURES", "BROKER_CFD", "STOCK"):
        return reject("PRODUCT_TYPE_UNVERIFIED")
    if value.direction=="SHORT" and value.short_allowed is not True:
        return reject("SHORT_VEHICLE_NOT_VERIFIED")
    if not all(flag is True for flag in (
                value.feed_audited,value.execution_costs_audited,
                value.contract_audited,value.fx_conversion_audited,
                value.margin_audited,value.authorization_verified,
                value.kill_switch_off,value.protective_stop_available)):
        return reject("UNVERIFIED_SOURCE_COST_RISK_AUTH_OR_KILL_SWITCH")
    if type(value.quote_timestamp_utc) is not int or (
            type(value.decision_timestamp_utc) is not int):
        return reject("INVALID_EVENT_CLOCK")
    age=value.decision_timestamp_utc-value.quote_timestamp_utc
    if age<0 or age>MAX_QUOTE_AGE_SECONDS:
        return reject("QUOTE_STALE_OR_FUTURE")
    try:
        equity=_d(value.current_equity_account,"EQUITY")
        existing=_d(value.existing_initial_risk_account,"EXISTING_RISK",
                    allow_zero=True)
        entry=_d(value.entry_price,"ENTRY")
        stop=_d(value.stop_price,"STOP")
        mult=_d(value.contract_multiplier,"MULTIPLIER")
        fx=_d(value.fx_quote_to_account,"FX_CONVERSION")
        step=_d(value.lot_step,"LOT_STEP")
        minimum=_d(value.min_lot,"MIN_LOT")
        maximum=_d(value.max_lot,"MAX_LOT")
        fees=_d(value.round_trip_fee_per_lot_account,"FEE",
                allow_zero=True)
        slip=_d(value.adverse_slippage_price_one_side,"SLIPPAGE",
                allow_zero=True)
        spread=_d(value.round_trip_spread_price,"SPREAD",
                  allow_zero=True)
        finance=_d(value.financing_buffer_per_lot_account,"FINANCE",
                   allow_zero=True)
        margin=_d(value.margin_per_lot_account,"MARGIN")
        available=_d(value.available_margin_account,"AVAILABLE_MARGIN",
                     allow_zero=True)
    except ValueError as exc:
        return reject(str(exc))
    if minimum>maximum or minimum%step!=0 or maximum<step:
        return reject("INVALID_LOT_GRANULARITY")
    if existing>=equity*MAX_COMBINED_INITIAL_RISK:
        return reject("PORTFOLIO_RISK_CAP_REACHED")
    if value.direction=="LONG" and stop>=entry:
        return reject("INVALID_LONG_STOP")
    if value.direction=="SHORT" and stop<=entry:
        return reject("INVALID_SHORT_STOP")
    # Reserve round-trip all-in known cost + two-sided slippage and a
    # separately audited financing buffer, beyond initial stop distance.
    unit_loss=(abs(entry-stop)+spread+2*slip)*mult*fx+fees+finance
    if unit_loss<=0:
        return reject("NONPOSITIVE_PER_LOT_LOSS")
    available_risk=min(equity*MAX_RISK_PER_POSITION,
                       equity*MAX_COMBINED_INITIAL_RISK-existing)
    if available_risk<=0:
        return reject("PORTFOLIO_RISK_CAP_REACHED")
    by_risk=available_risk/unit_loss
    by_margin=available/margin
    cap=min(by_risk,by_margin,maximum)
    units=(cap/step).to_integral_value(rounding=ROUND_FLOOR)*step
    if units<minimum:
        return reject("MIN_LOT_EXCEEDS_RISK_OR_MARGIN_BUDGET")
    risk=units*unit_loss
    if risk>available_risk or units*margin>available:
        return reject("RISK_OR_MARGIN_POSTROUND_BREACH")
    return {
        "status":"ELIGIBLE_SYNTHETIC_PAPER_PREFLIGHT",
        "symbol":value.symbol,
        "direction":value.direction,
        "units":float(units),
        "initial_stop":float(stop),
        "max_modelled_loss_account":float(risk),
        "current_equity_account":float(equity),
        "per_position_risk_fraction":float(risk/equity),
        "combined_nominal_risk_fraction":float((existing+risk)/equity),
        "reserved_margin_account":float(units*margin),
        "costs_included":"SPREAD_FEES_2X_ADVERSE_SLIPPAGE_FINANCING_BUFFER",
        "gap_tail_risk":"LOSS_CAN_EXCEED_STOP_BUDGET_ON_GAP",
        "paper_only":True,
        "orders_sent":0,
        # Externally supplied booleans are not provider-side evidence.
        "verified_real_world_inputs":False,
        "provenance_id":value.provenance_id,
    }

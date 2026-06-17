# ─────────────────────────────────────────────
#  FVG DETECTOR — Fair Value Gap Engine
# ─────────────────────────────────────────────
#
#  BULLISH FVG:
#    C1.low  >  C3.high  →  gap between them = imbalance zone
#    Price expected to retrace INTO this zone and bounce UP
#
#  BEARISH FVG:
#    C1.high <  C3.low   →  gap between them = imbalance zone
#    Price expected to retrace INTO this zone and bounce DOWN
#
#  C1 = candle[i-2], C2 = candle[i-1], C3 = candle[i]
# ─────────────────────────────────────────────

import pandas as pd
import logging
from dataclasses import dataclass, field
from typing import Literal
from utils.mt5_utils import get_pip_size
from config.settings import MIN_FVG_PIPS, MAX_FVG_AGE_BARS

logger = logging.getLogger(__name__)


@dataclass
class FVG:
    symbol:     str
    timeframe:  str
    direction:  Literal["bullish", "bearish"]
    top:        float          # Upper boundary of the gap
    bottom:     float          # Lower boundary of the gap
    midpoint:   float          # Mid of the gap
    bar_index:  int            # Bar where FVG was formed (C3 index)
    formed_at:  pd.Timestamp
    filled:     bool = False   # True once price fully closes through gap
    active:     bool = True    # False once expired or filled

    def size_pips(self, pip_size: float) -> float:
        return round((self.top - self.bottom) / pip_size, 1)


def detect_fvgs(df: pd.DataFrame, symbol: str, timeframe: str) -> list[FVG]:
    """
    Scan a DataFrame of candles and return all valid FVGs.
    Only returns FVGs within MAX_FVG_AGE_BARS of the latest candle.
    """
    pip_size = get_pip_size(symbol)
    min_gap  = MIN_FVG_PIPS * pip_size
    fvgs     = []
    latest   = len(df) - 1

    # Need at least 3 candles
    for i in range(2, len(df)):
        age = latest - i
        if age > MAX_FVG_AGE_BARS:
            continue                      # Too old, skip

        c1 = df.iloc[i - 2]
        c3 = df.iloc[i]

        # ── Bullish FVG ──────────────────────
        # Gap exists between C1 low and C3 high (C1.low > C3.high)
        if c1["Low"] > c3["High"]:
            gap_size = c1["Low"] - c3["High"]
            if gap_size >= min_gap:
                fvg = FVG(
                    symbol    = symbol,
                    timeframe = timeframe,
                    direction = "bullish",
                    top       = c1["Low"],
                    bottom    = c3["High"],
                    midpoint  = (c1["Low"] + c3["High"]) / 2,
                    bar_index = i,
                    formed_at = df.iloc[i]["time"],
                )
                fvgs.append(fvg)
                logger.debug(f"Bullish FVG [{symbol} {timeframe}] "
                             f"{fvg.bottom:.5f}–{fvg.top:.5f} "
                             f"({fvg.size_pips(pip_size)} pips) @ bar {i}")

        # ── Bearish FVG ──────────────────────
        # Gap exists between C3 low and C1 high (C3.low > C1.high)
        elif c3["Low"] > c1["High"]:
            gap_size = c3["Low"] - c1["High"]
            if gap_size >= min_gap:
                fvg = FVG(
                    symbol    = symbol,
                    timeframe = timeframe,
                    direction = "bearish",
                    top       = c3["Low"],
                    bottom    = c1["High"],
                    midpoint  = (c3["Low"] + c1["High"]) / 2,
                    bar_index = i,
                    formed_at = df.iloc[i]["time"],
                )
                fvgs.append(fvg)
                logger.debug(f"Bearish FVG [{symbol} {timeframe}] "
                             f"{fvg.bottom:.5f}–{fvg.top:.5f} "
                             f"({fvg.size_pips(pip_size)} pips) @ bar {i}")

    return fvgs


def is_price_in_fvg(fvg: FVG, current_price: float, pip_size: float,
                    tolerance_pips: float = 1.0) -> bool:
    """
    Check whether the current price has retraced INTO the FVG zone.
    Adds a small tolerance buffer so a wick touch counts.
    """
    tol = tolerance_pips * pip_size
    return (fvg.bottom - tol) <= current_price <= (fvg.top + tol)


def is_fvg_filled(fvg: FVG, df: pd.DataFrame) -> bool:
    """
    An FVG is 'filled' (invalidated) when a candle CLOSES fully through it:
      Bullish FVG filled → close below fvg.bottom
      Bearish FVG filled → close above fvg.top
    """
    recent = df.iloc[fvg.bar_index:]
    if fvg.direction == "bullish":
        return any(recent["Close"] < fvg.bottom)
    else:
        return any(recent["Close"] > fvg.top)
# ─────────────────────────────────────────────
#  TREND FILTER — Higher Timeframe Bias (H4)
# ─────────────────────────────────────────────
#
#  Uses H4 candles to determine trend direction.
#  Method: 50 EMA slope + last 3 swing structure
#
#  BULLISH BIAS  → price above 50 EMA + higher highs/lows
#  BEARISH BIAS  → price below 50 EMA + lower highs/lows
#  NEUTRAL       → mixed signals → NO TRADE
# ─────────────────────────────────────────────

import pandas as pd
import logging
from typing import Literal
from utils.mt5_utils import get_candles
from config.settings import HTF_TIMEFRAME

logger = logging.getLogger(__name__)

Bias = Literal["bullish", "bearish", "neutral"]


def get_ema(series: pd.Series, period: int) -> pd.Series:
    return series.ewm(span=period, adjust=False).mean()


def get_htf_bias(symbol: str) -> Bias:
    """
    Determine the H4 trend bias for a symbol.
    Returns 'bullish', 'bearish', or 'neutral'.
    """
    df = get_candles(symbol, HTF_TIMEFRAME, count=100)
    if df is None or len(df) < 60:
        logger.warning(f"Not enough H4 data for {symbol}, defaulting neutral")
        return "neutral"

    # ── EMA signal ───────────────────────────
    ema50       = get_ema(df["Close"], 50)
    last_close  = df["Close"].iloc[-1]
    last_ema    = ema50.iloc[-1]
    ema_bullish = last_close > last_ema
    ema_bearish = last_close < last_ema

    # ── Swing structure (last 3 highs & lows) ─
    highs = df["High"].iloc[-15:].values
    lows  = df["Low"].iloc[-15:].values

    # Find local swing highs (higher than neighbors)
    swing_highs = [highs[i] for i in range(1, len(highs) - 1)
                   if highs[i] > highs[i-1] and highs[i] > highs[i+1]]
    swing_lows  = [lows[i]  for i in range(1, len(lows) - 1)
                   if lows[i]  < lows[i-1]  and lows[i]  < lows[i+1]]

    hh = (len(swing_highs) >= 2 and swing_highs[-1] > swing_highs[-2])
    hl = (len(swing_lows)  >= 2 and swing_lows[-1]  > swing_lows[-2])
    lh = (len(swing_highs) >= 2 and swing_highs[-1] < swing_highs[-2])
    ll = (len(swing_lows)  >= 2 and swing_lows[-1]  < swing_lows[-2])

    structure_bullish = hh and hl
    structure_bearish = lh and ll

    # ── Combine signals ───────────────────────
    if ema_bullish and structure_bullish:
        bias = "bullish"
    elif ema_bearish and structure_bearish:
        bias = "bearish"
    elif ema_bullish and not structure_bearish:
        bias = "bullish"   # EMA wins if structure is mixed
    elif ema_bearish and not structure_bullish:
        bias = "bearish"
    else:
        bias = "neutral"

    logger.info(f"HTF Bias [{symbol} {HTF_TIMEFRAME}]: {bias.upper()} "
                f"(EMA={'↑' if ema_bullish else '↓'}, "
                f"Structure={'HH/HL' if structure_bullish else 'LH/LL' if structure_bearish else 'Mixed'})")
    return bias


def fvg_matches_bias(fvg_direction: str, bias: Bias) -> bool:
    """Only trade if FVG direction aligns with HTF bias."""
    if bias == "neutral":
        return False
    return fvg_direction == bias
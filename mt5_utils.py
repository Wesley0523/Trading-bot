# ─────────────────────────────────────────────
#  MT5 UTILITIES — Connection & Data Fetching
# ─────────────────────────────────────────────

import MetaTrader5 as mt5
import pandas as pd
import logging
from datetime import datetime
from config.settings import MT5_LOGIN, MT5_PASSWORD, MT5_SERVER

logger = logging.getLogger(__name__)

# ── Timeframe map ────────────────────────────
TF_MAP = {
    "M15": mt5.TIMEFRAME_M15,
    "M30": mt5.TIMEFRAME_M30,
    "H1":  mt5.TIMEFRAME_H1,
    "H4":  mt5.TIMEFRAME_H4,
    "D1":  mt5.TIMEFRAME_D1,
}


def connect() -> bool:
    """Initialize and log in to MT5."""
    if not mt5.initialize():
        logger.error(f"MT5 initialize() failed: {mt5.last_error()}")
        return False

    authorized = mt5.login(MT5_LOGIN, password=MT5_PASSWORD, server=MT5_SERVER)
    if not authorized:
        logger.error(f"MT5 login failed: {mt5.last_error()}")
        mt5.shutdown()
        return False

    info = mt5.account_info()
    logger.info(f"Connected → {info.name} | Balance: {info.balance} {info.currency}")
    return True


def disconnect():
    mt5.shutdown()
    logger.info("MT5 disconnected.")


def get_candles(symbol: str, timeframe: str, count: int = 100) -> pd.DataFrame | None:
    """Fetch OHLCV candles as a DataFrame."""
    tf = TF_MAP.get(timeframe)
    if tf is None:
        logger.error(f"Unknown timeframe: {timeframe}")
        return None

    rates = mt5.copy_rates_from_pos(symbol, tf, 0, count)
    if rates is None or len(rates) == 0:
        logger.warning(f"No data for {symbol} {timeframe}")
        return None

    df = pd.DataFrame(rates)
    df["time"] = pd.to_datetime(df["time"], unit="s")
    df.rename(columns={"open": "Open", "high": "High",
                        "low": "Low", "close": "Close",
                        "tick_volume": "Volume"}, inplace=True)
    return df[["time", "Open", "High", "Low", "Close", "Volume"]]


def get_pip_size(symbol: str) -> float:
    """Return pip size for a symbol (handles JPY pairs & Gold)."""
    info = mt5.symbol_info(symbol)
    if info is None:
        return 0.0001
    digits = info.digits
    if digits == 3 or digits == 5:
        return 10 ** -(digits - 1)   # 0.001 for JPY, 0.0001 for others
    return 10 ** -digits


def get_account_balance() -> float:
    info = mt5.account_info()
    return info.balance if info else 0.0


def get_open_positions(symbol: str = None, magic: int = None):
    """Return list of open positions, optionally filtered."""
    positions = mt5.positions_get()
    if positions is None:
        return []
    result = list(positions)
    if symbol:
        result = [p for p in result if p.symbol == symbol]
    if magic:
        result = [p for p in result if p.magic == magic]
    return result
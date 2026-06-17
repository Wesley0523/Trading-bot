# ─────────────────────────────────────────────
#  FVG BOT — CONFIGURATION
# ─────────────────────────────────────────────

# ── Exness MT5 Credentials ──────────────────
MT5_LOGIN    = 0          # Replace with your Exness account number
MT5_PASSWORD = ""         # Replace with your MT5 password
MT5_SERVER   = "Exness-MT5Real"  # Check exact server name in MT5

# ── Pairs to Trade ──────────────────────────
SYMBOLS = [
    "EURUSD", "GBPUSD", "XAUUSD",
    "EURGBP", "USDJPY", "GBPJPY", "NZDUSD"
]

# ── Timeframes ───────────────────────────────
# Execution TFs (FVG detected and traded here)
EXECUTION_TIMEFRAMES = ["M15", "M30", "H1"]

# Higher timeframe for trend filter
HTF_TIMEFRAME = "H4"

# ── Risk Management ──────────────────────────
RISK_PERCENT       = 1.0    # % of balance risked per trade
PARTIAL_CLOSE_PCT  = 0.50   # 50% closed at TP1
TP1_RR             = 2.0    # 1:2 Risk/Reward for TP1
TP2_RR             = 2.5    # 1:2.5 Risk/Reward for TP2
MOVE_SL_BREAKEVEN  = True   # Move SL to entry after TP1 hit

# ── FVG Filters ──────────────────────────────
MIN_FVG_PIPS       = 5      # Minimum gap size in pips
MAX_FVG_AGE_BARS   = 10     # Ignore FVGs older than N candles
USE_HTF_TREND      = True   # Only trade in HTF trend direction

# ── Execution ────────────────────────────────
MAGIC_NUMBER       = 20240101   # Unique ID for this bot's trades
SLIPPAGE           = 10          # Max slippage in points
CHECK_INTERVAL_SEC = 15          # Seconds between each scan cycle

# ── Logging ──────────────────────────────────
LOG_FILE = "fvg_bot.log"
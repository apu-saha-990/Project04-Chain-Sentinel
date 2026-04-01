"""
chainsentinel/config/settings.py
All configuration constants. Change values here only — never in core logic.
"""

from pathlib import Path

# ── Paths ─────────────────────────────────────────────────────────────────────
ROOT_DIR       = Path(__file__).parent.parent
CONFIG_DIR     = ROOT_DIR / "config"
REPORTS_DIR    = ROOT_DIR / "data" / "reports"
TRACES_DIR     = ROOT_DIR / "data" / "traces"
WALLETS_FILE   = CONFIG_DIR / "wallets.json"

# ── Monitoring ────────────────────────────────────────────────────────────────
WINDOW_HOURS   = 48          # How far back each run looks
MAX_REPORTS    = 10          # Max report files to keep (oldest pruned)
SPIKE_USD      = 50_000      # Single inbound tx threshold for spike alert
REQUEST_DELAY  = 0.26        # Seconds between Etherscan calls (~4 req/s)

# ── Contracts ─────────────────────────────────────────────────────────────────
USDT_CONTRACT  = "0xdac17f958d2ee523a2206206994597c13d831ec7"

# ── Tracer ────────────────────────────────────────────────────────────────────
MAX_HOPS                 = 7
EXCHANGE_TX_THRESHOLD    = 5_000    # tx count above this = likely exchange
EXCHANGE_VOL_THRESHOLD   = 1_000_000

# ── APIs ──────────────────────────────────────────────────────────────────────
ETHERSCAN_BASE = "https://api.etherscan.io/v2/api"
COINGECKO_URL  = "https://api.coingecko.com/api/v3/simple/price?ids=ethereum&vs_currencies=usd"

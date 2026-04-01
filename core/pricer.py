"""
chainsentinel/core/pricer.py
ETH spot price feed — isolated so the source can be swapped without
touching any analysis logic.
"""

import logging
import requests
from config.settings import COINGECKO_URL

log = logging.getLogger("chainsentinel.pricer")


def get_eth_usd() -> float:
    """Fetch current ETH/USD spot price from CoinGecko. Returns 0.0 on failure."""
    try:
        r = requests.get(COINGECKO_URL, timeout=10)
        r.raise_for_status()
        price = float(r.json()["ethereum"]["usd"])
        log.info("ETH spot: $%.2f", price)
        return price
    except Exception as e:
        log.error("ETH price fetch failed: %s — defaulting to $0", e)
        return 0.0

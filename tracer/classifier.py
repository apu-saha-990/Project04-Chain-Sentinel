"""
chainsentinel/tracer/classifier.py
Classifies addresses as exchange, mixer, origin, or regular.
Uses the exchange registry first, then heuristics.
"""

from chainsentinel.config.exchanges import lookup
from chainsentinel.config.settings import EXCHANGE_TX_THRESHOLD
from chainsentinel.core.fetcher import get_contract_name


def classify_address(address: str, tx_count: int, eth_balance: float) -> dict:
    """
    Returns a classification dict:
      type:       KNOWN_EXCHANGE | MIXER | LIKELY_EXCHANGE | REGULAR
      label:      human-readable name or None
      stop_trace: whether to stop tracing at this address
    """
    # Check known exchange/mixer registry first
    known = lookup(address)
    if known:
        return known

    # Heuristic — very high tx count = likely exchange hot wallet
    if tx_count > EXCHANGE_TX_THRESHOLD:
        etherscan_label = get_contract_name(address)
        label = (etherscan_label
                 or f"LIKELY EXCHANGE HOT WALLET (UNIDENTIFIED) — {tx_count:,} txs")
        return {
            "type":       "LIKELY_EXCHANGE",
            "label":      label,
            "stop_trace": True,
        }

    return {
        "type":       "REGULAR",
        "label":      None,
        "stop_trace": False,
    }

"""
chainsentinel/storage/wallet_store.py
Single interface for reading and writing the master wallet list.
"""

import json
import logging
from chainsentinel.config.settings import WALLETS_FILE

log = logging.getLogger("chainsentinel.wallet_store")


def load_wallets() -> list:
    data = json.loads(WALLETS_FILE.read_text())
    return data.get("wallets", [])


def load_known_wallets() -> dict:
    """Returns dict of address.lower() -> label."""
    return {w["address"].lower(): w["label"] for w in load_wallets()}


def address_exists(address: str) -> bool:
    known = load_known_wallets()
    return address.lower() in known


def add_wallet(address: str, label: str):
    data = json.loads(WALLETS_FILE.read_text())
    data["wallets"].append({"address": address, "label": label})
    WALLETS_FILE.write_text(json.dumps(data, indent=2))
    log.info("Added wallet: %s — %s", address, label)

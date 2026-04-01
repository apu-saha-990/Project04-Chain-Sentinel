"""
chainsentinel/core/fetcher.py
Single interface for all Etherscan API calls.
If the API changes, this is the only file to touch.
"""

import os
import time
import logging
import requests
from dotenv import load_dotenv
from config.settings import (
    ETHERSCAN_BASE, USDT_CONTRACT, REQUEST_DELAY
)

load_dotenv()
log = logging.getLogger("chainsentinel.fetcher")

API_KEY = os.getenv("ETHERSCAN_API_KEY", "")


def _get(params: dict, retries: int = 3) -> dict | None:
    params["apikey"] = API_KEY
    for attempt in range(retries):
        try:
            r = requests.get(ETHERSCAN_BASE, params=params, timeout=15)
            r.raise_for_status()
            data = r.json()
            if data.get("status") == "0" and data.get("message") not in ("No transactions found",):
                log.warning("Etherscan: %s", data.get("result", "unknown error"))
                return None
            return data
        except requests.RequestException as e:
            wait = 2 ** attempt
            log.warning("Request failed (attempt %d/%d): %s — retry in %ds",
                        attempt + 1, retries, e, wait)
            time.sleep(wait)
    return None


def get_normal_txs(address: str, from_ts: int) -> list:
    time.sleep(REQUEST_DELAY)
    data = _get({
        "chainid": 1, "module": "account", "action": "txlist",
        "address": address, "startblock": 0, "endblock": 99999999,
        "sort": "desc", "offset": 500, "page": 1,
    })
    if not data or not isinstance(data.get("result"), list):
        return []
    return [tx for tx in data["result"] if int(tx.get("timeStamp", 0)) >= from_ts]


def get_usdt_txs(address: str, from_ts: int) -> list:
    time.sleep(REQUEST_DELAY)
    data = _get({
        "chainid": 1, "module": "account", "action": "tokentx",
        "address": address, "contractaddress": USDT_CONTRACT,
        "startblock": 0, "endblock": 99999999,
        "sort": "desc", "offset": 500, "page": 1,
    })
    if not data or not isinstance(data.get("result"), list):
        return []
    return [tx for tx in data["result"] if int(tx.get("timeStamp", 0)) >= from_ts]


def get_all_normal_txs(address: str) -> list:
    """Fetch all normal txs with no time filter — used by tracer."""
    time.sleep(REQUEST_DELAY)
    data = _get({
        "chainid": 1, "module": "account", "action": "txlist",
        "address": address, "startblock": 0, "endblock": 99999999,
        "sort": "desc", "offset": 200, "page": 1,
    })
    if not data or not isinstance(data.get("result"), list):
        return []
    addr = address.lower()
    return [tx for tx in data["result"]
            if tx.get("to", "").lower() == addr
            and tx.get("isError", "0") == "0"
            and int(tx.get("value", "0")) > 0]


def get_all_usdt_txs(address: str) -> list:
    """Fetch all inbound USDT txs — used by tracer."""
    time.sleep(REQUEST_DELAY)
    data = _get({
        "chainid": 1, "module": "account", "action": "tokentx",
        "address": address, "contractaddress": USDT_CONTRACT,
        "startblock": 0, "endblock": 99999999,
        "sort": "desc", "offset": 200, "page": 1,
    })
    if not data or not isinstance(data.get("result"), list):
        return []
    addr = address.lower()
    return [tx for tx in data["result"] if tx.get("to", "").lower() == addr]


def get_tx_count(address: str) -> int:
    time.sleep(REQUEST_DELAY)
    data = _get({
        "chainid": 1, "module": "proxy", "action": "eth_getTransactionCount",
        "address": address, "tag": "latest",
    })
    if data and data.get("result"):
        try:
            return int(data["result"], 16)
        except Exception:
            pass
    return 0


def get_eth_balance(address: str) -> float:
    time.sleep(REQUEST_DELAY)
    data = _get({
        "chainid": 1, "module": "account", "action": "balance",
        "address": address, "tag": "latest",
    })
    if data and data.get("result"):
        try:
            return int(data["result"]) / 1e18
        except Exception:
            pass
    return 0.0


def get_contract_name(address: str) -> str | None:
    time.sleep(REQUEST_DELAY)
    data = _get({
        "chainid": 1, "module": "contract", "action": "getsourcecode",
        "address": address,
    })
    if data and isinstance(data.get("result"), list) and data["result"]:
        name = data["result"][0].get("ContractName", "")
        if name and name not in ("", "0"):
            return f"Contract: {name}"
    return None

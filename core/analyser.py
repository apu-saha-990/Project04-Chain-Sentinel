"""
chainsentinel/core/analyser.py
Pure analysis logic — takes fetched transactions, returns structured results.
No API calls here. No file I/O here. Just data in, analysis out.
"""

import json
import logging
from config.settings import SPIKE_USD
from storage.wallet_store import load_known_wallets

log = logging.getLogger("chainsentinel.analyser")


def analyse_wallet(address: str, label: str,
                   normal_txs: list, usdt_txs: list,
                   eth_price: float) -> dict:
    """
    Analyse a single wallet's transactions.
    Returns a structured dict with volumes, counts, and spike list.
    """
    addr         = address.lower()
    known        = load_known_wallets()

    eth_in  = sum(int(tx["value"]) for tx in normal_txs
                  if tx.get("to", "").lower() == addr and tx.get("isError", "0") == "0")
    eth_out = sum(int(tx["value"]) for tx in normal_txs
                  if tx.get("from", "").lower() == addr and tx.get("isError", "0") == "0")

    eth_in_val  = eth_in  / 1e18
    eth_out_val = eth_out / 1e18

    usdt_in  = sum(int(tx["value"]) for tx in usdt_txs if tx.get("to", "").lower() == addr)
    usdt_out = sum(int(tx["value"]) for tx in usdt_txs if tx.get("from", "").lower() == addr)

    usdt_in_val  = usdt_in  / 1e6
    usdt_out_val = usdt_out / 1e6

    spikes = []

    for tx in normal_txs:
        if tx.get("to", "").lower() == addr and tx.get("isError", "0") == "0":
            val_usd = (int(tx["value"]) / 1e18) * eth_price
            if val_usd >= SPIKE_USD:
                sender       = tx["from"]
                tracked_flag = _tracked_label(sender, known)
                spikes.append({
                    "hash":         tx["hash"],
                    "from":         sender,
                    "tracked":      tracked_flag,
                    "amount_eth":   round(int(tx["value"]) / 1e18, 6),
                    "amount_usd":   round(val_usd, 2),
                    "timestamp":    int(tx["timeStamp"]),
                    "token":        "ETH",
                })

    for tx in usdt_txs:
        if tx.get("to", "").lower() == addr:
            val_usd = int(tx["value"]) / 1e6
            if val_usd >= SPIKE_USD:
                sender       = tx["from"]
                tracked_flag = _tracked_label(sender, known)
                spikes.append({
                    "hash":        tx["hash"],
                    "from":        sender,
                    "tracked":     tracked_flag,
                    "amount_usdt": round(val_usd, 2),
                    "amount_usd":  round(val_usd, 2),
                    "timestamp":   int(tx["timeStamp"]),
                    "token":       "USDT",
                })

    return {
        "address":        address,
        "label":          label,
        "tx_count_normal": len(normal_txs),
        "tx_count_usdt":   len(usdt_txs),
        "eth_in":          round(eth_in_val, 6),
        "eth_out":         round(eth_out_val, 6),
        "eth_in_usd":      round(eth_in_val  * eth_price, 2),
        "eth_out_usd":     round(eth_out_val * eth_price, 2),
        "usdt_in":         round(usdt_in_val, 2),
        "usdt_out":        round(usdt_out_val, 2),
        "total_in_usd":    round(eth_in_val  * eth_price + usdt_in_val,  2),
        "total_out_usd":   round(eth_out_val * eth_price + usdt_out_val, 2),
        "spikes":          spikes,
        "spike_count":     len(spikes),
    }


def build_batch_totals(results: list) -> dict:
    return {
        "total_in_usd":   round(sum(w["total_in_usd"]  for w in results), 2),
        "total_out_usd":  round(sum(w["total_out_usd"] for w in results), 2),
        "total_eth_in":   round(sum(w["eth_in"]        for w in results), 6),
        "total_eth_out":  round(sum(w["eth_out"]       for w in results), 6),
        "total_usdt_in":  round(sum(w["usdt_in"]       for w in results), 2),
        "total_usdt_out": round(sum(w["usdt_out"]      for w in results), 2),
        "spike_count":    sum(w["spike_count"]          for w in results),
        "wallets_active": sum(
            1 for w in results
            if w["tx_count_normal"] + w["tx_count_usdt"] > 0
        ),
    }


def collect_all_spikes(results: list) -> list:
    """Flatten spikes from all wallet results into a single list."""
    all_spikes = []
    for w in results:
        for s in w.get("spikes", []):
            all_spikes.append({
                **s,
                "wallet":       w["address"],
                "wallet_label": w["label"],
            })
    return all_spikes


def _tracked_label(address: str, known: dict) -> str | None:
    """Return the label if address is in master wallet list, else None."""
    return known.get(address.lower())

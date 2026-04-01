"""
chainsentinel/tracer/hop_engine.py
Core hop traversal logic — follows inbound transactions backwards.
No CLI interaction here. Pure traversal engine.
"""

import logging
from datetime import datetime, timezone
from config.settings import MAX_HOPS
from core.fetcher import (
    get_all_normal_txs, get_all_usdt_txs,
    get_tx_count, get_eth_balance, get_contract_name
)
from tracer.classifier import classify_address
from storage.wallet_store import load_known_wallets

log = logging.getLogger("chainsentinel.hop_engine")


def run_trace(start_address: str, start_label: str, eth_price: float) -> tuple[dict, list]:
    """
    Trace the source of funds for a given address.
    Returns (trace_result dict, new_wallets_found list).
    """
    known         = load_known_wallets()
    visited       = set()
    new_wallets   = []

    trace_result  = {
        "target_address": start_address,
        "target_label":   start_label,
        "traced_at":      datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "hops":           [],
    }

    queue = [(start_address, 0, None)]

    while queue:
        address, depth, parent_tx = queue.pop(0)
        addr_lower = address.lower()

        if depth > MAX_HOPS:
            break
        if addr_lower in visited:
            log.debug("Loop detected at %s — skipping", address[:14])
            continue
        visited.add(addr_lower)

        inbound_eth  = get_all_normal_txs(address)
        inbound_usdt = get_all_usdt_txs(address)
        tx_count     = get_tx_count(address)
        eth_balance  = get_eth_balance(address)

        classification = classify_address(address, tx_count, eth_balance)

        is_known    = addr_lower in known
        known_label = known.get(addr_lower, "")
        is_origin   = not inbound_eth and not inbound_usdt

        # Largest inbound values + top sender
        largest_eth_in  = 0.0
        largest_usdt_in = 0.0
        top_sender      = None

        if inbound_eth:
            top_tx         = max(inbound_eth, key=lambda x: int(x.get("value", 0)))
            largest_eth_in = int(top_tx["value"]) / 1e18
            top_sender     = top_tx["from"]
        if inbound_usdt:
            top_usdt        = max(inbound_usdt, key=lambda x: int(x.get("value", 0)))
            largest_usdt_in = int(top_usdt["value"]) / 1e6

        # Tracked flag on top sender
        top_sender_tracked = known.get(top_sender.lower()) if top_sender else None

        hop_record = {
            "hop":                    depth,
            "address":                address,
            "known":                  is_known,
            "known_label":            known_label if is_known else None,
            "classification":         classification["type"],
            "exchange_label":         classification.get("label"),
            "tx_count":               tx_count,
            "eth_balance":            round(eth_balance, 4),
            "largest_eth_inbound":    round(largest_eth_in, 6),
            "largest_usdt_inbound":   round(largest_usdt_in, 2),
            "inbound_eth_tx_count":   len(inbound_eth),
            "inbound_usdt_tx_count":  len(inbound_usdt),
            "is_origin":              is_origin,
            "top_sender":             top_sender,
            "top_sender_tracked":     top_sender_tracked,
            "parent_tx":              parent_tx,
        }
        trace_result["hops"].append(hop_record)

        # Track newly discovered wallets
        if (not is_known
                and not classification["stop_trace"]
                and not is_origin
                and depth > 0):
            new_wallets.append({
                "address":         address,
                "suggested_label": f"Trace-Hop{depth}-from-{start_label[:30]}",
            })

        if classification["stop_trace"] or is_origin or depth == MAX_HOPS:
            continue

        if top_sender and top_sender.lower() not in visited:
            queue.append((
                top_sender,
                depth + 1,
                inbound_eth[0]["hash"] if inbound_eth else None,
            ))

    trace_result["new_wallets_discovered"] = new_wallets
    return trace_result, new_wallets

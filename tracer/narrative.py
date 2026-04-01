"""
chainsentinel/tracer/narrative.py
Builds a plain-english narrative from a completed hop trace result.
Injected into the trace JSON under the key 'narrative'.
"""

from chainsentinel.storage.wallet_store import load_known_wallets


def build_narrative(result: dict, eth_price: float) -> dict:
    hops        = result.get("hops", [])
    target      = hops[0] if hops else {}
    target_addr = result.get("target_address", "")
    target_lbl  = result.get("target_label", "")

    lines = []
    lines.append(f"TRACE NARRATIVE — {target_lbl}")
    lines.append(f"Target  : {target_addr}")
    lines.append(f"Traced  : {result.get('traced_at', '')}")
    lines.append(f"Hops    : {len(hops) - 1} (excluding target)")
    lines.append("")

    eth_bal  = target.get("eth_balance", 0)
    tx_count = target.get("tx_count", 0)
    eth_in   = target.get("largest_eth_inbound", 0)
    usdt_in  = target.get("largest_usdt_inbound", 0)

    lines.append("TARGET WALLET")
    usd_str = f" (${eth_bal * eth_price:,.0f})" if eth_price else ""
    lines.append(f"  {target_lbl} holds {eth_bal:.4f} ETH{usd_str}.")
    lines.append(f"  Total transactions on record: {tx_count:,}.")
    if eth_in:
        usd_str = f" (${eth_in * eth_price:,.0f})" if eth_price else ""
        lines.append(f"  Largest single inbound ETH: {eth_in:.4f} ETH{usd_str}.")
    if usdt_in:
        lines.append(f"  Largest single inbound USDT: ${usdt_in:,.0f}.")
    lines.append("")

    lines.append("HOP CHAIN")
    for hop in hops:
        depth    = hop["hop"]
        addr     = hop["address"]
        c_type   = hop["classification"]
        c_label  = hop.get("exchange_label") or hop.get("known_label") or ""
        is_known = hop.get("known", False)
        is_orig  = hop.get("is_origin", False)
        h_eth    = hop.get("largest_eth_inbound", 0)
        h_usdt   = hop.get("largest_usdt_inbound", 0)
        h_tx     = hop.get("tx_count", 0)
        h_bal    = hop.get("eth_balance", 0)
        t_sender = hop.get("top_sender")
        t_tracked = hop.get("top_sender_tracked")
        prefix   = "  TARGET" if depth == 0 else f"  HOP {depth}"

        if c_type in ("KNOWN_EXCHANGE", "LIKELY_EXCHANGE"):
            lines.append(f"{prefix}: {addr}")
            lines.append(f"    EXCHANGE IDENTIFIED — {c_label}")
            lines.append(f"    Funds entered the exchange system here. Trace stops.")
        elif c_type == "MIXER":
            lines.append(f"{prefix}: {addr}")
            lines.append(f"    MIXER / TORNADO CASH — {c_label}")
            lines.append(f"    Deliberate obfuscation. Strong laundering indicator. Trace stops.")
        elif is_known:
            lines.append(f"{prefix}: {addr}")
            lines.append(f"    KNOWN WALLET — {c_label}")
            lines.append(f"    Already in master list. Internal movement confirmed.")
            if h_eth:
                usd_str = f" (${h_eth * eth_price:,.0f})" if eth_price else ""
                lines.append(f"    Largest inbound: {h_eth:.4f} ETH{usd_str}.")
        elif is_orig:
            lines.append(f"{prefix}: {addr}")
            lines.append(f"    ORIGIN — no inbound transactions found.")
            usd_str = f" (${h_bal * eth_price:,.0f})" if eth_price else ""
            lines.append(f"    Holds {h_bal:.4f} ETH{usd_str} with {h_tx:,} total txs.")
        else:
            lines.append(f"{prefix}: {addr}")
            lines.append(f"    Intermediate. {h_tx:,} txs. Balance: {h_bal:.4f} ETH.")
            if h_eth:
                usd_str = f" (${h_eth * eth_price:,.0f})" if eth_price else ""
                lines.append(f"    Largest inbound ETH: {h_eth:.4f}{usd_str}.")
            if h_usdt:
                lines.append(f"    Largest inbound USDT: ${h_usdt:,.0f}.")

        if t_sender:
            tracked_note = f"  [TRACKED: {t_tracked}]" if t_tracked else ""
            lines.append(f"    Top sender: {t_sender}{tracked_note}")
        lines.append("")

    lines.append("FINDINGS")
    exchange_hops = [h for h in hops if h["classification"] in ("KNOWN_EXCHANGE", "LIKELY_EXCHANGE")]
    mixer_hops    = [h for h in hops if h["classification"] == "MIXER"]
    known_hops    = [h for h in hops if h.get("known") and h["hop"] > 0]
    origin_hops   = [h for h in hops if h.get("is_origin")]

    if mixer_hops:
        lines.append(f"  *** MIXER at hop(s) {[h['hop'] for h in mixer_hops]}."
                     " Funds deliberately obfuscated. Strong laundering indicator.")
    if exchange_hops:
        for h in exchange_hops:
            lbl = h.get("exchange_label") or "Unknown Exchange"
            lines.append(f"  Exchange at hop {h['hop']}: {lbl} ({h['address']})")
        lines.append("  Funds entered from an exchange.")
    if known_hops:
        lines.append(f"  {len(known_hops)} hop(s) matched tracked wallets (internal movement):")
        for h in known_hops:
            lines.append(f"    Hop {h['hop']}: {h.get('known_label')} — {h['address']}")
    if origin_hops:
        lines.append(f"  Origin reached at hop {origin_hops[0]['hop']}: {origin_hops[0]['address']}")
    if not exchange_hops and not mixer_hops and not origin_hops:
        lines.append("  Max hops reached. Continue tracing from last hop address.")

    new_w = result.get("new_wallets_discovered", [])
    if new_w:
        lines.append("")
        lines.append(f"NEW WALLETS DISCOVERED ({len(new_w)})")
        for w in new_w:
            lines.append(f"  - {w['address']}  ({w['suggested_label']})")

    lines.append("")
    lines.append("=" * 64)

    return {
        "summary":                f"TRACE — {target_lbl}",
        "hops_traced":            len(hops) - 1,
        "exchange_detected":      len(exchange_hops) > 0,
        "exchange_names":         [h.get("exchange_label", "") for h in exchange_hops],
        "mixer_detected":         len(mixer_hops) > 0,
        "origin_reached":         len(origin_hops) > 0,
        "known_wallets_in_chain": len(known_hops),
        "new_wallets_found":      len(new_w),
        "text":                   "\n".join(lines),
    }

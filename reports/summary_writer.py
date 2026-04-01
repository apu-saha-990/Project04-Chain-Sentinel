"""
chainsentinel/reports/summary_writer.py
Writes the plain-english run summary — what happened, what matters, what to do next.
"""

from datetime import datetime, timezone
from pathlib import Path
from chainsentinel.config.settings import REPORTS_DIR
from chainsentinel.storage.wallet_store import load_known_wallets


def write(report: dict, ts_slug: str) -> Path:
    r       = report
    bt      = r["batch_totals"]
    spikes  = r["spikes"]
    wallets = r["wallets"]
    ep      = r["eth_spot_usd"]
    diff    = r.get("diff_from_previous", {})
    trend   = r.get("trend_last_10", [])

    active   = [w for w in wallets if w["total_in_usd"] > 0 or w["total_out_usd"] > 0]
    inactive = [w for w in wallets if w["total_in_usd"] == 0 and w["total_out_usd"] == 0]
    known    = load_known_wallets()

    spike_by_wallet: dict = {}
    for s in spikes:
        spike_by_wallet.setdefault(s["wallet_label"], []).append(s)

    top_spike_wallets = sorted(
        spike_by_wallet.items(),
        key=lambda x: sum(s["amount_usd"] for s in x[1]),
        reverse=True,
    )

    internal = [s for s in spikes if s.get("tracked")]
    biggest  = max(spikes, key=lambda x: x["amount_usd"]) if spikes else None

    def fmt_usd(v): return f"${v:,.2f}"

    L = []
    L.append("=" * 72)
    L.append("  CHAINSENTINEL — RUN SUMMARY")
    L.append(f"  Generated : {r['generated_at']}")
    L.append(f"  Window    : {r['window_from']}  to  {r['generated_at']}  ({r['window_hours']}h)")
    L.append(f"  ETH price : ${ep:,.2f}")
    L.append("=" * 72)

    L.append("")
    L.append("  OVERVIEW")
    L.append("  " + "-" * 60)
    net       = bt["total_in_usd"] - bt["total_out_usd"]
    direction = "accumulating" if net >= 0 else "distributing"
    L.append(f"  {len(wallets)} wallets scanned. {bt['wallets_active']} active. {len(inactive)} dormant.")
    L.append(f"  Total IN   : {fmt_usd(bt['total_in_usd'])}")
    L.append(f"  Total OUT  : {fmt_usd(bt['total_out_usd'])}")
    L.append(f"  Net flow   : {'+' if net >= 0 else ''}{fmt_usd(net)}  ({direction})")
    L.append(f"  ETH in     : {bt['total_eth_in']:,.4f} ETH  ({fmt_usd(bt['total_eth_in'] * ep)})")
    L.append(f"  USDT in    : {fmt_usd(bt['total_usdt_in'])}")

    if diff.get("previous_report"):
        L.append("")
        L.append("  CHANGES SINCE LAST REPORT")
        L.append("  " + "-" * 60)
        d_in  = diff.get("total_in_usd_delta") or 0
        d_out = diff.get("total_out_usd_delta") or 0
        L.append(f"  Previous   : {diff['previous_report']}")
        L.append(f"  IN  delta  : {'+' if d_in >= 0 else ''}{fmt_usd(d_in)}")
        L.append(f"  OUT delta  : {'+' if d_out >= 0 else ''}{fmt_usd(d_out)}")
        changes = diff.get("wallet_changes", [])
        new_w   = [c for c in changes if c.get("status") == "NEW_WALLET"]
        moved   = [c for c in changes if c.get("status") != "NEW_WALLET"]
        if new_w:
            L.append(f"  Newly active : {len(new_w)} wallet(s)")
            for c in new_w:
                L.append(f"    + {c['label']}")
        if moved:
            L.append(f"  Changed      : {len(moved)} wallet(s)")
            for c in sorted(moved, key=lambda x: abs(x["delta_in_usd"]), reverse=True)[:5]:
                si = "+" if c["delta_in_usd"] >= 0 else ""
                L.append(f"    ~ {c['label']}")
                L.append(f"      IN {si}{fmt_usd(c['delta_in_usd'])}   OUT {fmt_usd(c['delta_out_usd'])}   TXs {c['delta_tx_count']:+d}")
    else:
        L.append("")
        L.append("  CHANGES SINCE LAST REPORT")
        L.append("  " + "-" * 60)
        L.append("  First run — baseline established. Next report will show deltas.")

    if len(trend) > 1:
        L.append("")
        L.append("  TREND ACROSS REPORTS")
        L.append("  " + "-" * 60)
        first = trend[0]
        last  = trend[-1]
        delta = last["total_in_usd"] - first["total_in_usd"]
        L.append(f"  Inbound growth : {'+' if delta >= 0 else ''}{fmt_usd(delta)}")
        L.append(f"  Total spikes   : {sum(t['spike_count'] for t in trend)} across all reports")
        max_in = max(t["total_in_usd"] for t in trend) or 1
        for t in trend:
            dt  = (t["generated_at"] or "")[:16].replace("T", " ")
            bar = "█" * int(t["total_in_usd"] / max_in * 24)
            L.append(f"  {dt}  {fmt_usd(t['total_in_usd']):>16}  {bar}")

    L.append("")
    L.append("  ACTIVE WALLETS")
    L.append("  " + "-" * 60)
    for w in sorted(active, key=lambda x: x["total_in_usd"], reverse=True):
        spk = f"   *** SPIKE x{w['spike_count']}" if w["spike_count"] else ""
        L.append(f"  {w['label']}{spk}")
        L.append(f"    Address : {w['address']}")
        L.append(f"    IN  : {fmt_usd(w['total_in_usd']):>16}   OUT : {fmt_usd(w['total_out_usd']):>16}")
        if w["eth_in"]:
            L.append(f"    ETH in  : {w['eth_in']:,.4f} ETH  ({fmt_usd(w['eth_in'] * ep)})")
        if w["usdt_in"]:
            L.append(f"    USDT in : {fmt_usd(w['usdt_in'])}")
        L.append(f"    TXs     : {w['tx_count_normal']} normal  |  {w['tx_count_usdt']} USDT")

    L.append("")
    L.append(f"  SPIKE SUMMARY — {bt['spike_count']} TXs ABOVE $50,000")
    L.append("  " + "-" * 60)

    if biggest:
        tok = biggest["token"]
        amt = (f"{biggest['amount_eth']:,.4f} ETH  ({fmt_usd(biggest['amount_usd'])})"
               if tok == "ETH" else fmt_usd(biggest["amount_usd"]) + " USDT")
        tracked = f"  [TRACKED: {biggest['tracked']}]" if biggest.get("tracked") else ""
        L.append(f"  Largest tx  : {amt}")
        L.append(f"    Wallet  : {biggest['wallet_label']}")
        L.append(f"    From    : {biggest['from']}{tracked}")
        L.append(f"    TX Hash : {biggest['hash']}")

    L.append("")
    L.append("  Per-wallet spike totals:")
    for label, txs in top_spike_wallets:
        total   = sum(s["amount_usd"] for s in txs)
        largest = max(txs, key=lambda x: x["amount_usd"])
        tok     = largest["token"]
        lg_str  = (f"{largest['amount_eth']:,.4f} ETH  ({fmt_usd(largest['amount_usd'])})"
                   if tok == "ETH" else fmt_usd(largest["amount_usd"]) + " USDT")
        L.append(f"  {label}")
        L.append(f"    {len(txs)} spike(s)   Combined: {fmt_usd(total)}   Largest: {lg_str}")

    if internal:
        L.append("")
        L.append(f"  INTERNAL MOVEMENTS — {len(internal)} txs between tracked wallets")
        L.append("  " + "-" * 60)
        L.append("  Money cycling between wallets already in your master list:")
        for m in sorted(internal, key=lambda x: x["amount_usd"], reverse=True):
            tok = m["token"]
            amt = (f"{m['amount_eth']:,.4f} ETH  ({fmt_usd(m['amount_usd'])})"
                   if tok == "ETH" else fmt_usd(m["amount_usd"]) + " USDT")
            L.append(f"  [TRACKED: {m['tracked']}]  ->  {m['wallet_label']}")
            L.append(f"    Amount  : {amt}")
            L.append(f"    From    : {m['from']}")
            L.append(f"    TX Hash : {m['hash']}")

    if inactive:
        L.append("")
        L.append(f"  DORMANT WALLETS — {len(inactive)}")
        L.append("  " + "-" * 60)
        for w in inactive:
            L.append(f"  - {w['label']}")
            L.append(f"    {w['address']}")

    L.append("")
    L.append("  RECOMMENDED NEXT STEPS")
    L.append("  " + "-" * 60)
    step = 1
    if top_spike_wallets:
        top_label, top_txs = top_spike_wallets[0]
        top_obj  = next((w for w in wallets if w["label"] == top_label), None)
        top_addr = top_obj["address"] if top_obj else "unknown"
        L.append(f"  {step}. Run hop trace on: {top_label}")
        L.append(f"     Address : {top_addr}")
        L.append(f"     Reason  : Highest combined spike value {fmt_usd(sum(s['amount_usd'] for s in top_txs))}")
        step += 1
    if len(top_spike_wallets) > 1:
        sl, st = top_spike_wallets[1]
        so     = next((w for w in wallets if w["label"] == sl), None)
        sa     = so["address"] if so else "unknown"
        L.append(f"  {step}. Also trace: {sl}")
        L.append(f"     Address : {sa}")
        L.append(f"     Reason  : {len(st)} spikes totalling {fmt_usd(sum(s['amount_usd'] for s in st))}")
        step += 1
    if internal:
        L.append(f"  {step}. Investigate {len(internal)} internal movement(s) — possible layering")
        step += 1
    if len(inactive) > 40:
        L.append(f"  {step}. {len(inactive)} wallets dormant — review if any can be retired")

    L.append("")
    L.append("=" * 72)
    L.append(f"  END OF SUMMARY — eth_summary_{ts_slug}.txt")
    L.append("=" * 72)

    path = REPORTS_DIR / f"eth_summary_{ts_slug}.txt"
    path.write_text("\n".join(L))
    return path

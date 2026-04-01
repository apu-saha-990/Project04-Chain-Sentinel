"""
chainsentinel/reports/txt_writer.py
Writes the full human-readable .txt report.
Full detail — every wallet, every transaction, every address in full.
"""

from datetime import datetime, timezone
from pathlib import Path
from config.settings import REPORTS_DIR


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

    spike_by_wallet: dict = {}
    for s in spikes:
        spike_by_wallet.setdefault(s["wallet_label"], []).append(s)

    def fmt_eth(v): return f"{v:,.4f} ETH  (${v * ep:,.2f})"
    def fmt_usd(v): return f"${v:,.2f}"

    L = []
    L.append("=" * 72)
    L.append("  CHAINSENTINEL — ETH ACTIVITY REPORT")
    L.append(f"  Generated : {r['generated_at']}")
    L.append(f"  Window    : {r['window_from']}  to  {r['generated_at']}  ({r['window_hours']}h)")
    L.append(f"  ETH price : ${ep:,.2f}")
    if diff.get("note"):
        L.append(f"  Note      : {diff['note']}")
    L.append("=" * 72)

    L.append("")
    L.append("  BATCH TOTALS")
    L.append("  " + "-" * 60)
    L.append(f"  Wallets     : {len(wallets)} total  |  {bt['wallets_active']} active")
    L.append(f"  Total IN    : {fmt_usd(bt['total_in_usd'])}")
    L.append(f"  Total OUT   : {fmt_usd(bt['total_out_usd'])}")
    L.append(f"  ETH in      : {fmt_eth(bt['total_eth_in'])}")
    L.append(f"  ETH out     : {fmt_eth(bt['total_eth_out'])}")
    L.append(f"  USDT in     : {fmt_usd(bt['total_usdt_in'])}")
    L.append(f"  USDT out    : {fmt_usd(bt['total_usdt_out'])}")
    L.append(f"  Spikes >$50k: {bt['spike_count']} transactions")

    if diff.get("previous_report"):
        L.append("")
        L.append("  CHANGES VS PREVIOUS REPORT")
        L.append("  " + "-" * 60)
        L.append(f"  Previous   : {diff['previous_report']}")
        si = "+" if (diff.get("total_in_usd_delta") or 0) >= 0 else ""
        so = "+" if (diff.get("total_out_usd_delta") or 0) >= 0 else ""
        L.append(f"  IN  delta  : {si}{fmt_usd(diff.get('total_in_usd_delta') or 0)}")
        L.append(f"  OUT delta  : {so}{fmt_usd(diff.get('total_out_usd_delta') or 0)}")
        changes = diff.get("wallet_changes", [])
        if changes:
            L.append(f"  Changes    : {len(changes)} wallet(s)")
            for c in changes:
                if c.get("status") == "NEW_WALLET":
                    L.append(f"    + NEW  : {c['label']}")
                else:
                    si = "+" if c["delta_in_usd"] >= 0 else ""
                    so = "+" if c["delta_out_usd"] >= 0 else ""
                    L.append(f"    ~ {c['label']}")
                    L.append(f"      IN {si}{fmt_usd(c['delta_in_usd'])}  OUT {so}{fmt_usd(c['delta_out_usd'])}  TXs {c['delta_tx_count']:+d}")

    if len(trend) > 1:
        L.append("")
        L.append("  TREND — LAST 10 REPORTS")
        L.append("  " + "-" * 60)
        max_in = max(t["total_in_usd"] for t in trend) or 1
        for t in trend:
            dt      = (t["generated_at"] or "")[:16].replace("T", " ")
            bar_len = int(t["total_in_usd"] / max_in * 24)
            bar     = "█" * bar_len
            L.append(f"  {dt}  {fmt_usd(t['total_in_usd']):>16}  {bar}")

    L.append("")
    L.append("=" * 72)
    L.append(f"  ACTIVE WALLETS ({len(active)})")
    L.append("=" * 72)

    for w in sorted(active, key=lambda x: x["total_in_usd"], reverse=True):
        L.append("")
        L.append(f"  [{w['label']}]")
        L.append(f"  Address      : {w['address']}")
        L.append(f"  Transactions : {w['tx_count_normal']} normal  |  {w['tx_count_usdt']} USDT")
        if w["eth_in"] or w["eth_out"]:
            L.append(f"  ETH in       : {fmt_eth(w['eth_in'])}")
            L.append(f"  ETH out      : {fmt_eth(w['eth_out'])}")
        if w["usdt_in"] or w["usdt_out"]:
            L.append(f"  USDT in      : {fmt_usd(w['usdt_in'])}")
            L.append(f"  USDT out     : {fmt_usd(w['usdt_out'])}")
        L.append(f"  Total IN     : {fmt_usd(w['total_in_usd'])}")
        L.append(f"  Total OUT    : {fmt_usd(w['total_out_usd'])}")
        if w["spike_count"]:
            L.append(f"  *** SPIKES   : {w['spike_count']} tx(s) above $50,000")
        L.append("  " + "-" * 68)

    L.append("")
    L.append("=" * 72)
    L.append(f"  INACTIVE WALLETS ({len(inactive)}) — zero activity")
    L.append("=" * 72)
    for w in inactive:
        L.append(f"  - {w['label']}")
        L.append(f"    {w['address']}")

    L.append("")
    L.append("=" * 72)
    L.append(f"  SPIKE DETAIL — {bt['spike_count']} LARGE INBOUND TRANSACTIONS > $50,000")
    L.append("=" * 72)

    for wallet_label, txs in spike_by_wallet.items():
        total = sum(s["amount_usd"] for s in txs)
        L.append("")
        L.append(f"  [{wallet_label}]")
        L.append(f"  {len(txs)} spike(s)  |  Combined: {fmt_usd(total)}")
        L.append("  " + "-" * 64)
        for s in sorted(txs, key=lambda x: x["amount_usd"], reverse=True):
            ts  = datetime.fromtimestamp(s["timestamp"], tz=timezone.utc).strftime("%d %b %Y %H:%M UTC")
            tok = s["token"]
            amt = (f"{s['amount_eth']:,.4f} ETH  ({fmt_usd(s['amount_usd'])})"
                   if tok == "ETH" else fmt_usd(s["amount_usd"]) + " USDT")
            tracked = f"  [TRACKED: {s['tracked']}]" if s.get("tracked") else ""
            L.append(f"  {ts}")
            L.append(f"  Amount  : {amt}")
            L.append(f"  From    : {s['from']}{tracked}")
            L.append(f"  TX Hash : {s['hash']}")
            L.append("  " + "-" * 64)

    L.append("")
    L.append("=" * 72)
    L.append(f"  END OF REPORT — eth_report_{ts_slug}.txt")
    L.append("=" * 72)

    path = REPORTS_DIR / f"eth_report_{ts_slug}.txt"
    path.write_text("\n".join(L))
    return path

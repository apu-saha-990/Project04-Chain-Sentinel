"""
chainsentinel/cli/monitor_cli.py
Entry point for the monitoring run.
Orchestrates: fetch → analyse → diff → build → write → prompt for trace.
"""

import os
import sys
import json
import logging
import subprocess
from datetime import datetime, timezone, timedelta
from pathlib import Path

from chainsentinel.config.settings   import WINDOW_HOURS, SPIKE_USD
from chainsentinel.core.fetcher      import get_normal_txs, get_usdt_txs
from chainsentinel.core.pricer       import get_eth_usd
from chainsentinel.core.analyser     import analyse_wallet
from chainsentinel.reports.builder   import build_report
from chainsentinel.reports.txt_writer     import write as write_txt
from chainsentinel.reports.summary_writer import write as write_summary
from chainsentinel.storage.report_store  import save_report, prune_old_reports
from chainsentinel.storage.wallet_store  import load_wallets

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%SZ",
)
log = logging.getLogger("chainsentinel.monitor")


def run():
    api_key = os.getenv("ETHERSCAN_API_KEY", "")
    if not api_key:
        log.error("ETHERSCAN_API_KEY not set. Add it to .env")
        sys.exit(1)

    wallets   = load_wallets()
    run_at    = datetime.now(tz=timezone.utc)
    from_ts   = int((run_at - timedelta(hours=WINDOW_HOURS)).timestamp())
    eth_price = get_eth_usd()
    ts_slug   = run_at.strftime("%Y%m%d_%H%M%S")

    log.info("=== ChainSentinel Monitor — %s ===", run_at.strftime("%Y-%m-%dT%H:%M:%SZ"))
    log.info("Wallets: %d | Window: %dh | ETH: $%.2f", len(wallets), WINDOW_HOURS, eth_price)

    results    = []
    all_spikes = []

    for i, w in enumerate(wallets, 1):
        addr  = w["address"]
        label = w["label"]
        log.info("[%d/%d] %s (%s...)", i, len(wallets), label, addr[:10])

        normal_txs = get_normal_txs(addr, from_ts)
        usdt_txs   = get_usdt_txs(addr, from_ts)
        result     = analyse_wallet(addr, label, normal_txs, usdt_txs, eth_price)
        results.append(result)

        if result["spikes"]:
            for s in result["spikes"]:
                all_spikes.append({**s, "wallet": addr, "wallet_label": label})
            log.warning("  SPIKE: %d large inbound tx(s) on %s", result["spike_count"], label)

        log.info("  IN: $%.0f  OUT: $%.0f  TXs: %d",
                 result["total_in_usd"], result["total_out_usd"],
                 result["tx_count_normal"] + result["tx_count_usdt"])

    # Build + save all outputs
    report = build_report(results, eth_price)
    prune_old_reports()
    json_path    = save_report(report, ts_slug)
    txt_path     = write_txt(report, ts_slug)
    summary_path = write_summary(report, ts_slug)

    bt = report["batch_totals"]
    _print_summary(report, bt, all_spikes, eth_price, WINDOW_HOURS,
                   len(wallets), json_path, txt_path, summary_path)

    # Prompt for hop trace if spikes found
    if all_spikes:
        print(f"\n  {len(all_spikes)} spike(s) flagged.")
        ans = input("  Activate hop trace? [y/N]: ").strip().lower()
        if ans == "y":
            flagged = list({s["wallet"] for s in all_spikes})
            trace   = Path(__file__).parent / "trace_cli.py"
            if trace.exists():
                subprocess.run(
                    [sys.executable, str(trace), "--flagged", json.dumps(flagged)],
                    env=os.environ.copy(),
                )
            else:
                print(f"  trace_cli.py not found at {trace}")
    else:
        log.info("No spikes — hop trace not needed.")


def _print_summary(report, bt, all_spikes, eth_price, window_hours,
                   total_wallets, json_path, txt_path, summary_path):
    diff  = report.get("diff_from_previous", {})
    trend = report.get("trend_last_10", [])

    print("\n" + "=" * 64)
    print("  CHAINSENTINEL — BATCH SUMMARY")
    print("=" * 64)
    print(f"  Generated  : {report['generated_at']}")
    print(f"  Window     : Last {window_hours}h")
    print(f"  ETH price  : ${eth_price:,.2f}")
    print(f"  Wallets    : {total_wallets} total | {bt['wallets_active']} active")
    print(f"  Total IN   : ${bt['total_in_usd']:>15,.2f}")
    print(f"  Total OUT  : ${bt['total_out_usd']:>15,.2f}")
    print(f"  ETH in     :  {bt['total_eth_in']:>14,.4f} ETH")
    print(f"  USDT in    : ${bt['total_usdt_in']:>15,.2f}")

    if diff.get("previous_report"):
        d_in  = diff.get("total_in_usd_delta") or 0
        d_out = diff.get("total_out_usd_delta") or 0
        print(f"\n  VS PREVIOUS ({diff['previous_report'][:10]})")
        print(f"  IN  delta  : {'+' if d_in >= 0 else ''}${d_in:,.2f}")
        print(f"  OUT delta  : {'+' if d_out >= 0 else ''}${d_out:,.2f}")
        changes = diff.get("wallet_changes", [])
        if changes:
            print(f"  Changed    : {len(changes)} wallet(s)")

    if len(trend) > 1:
        print(f"\n  TREND ({len(trend)} reports)")
        for t in trend:
            dt = (t["generated_at"] or "")[:10]
            print(f"    {dt}  IN: ${t['total_in_usd']:>13,.0f}  SPIKES: {t['spike_count']}")

    if all_spikes:
        print(f"\n  SPIKES > ${SPIKE_USD:,}  ({len(all_spikes)} tx(s))")
        for s in all_spikes:
            tok     = s["token"]
            amt     = (f"{s['amount_eth']:,.4f} ETH (${s['amount_usd']:,.0f})"
                       if tok == "ETH" else f"${s['amount_usd']:,.0f} USDT")
            tracked = f"  [TRACKED: {s['tracked']}]" if s.get("tracked") else ""
            print(f"    {s['wallet_label']}")
            print(f"      {amt}  from {s['from']}{tracked}")
            print(f"      tx: {s['hash']}")
    else:
        print("\n  No spikes detected.")

    print("=" * 64)
    print(f"  JSON    : {json_path}")
    print(f"  Report  : {txt_path}")
    print(f"  Summary : {summary_path}")
    print("=" * 64 + "\n")


if __name__ == "__main__":
    run()

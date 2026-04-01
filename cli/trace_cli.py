"""
chainsentinel/cli/trace_cli.py
Entry point for the hop tracer.
Handles all user interaction — the engine logic lives in tracer/.
"""

import argparse
import json
import os
import sys
import logging
from datetime import datetime, timezone
from pathlib import Path

from core.pricer         import get_eth_usd
from tracer.hop_engine   import run_trace
from tracer.narrative    import build_narrative
from storage.trace_store import save_trace
from storage.wallet_store import load_known_wallets, add_wallet
from config.settings    import MAX_HOPS

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%SZ",
)
log = logging.getLogger("chainsentinel.trace")


def run():
    api_key = os.getenv("ETHERSCAN_API_KEY", "")
    if not api_key:
        log.error("ETHERSCAN_API_KEY not set.")
        sys.exit(1)

    parser = argparse.ArgumentParser(description="ChainSentinel Hop Tracer")
    parser.add_argument("--address",  type=str, default=None)
    parser.add_argument("--flagged",  type=str, default=None,
                        help="JSON array of flagged addresses from monitor")
    args = parser.parse_args()

    known     = load_known_wallets()
    eth_price = get_eth_usd()
    targets   = []

    # ── Build target list ─────────────────────────────────────────────────────
    if args.flagged:
        flagged_addresses = json.loads(args.flagged)
        print(f"\n  Monitor flagged {len(flagged_addresses)} wallet(s):\n")
        for i, addr in enumerate(flagged_addresses, 1):
            label = known.get(addr.lower(), "Unknown")
            print(f"  [{i}] {addr}")
            print(f"      {label}")
        print(f"  [{len(flagged_addresses) + 1}] Enter address manually")

        choice = input("\n  Select wallet(s) to trace (e.g. 1,2 or 'all'): ").strip().lower()
        if choice == "all":
            for addr in flagged_addresses:
                targets.append((addr, known.get(addr.lower(), "Flagged-Wallet")))
        else:
            try:
                for idx in [int(x.strip()) - 1 for x in choice.split(",")]:
                    if idx == len(flagged_addresses):
                        manual = input("  Enter address: ").strip()
                        targets.append((manual, known.get(manual.lower(), "Manual-Entry")))
                    elif 0 <= idx < len(flagged_addresses):
                        addr = flagged_addresses[idx]
                        targets.append((addr, known.get(addr.lower(), "Flagged-Wallet")))
            except Exception:
                print("  Invalid selection.")
                sys.exit(1)

    elif args.address:
        addr  = args.address
        label = known.get(addr.lower(), "Manual-Entry")
        targets.append((addr, label))

    else:
        print("\n  ChainSentinel Hop Tracer")
        print("  " + "-" * 40)
        addr  = input("  Enter wallet address to trace: ").strip()
        label = known.get(addr.lower()) or input("  Label (Enter to skip): ").strip() or "Manual-Entry"
        targets.append((addr, label))

    if not targets:
        print("  No targets selected.")
        sys.exit(0)

    all_new_wallets = []

    for addr, label in targets:
        _run_single_trace(addr, label, known, eth_price, all_new_wallets)

    # ── Prompt to add new wallets ─────────────────────────────────────────────
    _prompt_add_wallets(all_new_wallets, known)

    print(f"\n{'=' * 64}")
    print("  Hop trace complete.")
    print(f"{'=' * 64}\n")


def _run_single_trace(addr: str, label: str, known: dict,
                      eth_price: float, all_new_wallets: list):
    print(f"\n{'=' * 64}")
    print(f"  TRACING: {label}")
    print(f"  Address: {addr}")
    print(f"  Max hops: {MAX_HOPS}")
    print(f"{'=' * 64}")

    result, new_wallets = run_trace(addr, label, eth_price)
    all_new_wallets.extend(new_wallets)

    # Print hop chain to terminal
    for hop in result["hops"]:
        depth    = hop["hop"]
        indent   = "  " * depth
        prefix   = "TARGET" if depth == 0 else f"HOP {depth}"
        c_type   = hop["classification"]
        c_label  = hop.get("exchange_label") or hop.get("known_label") or ""
        is_known = hop.get("known", False)
        is_orig  = hop.get("is_origin", False)
        h_eth    = hop.get("largest_eth_inbound", 0)
        h_usdt   = hop.get("largest_usdt_inbound", 0)
        t_sender = hop.get("top_sender")
        t_tracked = hop.get("top_sender_tracked")

        print(f"\n  {indent}[{prefix}] {hop['address']}")

        if c_type == "MIXER":
            print(f"  {indent}        *** MIXER: {c_label}")
        elif c_type in ("KNOWN_EXCHANGE", "LIKELY_EXCHANGE"):
            print(f"  {indent}        EXCHANGE: {c_label}")
        elif is_known:
            print(f"  {indent}        KNOWN WALLET: {c_label}")
        elif is_orig:
            print(f"  {indent}        ORIGIN — no inbound txs found")

        print(f"  {indent}        txs: {hop['tx_count']:,}  |  ETH bal: {hop['eth_balance']:.4f}")
        if h_eth:
            print(f"  {indent}        largest inbound ETH : {h_eth:.4f} ETH  (${h_eth * eth_price:,.0f})")
        if h_usdt:
            print(f"  {indent}        largest inbound USDT: ${h_usdt:,.0f}")
        if t_sender:
            tracked_note = f"  [TRACKED: {t_tracked}]" if t_tracked else ""
            print(f"  {indent}        top sender: {t_sender}{tracked_note}")

    # Build narrative and inject into result
    narrative    = build_narrative(result, eth_price)
    result["narrative"] = narrative

    ts_slug   = datetime.now(tz=timezone.utc).strftime("%Y%m%d_%H%M%S")
    trace_path = save_trace(result, label, ts_slug)

    print(f"\n  {'─' * 60}")
    print("  NARRATIVE")
    print(f"  {'─' * 60}")
    print(narrative["text"])
    print(f"\n  Trace saved: {trace_path}")


def _prompt_add_wallets(new_wallets: list, known: dict):
    seen   = set()
    unique = [w for w in new_wallets
              if w["address"].lower() not in known
              and w["address"].lower() not in seen
              and not seen.add(w["address"].lower())]

    if not unique:
        return

    print(f"\n  {'─' * 64}")
    print(f"  NEW WALLETS DISCOVERED ({len(unique)}) — not in master list")
    print(f"  {'─' * 64}")
    for i, w in enumerate(unique, 1):
        print(f"  [{i}] {w['address']}")
        print(f"      Suggested: {w['suggested_label']}")

    ans = input("\n  Add to wallets.json? Enter numbers, 'all', or 'none': ").strip().lower()
    if ans in ("", "none", "n"):
        return

    indices = list(range(len(unique))) if ans == "all" else [
        int(x.strip()) - 1 for x in ans.split(",") if x.strip().isdigit()
    ]

    for idx in indices:
        if 0 <= idx < len(unique):
            w      = unique[idx]
            custom = input(f"  Label for {w['address'][:16]}... [{w['suggested_label']}]: ").strip()
            label  = custom or w["suggested_label"]
            add_wallet(w["address"], label)
            print(f"  Added: {label}")


if __name__ == "__main__":
    run()

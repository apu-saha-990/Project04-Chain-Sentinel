"""
chainsentinel/reports/builder.py
Assembles the complete report data structure from analysed results.
Pure data assembly — no file I/O, no API calls.
"""

from datetime import datetime, timezone, timedelta
from chainsentinel.config.settings import WINDOW_HOURS
from chainsentinel.core.analyser  import build_batch_totals, collect_all_spikes
from chainsentinel.core.differ    import build_diff, finalise_diff, build_trend
from chainsentinel.storage.report_store import load_previous_report, load_all_reports


def build_report(results: list, eth_price: float) -> dict:
    run_at   = datetime.now(tz=timezone.utc)
    from_ts  = int((run_at - timedelta(hours=WINDOW_HOURS)).timestamp())

    batch_totals = build_batch_totals(results)
    all_spikes   = collect_all_spikes(results)

    prev_report  = load_previous_report()
    diff         = build_diff(results, prev_report)
    diff         = finalise_diff(diff, batch_totals)

    all_reports  = load_all_reports()
    trend        = build_trend(all_reports)

    return {
        "generated_at":       run_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "window_hours":       WINDOW_HOURS,
        "window_from":        datetime.fromtimestamp(from_ts, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "eth_spot_usd":       eth_price,
        "batch_totals":       batch_totals,
        "diff_from_previous": diff,
        "trend_last_10":      trend,
        "spikes":             all_spikes,
        "wallets":            results,
    }

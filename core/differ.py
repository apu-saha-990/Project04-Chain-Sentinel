"""
chainsentinel/core/differ.py
Diff engine — compares current run against previous report.
Pure logic, no file I/O, no API calls.
"""


def build_diff(current_wallets: list, prev_report: dict | None) -> dict:
    if not prev_report:
        return {"note": "First run — baseline established this run"}

    prev_map = {w["address"].lower(): w for w in prev_report.get("wallets", [])}
    changes  = []

    for w in current_wallets:
        addr = w["address"].lower()
        prev = prev_map.get(addr)
        if not prev:
            changes.append({
                "address": w["address"],
                "label":   w["label"],
                "status":  "NEW_WALLET",
            })
            continue

        delta_in  = round(w["total_in_usd"]  - prev.get("total_in_usd",  0), 2)
        delta_out = round(w["total_out_usd"] - prev.get("total_out_usd", 0), 2)
        delta_tx  = (
            w["tx_count_normal"] + w["tx_count_usdt"]
            - prev.get("tx_count_normal", 0)
            - prev.get("tx_count_usdt", 0)
        )

        if delta_in or delta_out or delta_tx:
            changes.append({
                "address":       w["address"],
                "label":         w["label"],
                "delta_in_usd":  delta_in,
                "delta_out_usd": delta_out,
                "delta_tx_count": delta_tx,
            })

    prev_bt  = prev_report.get("batch_totals", {})
    return {
        "previous_report":      prev_report.get("generated_at", "unknown"),
        "wallet_changes":       changes,
        "total_in_usd_delta":   None,
        "total_out_usd_delta":  None,
        "_prev_in":             prev_bt.get("total_in_usd",  0),
        "_prev_out":            prev_bt.get("total_out_usd", 0),
    }


def finalise_diff(diff: dict, batch_totals: dict) -> dict:
    """Inject batch-level deltas once totals are known."""
    diff["total_in_usd_delta"]  = round(
        batch_totals["total_in_usd"]  - diff.pop("_prev_in",  0), 2)
    diff["total_out_usd_delta"] = round(
        batch_totals["total_out_usd"] - diff.pop("_prev_out", 0), 2)
    return diff


def build_trend(reports: list) -> list:
    """Build trend data across last N reports."""
    trend = []
    for r in reports:
        trend.append({
            "report":        r.get("_filename", ""),
            "generated_at":  r.get("generated_at"),
            "total_in_usd":  r.get("batch_totals", {}).get("total_in_usd",  0),
            "total_out_usd": r.get("batch_totals", {}).get("total_out_usd", 0),
            "spike_count":   r.get("batch_totals", {}).get("spike_count",   0),
        })
    return trend

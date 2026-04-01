"""
chainsentinel/storage/report_store.py
Handles all report file persistence — save, load, prune.
One place for all file I/O related to reports.
"""

import json
import logging
from pathlib import Path
from chainsentinel.config.settings import REPORTS_DIR, MAX_REPORTS

log = logging.getLogger("chainsentinel.report_store")


def ensure_dirs():
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)


def save_report(report: dict, ts_slug: str) -> Path:
    ensure_dirs()
    path = REPORTS_DIR / f"eth_report_{ts_slug}.json"
    path.write_text(json.dumps(report, indent=2))
    log.info("Report saved: %s", path.name)
    return path


def load_previous_report() -> dict | None:
    reports = sorted(REPORTS_DIR.glob("eth_report_*.json"))
    if not reports:
        return None
    try:
        data = json.loads(reports[-1].read_text())
        data["_filename"] = reports[-1].name
        return data
    except Exception:
        return None


def load_all_reports() -> list:
    reports = sorted(REPORTS_DIR.glob("eth_report_*.json"))
    result  = []
    for r in reports:
        try:
            data = json.loads(r.read_text())
            data["_filename"] = r.name
            result.append(data)
        except Exception:
            continue
    return result


def prune_old_reports():
    """Keep only the last MAX_REPORTS sets of files, delete older ones."""
    reports = sorted(REPORTS_DIR.glob("eth_report_*.json"))
    while len(reports) >= MAX_REPORTS:
        oldest  = reports.pop(0)
        ts_slug = oldest.stem.replace("eth_report_", "")
        oldest.unlink()
        for fname in [f"eth_report_{ts_slug}.txt", f"eth_summary_{ts_slug}.txt"]:
            f = REPORTS_DIR / fname
            if f.exists():
                f.unlink()
        log.info("Pruned: %s", oldest.name)

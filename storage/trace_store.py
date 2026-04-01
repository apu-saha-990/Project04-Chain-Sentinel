"""
chainsentinel/storage/trace_store.py
Handles all trace file persistence.
"""

import json
import logging
from pathlib import Path
from config.settings import TRACES_DIR

log = logging.getLogger("chainsentinel.trace_store")


def ensure_dirs():
    TRACES_DIR.mkdir(parents=True, exist_ok=True)


def save_trace(result: dict, label: str, ts_slug: str) -> Path:
    ensure_dirs()
    safe_label = label.replace(" ", "_").replace("/", "-")[:40]
    path       = TRACES_DIR / f"trace_{safe_label}_{ts_slug}.json"
    path.write_text(json.dumps(result, indent=2))
    log.info("Trace saved: %s", path.name)
    return path


def load_all_traces() -> list:
    if not TRACES_DIR.exists():
        return []
    result = []
    for f in sorted(TRACES_DIR.glob("trace_*.json")):
        try:
            data = json.loads(f.read_text())
            data["_filename"] = f.name
            result.append(data)
        except Exception:
            continue
    return result

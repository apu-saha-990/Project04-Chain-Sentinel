"""
chainsentinel/tests/test_differ.py
"""
import pytest
from core.differ import build_diff, finalise_diff, build_trend


def _wallet(addr, label, total_in, total_out, tx_n=1, tx_u=0):
    return {
        "address": addr, "label": label,
        "total_in_usd": total_in, "total_out_usd": total_out,
        "tx_count_normal": tx_n, "tx_count_usdt": tx_u,
    }


def test_first_run_returns_note():
    diff = build_diff([], None)
    assert "note" in diff


def test_new_wallet_detected():
    current = [_wallet("0xNEW", "New", 1000, 500)]
    prev    = {"generated_at": "2026-01-01T00:00:00Z", "wallets": [], "batch_totals": {}}
    diff    = build_diff(current, prev)
    assert diff["wallet_changes"][0]["status"] == "NEW_WALLET"


def test_delta_calculated():
    current = [_wallet("0xABC", "Test", 2000, 1000)]
    prev    = {
        "generated_at": "2026-01-01T00:00:00Z",
        "batch_totals": {"total_in_usd": 1500, "total_out_usd": 800},
        "wallets": [_wallet("0xABC", "Test", 1500, 800)],
    }
    diff = build_diff(current, prev)
    diff = finalise_diff(diff, {"total_in_usd": 2000, "total_out_usd": 1000})
    assert diff["total_in_usd_delta"]  == 500.0
    assert diff["total_out_usd_delta"] == 200.0


def test_unchanged_wallet_not_in_changes():
    current = [_wallet("0xABC", "Test", 1000, 500)]
    prev    = {
        "generated_at": "2026-01-01T00:00:00Z",
        "batch_totals": {},
        "wallets": [_wallet("0xABC", "Test", 1000, 500)],
    }
    diff = build_diff(current, prev)
    assert len(diff["wallet_changes"]) == 0


def test_build_trend():
    reports = [
        {"generated_at": "2026-01-01T00:00:00Z", "batch_totals": {"total_in_usd": 100, "total_out_usd": 50, "spike_count": 1}, "_filename": "r1.json"},
        {"generated_at": "2026-01-02T00:00:00Z", "batch_totals": {"total_in_usd": 200, "total_out_usd": 80, "spike_count": 3}, "_filename": "r2.json"},
    ]
    trend = build_trend(reports)
    assert len(trend) == 2
    assert trend[1]["total_in_usd"] == 200

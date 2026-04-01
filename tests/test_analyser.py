"""
chainsentinel/tests/test_analyser.py
"""
import pytest
from core.analyser import analyse_wallet, build_batch_totals


def _make_tx(to, value, is_error="0", timestamp=1700000000):
    return {"to": to, "from": "0xSENDER", "value": str(value),
            "isError": is_error, "timeStamp": str(timestamp), "hash": "0xHASH"}


def _make_usdt(to, value, timestamp=1700000000):
    return {"to": to, "from": "0xSENDER", "value": str(value),
            "timeStamp": str(timestamp), "hash": "0xHASH"}


ADDR = "0xTestAddress"
ADDR_L = ADDR.lower()


def test_eth_in_calculated():
    txs = [_make_tx(ADDR, int(1e18))]  # 1 ETH
    result = analyse_wallet(ADDR, "Test", txs, [], eth_price=2000.0)
    assert result["eth_in"] == 1.0
    assert result["eth_in_usd"] == 2000.0


def test_spike_detected():
    txs = [_make_tx(ADDR, int(30 * 1e18))]  # 30 ETH @ $2000 = $60k
    result = analyse_wallet(ADDR, "Test", txs, [], eth_price=2000.0)
    assert result["spike_count"] == 1
    assert result["spikes"][0]["amount_usd"] == 60000.0


def test_no_spike_below_threshold():
    txs = [_make_tx(ADDR, int(1e18))]  # 1 ETH @ $2000 = $2k
    result = analyse_wallet(ADDR, "Test", txs, [], eth_price=2000.0)
    assert result["spike_count"] == 0


def test_usdt_in_calculated():
    txs = [_make_usdt(ADDR, int(100 * 1e6))]  # 100 USDT
    result = analyse_wallet(ADDR, "Test", [], txs, eth_price=2000.0)
    assert result["usdt_in"] == 100.0


def test_batch_totals():
    results = [
        {"total_in_usd": 100.0, "total_out_usd": 50.0, "eth_in": 0.05, "eth_out": 0.02,
         "usdt_in": 0.0, "usdt_out": 0.0, "spike_count": 1,
         "tx_count_normal": 2, "tx_count_usdt": 0},
        {"total_in_usd": 200.0, "total_out_usd": 150.0, "eth_in": 0.1, "eth_out": 0.07,
         "usdt_in": 0.0, "usdt_out": 0.0, "spike_count": 0,
         "tx_count_normal": 0, "tx_count_usdt": 0},
    ]
    bt = build_batch_totals(results)
    assert bt["total_in_usd"]  == 300.0
    assert bt["total_out_usd"] == 200.0
    assert bt["spike_count"]   == 1
    assert bt["wallets_active"] == 1

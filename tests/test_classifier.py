"""
chainsentinel/tests/test_classifier.py
"""
from chainsentinel.tracer.classifier import classify_address


def test_known_exchange_detected():
    # Binance Hot Wallet 1
    result = classify_address("0x28c6c06298d514db089934071355e5743bf21d60", 999999, 100.0)
    assert result["type"] == "KNOWN_EXCHANGE"
    assert result["stop_trace"] is True
    assert "Binance" in result["label"]


def test_tornado_cash_is_mixer():
    result = classify_address("0x910cbd523d972eb0a6f4cae4618ad62622b39dbf", 999999, 0.0)
    assert result["type"] == "MIXER"
    assert result["stop_trace"] is True


def test_high_tx_count_flagged_as_likely_exchange():
    result = classify_address("0x1234567890abcdef1234567890abcdef12345678", 10000, 50.0)
    assert result["type"] == "LIKELY_EXCHANGE"
    assert result["stop_trace"] is True


def test_regular_wallet_not_flagged():
    result = classify_address("0xabcdef1234567890abcdef1234567890abcdef12", 10, 0.5)
    assert result["type"] == "REGULAR"
    assert result["stop_trace"] is False


def test_case_insensitive_lookup():
    result = classify_address("0x28C6C06298D514DB089934071355E5743BF21D60", 999999, 100.0)
    assert result["type"] == "KNOWN_EXCHANGE"

"""
chainsentinel/tests/conftest.py
Patches wallet store so tests don't need a real wallets.json
"""
import pytest
from unittest.mock import patch


@pytest.fixture(autouse=True)
def mock_wallet_store():
    known = {
        "0xknownaddress": "Known-Test-Wallet",
    }
    with patch("chainsentinel.storage.wallet_store.load_known_wallets", return_value=known):
        yield

"""
chainsentinel/config/exchanges.py
Registry of known exchange hot wallets and mixer contracts.
To add a new exchange: add address.lower() -> "Exchange Name" to KNOWN_EXCHANGES.
"""

KNOWN_EXCHANGES: dict[str, str] = {
    # Binance
    "0x28c6c06298d514db089934071355e5743bf21d60": "Binance Hot Wallet 1",
    "0x21a31ee1afc51d94c2efccaa2092ad1028285549": "Binance Hot Wallet 2",
    "0xdfd5293d8e347dfe59e90efd55b2956a1343963d": "Binance Hot Wallet 3",
    "0x56eddb7aa87536c09ccc2793473599fd21a8b17f": "Binance Hot Wallet 4",
    "0x9696f59e4d72e237be84ffd425dcad154bf96976": "Binance 5",
    "0x4976a4a02f38326660d17bf34b431dc6e2eb2327": "Binance 6",
    "0xbe0eb53f46cd790cd13851d5eff43d12404d33e8": "Binance Cold Wallet",
    "0xf977814e90da44bfa03b6295a0616a897441acec": "Binance 8",
    "0x001866ae5b3de6caa5a51543fd9fb64f524f5478": "Binance 9",
    "0x8b99f3660622e21f2910ecca7fbe51d654a1517d": "Binance 10",
    # Coinbase
    "0x71660c4005ba85c37ccec55d0c4493e66fe775d3": "Coinbase Hot Wallet 1",
    "0x503828976d22510aad0201ac7ec88293211d23da": "Coinbase Hot Wallet 2",
    "0xddfabcdc4d8ffc6d5beaf154f18b778f892a0740": "Coinbase 3",
    "0x3cd751e6b0078be393132286c442345e5dc49699": "Coinbase 4",
    "0xb5d85cbf7cb3ee0d56b3bb207d5fc4b82f43f511": "Coinbase 5",
    "0xa090e606e30bd747d4e6245a1517ebe430f0057e": "Coinbase 6",
    "0xf6874c88757721a02f9a558f1c1f6af0ef292843": "Coinbase Prime",
    # Kraken
    "0x2910543af39aba0cd09dbb2d50200b3e800a63d2": "Kraken Hot Wallet 1",
    "0x0a869d79a7052c7f1b55a8ebabbea3420f0d1e13": "Kraken 2",
    "0xe853c56864a2ebe4576a807d26fdc4a0ada51919": "Kraken 3",
    "0x267be1c1d684f78cb4f6a176c4911b741e4ffdc0": "Kraken 4",
    # OKX
    "0x6cc5f688a315f3dc28a7781717a9a798a59fda7b": "OKX Hot Wallet 1",
    "0x236f9f97e0e62388479bf9e5ba4889e46b0273c3": "OKX 2",
    "0xa7efae728d2936e78bda97dc267687568dd593f3": "OKX 3",
    # Bybit
    "0xf89d7b9c864f589bbf53a82105107622b35eaa40": "Bybit Hot Wallet 1",
    "0xfd1d36995d76c0f75bbe4637c84c06e4a68bbb3a": "Bybit 2",
    # Huobi / HTX
    "0xab5c66752a9e8167967685f1450532fb96d5d24f": "Huobi Hot Wallet 1",
    "0x6748f50f686bfbca6fe8ad62b22228b87f31ff2b": "Huobi 2",
    "0xfdb16996831753d5331ff813c29a93c76834a0ad": "Huobi 3",
    "0xe93381fb4c4f14bda253907b18fad305d799241a": "Huobi 4",
    # KuCoin
    "0xd6216fc19db775df9774a6e33526131da7d19a2c": "KuCoin Hot Wallet 1",
    "0x2b5634c42055806a59e9107ed44d43c426e58258": "KuCoin 2",
    # Gate.io
    "0x0d0707963952f2fba59dd06f2b425ace40b492fe": "Gate.io Hot Wallet 1",
    "0x7793cd85c11a924478d358d49b05b37e91b5810f": "Gate.io 2",
    # Bitfinex
    "0x1151314c646ce4e0efd76d1af4760ae66a9fe30f": "Bitfinex Hot Wallet 1",
    "0x742d35cc6634c0532925a3b844bc454e4438f44e": "Bitfinex 2",
    # MEXC
    "0x75e89d5979e4f6fba9f97c104f2a18c6f5e7e1b9": "MEXC Hot Wallet",
    # LBank
    "0x4b1a99467a284cc690e3237bc69105956816f762": "LBank Hot Wallet",
    # Crypto.com
    "0x6262998ced04146fa42253a5c0af90ca02dfd2a3": "Crypto.com Hot Wallet 1",
    "0x46340b20830761efd32832a74d7169b29feb9758": "Crypto.com 2",
    # Gemini
    "0xd24400ae8bfebb18ca49be86258a3c749cf46853": "Gemini Hot Wallet 1",
    "0x07ee55aa48bb72dcc6e9d78256648910de513eca": "Gemini 2",
    # Bitstamp
    "0x00bdb5699745f5b860228c8f939abf1b9ae374ed": "Bitstamp Hot Wallet 1",
    # ChangeNOW
    "0x077d360f11d220e4d5d9ba048ab820311601bd5c": "ChangeNOW",
    # Tornado Cash (mixer)
    "0xd90e2f925da726b50c4ed8d0fb90ad053324f31b": "Tornado Cash Router",
    "0x722122df12d4e14e13ac3b6895a86e84145b6967": "Tornado Cash 0.1 ETH",
    "0x910cbd523d972eb0a6f4cae4618ad62622b39dbf": "Tornado Cash 1 ETH",
    "0xa160cdab225685da1d56aa342ad8841c3b53f291": "Tornado Cash 10 ETH",
    "0x47ce0c6ed5b0ce3d3a51fdb1c52dc66a7c3c2936": "Tornado Cash 100 ETH",
}

MIXER_KEYWORDS = ["tornado", "mixer", "tumbler", "wasabi"]


def lookup(address: str) -> dict | None:
    """
    Returns classification dict if address is a known exchange or mixer.
    Returns None if unknown.
    """
    addr = address.lower()
    if addr not in KNOWN_EXCHANGES:
        return None
    name     = KNOWN_EXCHANGES[addr]
    is_mixer = any(kw in name.lower() for kw in MIXER_KEYWORDS)
    return {
        "type":       "MIXER" if is_mixer else "KNOWN_EXCHANGE",
        "label":      name,
        "stop_trace": True,
    }

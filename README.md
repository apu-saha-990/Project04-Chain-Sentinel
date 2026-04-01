# ChainSentinel

Automated ETH wallet monitoring, spike detection, hop tracing, and forensic report generation.

Monitors a defined set of Ethereum wallets every 48 hours. Flags large inbound transactions, traces their origin through up to 7 hops, identifies exchange hot wallets and mixers, detects internal fund cycling between tracked wallets, and produces timestamped forensic reports in `.txt` and `.docx` format ready for legal review.

---

## What It Does

**Monitor** — scans all wallets every run, detects any single inbound transaction above $50,000, computes ETH and USDT volumes, diffs against the previous report to show what changed, and maintains a 10-report trend.

**Tracer** — when spikes are flagged, follows the inbound transaction chain backwards up to 7 hops. Identifies Binance, Coinbase, Kraken, OKX, Bybit, and 40+ other exchange hot wallets by name. Flags Tornado Cash and mixer contracts immediately. Detects when a hop address is already in your tracked wallet list — confirming internal cycling.

**Reports** — every run produces three files with the same timestamp:
- `eth_report_TIMESTAMP.json` — full structured data
- `eth_report_TIMESTAMP.txt` — human-readable detail, full addresses, full TX hashes
- `eth_summary_TIMESTAMP.txt` — plain-english summary with next-step recommendations

**Forensic Document** — run separately to compile all reports and traces into a single attorney-ready `.docx` with cover page, executive summary, activity timeline, wallet profiles, hop trace analysis, internal movement map, and conclusions.

---

## Project Structure

```
chainsentinel/
├── config/
│   ├── settings.py          # all constants — thresholds, paths, limits
│   ├── exchanges.py         # known exchange hot wallet registry (50+ entries)
│   └── wallets.json         # master wallet list — add/remove wallets here
│
├── core/
│   ├── fetcher.py           # all Etherscan API calls — single interface
│   ├── analyser.py          # spike detection, volume calculation, analysis
│   ├── differ.py            # diff engine — compare runs, build deltas
│   └── pricer.py            # ETH spot price feed (CoinGecko)
│
├── reports/
│   ├── builder.py           # assembles report data structure
│   ├── txt_writer.py        # full human-readable report
│   ├── summary_writer.py    # plain-english run summary
│   └── docx_writer.js       # forensic .docx generator (Node.js)
│
├── tracer/
│   ├── hop_engine.py        # hop traversal logic
│   ├── classifier.py        # exchange / mixer / origin classification
│   └── narrative.py        # plain-english narrative builder
│
├── storage/
│   ├── report_store.py      # save, load, prune report files
│   ├── trace_store.py       # save, load trace files
│   └── wallet_store.py      # read and update master wallet list
│
├── cli/
│   ├── monitor_cli.py       # monitor entry point
│   └── trace_cli.py         # tracer entry point
│
├── tests/
│   ├── test_analyser.py
│   ├── test_differ.py
│   └── test_classifier.py
│
├── data/                    # created on first run — gitignored
│   ├── reports/             # JSON + TXT reports kept here
│   └── traces/              # trace JSON files kept here
│
├── run.sh                   # cron-friendly entry point
├── .env.example
├── requirements.txt
└── package.json
```

---

## Setup

**1. Clone and install**
```bash
git clone https://github.com/YOUR_USERNAME/chainsentinel.git
cd chainsentinel
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

**2. Install Node dependencies** (for forensic .docx report only)
```bash
npm install
```

**3. Configure environment**
```bash
cp .env.example .env
# Edit .env and add your Etherscan API key
```

**4. Add your wallets**

Edit `config/wallets.json` — add any ETH address with a label:
```json
{"address": "0xYourAddress", "label": "Your-Label"}
```

---

## Usage

**Run the monitor manually**
```bash
./run.sh
# or
python3 -m chainsentinel.cli.monitor_cli
```

**Run the tracer manually**
```bash
./run.sh trace --address 0xABC...
# or interactive
python3 -m chainsentinel.cli.trace_cli
```

**Generate forensic .docx report**
```bash
./run.sh report
# or
node reports/docx_writer.js
```

**Run tests**
```bash
./run.sh test
# or
pytest tests/ -v
```

---

## Cron Setup

Run the monitor daily at 06:00 UTC:
```bash
crontab -e
# Add:
0 6 * * * /path/to/chainsentinel/run.sh >> /var/log/chainsentinel.log 2>&1
```

---

## Spike Detection

Any single inbound ETH or USDT transaction exceeding **$50,000 USD** triggers a spike alert. Threshold is configurable in `config/settings.py`:
```python
SPIKE_USD = 50_000
```

---

## Tracked Wallet Flagging

When a spike sender address matches a wallet already in your master list, it is flagged inline:
```
From: 0x0003b5aa5e30e97fcc596bb5d0f3a75255e08d4e  [TRACKED: Convergence-B-101M-Held]
```
This confirms internal fund cycling between controlled addresses.

---

## Report Retention

The last **10 report sets** are kept. Older ones are pruned automatically. Configurable in `config/settings.py`:
```python
MAX_REPORTS = 10
```

---

## API Usage

Each monitor run makes **2 Etherscan calls per wallet** (normal txs + USDT txs).

- 56 wallets = 112 calls per run
- Etherscan free tier limit = 100,000 calls/day
- Usage per daily run = 0.1% of limit

Rate limit: 4 requests/second with exponential backoff on failure.

---

## Requirements

- Python 3.11+
- Node.js 18+ (for `.docx` report only)
- Etherscan API key (free tier sufficient)

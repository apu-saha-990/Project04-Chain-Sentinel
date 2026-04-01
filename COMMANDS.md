# ChainSentinel — Command Reference

## Getting Started

```bash
git clone https://github.com/apu-saha-990/Project04-Chain-Sentinel.git
cd chain_sentinel
chmod +x setup.sh run.sh
./setup.sh
```

`setup.sh` handles everything — Python, Node, venv, packages, `.env`, data directories.
Once it reports all green, you are ready.

---

## Running ChainSentinel

```bash
./run.sh
```

Launches the interactive menu. Pick a number and hit Enter.

| Option | What it does |
|--------|-------------|
| 1 | Run Monitor — scan all wallets, detect spikes, generate reports |
| 2 | Run Tracer — trace source of funds hop by hop |
| 3 | Generate Report — build forensic .docx from all saved data |
| 4 | Run Tests — verify everything is working |
| Q | Quit |

---

## Direct Commands (no menu)

```bash
./run.sh monitor                          # run monitor directly
./run.sh trace                            # run tracer interactive
./run.sh trace --address 0xABC123...      # trace a specific address
./run.sh report                           # generate forensic .docx
./run.sh test                             # run tests
```

---

## Wallet Management

Add or edit wallets:
```bash
nano config/wallets.json
```

Check how many wallets are loaded:
```bash
python3 -c "import json; w=json.load(open('config/wallets.json')); print(len(w['wallets']), 'wallets')"
```

Check if a specific address is in the master list:
```bash
python3 -c "
import json
addr = '0xYOUR_ADDRESS_HERE'.lower()
w = json.load(open('config/wallets.json'))
match = next((x for x in w['wallets'] if x['address'].lower() == addr), None)
print(match if match else 'Not found')
"
```

Fresh clone — create your wallet list from the example:
```bash
cp config/wallets.example.json config/wallets.json
nano config/wallets.json
```

---

## Reports

List all saved reports:
```bash
ls -lh data/reports/eth_report_*.json
```

List all summaries:
```bash
ls -lh data/reports/eth_summary_*.txt
```

List all traces:
```bash
ls -lh data/traces/trace_*.json
```

View latest summary:
```bash
cat data/reports/$(ls data/reports/eth_summary_*.txt | tail -1)
```

View latest full report:
```bash
cat data/reports/$(ls data/reports/eth_report_*.txt | tail -1)
```

Count stored reports:
```bash
ls data/reports/eth_report_*.json 2>/dev/null | wc -l
```

Delete all reports and start fresh:
```bash
rm -rf data/
```

---

## Git

Push changes:
```bash
git add -A
git commit -m "your message"
git push origin main
```

Check nothing sensitive is staged:
```bash
git status
```

> `data/` is gitignored — reports and traces never get pushed.
> `.env` is gitignored — your API key never gets pushed.
> `config/wallets.json` is gitignored — your wallet list never gets pushed.

---

## Troubleshooting

**API key not set or not working:**
```bash
cat .env
source .venv/bin/activate
```

**Permission denied:**
```bash
chmod +x run.sh setup.sh
```

**Something broken — run setup to re-verify:**
```bash
./setup.sh
```

**Check Etherscan API is alive:**
```bash
curl "https://api.etherscan.io/v2/api?chainid=1&module=account&action=balance&address=0x0000000000000000000000000000000000000000&tag=latest&apikey=YOUR_KEY"
```

**Save a run to log file:**
```bash
./run.sh monitor 2>&1 | tee run.log
```

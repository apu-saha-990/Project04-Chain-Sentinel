# ChainSentinel — Command Reference

## First Time Setup

```bash
git clone https://github.com/YOUR_USERNAME/chainsentinel.git
cd chainsentinel
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
npm install
cp .env.example .env
```

Edit `.env` and add your key:
```
ETHERSCAN_API_KEY=your_key_here
```

---

## Daily Use

### Activate environment
```bash
cd chainsentinel
source .venv/bin/activate
```

### Run the monitor
```bash
./run.sh
```

### Run the tracer — interactive
```bash
./run.sh trace
```

### Run the tracer — specific address
```bash
./run.sh trace --address 0xABC123...
```

### Generate forensic .docx report
```bash
./run.sh report
```

### Run tests
```bash
./run.sh test
```

---

## Wallet Management

Add a wallet — edit directly:
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

---

## Reports

List all saved reports:
```bash
ls -lh data/reports/eth_report_*.json
```

List all saved summaries:
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

View latest report:
```bash
cat data/reports/$(ls data/reports/eth_report_*.txt | tail -1)
```

Count how many reports are stored:
```bash
ls data/reports/eth_report_*.json 2>/dev/null | wc -l
```

Manually delete all reports and start fresh:
```bash
rm -rf data/
```

---

## Git

Push to GitHub:
```bash
git add -A
git commit -m "your message"
git push origin main
```

Check what would be pushed (nothing sensitive):
```bash
git status
```

> `data/` is in `.gitignore` — reports and traces are never pushed.
> `.env` is in `.gitignore` — your API key is never pushed.

---

## Troubleshooting

**ETHERSCAN_API_KEY not set:**
```bash
cat .env  # check it's there
source .venv/bin/activate  # make sure venv is active
```

**Module not found:**
```bash
source .venv/bin/activate
pip install -e .
```

**Permission denied on run.sh:**
```bash
chmod +x run.sh
```

**Check Etherscan API is responding:**
```bash
curl "https://api.etherscan.io/v2/api?chainid=1&module=account&action=balance&address=0x0000000000000000000000000000000000000000&tag=latest&apikey=YOUR_KEY"
```

**Save run output to file:**
```bash
python3 -m chainsentinel.cli.monitor_cli 2>&1 | tee run.log
```

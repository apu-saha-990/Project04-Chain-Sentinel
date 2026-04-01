#!/usr/bin/env bash
# ChainSentinel — single entry point
# Used by cron and for manual runs
#
# CRON (daily at 06:00):
#   0 6 * * * /path/to/chainsentinel/run.sh >> /var/log/chainsentinel.log 2>&1
#
# USAGE:
#   ./run.sh              — run monitor
#   ./run.sh trace        — run tracer (interactive)
#   ./run.sh trace --address 0xABC...

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Activate venv if it exists
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
fi

# Load .env if present
if [ -f ".env" ]; then
    export $(grep -v '^#' .env | xargs)
fi

COMMAND="${1:-monitor}"

case "$COMMAND" in
    monitor)
        python3 -m chainsentinel.cli.monitor_cli
        ;;
    trace)
        shift
        python3 -m chainsentinel.cli.trace_cli "$@"
        ;;
    report)
        node reports/docx_writer.js
        ;;
    test)
        python3 -m pytest tests/ -v
        ;;
    *)
        echo "Usage: $0 [monitor|trace|report|test]"
        exit 1
        ;;
esac

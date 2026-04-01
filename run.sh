#!/usr/bin/env bash
# ChainSentinel — master entry point

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

# ── Menu ──────────────────────────────────────────────────────────────────────

show_menu() {
    clear
    echo ""
    echo "  ██████╗██╗  ██╗ █████╗ ██╗███╗   ██╗    ███████╗███████╗███╗   ██╗████████╗██╗███╗   ██╗███████╗██╗"
    echo " ██╔════╝██║  ██║██╔══██╗██║████╗  ██║    ██╔════╝██╔════╝████╗  ██║╚══██╔══╝██║████╗  ██║██╔════╝██║"
    echo " ██║     ███████║███████║██║██╔██╗ ██║    ███████╗█████╗  ██╔██╗ ██║   ██║   ██║██╔██╗ ██║█████╗  ██║"
    echo " ██║     ██╔══██║██╔══██║██║██║╚██╗██║    ╚════██║██╔══╝  ██║╚██╗██║   ██║   ██║██║╚██╗██║██╔══╝  ██║"
    echo " ╚██████╗██║  ██║██║  ██║██║██║ ╚████║    ███████║███████╗██║ ╚████║   ██║   ██║██║ ╚████║███████╗███████╗"
    echo "  ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝╚═╝  ╚═══╝   ╚══════╝╚══════╝╚═╝  ╚═══╝   ╚═╝   ╚═╝╚═╝  ╚═══╝╚══════╝╚══════╝"
    echo ""
    echo "  ETH Wallet Monitor · Hop Tracer · Forensic Reports"
    echo ""
    echo "  ─────────────────────────────────────────────────────────"
    echo ""
    echo "    [1]  Run Monitor          Scan all wallets, detect spikes"
    echo "    [2]  Run Tracer           Trace source of funds hop by hop"
    echo "    [3]  Generate Report      Build forensic .docx report"
    echo "    [4]  Run Tests            Verify everything is working"
    echo ""
    echo "    [Q]  Quit"
    echo ""
    echo "  ─────────────────────────────────────────────────────────"
    echo ""
    printf "  Select: "
}

# ── Direct call with argument (for scripts / trace --address etc) ─────────────

if [ $# -gt 0 ]; then
    COMMAND="$1"
    shift
    case "$COMMAND" in
        monitor|1)
            python3 -m cli.monitor_cli
            ;;
        trace|2)
            python3 -m cli.trace_cli "$@"
            ;;
        report|3)
            node reports/docx_writer.js "$@"
            ;;
        test|4)
            python3 -m pytest tests/ -v
            ;;
        *)
            echo "Unknown command: $COMMAND"
            echo "Usage: ./run.sh [monitor|trace|report|test]"
            exit 1
            ;;
    esac
    exit 0
fi

# ── Interactive menu ──────────────────────────────────────────────────────────

while true; do
    show_menu
    read -r choice
    echo ""
    case "$choice" in
        1)
            echo "  Starting monitor..."
            echo ""
            python3 -m cli.monitor_cli
            echo ""
            printf "  Press Enter to return to menu..."
            read -r
            ;;
        2)
            echo "  Starting tracer..."
            echo ""
            python3 -m cli.trace_cli
            echo ""
            printf "  Press Enter to return to menu..."
            read -r
            ;;
        3)
            echo "  Generating forensic report..."
            echo ""
            node reports/docx_writer.js
            echo ""
            printf "  Press Enter to return to menu..."
            read -r
            ;;
        4)
            echo "  Running tests..."
            echo ""
            python3 -m pytest tests/ -v
            echo ""
            printf "  Press Enter to return to menu..."
            read -r
            ;;
        q|Q)
            echo "  Goodbye."
            echo ""
            exit 0
            ;;
        *)
            echo "  Invalid option. Press Enter to try again."
            read -r
            ;;
    esac
done

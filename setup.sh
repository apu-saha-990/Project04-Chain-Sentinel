#!/usr/bin/env bash
# ChainSentinel — Setup & Dependency Checker
# Run this once before using ChainSentinel for the first time.
# Run again anytime to verify everything is still healthy.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# ── Colours ───────────────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Colour

PASS="${GREEN}✓${NC}"
FAIL="${RED}✗${NC}"
WARN="${YELLOW}!${NC}"
INFO="${BLUE}→${NC}"

ERRORS=0

# ── Helpers ───────────────────────────────────────────────────────────────────

print_header() {
    clear
    echo ""
    echo -e "  ${BOLD}ChainSentinel — Setup & Dependency Check${NC}"
    echo "  ─────────────────────────────────────────────────────────"
    echo ""
}

ok()   { echo -e "  ${PASS}  $1"; }
fail() { echo -e "  ${FAIL}  $1"; ERRORS=$((ERRORS + 1)); }
warn() { echo -e "  ${WARN}  $1"; }
info() { echo -e "  ${INFO}  $1"; }

ask() {
    printf "\n  %s [y/N]: " "$1"
    read -r ans
    echo ""
    [[ "$ans" =~ ^[Yy]$ ]]
}

# ── Checks ────────────────────────────────────────────────────────────────────

check_python() {
    echo -e "  ${BOLD}Python${NC}"
    if command -v python3 &>/dev/null; then
        VERSION=$(python3 --version 2>&1 | awk '{print $2}')
        MAJOR=$(echo "$VERSION" | cut -d. -f1)
        MINOR=$(echo "$VERSION" | cut -d. -f2)
        if [ "$MAJOR" -ge 3 ] && [ "$MINOR" -ge 11 ]; then
            ok "Python $VERSION"
        else
            fail "Python $VERSION found — need 3.11 or higher"
            if ask "Attempt to install Python 3.11 via apt?"; then
                sudo apt update && sudo apt install -y python3.11 python3.11-venv
            fi
        fi
    else
        fail "Python 3 not found"
        if ask "Install Python 3.11 via apt?"; then
            sudo apt update && sudo apt install -y python3.11 python3.11-venv
        fi
    fi
}

check_pip() {
    echo ""
    echo -e "  ${BOLD}pip${NC}"
    if python3 -m pip --version &>/dev/null; then
        ok "pip available"
    else
        fail "pip not found"
        if ask "Install pip?"; then
            sudo apt install -y python3-pip
        fi
    fi
}

check_node() {
    echo ""
    echo -e "  ${BOLD}Node.js${NC}"
    if command -v node &>/dev/null; then
        VERSION=$(node --version)
        MAJOR=$(echo "$VERSION" | tr -d 'v' | cut -d. -f1)
        if [ "$MAJOR" -ge 18 ]; then
            ok "Node.js $VERSION"
        else
            fail "Node.js $VERSION found — need v18 or higher"
            if ask "Install Node.js 18 via NodeSource?"; then
                curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
                sudo apt install -y nodejs
            fi
        fi
    else
        fail "Node.js not found (needed for forensic .docx report)"
        if ask "Install Node.js 18 via NodeSource?"; then
            curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
            sudo apt install -y nodejs
        fi
    fi
}

check_npm_packages() {
    echo ""
    echo -e "  ${BOLD}Node packages${NC}"
    if [ -d "node_modules/docx" ]; then
        ok "docx package installed"
    else
        fail "Node packages not installed"
        if ask "Run npm install now?"; then
            npm install
            ok "Node packages installed"
        fi
    fi
}

check_venv() {
    echo ""
    echo -e "  ${BOLD}Python virtual environment${NC}"
    if [ -d ".venv" ]; then
        ok "Virtual environment exists (.venv)"
    else
        fail "No virtual environment found"
        if ask "Create virtual environment now?"; then
            python3 -m venv .venv
            ok "Virtual environment created"
        fi
    fi
}

check_python_packages() {
    echo ""
    echo -e "  ${BOLD}Python packages${NC}"

    # Activate venv for the check
    if [ -f ".venv/bin/activate" ]; then
        source .venv/bin/activate
    fi

    MISSING=()

    python3 -c "import requests" 2>/dev/null    || MISSING+=("requests")
    python3 -c "import dotenv" 2>/dev/null      || MISSING+=("python-dotenv")
    python3 -c "import pytest" 2>/dev/null      || MISSING+=("pytest")

    if [ ${#MISSING[@]} -eq 0 ]; then
        ok "All Python packages installed"
    else
        fail "Missing packages: ${MISSING[*]}"
        if ask "Run pip install -r requirements.txt now?"; then
            pip install -r requirements.txt
            ok "Python packages installed"
        fi
    fi

    # Check chainsentinel itself is installed
    if python3 -c "import cli.monitor_cli" 2>/dev/null; then
        ok "ChainSentinel package installed"
    else
        fail "ChainSentinel package not installed"
        if ask "Run pip install -e . now?"; then
            pip install -e .
            ok "ChainSentinel installed"
        fi
    fi
}

check_env_file() {
    echo ""
    echo -e "  ${BOLD}Environment (.env)${NC}"
    if [ -f ".env" ]; then
        if grep -q "ETHERSCAN_API_KEY=your_etherscan_api_key_here" .env; then
            warn ".env exists but API key is still the placeholder"
            echo ""
            echo "  Edit .env and replace the placeholder with your real key:"
            echo "  ETHERSCAN_API_KEY=your_real_key_here"
            echo ""
            printf "  Open .env in nano now? [y/N]: "
            read -r ans
            echo ""
            if [[ "$ans" =~ ^[Yy]$ ]]; then
                nano .env
            fi
        elif grep -q "ETHERSCAN_API_KEY=" .env; then
            KEY=$(grep "ETHERSCAN_API_KEY=" .env | cut -d= -f2)
            if [ -z "$KEY" ]; then
                warn ".env exists but ETHERSCAN_API_KEY is empty"
                ERRORS=$((ERRORS + 1))
            else
                ok ".env configured with API key"
            fi
        else
            warn ".env exists but ETHERSCAN_API_KEY not found in it"
            ERRORS=$((ERRORS + 1))
        fi
    else
        fail ".env file not found"
        if ask "Create .env from .env.example now?"; then
            cp .env.example .env
            ok ".env created"
            echo ""
            echo "  Now edit .env and add your Etherscan API key:"
            echo ""
            printf "  Open .env in nano now? [y/N]: "
            read -r ans
            echo ""
            if [[ "$ans" =~ ^[Yy]$ ]]; then
                nano .env
            fi
        fi
    fi
}

check_data_dirs() {
    echo ""
    echo -e "  ${BOLD}Data directories${NC}"
    mkdir -p data/reports data/traces
    ok "data/reports/ ready"
    ok "data/traces/ ready"
}

check_run_permissions() {
    echo ""
    echo -e "  ${BOLD}Permissions${NC}"
    if [ -x "run.sh" ]; then
        ok "run.sh is executable"
    else
        chmod +x run.sh
        ok "run.sh — fixed permissions"
    fi
    if [ -x "setup.sh" ]; then
        ok "setup.sh is executable"
    else
        chmod +x setup.sh
        ok "setup.sh — fixed permissions"
    fi
}

# ── Final result ──────────────────────────────────────────────────────────────

print_result() {
    echo ""
    echo "  ─────────────────────────────────────────────────────────"
    echo ""
    if [ "$ERRORS" -eq 0 ]; then
        echo -e "  ${GREEN}${BOLD}All checks passed. ChainSentinel is ready.${NC}"
        echo ""
        echo "  Run:  ./run.sh"
    else
        echo -e "  ${RED}${BOLD}${ERRORS} issue(s) need attention before running ChainSentinel.${NC}"
        echo ""
        echo "  Fix the issues above, then run ./setup.sh again to verify."
    fi
    echo ""
    echo "  ─────────────────────────────────────────────────────────"
    echo ""
}

# ── Main ──────────────────────────────────────────────────────────────────────

print_header

check_python
check_pip
check_node
check_venv
check_python_packages
check_npm_packages
check_env_file
check_data_dirs
check_run_permissions

print_result

exit 0

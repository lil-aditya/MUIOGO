#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

VENV_DIR="${MUIOGO_VENV_DIR:-$HOME/.venvs/muiogo}"
DATA_STORAGE="$PROJECT_ROOT/WebAPP/DataStorage"
DEMO_DATA="$DATA_STORAGE/CLEWs Demo"
DEMO_MARKER="$DATA_STORAGE/.demo_data_installed.json"
ENV_FILE="$PROJECT_ROOT/.env"

echo "MUIOGO Uninstall / Reset"
echo "------------------------"
echo
echo "The following items may be removed:"
echo "  Virtual environment: $VENV_DIR"
echo "  Demo data directory: $DEMO_DATA"
echo "  Demo marker file: $DEMO_MARKER"
echo "  .env entries for MUIOGO"

echo
read -p "Continue? (y/N): " confirm

if [[ "$confirm" != "y" ]]; then
    echo "Aborted."
    exit 0
fi

if [ -d "$VENV_DIR" ]; then
    rm -rf "$VENV_DIR"
    echo "Removed virtual environment."
fi

if [ -d "$DEMO_DATA" ]; then
    rm -rf "$DEMO_DATA"
    echo "Removed demo data."
fi

if [ -f "$DEMO_MARKER" ]; then
    rm "$DEMO_MARKER"
    echo "Removed demo marker."
fi

if [ -f "$ENV_FILE" ]; then
    sed -i.bak '/MUIOGO_SECRET_KEY/d' "$ENV_FILE"
    sed -i.bak '/SOLVER_GLPK_PATH/d' "$ENV_FILE"
    sed -i.bak '/SOLVER_CBC_PATH/d' "$ENV_FILE"
    echo "Removed MUIOGO variables from .env"
fi

echo
echo "Uninstall complete."
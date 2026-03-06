#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────────────────────
# MUIOGO macOS Test Reset
#
# Removes the local MUIOGO venv, repo .env, demo data installed by setup,
# and Homebrew solver packages so setup can be tested from a clean state.
#
# Usage:
#   ./scripts/reset_macos_test.sh
# ──────────────────────────────────────────────────────────────────────────────
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
VENV_DIR="${MUIOGO_VENV_DIR:-$HOME/.venvs/muiogo}"
ENV_FILE="$PROJECT_ROOT/.env"
DEMO_MARKER="$PROJECT_ROOT/WebAPP/DataStorage/.demo_data_installed.json"
DEMO_DIR="$PROJECT_ROOT/WebAPP/DataStorage/CLEWs Demo"

if [ "$(uname -s)" != "Darwin" ]; then
    echo "ERROR: This reset script is for macOS only."
    exit 1
fi

REAL_HOME="$(cd "$HOME" && pwd)"
REAL_VENV_DIR="$VENV_DIR"

case "$REAL_VENV_DIR" in
    "~/"*)
        REAL_VENV_DIR="$REAL_HOME/${REAL_VENV_DIR#~/}"
        ;;
esac

case "$REAL_VENV_DIR" in
    /*)
        ;;
    *)
        REAL_VENV_DIR="$PWD/$REAL_VENV_DIR"
        ;;
esac

REAL_VENV_DIR="${REAL_VENV_DIR%/}"
REAL_VENV_BASENAME="$(basename "$REAL_VENV_DIR")"
REAL_VENV_PARENT="$(dirname "$REAL_VENV_DIR")"

if [ -z "$REAL_VENV_BASENAME" ] || [ "$REAL_VENV_BASENAME" = "." ] || [ "$REAL_VENV_BASENAME" = ".." ]; then
    echo "ERROR: Refusing to remove unsafe venv path: $REAL_VENV_DIR"
    exit 1
fi

if ! REAL_VENV_PARENT="$(cd "$REAL_VENV_PARENT" 2>/dev/null && pwd -P)"; then
    echo "ERROR: Could not resolve venv parent directory: $REAL_VENV_PARENT"
    exit 1
fi

REAL_VENV_DIR="$REAL_VENV_PARENT/$REAL_VENV_BASENAME"

case "$REAL_VENV_DIR" in
    ""|"/"|"$REAL_HOME"|"$REAL_HOME/"|"$REAL_HOME/.venvs"|"$REAL_HOME/.venvs/")
        echo "ERROR: Refusing to remove unsafe venv path: $REAL_VENV_DIR"
        echo "Set MUIOGO_VENV_DIR to the MUIOGO venv directory, not a parent folder."
        exit 1
        ;;
esac

case "$REAL_VENV_DIR" in
    "$REAL_HOME/.venvs/"*|"$REAL_HOME/.venvs")
        ;;
    *)
        echo "ERROR: Refusing to remove venv outside $REAL_HOME/.venvs: $REAL_VENV_DIR"
        echo "Unset MUIOGO_VENV_DIR or point it at the dedicated MUIOGO venv directory."
        exit 1
        ;;
esac

echo "This will remove MUIOGO test state from this Mac:"
echo "  - $REAL_VENV_DIR"
echo "  - $ENV_FILE"
echo "  - $DEMO_MARKER"
echo "  - $DEMO_DIR"
if command -v brew >/dev/null 2>&1; then
    echo "  - Homebrew packages glpk and cbc (if installed)"
else
    echo "  - Homebrew solver uninstall will be skipped (brew not found)"
fi
echo
read -r -p "Continue? [y/N]: " reply
case "$reply" in
    [Yy]|[Yy][Ee][Ss]) ;;
    *)
        echo "Cancelled."
        exit 1
        ;;
esac

remove_path() {
    local target="$1"
    if [ -e "$target" ]; then
        rm -rf "$target"
        echo "Removed $target"
    else
        echo "Not present: $target"
    fi
}

remove_path "$REAL_VENV_DIR"
remove_path "$ENV_FILE"
remove_path "$DEMO_MARKER"
remove_path "$DEMO_DIR"

if command -v brew >/dev/null 2>&1; then
    if brew list --formula glpk >/dev/null 2>&1; then
        if brew uninstall glpk; then
            echo "Uninstalled Homebrew formula: glpk"
        else
            echo "WARNING: Could not uninstall Homebrew formula: glpk"
        fi
    else
        echo "Homebrew formula not installed: glpk"
    fi

    if brew list --formula cbc >/dev/null 2>&1; then
        if brew uninstall cbc; then
            echo "Uninstalled Homebrew formula: cbc"
        else
            echo "WARNING: Could not uninstall Homebrew formula: cbc"
        fi
    else
        echo "Homebrew formula not installed: cbc"
    fi
fi

echo
if [ -n "${SOLVER_GLPK_PATH:-}" ] || [ -n "${SOLVER_CBC_PATH:-}" ]; then
    echo "NOTE: SOLVER_GLPK_PATH or SOLVER_CBC_PATH is set in the current shell."
fi
echo "Open a NEW terminal before running ./scripts/setup.sh again."

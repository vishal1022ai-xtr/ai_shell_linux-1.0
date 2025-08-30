#!/usr/bin/env bash
#
# Unified AI Shell v5.0 - Startup Script
#
# This script is the recommended way to start the AI Shell.
# It handles environment setup, dependency checks, and then launches the main application.
#

# --- Style Definitions (for beautiful output) ---
COLOR_BLUE='\033[1;34m'
COLOR_GREEN='\033[1;32m'
COLOR_YELLOW='\033[1;33m'
COLOR_RED='\033[1;31m'
COLOR_RESET='\033[0m'

# Helper function for printing styled messages
info() {
    echo -e "${COLOR_BLUE}ℹ ${1}${COLOR_RESET}"
}

success() {
    echo -e "${COLOR_GREEN}✓ ${1}${COLOR_RESET}"
}

warn() {
    echo -e "${COLOR_YELLOW}⚠ ${1}${COLOR_RESET}"
}

error() {
    echo -e "${COLOR_RED}✗ ${1}${COLOR_RESET}"
}

# --- Main Script Logic ---

# Immediately exit if any command fails
set -e

info "Starting the Unified AI Shell..."

# 1. Navigate to the script's directory to ensure all paths are relative
#    This allows the script to be run from anywhere on the system.
cd "$(dirname "$0")"
success "Running in directory: $(pwd)"

# 2. Check for and set up the Python virtual environment
VENV_DIR="venv"
if [ ! -d "$VENV_DIR" ]; then
    warn "Virtual environment not found. Creating one..."
    # Find a suitable python3 interpreter
    if command -v python3 &>/dev/null; then
        PYTHON_EXEC="python3"
    elif command -v python &>/dev/null; then
        PYTHON_EXEC="python"
    else
        error "Python 3 is not installed or not in PATH. Please install Python 3.8+."
        exit 1
    fi
    $PYTHON_EXEC -m venv "$VENV_DIR"
    success "Virtual environment created at './${VENV_DIR}'."
fi

# 3. Activate the virtual environment
# The 'source' command loads the venv's activation script into the current shell session.
source "${VENV_DIR}/bin/activate"
success "Virtual environment activated."

# 4. Install/Verify dependencies from requirements.txt
info "Checking project dependencies..."
if [ -f "requirements.txt" ]; then
    # Use the virtual environment's pip to install all required packages
    python -m pip install -r requirements.txt --quiet
    success "All dependencies are installed and up to date."
else
    error "'requirements.txt' not found! Cannot verify dependencies."
    exit 1
fi

# 5. Launch the main Python application
info "Launching the AI Shell application (main.py)..."
echo "--------------------------------------------------"
# The 'exec' command replaces the shell process with the Python process.
exec python main.py "$@"



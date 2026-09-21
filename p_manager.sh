#!/bin/bash

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

VENV="$SCRIPT_DIR/.venv"

echo "=== SN Generator ==="

# -----------------------------
# Create virtual environment
# -----------------------------

if [ ! -d "$VENV" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv "$VENV"
fi

# -----------------------------
# Activate environment
# -----------------------------

source "$VENV/bin/activate"

# -----------------------------
# Install dependencies
# -----------------------------

echo "Installing Python dependencies..."

python -m pip install --upgrade pip
python -m pip install psycopg2-binary

# -----------------------------
# Database configuration
# -----------------------------

export SN_DB_HOST="postgres"
export SN_DB_PORT="5432"
export SN_DB_NAME="your_database"
export SN_DB_USER="SN_GENERATOR"
export SN_DB_PASSWORD="your_password"

# -----------------------------
# Python service
# -----------------------------

export SN_GENERATOR_HOST="0.0.0.0"
export SN_GENERATOR_PORT="9001"

echo "Starting SN Generator..."
echo "Listening on port $SN_GENERATOR_PORT"

if ! docker ps --format '{{.Names}}' | grep -q '^postgres$'; then
    echo "PostgreSQL container is not running, unit testing starting"
    python serialgen.py --u
    exit 1
fi


python serialgen.py


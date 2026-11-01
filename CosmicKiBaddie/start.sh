#!/usr/bin/env bash
# ==============================================================================
# Cosmic ki baddie - Startup & Deployment Script
# Tailored for Side Quest Studio
# ==============================================================================

set -e

echo "🌌 Initializing Cosmic ki baddie..."

# Navigate to script directory
cd "$(dirname "$0")"

# Create data directory for SQLite database
mkdir -p data

# Check Python environment
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.10+."
    exit 1
fi

echo "📦 Verifying dependencies from requirements.txt..."
python3 -m pip install -q -r requirements.txt || true

# Check for .env file
if [ ! -f .env ]; then
    if [ -f .env.example ]; then
        echo "⚠️ .env file not found. Copying .env.example to .env..."
        cp .env.example .env
        echo "⚠️ Please edit .env and insert your DISCORD_TOKEN before starting the bot."
    fi
fi

echo "🚀 Starting Cosmic ki baddie..."
exec python3 main.py

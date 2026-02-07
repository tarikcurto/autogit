#!/bin/bash

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT_PATH="$SCRIPT_DIR/autogit.py"
CONFIG_PATH="$SCRIPT_DIR/config.json"
CRON_IDENTIFIER="autogit-auto-sync"
CRON_SCHEDULE="*/5 * * * *"  # Every 5 minutes

# Check if autogit.py exists
if [ ! -f "$SCRIPT_PATH" ]; then
    echo "[ERROR] autogit.py not found at $SCRIPT_PATH"
    exit 1
fi

# Check if config.json exists
if [ ! -f "$CONFIG_PATH" ]; then
    echo "[ERROR] config.json not found at $CONFIG_PATH"
    exit 1
fi

# Check if cron is available
if ! command -v crontab &> /dev/null; then
    echo "[ERROR] crontab command not found. Please install cron."
    exit 1
fi

echo "[INFO] Checking if autogit cron job is already installed..."

# Get current crontab (if it exists)
CURRENT_CRONTAB=$(crontab -l 2>/dev/null || echo "")

# Check if autogit is already in crontab
if echo "$CURRENT_CRONTAB" | grep -q "$CRON_IDENTIFIER"; then
    echo "[OK] autogit cron job already installed."
    echo ""
    echo "Current cron entry:"
    echo "$CURRENT_CRONTAB" | grep "$CRON_IDENTIFIER"
    exit 0
fi

# Create new crontab entry with identifier comment
NEW_CRON_ENTRY="# $CRON_IDENTIFIER
$CRON_SCHEDULE python3 $SCRIPT_PATH -c $CONFIG_PATH >> /tmp/autogit.log 2>&1"

# Install new cron job
echo "$CURRENT_CRONTAB" | {
    cat
    echo ""
    echo "$NEW_CRON_ENTRY"
} | crontab -

echo "[OK] autogit cron job installed successfully."
echo ""
echo "Schedule: $CRON_SCHEDULE"
echo "Script: $SCRIPT_PATH"
echo "Config: $CONFIG_PATH"
echo "Logs: /tmp/autogit.log"
echo ""
echo "To view the installed cron job, run: crontab -l"
echo "To remove it, run: crontab -e and delete the autogit entry"

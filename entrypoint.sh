#!/bin/bash
set -e

# Install Python dependencies via uv
echo "Installing Python dependencies..."
uv pip install -r - <<< "bottle"

# Start CUPS daemon
echo "Starting CUPS daemon..."
/etc/init.d/cups start || true

# If PRINTER is a URI, create a CUPS queue for it
PRINTER="${PRINTER:-}"
if [[ "$PRINTER" == ipp://* || "$PRINTER" == ipps://* || "$PRINTER" == socket://* || "$PRINTER" == lpd://* ]]; then
    QUEUE_NAME="remote-printer"
    echo "Creating CUPS queue '$QUEUE_NAME' pointing to $PRINTER..."
    lpadmin -p "$QUEUE_NAME" -E -v "$PRINTER" -m everywhere 2>/dev/null || true
    export PRINTER="$QUEUE_NAME"
    echo "Queue created. Using queue: $PRINTER"
fi

# Run the app
exec uv run /app/spoolcat.py

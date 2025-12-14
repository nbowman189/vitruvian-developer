#!/bin/bash

# Start both public and private workspace servers
# Public Portfolio: http://localhost:8080
# Private Workspace: http://localhost:8081

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=========================================="
echo "Starting Both Servers"
echo "=========================================="
echo ""
echo "Public Portfolio Server (port 8080)"
echo "  Access: http://localhost:8080"
echo "  Run: python3 app.py"
echo ""
echo "Private Workspace Server (port 8081)"
echo "  Access: http://localhost:8081"
echo "  Run: python3 app-private.py"
echo ""
echo "Press Ctrl+C to stop"
echo "=========================================="
echo ""

# Start public server in background
echo "Starting public server..."
cd "$SCRIPT_DIR"
python3 app.py &
PUBLIC_PID=$!

# Brief delay to ensure first server starts
sleep 2

# Start private server in background
echo "Starting private server..."
python3 app-private.py &
PRIVATE_PID=$!

echo ""
echo "Both servers are running!"
echo "  Public (Portfolio): http://localhost:8080"
echo "  Private (Workspace): http://localhost:8081"
echo ""
echo "PIDs: Public=$PUBLIC_PID, Private=$PRIVATE_PID"
echo "Press Ctrl+C to stop both servers"
echo ""

# Wait for both processes
wait $PUBLIC_PID $PRIVATE_PID

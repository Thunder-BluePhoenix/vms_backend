#!/bin/bash

# vms/chat_vms/start_socket_server.sh
# Script to start Socket.IO server for chat application

echo "Starting Chat Socket.IO Server..."

# Navigate to the correct directory
cd "$(dirname "$0")"

# Set Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)/../.."

# Start the socket server
python3 socket_server.py &

# Store PID for later cleanup
echo $! > socket_server.pid

echo "Socket.IO server started with PID $(cat socket_server.pid)"
echo "Server running on http://127.0.0.1:8013"
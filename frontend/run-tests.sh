#!/bin/bash

# GCPHound Frontend Test Runner
# This script manages the server lifecycle and runs tests systematically

set -e

echo "🚀 GCPHound Frontend Test Runner"
echo "================================="

# Function to cleanup background processes
cleanup() {
    echo "🧹 Cleaning up background processes..."
    pkill -f "vite.*preview" 2>/dev/null || true
    pkill -f "playwright" 2>/dev/null || true
    wait 2>/dev/null || true
}

# Set trap to cleanup on exit
trap cleanup EXIT

# Build the application first
echo "📦 Building application..."
npm run build

# Kill any existing servers
cleanup

# Start the preview server in background
echo "🖥️  Starting preview server..."
npm run preview > server.log 2>&1 &
SERVER_PID=$!

# Wait for server to be ready
echo "⏳ Waiting for server to start..."
for i in {1..30}; do
    if curl -s http://localhost:4173 > /dev/null 2>&1; then
        echo "✅ Server is ready!"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "❌ Server failed to start within 30 seconds"
        exit 1
    fi
    sleep 1
done

# Run tests with server running
echo "🧪 Running E2E tests..."
export SKIP_SERVER_START=true
export E2E_BASE_URL=http://localhost:4173

# Run tests based on arguments or run all
if [ $# -eq 0 ]; then
    echo "Running all E2E tests..."
    npm run test:e2e:automated
else
    echo "Running specific tests: $@"
    npm run test:e2e:automated -- "$@"
fi

echo "✅ Tests completed!" 
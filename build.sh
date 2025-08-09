#!/bin/bash

set -e

# Detect docker-compose
if command -v docker-compose &> /dev/null; then
    COMPOSE="docker-compose"
else
    COMPOSE="docker compose"
fi

echo "🔨 Building Docker image..."
$COMPOSE build

echo "✅ Done! Run './start.sh' to start the server"
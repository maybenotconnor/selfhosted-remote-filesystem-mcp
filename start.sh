#!/bin/bash

set -e

# Detect docker-compose command
if command -v docker-compose &> /dev/null; then
    COMPOSE="docker-compose"
else
    COMPOSE="docker compose"
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🚀 Remote Filesystem MCP Server"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Create directories
[ ! -d "data" ] && mkdir -p data && echo "📁 Created ./data directory"
[ ! -d "config" ] && mkdir -p config && echo "🔐 Created ./config directory"

# Build and start
echo "🔨 Building..."
$COMPOSE build --quiet

echo "🎯 Starting..."
$COMPOSE up -d

# Wait and show logs
sleep 2

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔑 AUTHENTICATION TOKENS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
$COMPOSE logs filesystem-mcp 2>/dev/null | grep -A 20 "AUTHENTICATION" || true

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Server ready at: http://localhost:8080/mcp"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📖 Commands:"
echo "   Logs:    $COMPOSE logs -f"
echo "   Stop:    $COMPOSE down"
echo "   Tokens:  cat ./config/tokens.txt"
#!/bin/bash

# Build script for Remote Filesystem MCP Server

set -e

echo "🔨 Building Remote Filesystem MCP Server..."
echo "=========================================="

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if docker-compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "⚠️  docker-compose not found, trying docker compose..."
    COMPOSE_CMD="docker compose"
else
    COMPOSE_CMD="docker-compose"
fi

# Build the Docker image
echo "📦 Building Docker image..."
$COMPOSE_CMD build

echo ""
echo "✅ Build completed successfully!"
echo ""
echo "🚀 To start the server, run:"
echo "   $COMPOSE_CMD up -d"
echo ""
echo "📖 To view logs and get auth tokens:"
echo "   $COMPOSE_CMD logs filesystem-mcp"
echo ""
echo "🛑 To stop the server:"
echo "   $COMPOSE_CMD down"
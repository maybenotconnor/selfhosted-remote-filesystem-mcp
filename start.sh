#!/bin/bash

# Quick start script for Remote Filesystem MCP Server

set -e

echo "🚀 Remote Filesystem MCP Server - Quick Start"
echo "============================================="
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    echo "   Visit: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if docker-compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "⚠️  docker-compose not found, trying docker compose..."
    COMPOSE_CMD="docker compose"
else
    COMPOSE_CMD="docker-compose"
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file from template..."
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo "   ✅ Created .env file. You can edit it to customize settings."
    else
        echo "   ⚠️  No .env.example found, using defaults."
    fi
fi

# Create data directory if it doesn't exist
if [ ! -d "data" ]; then
    echo "📁 Creating data directory..."
    mkdir -p data
    echo "   ✅ Created ./data directory"
fi

# Build the image
echo ""
echo "🔨 Building Docker image..."
$COMPOSE_CMD build --quiet

# Start the server
echo "🎯 Starting server..."
$COMPOSE_CMD up -d

# Wait for server to start
echo "⏳ Waiting for server to initialize..."
sleep 3

# Show the logs to display auth tokens
echo ""
echo "="*60
echo "📋 Server Logs (showing authentication tokens):"
echo "="*60
$COMPOSE_CMD logs filesystem-mcp | head -30

echo ""
echo "="*60
echo "✅ Server is running!"
echo "="*60
echo ""
echo "📍 Endpoints:"
echo "   - MCP: http://localhost:8080/mcp"
echo "   - Health: http://localhost:8080/health"
echo ""
echo "🔑 Authentication tokens are shown above."
echo "   Copy them for use with MCP clients."
echo ""
echo "📖 Commands:"
echo "   View logs:    $COMPOSE_CMD logs -f filesystem-mcp"
echo "   Stop server:  $COMPOSE_CMD down"
echo "   Restart:      $COMPOSE_CMD restart"
echo ""
echo "📚 For more information, see README.md"
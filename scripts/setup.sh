#!/bin/bash

# Tor Selenium X - Setup Script
# This script sets up the development environment

set -e

echo "🚀 Setting up Tor Selenium X development environment..."

# Install dependencies
echo "📦 Installing Python dependencies..."
uv sync --extra dev --extra selenium

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p logs
mkdir -p htmlcov

# Set up pre-commit hooks (if available)
if command -v pre-commit &> /dev/null; then
    echo "🔧 Setting up pre-commit hooks..."
    uv run pre-commit install
fi

echo "✅ Setup complete!"
echo ""
echo "Available commands:"
echo "  make help  - Show available commands"
echo "  make test  - Run tests"
echo "  make dev   - Run in development mode"
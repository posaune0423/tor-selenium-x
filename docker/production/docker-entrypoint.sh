#!/bin/bash
set -e

# Production environment permission setup for cookie storage
echo "🚀 Starting production environment..."
echo "Container startup at: $(date)"

# Get user information
USER_ID=${USER_ID:-1000}
GROUP_ID=${GROUP_ID:-1000}
echo "Target USER_ID: $USER_ID"
echo "Target GROUP_ID: $GROUP_ID"

# Enhanced production data directory permission setup
echo "📁 Setting up production data permissions..."
if [ -d "/app/data" ]; then
    # Create all data subdirectories if they don't exist
    mkdir -p /app/data/{screenshots,scraping_results,logs,coverage,cookies}

    # Set ownership if running as root (should be during startup)
    if [ "$(id -u)" -eq 0 ]; then
        echo "🔑 Setting ownership to UID:GID = $USER_ID:$GROUP_ID"

        # Set ownership with error handling
        if ! chown -R $USER_ID:$GROUP_ID /app/data 2>/dev/null; then
            echo "⚠️  Could not set ownership, but continuing..."
        fi

        # Set directory permissions (755) and file permissions (644)
        find /app/data -type d -exec chmod 755 {} \; 2>/dev/null || echo "⚠️  Directory permissions could not be set"
        find /app/data -type f -exec chmod 644 {} \; 2>/dev/null || echo "⚠️  File permissions could not be set"

        # Special permissions for cookie directory (700 for security)
        chmod 700 /app/data/cookies 2>/dev/null || echo "⚠️  Cookie directory permissions could not be set"

        echo "✅ Production data directory permissions configured"
    fi

    # Verify write permissions
    if [ -w "/app/data" ]; then
        echo "✅ Write permission test: PASSED"
        # Clean test file
        rm -f /app/data/test_write_permission 2>/dev/null || true
    else
        echo "⚠️  Write permission test: FAILED"
    fi
else
    echo "⚠️  Data directory not found, creating..."
    mkdir -p /app/data/{screenshots,scraping_results,logs,coverage,cookies}
fi

# Tor setup for production
echo "🔐 Configuring Tor for production..."
if [ "$(id -u)" -eq 0 ]; then
    # Ensure Tor directories exist
    mkdir -p /var/lib/tor
    chown -R debian-tor:debian-tor /var/lib/tor 2>/dev/null || echo "⚠️  Could not set Tor ownership"
    chmod 700 /var/lib/tor 2>/dev/null || echo "⚠️  Could not set Tor permissions"
    echo "✅ Tor directories configured"
fi

# Start Xvfb for headless display
echo "🖥️  Starting Xvfb..."
Xvfb :99 -screen 0 1920x1080x24 -ac +extension GLX +render -noreset > /dev/null 2>&1 &
XVFB_PID=$!
echo "Xvfb started with PID: $XVFB_PID"

# Start Tor
echo "🔒 Starting Tor for production..."
if command -v tor >/dev/null 2>&1; then
    tor -f /etc/tor/torrc > /dev/null 2>&1 &
    TOR_PID=$!
    echo "Tor started with PID: $TOR_PID"

    # Wait for Tor to be ready
    echo "⏳ Waiting for Tor to initialize..."
    sleep 5

    # Verify Tor connection
    echo "🔍 Verifying Tor connection..."
    for i in {1..5}; do
        if nc -z 127.0.0.1 9050; then
            echo "✅ SOCKS port 9050 is available!"
            break
        else
            echo "🧪 Checking Tor connection... (attempt $i/5)"
            sleep 2
        fi
    done
else
    echo "⚠️  Tor not found, continuing without Tor service"
fi

echo "🌟 Production environment ready!"
echo "Environment variables:"
echo "  DISPLAY: $DISPLAY"
echo "  TBB_PATH: $TBB_PATH"
echo "  USER_ID: $USER_ID"
echo "  GROUP_ID: $GROUP_ID"
echo "  Current working directory: $(pwd)"

# Switch to non-root user if running as root
if [ "$(id -u)" -eq 0 ]; then
    echo "🔄 Switching to non-root user (UID: $USER_ID)..."
    echo "▶️  Executing command as user: $@"
    exec gosu $USER_ID:$GROUP_ID "$@"
else
    echo "👤 Already running as non-root user (UID: $(id -u))"
    echo "▶️  Executing command: $@"
    exec "$@"
fi

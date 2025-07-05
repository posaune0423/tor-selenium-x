#!/bin/bash
set -e

# Enhanced file permission setup for mounted volumes
echo "🐳 Setting up Docker environment..."
echo "Container startup at: $(date)"

# Get user information
USER_ID=${USER_ID:-1000}
GROUP_ID=${GROUP_ID:-1000}
echo "Target USER_ID: $USER_ID"
echo "Target GROUP_ID: $GROUP_ID"

# Check current user
CURRENT_UID=$(id -u)
CURRENT_GID=$(id -g)
echo "Current UID: $CURRENT_UID"
echo "Current GID: $CURRENT_GID"

# Enhanced data directory permission setup
echo "📁 Setting up data directory permissions..."
if [ -d "/app/data" ]; then
    # Create all data subdirectories if they don't exist
    mkdir -p /app/data/{screenshots,scraping_results,logs,coverage,cookies}

    # Display current ownership
    echo "Current /app/data ownership:"
    ls -ld /app/data

    echo "Current /app/data subdirectories:"
    ls -la /app/data/

    # Set ownership and permissions with error handling
    echo "Setting ownership to UID:GID = $USER_ID:$GROUP_ID"

    # Use find to ensure all files and directories are covered
    if find /app/data -exec chown $USER_ID:$GROUP_ID {} + 2>/dev/null; then
        echo "✅ Ownership set successfully"
    else
        echo "⚠️  Some files could not be owned, but continuing..."
    fi

    # Set permissions: directories 755, files 644
    if find /app/data -type d -exec chmod 755 {} + 2>/dev/null; then
        echo "✅ Directory permissions (755) set successfully"
    else
        echo "⚠️  Some directory permissions could not be set"
    fi

    if find /app/data -type f -exec chmod 644 {} + 2>/dev/null; then
        echo "✅ File permissions (644) set successfully"
    else
        echo "⚠️  Some file permissions could not be set"
    fi

    # Special handling for cookie directory - more restrictive permissions
    if [ -d "/app/data/cookies" ]; then
        chmod 700 /app/data/cookies 2>/dev/null || true
        echo "✅ Cookie directory permissions set to 700"
    fi

    # Verify final permissions
    echo "Final /app/data ownership and permissions:"
    ls -ld /app/data
    echo "Cookie directory:"
    ls -ld /app/data/cookies

    # Test write permissions
    TEST_FILE="/app/data/test_write_$(date +%s).tmp"
    if touch "$TEST_FILE" 2>/dev/null; then
        echo "✅ Write permission test: PASSED"
        rm -f "$TEST_FILE"
    else
        echo "❌ Write permission test: FAILED"
        echo "This may cause issues with file saving"
    fi

else
    echo "❌ /app/data directory not found!"
    echo "Available directories in /app:"
    ls -la /app/
fi

# Tor data directory permissions (separate from user data)
echo "🔐 Setting up Tor directory permissions..."
if [ -d "/var/lib/tor" ]; then
    chown -R debian-tor:debian-tor /var/lib/tor 2>/dev/null || true
    chmod 700 /var/lib/tor 2>/dev/null || true
    echo "✅ Tor directory permissions set"
else
    echo "⚠️  Tor directory not found, creating..."
    mkdir -p /var/lib/tor
    chown -R debian-tor:debian-tor /var/lib/tor 2>/dev/null || true
    chmod 700 /var/lib/tor 2>/dev/null || true
fi

# Start Xvfb for headless browser support
echo "🖥️  Starting Xvfb..."
Xvfb :99 -screen 0 1920x1080x24 &
XVFB_PID=$!
echo "Xvfb started with PID: $XVFB_PID"

# Start Tor service
echo "🔒 Starting Tor..."
# Use gosu to run Tor as debian-tor user
gosu debian-tor tor -f /etc/tor/torrc &
TOR_PID=$!
echo "Tor started with PID: $TOR_PID"

# Wait for Tor to initialize
echo "⏳ Waiting for Tor to initialize..."
sleep 5

# Enhanced Tor connection verification
echo "🔍 Verifying Tor connection..."
RETRY_COUNT=0
MAX_RETRIES=15

# Check if SOCKS port is available
while ! nc -z localhost 9050; do
    RETRY_COUNT=$((RETRY_COUNT + 1))
    if [ $RETRY_COUNT -ge $MAX_RETRIES ]; then
        echo "❌ SOCKS port 9050 not available after $MAX_RETRIES attempts"
        echo "Tor may not be working properly, but continuing..."
        break
    fi
    echo "⏳ Waiting for SOCKS port... (attempt $RETRY_COUNT/$MAX_RETRIES)"
    sleep 1
done

# Test Tor connection if SOCKS port is available
if nc -z localhost 9050; then
    echo "✅ SOCKS port 9050 is available!"

    # Simple connection test with timeout
    RETRY_COUNT=0
    MAX_RETRIES=10

    until curl -s --socks5 localhost:9050 --connect-timeout 5 --max-time 10 http://httpbin.org/ip > /dev/null; do
        RETRY_COUNT=$((RETRY_COUNT + 1))
        if [ $RETRY_COUNT -ge $MAX_RETRIES ]; then
            echo "⚠️  Tor connection test failed after $MAX_RETRIES attempts"
            echo "SOCKS proxy is available but external connectivity may be limited"
            echo "This is normal in some network environments. Continuing..."
            break
        fi
        echo "🧪 Testing Tor connection... (attempt $RETRY_COUNT/$MAX_RETRIES)"
        sleep 3
    done

    # Show current IP if connection is working
    if curl -s --socks5 localhost:9050 --connect-timeout 5 --max-time 10 http://httpbin.org/ip > /tmp/tor_ip.json 2>/dev/null; then
        echo "🌍 Tor is ready and working!"
        echo "Current IP via Tor:"
        cat /tmp/tor_ip.json | head -5
        rm -f /tmp/tor_ip.json
    fi
else
    echo "⚠️  SOCKS port not available, but continuing..."
    echo "The application may still work with tbselenium's built-in Tor"
fi

# Setup cleanup function
cleanup() {
    echo "🛑 Shutting down services..."
    if [ ! -z "$TOR_PID" ]; then
        echo "Stopping Tor (PID: $TOR_PID)"
        kill $TOR_PID 2>/dev/null || true
    fi
    if [ ! -z "$XVFB_PID" ]; then
        echo "Stopping Xvfb (PID: $XVFB_PID)"
        kill $XVFB_PID 2>/dev/null || true
    fi
    echo "Cleanup completed"
}

# Register signal handlers
trap cleanup EXIT INT TERM

# Final environment info
echo "🚀 Docker environment ready!"
echo "Environment variables:"
echo "  DISPLAY: $DISPLAY"
echo "  TBB_PATH: $TBB_PATH"
echo "  USER_ID: $USER_ID"
echo "  GROUP_ID: $GROUP_ID"
echo "  Current working directory: $(pwd)"

# Execute the provided command as the target user
echo "▶️  Executing command as user appuser: $@"
exec gosu appuser "$@"

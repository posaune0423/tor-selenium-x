#!/bin/bash
set -e

# ファイル権限を調整（マウントされたボリューム用）
echo "Adjusting file permissions..."
if [ -d "/app/data" ]; then
    chown -R appuser:appuser /app/data 2>/dev/null || true
    chmod -R 755 /app/data 2>/dev/null || true
fi

# Torデータディレクトリの権限を確認・修正
if [ -d "/var/lib/tor" ]; then
    chown -R debian-tor:debian-tor /var/lib/tor 2>/dev/null || true
    chmod 700 /var/lib/tor 2>/dev/null || true
fi

# Xvfbを起動（ヘッドレスブラウザ用）
echo "Starting Xvfb..."
Xvfb :99 -screen 0 1920x1080x24 &
XVFB_PID=$!

# Torを適切なユーザー（debian-tor）として起動
echo "Starting Tor..."
# gosuを使用してTorを起動（Dockerに最適化）
gosu debian-tor tor -f /etc/tor/torrc &
TOR_PID=$!

# Torが起動するまで待機
echo "Waiting for Tor to start..."
sleep 5

# Torの接続確認 - より効率的なチェック
echo "Checking Tor connection..."
RETRY_COUNT=0
MAX_RETRIES=15  # 30から15に削減

# まずSOCKSポートが開いているかチェック
while ! nc -z localhost 9050; do
    RETRY_COUNT=$((RETRY_COUNT + 1))
    if [ $RETRY_COUNT -ge $MAX_RETRIES ]; then
        echo "SOCKS port 9050 not available after $MAX_RETRIES attempts"
        break
    fi
    echo "Waiting for SOCKS port... (attempt $RETRY_COUNT/$MAX_RETRIES)"
    sleep 1
done

# SOCKSポートが利用可能になったら、簡単な接続テストを実行
if nc -z localhost 9050; then
    echo "SOCKS port 9050 is available!"

    # 簡単な接続テスト（タイムアウトを短縮）
    RETRY_COUNT=0
    MAX_RETRIES=10

    until curl -s --socks5 localhost:9050 --connect-timeout 5 --max-time 10 http://httpbin.org/ip > /dev/null; do
        RETRY_COUNT=$((RETRY_COUNT + 1))
        if [ $RETRY_COUNT -ge $MAX_RETRIES ]; then
            echo "Tor connection test failed after $MAX_RETRIES attempts, but SOCKS is available"
            echo "This may be due to network restrictions or slow bootstrap. Continuing..."
            break
        fi
        echo "Testing Tor connection... (attempt $RETRY_COUNT/$MAX_RETRIES)"
        sleep 3
    done

    # 接続成功時の情報表示
    if curl -s --socks5 localhost:9050 --connect-timeout 5 --max-time 10 http://httpbin.org/ip > /tmp/tor_ip.json 2>/dev/null; then
        echo "Tor is ready and working!"
        echo "Current IP via Tor:"
        cat /tmp/tor_ip.json
        rm -f /tmp/tor_ip.json
    fi
else
    echo "Warning: SOCKS port not available, but continuing..."
fi

# クリーンアップ関数
cleanup() {
    echo "Shutting down services..."
    if [ ! -z "$TOR_PID" ]; then
        kill $TOR_PID 2>/dev/null || true
    fi
    if [ ! -z "$XVFB_PID" ]; then
        kill $XVFB_PID 2>/dev/null || true
    fi
}

# シグナルハンドラを設定
trap cleanup EXIT INT TERM

# 引数で渡されたコマンドをappuserとして実行
exec gosu appuser "$@"

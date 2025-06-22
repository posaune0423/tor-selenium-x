#!/bin/bash
set -e

# 本番環境用のシンプルなエントリーポイント

# Xvfbを開始（ヘッドレス実行用）
echo "Starting Xvfb..."
Xvfb $DISPLAY -screen 0 1024x768x24 &
XVFB_PID=$!

# Torサービスを開始
echo "Starting Tor service..."
tor -f /etc/tor/torrc &
TOR_PID=$!

# Torが起動するまで待機
echo "Waiting for Tor to start..."
sleep 10

# Torの接続確認
echo "Checking Tor connection..."
RETRY_COUNT=0
MAX_RETRIES=30

until curl -s --socks5 localhost:9050 --connect-timeout 10 http://httpbin.org/ip > /dev/null; do
    RETRY_COUNT=$((RETRY_COUNT + 1))
    if [ $RETRY_COUNT -ge $MAX_RETRIES ]; then
        echo "Failed to establish Tor connection after $MAX_RETRIES attempts"
        break
    fi
    echo "Waiting for Tor connection... (attempt $RETRY_COUNT/$MAX_RETRIES)"
    sleep 2
done

# Tor情報を表示
if curl -s --socks5 localhost:9050 --connect-timeout 10 http://httpbin.org/ip > /tmp/tor_ip.json 2>/dev/null; then
    echo "Tor is ready!"
    echo "Current IP via Tor:"
    cat /tmp/tor_ip.json
    rm -f /tmp/tor_ip.json
else
    echo "Warning: Tor may not be fully ready, but continuing..."
fi

# クリーンアップ関数
cleanup() {
    echo "Shutting down..."
    kill $XVFB_PID 2>/dev/null || true
    kill $TOR_PID 2>/dev/null || true
    exit 0
}

# シグナルハンドラーを設定
trap cleanup SIGTERM SIGINT

echo "Services ready"

# メインコマンドを実行
exec "$@"

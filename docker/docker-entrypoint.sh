#!/bin/bash
set -e

# Xvfbを起動（ヘッドレスブラウザ用）
echo "Starting Xvfb..."
Xvfb :99 -screen 0 1920x1080x24 &
XVFB_PID=$!

# Torを起動
echo "Starting Tor..."
tor -f /etc/tor/torrc &
TOR_PID=$!

# Torが起動するまで待機
echo "Waiting for Tor to start..."
sleep 5

# Torの接続確認
until curl -s --socks5 localhost:9050 http://httpbin.org/ip > /dev/null; do
    echo "Waiting for Tor connection..."
    sleep 2
done

echo "Tor is ready!"

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

# 引数で渡されたコマンドを実行
exec "$@"

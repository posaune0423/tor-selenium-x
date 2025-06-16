#!/bin/bash
set -e

# Torを起動
echo "Starting Tor..."
tor -f /etc/tor/torrc &

# Torが起動するまで待機
echo "Waiting for Tor to start..."
sleep 5

# Torの接続確認
until curl -s --socks5 localhost:9050 http://httpbin.org/ip > /dev/null; do
    echo "Waiting for Tor connection..."
    sleep 2
done

echo "Tor is ready!"

# 引数で渡されたコマンドを実行
exec "$@"
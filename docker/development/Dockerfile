# Python 3.12をベースとしたマルチステージビルド
FROM python:3.12-slim AS base

# アーキテクチャを自動検出
ARG TARGETARCH
RUN echo "Building for architecture: $TARGETARCH"

# 必要なシステムパッケージをインストール
RUN apt-get update && apt-get install -y \
    tor \
    wget \
    gnupg \
    unzip \
    curl \
    ca-certificates \
    chromium \
    chromium-driver \
    firefox-esr \
    xvfb \
    dbus-x11 \
    && rm -rf /var/lib/apt/lists/*

# geckodriverをダウンロードしてインストール
RUN GECKO_VERSION=$(curl -s https://api.github.com/repos/mozilla/geckodriver/releases/latest | grep tag_name | cut -d '"' -f 4) && \
    ARCH=$(dpkg --print-architecture) && \
    if [ "$ARCH" = "arm64" ]; then GECKO_ARCH="linux-aarch64"; else GECKO_ARCH="linux64"; fi && \
    wget -O /tmp/geckodriver.tar.gz "https://github.com/mozilla/geckodriver/releases/download/${GECKO_VERSION}/geckodriver-${GECKO_VERSION}-${GECKO_ARCH}.tar.gz" && \
    tar -xzf /tmp/geckodriver.tar.gz -C /tmp && \
    mv /tmp/geckodriver /usr/local/bin/ && \
    chmod +x /usr/local/bin/geckodriver && \
    rm /tmp/geckodriver.tar.gz

# Xvfbディスプレイの設定
ENV DISPLAY=:99

# UVをインストール
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# tbselenium用の完全なTor Browser構造を作成
RUN mkdir -p /opt/torbrowser/Browser/TorBrowser/Data/Browser/profile.default && \
    mkdir -p /opt/torbrowser/Browser/TorBrowser/Tor && \
    mkdir -p /opt/torbrowser/Browser/TorBrowser/Data/Tor && \
    ln -s /usr/bin/firefox-esr /opt/torbrowser/Browser/firefox && \
    ln -s /usr/bin/tor /opt/torbrowser/Browser/TorBrowser/Tor/tor && \
    echo '#!/bin/bash\nexec firefox-esr "$@"' > /opt/torbrowser/start-tor-browser && \
    chmod +x /opt/torbrowser/start-tor-browser

# 作業ディレクトリを設定
WORKDIR /app

# Pythonプロジェクトファイルをコピー
COPY pyproject.toml uv.lock ./

# 依存関係をインストール
RUN uv sync --frozen --no-editable

# ソースコードをコピー
COPY src/ ./src/
COPY tests/ ./tests/

# Torの設定ファイルを作成
RUN echo "SocksPort 9050" > /etc/tor/torrc && \
    echo "ControlPort 9051" >> /etc/tor/torrc && \
    echo "CookieAuthentication 0" >> /etc/tor/torrc && \
    echo "HashedControlPassword" >> /etc/tor/torrc && \
    echo "RunAsDaemon 0" >> /etc/tor/torrc

# Docker entrypoint スクリプトをコピー
COPY docker/development/docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

# reports ディレクトリを作成
RUN mkdir -p /app/reports

# 非rootユーザーを作成
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app /opt/torbrowser

USER appuser

# エントリーポイントを設定
ENTRYPOINT ["/docker-entrypoint.sh"]

# デフォルトコマンド
CMD ["uv", "run", "src/main.py"]

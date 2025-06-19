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

# Xvfbディスプレイの設定
ENV DISPLAY=:99

# ChromeDriverを自動管理するため、webdriver-managerを使用
# システムのChromeDriverは不要

# UVをインストール
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# 作業ディレクトリを設定
WORKDIR /app

# Pythonプロジェクトファイルをコピー
COPY pyproject.toml uv.lock README.md ./

# 依存関係をインストール
RUN uv sync --frozen --extra selenium

# ソースコードをコピー
COPY src/ ./src/

# Torの設定ファイルを作成
RUN echo "SocksPort 9050" > /etc/tor/torrc && \
    echo "ControlPort 9051" >> /etc/tor/torrc && \
    echo "RunAsDaemon 0" >> /etc/tor/torrc

# Docker entrypoint スクリプトをコピー
COPY docker/docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh


# 非rootユーザーを作成（セキュリティ向上）
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

# ポートを開放（必要に応じて）
EXPOSE 9050 9051

# エントリーポイントを設定
ENTRYPOINT ["/docker-entrypoint.sh"]

# デフォルトコマンド - main.pyを使用
CMD ["uv", "run", "src/main.py"]

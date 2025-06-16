# Python 3.12をベースとしたマルチステージビルド
FROM python:3.12-slim as base

# 必要なシステムパッケージをインストール
RUN apt-get update && apt-get install -y \
    tor \
    wget \
    gnupg \
    unzip \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Google Chrome Stable をインストール
RUN wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# ChromeDriverを自動管理するため、webdriver-managerを使用
# システムのChromeDriverは不要

# UVをインストール
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# 作業ディレクトリを設定
WORKDIR /app

# Pythonプロジェクトファイルをコピー
COPY pyproject.toml uv.lock ./

# 依存関係をインストール
RUN uv sync --frozen --extra selenium

# ソースコードをコピー
COPY src/ ./src/

# Torの設定ファイルを作成
RUN echo "SocksPort 9050" > /etc/tor/torrc && \
    echo "ControlPort 9051" >> /etc/tor/torrc

# スクリプトを実行可能にする
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

# ポートを開放（必要に応じて）
EXPOSE 9050 9051

# エントリーポイントを設定
ENTRYPOINT ["/docker-entrypoint.sh"]

# デフォルトコマンド
CMD ["uv", "run", "src/tor_scraper.py"]
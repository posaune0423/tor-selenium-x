# tbselenium本番用Dockerfile
FROM python:3.12-slim

# 本番環境設定
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DISPLAY=:99

# 必要最小限のシステムパッケージをインストール
RUN apt-get update && apt-get install -y --no-install-recommends \
    tor \
    wget \
    curl \
    firefox-esr \
    xvfb \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# geckodriverをダウンロードしてインストール（特定バージョンを使用してビルドを安定化）
RUN GECKO_VERSION="v0.34.0" && \
    ARCH=$(dpkg --print-architecture) && \
    if [ "$ARCH" = "arm64" ]; then GECKO_ARCH="linux-aarch64"; else GECKO_ARCH="linux64"; fi && \
    wget -O /tmp/geckodriver.tar.gz "https://github.com/mozilla/geckodriver/releases/download/${GECKO_VERSION}/geckodriver-${GECKO_VERSION}-${GECKO_ARCH}.tar.gz" && \
    tar -xzf /tmp/geckodriver.tar.gz -C /tmp && \
    mv /tmp/geckodriver /usr/local/bin/ && \
    chmod +x /usr/local/bin/geckodriver && \
    rm /tmp/geckodriver.tar.gz

# 非rootユーザーを作成
RUN useradd -m -u 1000 appuser

# 作業ディレクトリ設定
WORKDIR /app

# UVをインストール
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Firefox ESR用のTor Browser構造を作成
RUN mkdir -p /opt/torbrowser/Browser/TorBrowser/Data/Browser/profile.default && \
    mkdir -p /opt/torbrowser/Browser/TorBrowser/Data/Tor && \
    ln -s /usr/bin/firefox-esr /opt/torbrowser/Browser/firefox

# Torの設定ファイルを作成（セキュアな設定）
RUN echo "SocksPort 9050" > /etc/tor/torrc && \
    echo "ControlPort 9051" >> /etc/tor/torrc && \
    echo "CookieAuthentication 1" >> /etc/tor/torrc && \
    echo "CookieAuthFileGroupReadable 1" >> /etc/tor/torrc && \
    echo "DataDirectory /var/lib/tor" >> /etc/tor/torrc && \
    echo "RunAsDaemon 0" >> /etc/tor/torrc && \
    echo "Log notice stdout" >> /etc/tor/torrc && \
    echo "## Disable control password for cookie auth" >> /etc/tor/torrc && \
    mkdir -p /var/lib/tor && \
    chown -R debian-tor:debian-tor /var/lib/tor

# Pythonプロジェクトファイルをコピー
COPY pyproject.toml uv.lock ./

# 依存関係をインストール（本番用）
RUN uv sync --frozen --no-dev --no-editable

# ソースコードをコピー
COPY src/ ./src/

# data ディレクトリを作成
RUN mkdir -p /app/data \
    && chown -R appuser:appuser /app /opt/torbrowser

# 本番用エントリーポイント
COPY docker/production/docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

# 非rootユーザーに切り替え
USER appuser

# ヘルスチェック
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import tbselenium; print('OK')" || exit 1

# Railway用のポート設定
EXPOSE ${PORT:-8000}

# エントリーポイントを設定
ENTRYPOINT ["/docker-entrypoint.sh"]

# デフォルトコマンド
CMD ["uv", "run", "src/main.py"]

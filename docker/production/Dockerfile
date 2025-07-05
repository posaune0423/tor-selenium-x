# tbselenium本番用Dockerfile
FROM python:3.12-slim

# Auto-detect architecture
ARG TARGETARCH
ARG USER_ID=1000
ARG GROUP_ID=1000
RUN echo "Building production for architecture: $TARGETARCH"
RUN echo "Building production with USER_ID: $USER_ID, GROUP_ID: $GROUP_ID"

# 本番環境設定
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DISPLAY=:99 \
    TOR_BROWSER_PATH=/opt/torbrowser \
    TBB_PATH=/opt/torbrowser \
    TBSELENIUM_TBB_PATH=/opt/torbrowser

# 必要最小限のシステムパッケージをインストール
RUN apt-get update && apt-get install -y --no-install-recommends \
    tor \
    wget \
    curl \
    firefox-esr \
    xvfb \
    gosu \
    netcat-openbsd \
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

# Install UV package manager
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Firefox ESR用のTor Browser構造を作成
RUN mkdir -p /opt/torbrowser/Browser/TorBrowser/Data/Browser/profile.default \
             /opt/torbrowser/Browser/TorBrowser/Tor \
             /opt/torbrowser/Browser/TorBrowser/Data/Tor && \
    ln -s /usr/bin/firefox-esr /opt/torbrowser/Browser/firefox && \
    ln -s /usr/bin/tor /opt/torbrowser/Browser/TorBrowser/Tor/tor && \
    echo '#!/bin/bash\nexec firefox-esr "$@"' > /opt/torbrowser/start-tor-browser && \
    chmod +x /opt/torbrowser/start-tor-browser

# 作業ディレクトリ設定
WORKDIR /app

# Pythonプロジェクトファイルをコピー
COPY pyproject.toml uv.lock ./

# 依存関係をインストール（本番用）
RUN uv sync --frozen --no-dev --no-editable

# ソースコードをコピー
COPY src/ ./src/

# Configure Tor with secure settings
RUN echo "SocksPort 9050\n\
ControlPort 9051\n\
CookieAuthentication 1\n\
CookieAuthFileGroupReadable 1\n\
DataDirectory /var/lib/tor\n\
RunAsDaemon 0\n\
Log notice stdout" > /etc/tor/torrc && \
    mkdir -p /var/lib/tor && \
    chown -R debian-tor:debian-tor /var/lib/tor && \
    chmod 700 /var/lib/tor

# 本番用エントリーポイント
COPY docker/production/docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

# Create data directories with proper structure
RUN mkdir -p /app/data/{screenshots,logs,coverage,scraping_results,cookies}

# Create non-root user with host-matching UIDs for file permission compatibility
RUN set -e && \
    # Check if group exists, create if not
    if ! getent group ${GROUP_ID} >/dev/null 2>&1; then \
        groupadd -g ${GROUP_ID} appuser; \
    else \
        GROUP_NAME=$(getent group ${GROUP_ID} | cut -d: -f1); \
        echo "Using existing group: $GROUP_NAME (GID: ${GROUP_ID})"; \
    fi && \
    # Check if user exists, create if not
    if ! getent passwd ${USER_ID} >/dev/null 2>&1; then \
        useradd -m -u ${USER_ID} -g ${GROUP_ID} -s /bin/bash appuser; \
    else \
        USER_NAME=$(getent passwd ${USER_ID} | cut -d: -f1); \
        echo "Using existing user: $USER_NAME (UID: ${USER_ID})"; \
    fi && \
    # Set ownership and permissions
    chown -R ${USER_ID}:${GROUP_ID} /app /opt/torbrowser && \
    chmod -R 755 /app /opt/torbrowser && \
    # Ensure debian-tor user exists (should already exist from tor package)
    if ! id debian-tor >/dev/null 2>&1; then \
        echo "Creating debian-tor user"; \
        groupadd -r debian-tor && useradd -r -g debian-tor debian-tor; \
    else \
        echo "debian-tor user already exists"; \
    fi && \
    chown -R debian-tor:debian-tor /var/lib/tor && \
    chmod 700 /var/lib/tor

# ヘルスチェック
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import tbselenium; print('OK')" || exit 1

# Railway用のポート設定
EXPOSE ${PORT:-8000}

# エントリーポイントを設定
ENTRYPOINT ["/docker-entrypoint.sh"]

# デフォルトコマンド
CMD ["uv", "run", "src/main.py"]

# Python 3.12 multi-stage build for X scraper
FROM python:3.12-slim AS base

# Auto-detect architecture
ARG TARGETARCH
RUN echo "Building for architecture: $TARGETARCH"

# Install system dependencies in single layer
RUN apt-get update && apt-get install -y --no-install-recommends \
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
    gosu \
    sudo \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Install geckodriver with version pinning for stability
RUN GECKO_VERSION="v0.34.0" && \
    ARCH=$(dpkg --print-architecture) && \
    if [ "$ARCH" = "arm64" ]; then GECKO_ARCH="linux-aarch64"; else GECKO_ARCH="linux64"; fi && \
    wget -O /tmp/geckodriver.tar.gz "https://github.com/mozilla/geckodriver/releases/download/${GECKO_VERSION}/geckodriver-${GECKO_VERSION}-${GECKO_ARCH}.tar.gz" && \
    tar -xzf /tmp/geckodriver.tar.gz -C /tmp && \
    mv /tmp/geckodriver /usr/local/bin/ && \
    chmod +x /usr/local/bin/geckodriver && \
    rm -f /tmp/geckodriver.tar.gz

# Set environment variables
ENV DISPLAY=:99 \
    TOR_BROWSER_PATH=/opt/torbrowser \
    TBB_PATH=/opt/torbrowser \
    TBSELENIUM_TBB_PATH=/opt/torbrowser

# Install UV package manager
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Create Tor Browser structure for tbselenium compatibility
RUN mkdir -p /opt/torbrowser/Browser/TorBrowser/Data/Browser/profile.default \
             /opt/torbrowser/Browser/TorBrowser/Tor \
             /opt/torbrowser/Browser/TorBrowser/Data/Tor && \
    ln -s /usr/bin/firefox-esr /opt/torbrowser/Browser/firefox && \
    ln -s /usr/bin/tor /opt/torbrowser/Browser/TorBrowser/Tor/tor && \
    echo '#!/bin/bash\nexec firefox-esr "$@"' > /opt/torbrowser/start-tor-browser && \
    chmod +x /opt/torbrowser/start-tor-browser

# Set working directory
WORKDIR /app

# Copy and install Python dependencies (separate layer for caching)
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-editable

# Copy source code
COPY src/ ./src/
COPY tests/ ./tests/

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

# Copy and set up entrypoint
COPY docker/development/docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

# Create data directories with proper structure
RUN mkdir -p /app/data/{screenshots,logs,coverage,scraping_results,cookies}

# Create non-root user with consistent UIDs
RUN groupadd -g 1000 appuser && \
    useradd -m -u 1000 -g 1000 -s /bin/bash appuser && \
    chown -R appuser:appuser /app /opt/torbrowser && \
    chmod -R 755 /app /opt/torbrowser && \
    id debian-tor >/dev/null 2>&1 || (groupadd -r debian-tor && useradd -r -g debian-tor debian-tor) && \
    chown -R debian-tor:debian-tor /var/lib/tor && \
    chmod 700 /var/lib/tor

# Set entrypoint and default command
ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["uv", "run", "src/main.py"]

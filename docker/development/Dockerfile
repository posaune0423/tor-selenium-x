# Python 3.12 multi-stage build for X scraper
FROM python:3.12-slim AS base

# Auto-detect architecture
ARG TARGETARCH
ARG USER_ID=1000
ARG GROUP_ID=1000
RUN echo "Building for architecture: $TARGETARCH"
RUN echo "Building with USER_ID: $USER_ID, GROUP_ID: $GROUP_ID"

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
RUN uv sync --frozen --no-editable --extra dev

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

# Set entrypoint and default command
ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["uv", "run", "src/main.py"]

# Tor Selenium X

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/docker-ready-green.svg)](https://www.docker.com/)

X (Twitter) scraper using Tor Browser with tbselenium for privacy and reliability.

## Features

- **Privacy First**: Uses Tor Browser for anonymous scraping
- **Stable Architecture**: Built with tbselenium library
- **Docker Ready**: Development and production environments
- **Type Safe**: Full type hints and comprehensive testing

## Quick Start

### Using Docker (Recommended)

```bash
# Clone repository
git clone https://github.com/your-username/tor-selenium-x.git
cd tor-selenium-x

# Start development environment
make dev

# View logs
make logs
```

### Local Development

```bash
# Install dependencies
uv install

# Run scraper
uv run python src/main.py
```

## Usage

```python
from src.x_scraper import XScraper

# Initialize scraper
scraper = XScraper(
    tbb_path="/opt/torbrowser",
    headless=True,
    socks_port=9050,
    control_port=9051,
)

try:
    # Start and connect
    scraper.start()
    scraper.navigate_to_x()
    
    # Search tweets
    tweets = scraper.search_tweets("Python programming", max_tweets=10)
    
    # Get user profile
    profile = scraper.get_user_profile("username")
    
    # Save data
    scraper.save_tweets_to_json(tweets, "tweets")
    scraper.save_profile_to_json(profile, "profile")
    
finally:
    scraper.close()
```

## Project Structure

```
src/
├── main.py          # Entry point
├── x_scraper.py     # Main scraper class
├── models.py        # Data models
└── utils.py         # Utilities

docker/
├── development/     # Development environment
└── production/      # Production environment
```

## Commands

```bash
# Development
make dev                # Start development environment
make test              # Run tests
make lint              # Code linting
make format            # Code formatting

# Production
make build-prod        # Build production image
make run-prod          # Run production container
```

## Requirements

- Python 3.12+
- Docker & Docker Compose
- 1GB RAM minimum (2GB recommended)

## Contributing

1. Fork the repository
2. Create your feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request

## License

MIT License

## X (Twitter) Scraper with Tor

A Python-based X (Twitter) scraper that uses Tor Browser for anonymous browsing and comprehensive scraping capabilities.

## Features

- Anonymous browsing through Tor network
- X (Twitter) login with session management
- Tweet searching and collection
- User profile scraping
- Anti-detection measures
- Human-like behavior simulation
- Comprehensive data models

## Requirements

- Python 3.12+
- Tor Browser
- UV package manager

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd tor-selenium-x
```

2. Install dependencies:
```bash
uv sync
```

3. Install Tor Browser:
   - Download from https://www.torproject.org/download/
   - Install in one of the common locations or set `TOR_BROWSER_PATH` environment variable

## Configuration

### Environment Variables

For login functionality, set the following environment variables:

```bash
export TOR_BROWSER_PATH="/path/to/tor-browser"
export X_EMAIL="your-email@example.com"
export X_PASSWORD="your-password"
export X_USERNAME="your-username"
```

Or create a `.env` file in the project root:

```env
# X (Twitter) Scraper Configuration
# Tor Browser Settings
TOR_BROWSER_PATH=/Applications/Tor Browser.app
# Examples for different platforms:
# Linux: TOR_BROWSER_PATH=/opt/torbrowser
# macOS: TOR_BROWSER_PATH=/Applications/Tor Browser.app
# Docker: TOR_BROWSER_PATH=/app/tor-browser

# X (Twitter) Login Credentials (Optional)
# Only set these if you want to use login functionality
X_EMAIL=your-email@example.com
X_PASSWORD=your-password
X_USERNAME=your-username

# Logging Configuration (Optional)
LOG_LEVEL=INFO
# Options: DEBUG, INFO, WARNING, ERROR, CRITICAL

# Scraper Settings (Optional)
HEADLESS=true
USE_STEM=false
SOCKS_PORT=9050
CONTROL_PORT=9051
```

### Tor Browser Path

The scraper automatically searches for Tor Browser in common locations:

- Linux: `/opt/torbrowser`, `/usr/local/tor-browser`, `~/tor-browser`
- macOS: `/Applications/Tor Browser.app`, `~/Applications/Tor Browser.app`
- Docker: `/app/tor-browser`, `/usr/local/bin/tor-browser`

## Usage

### Basic Usage

```bash
# Run the scraper
uv run python src/main.py
```

### Development Mode

```bash
# Start development environment
make dev

# Run tests
make test

# Lint code
make lint

# Format code
make format
```

## Examples

The main script includes several examples:

### Example 0: Login Flow (Optional)

- Attempts to login using environment variables
- Falls back to anonymous browsing if credentials not provided
- Demonstrates session management

### Example 1: Search Tweets

- Searches for tweets with a specific query
- Collects tweet data including text, author, metrics
- Saves results to JSON file

### Example 2: User Profile Scraping

- Retrieves user profile information
- Extracts follower counts, bio, location, etc.
- Saves profile data to JSON file

### Example 3: Authenticated Operations

- Demonstrates accessing logged-in features
- Shows home timeline access
- Requires successful login from Example 0

## Data Models

The scraper uses comprehensive data models for structured data:

- `XCredentials`: Login credentials
- `Tweet`: Tweet data with engagement metrics
- `UserProfile`: User profile information
- `SessionState`: Session management state

## Security Features

- Tor network routing for anonymity
- Human-like behavior simulation
- Anti-detection measures
- Session cookie management
- Rate limiting and delays

## Troubleshooting

### Tor Browser Not Found

```bash
# Set the path manually
export TOR_BROWSER_PATH="/path/to/your/tor-browser"
```

### Login Issues

- Ensure credentials are correct
- Check for 2FA requirements
- Verify account is not restricted
- Check network connectivity

### Rate Limiting

- The scraper includes built-in delays
- Adjust delay parameters if needed
- Consider using longer delays for large operations

## Development

### Project Structure

```
tor-selenium-x/
├── src/                 # Source code
│   ├── main.py         # Main entry point with examples
│   ├── x_scraper.py    # Core scraper class
│   ├── models.py       # Data models
│   └── utils/          # Utility modules
│       ├── __init__.py
│       ├── selenium_helpers.py
│       ├── human_simulation.py
│       ├── anti_detection.py
│       └── logger.py
├── tests/              # Test files
├── reports/            # Generated reports and data
│   ├── logs/           # Log files (timestamp-based)
│   ├── coverage/       # Test coverage reports
│   └── data/           # Scraped data files
├── pyproject.toml      # Project configuration
├── .env                # Environment variables (create from .env.example)
├── .gitignore
└── README.md
```

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes with proper tests
4. Run linting and tests
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Disclaimer

This tool is for educational and research purposes only. Always respect website terms of service and applicable laws. Use responsibly and ethically.

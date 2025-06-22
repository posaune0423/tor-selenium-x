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

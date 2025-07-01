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
├── data/               # Generated data and reports
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

# X (Twitter) Scraper with Tor Browser

A robust X (Twitter) scraper using Tor Browser for privacy and advanced authentication handling.

## Features

- **Privacy-focused**: Uses Tor Browser for anonymous scraping
- **Smart Authentication**: Manual login flow to handle CAPTCHA and 2FA automatically
- **Session Persistence**: Saves authentication cookies for future automated use
- **Comprehensive Data Extraction**: Profile information, tweets, engagement metrics
- **Anti-Detection**: Human-like behavior simulation and browser fingerprint management
- **Rate Limiting**: Built-in delays and respectful scraping practices

## 🔐 Authentication Strategy

Instead of trying to automate CAPTCHA solving (which becomes outdated quickly), this scraper uses a **manual login flow**:

1. **First-time setup**: User logs in manually through the browser
2. **Cookie persistence**: Authentication cookies are automatically saved
3. **Automated scraping**: Future sessions use saved cookies for seamless operation

This approach is:
- ✅ **Reliable**: No dependency on brittle CAPTCHA-solving logic
- ✅ **Maintainable**: Resistant to X.com UI changes
- ✅ **Human-like**: Authentic user behavior reduces detection risk
- ✅ **Flexible**: Handles 2FA, CAPTCHA, and other challenges naturally

## Installation

### Prerequisites

1. **Python 3.12+** with `uv` package manager
2. **Tor Browser Bundle** installed on your system

### Setup

```bash
# Clone the repository
git clone <repository-url>
cd tor-selenium-x

# Install dependencies with uv
uv sync --all-extras

# Set up development environment
make dev
```

### Tor Browser Setup

Download and install Tor Browser from: https://www.torproject.org/download/

Note the installation path, you'll need it for the `--tbb-path` argument.

## Usage

### 1. First-Time Manual Login Setup

Run this command to set up authentication cookies:

```bash
# Linux/macOS
python -m src.main --setup-login --tbb-path /path/to/tor-browser

# Example paths:
# Linux: /home/user/tor-browser_en-US
# macOS: /Applications/Tor Browser.app/Contents/MacOS/Tor
# Windows: C:\Users\User\Desktop\Tor Browser\Browser
```

This will:
1. Open a Tor Browser window (non-headless)
2. Navigate to X.com login page
3. Wait for you to log in manually
4. Handle any CAPTCHA or 2FA challenges
5. Automatically detect successful login
6. Save session cookies for future use

### 2. Automated Scraping

Once cookies are saved, run automated scraping:

```bash
python -m src.main --run-scraping --tbb-path /path/to/tor-browser
```

This will:
1. Start in headless mode for faster operation
2. Automatically restore your authentication session
3. Run example scraping operations
4. Save results to JSON files

### 3. Custom Data Directory

Use a custom directory for storing cookies and data:

```bash
# Setup with custom directory
python -m src.main --setup-login --tbb-path /path/to/tor-browser --data-dir ./my_data

# Run scraping with custom directory
python -m src.main --run-scraping --tbb-path /path/to/tor-browser --data-dir ./my_data
```

## Advanced Usage

### Programmatic API

```python
from src.x_scraper import XScraper

# Manual login setup
scraper = XScraper(tbb_path="/path/to/tor-browser", headless=False)
scraper.start()
success = scraper.manual_login_flow(timeout_minutes=10)
scraper.close()

# Automated scraping with saved cookies
scraper = XScraper(tbb_path="/path/to/tor-browser", headless=True)
scraper.start()

# Session is automatically restored from cookies
tweets = scraper.search_tweets("Python programming", max_tweets=20)
profile = scraper.get_user_profile("elonmusk")

scraper.close()
```

### Configuration Options

```python
scraper = XScraper(
    tbb_path="/path/to/tor-browser",
    headless=True,              # False for manual login, True for automation
    use_stem=True,              # Use Stem to manage Tor process
    socks_port=9050,            # SOCKS proxy port (default: 9050)
    control_port=9051,          # Tor control port (default: 9051)
    data_dir="./custom_data",   # Custom data directory
)
```

## Data Output

### Tweet Data Structure

```json
{
  "id": "1234567890",
  "text": "Tweet content here...",
  "author": "username",
  "timestamp": "2024-01-01T12:00:00Z",
  "likes": 42,
  "retweets": 10,
  "replies": 5,
  "url": "https://x.com/user/status/1234567890",
  "hashtags": ["#example"],
  "mentions": ["@user"]
}
```

### Profile Data Structure

```json
{
  "username": "elonmusk",
  "display_name": "Elon Musk",
  "bio": "Profile bio here...",
  "location": "Austin, TX",
  "website": "https://example.com",
  "followers_count": 1000000,
  "following_count": 100,
  "verified": true,
  "joined_date": "2009-06-02"
}
```

## Troubleshooting

### Manual Login Issues

**Browser doesn't open:**
- Make sure `headless=False` when running manual login setup
- Verify Tor Browser path is correct
- Check that Tor Browser can be launched manually

**Login timeout:**
- Increase timeout: `scraper.manual_login_flow(timeout_minutes=20)`
- Complete login process quickly
- Ensure stable internet connection

**Session not detected:**
- Wait for complete page load after login
- Don't close browser until success message appears
- Try refreshing the page if login seems stuck

### Automated Scraping Issues

**"Failed to restore session":**
- Run manual login setup first: `--setup-login`
- Check if cookies have expired (re-run setup)
- Verify internet connection and X.com accessibility

**Rate limiting or blocks:**
- Increase delays between requests
- Use different Tor circuits
- Avoid aggressive scraping patterns

### Common Error Solutions

**"Tor Browser path does not exist":**
```bash
# Find your Tor Browser installation
find / -name "tor-browser*" 2>/dev/null
# or
locate tor-browser
```

**"Driver initialization failed":**
- Ensure Tor Browser is properly installed
- Check permissions on Tor Browser directory
- Default ports are now standardized to 9050/9051 (SOCKS/Control)

**"No main content elements found":**
- X.com structure may have changed
- Try updating the scraper code
- Check if X.com is accessible in your region

## Development

### Project Structure

```
tor-selenium-x/
├── src/
│   ├── main.py              # CLI interface and workflows
│   ├── x_scraper.py         # Main scraper class
│   ├── models.py            # Data models
│   └── utils/               # Utility functions
├── tests/                   # Test suite
├── docker/                  # Docker configurations
└── data/                    # Output directory
```

### Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass: `make test`
5. Submit a pull request

### Testing

```bash
# Run all tests
make test

# Run with coverage
uv run pytest --cov=src

# Run specific test file
uv run pytest tests/test_x_scraper.py
```

## Legal and Ethical Considerations

- ⚖️ **Respect X.com Terms of Service**: Use responsibly and within platform guidelines
- 🤝 **Rate Limiting**: Built-in delays prevent overwhelming X.com servers  
- 🔒 **Privacy**: Tor Browser ensures your scraping activity remains private
- 📊 **Research Use**: Intended for legitimate research, analysis, and educational purposes

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For issues, questions, or contributions:
1. Check existing GitHub issues
2. Create a new issue with detailed description
3. Provide logs and error messages
4. Include system information (OS, Python version, Tor Browser version)

## Changelog

### v2.0.0 - Manual Login Flow
- ✨ Added manual authentication workflow
- 🍪 Persistent session cookie management  
- 🤖 Separated setup and automation phases
- 📱 CLI interface with clear operation modes
- 🛡️ Enhanced anti-detection measures

### v1.0.0 - Initial Release
- 🕷️ Basic scraping functionality
- 🔐 Tor Browser integration
- 📊 Profile and tweet extraction

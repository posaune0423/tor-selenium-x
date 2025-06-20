# Tor Selenium X

X (Twitter) scraper using Tor Browser with [tbselenium](https://github.com/webfp/tor-browser-selenium).

## Features

- **Anonymous scraping** through Tor Browser
- **Search tweets** by keywords
- **Get user profiles** and tweet history  
- **Export data** to JSON format
- **Rate limiting** and anti-detection measures
- **Comprehensive test suite**

## Requirements

- Python 3.12+
- Tor Browser (downloaded and extracted)
- `geckodriver` v0.31.0

## Installation

1. Install dependencies:
```bash
uv sync
```

2. Download and extract [Tor Browser](https://www.torproject.org/download/)

3. Download [geckodriver v0.31.0](https://github.com/mozilla/geckodriver/releases/tag/v0.31.0) and add to PATH

4. Set environment variable:
```bash
export TBB_PATH=/path/to/tor-browser/
```

## Usage

### Basic Usage

```python
from src.x_scraper import XScraper

# Initialize scraper
scraper = XScraper(tbb_path="/path/to/tor-browser/", headless=True)

# Start scraper and connect to Tor
if scraper.start():
    # Navigate to X
    scraper.navigate_to_x()
    
    # Search for tweets
    tweets = scraper.search_tweets("Python programming", max_tweets=10)
    
    # Get user profile
    profile = scraper.get_user_profile("elonmusk")
    
    # Get user tweets
    user_tweets = scraper.get_user_tweets("elonmusk", max_tweets=20)
    
    # Save data
    scraper.save_tweets_to_json(tweets, "search_results.json")
    scraper.save_profile_to_json(profile, "user_profile.json")
    
    # Close scraper
    scraper.close()
```

### Using Context Manager

```python
from src.x_scraper import XScraper

with XScraper(tbb_path="/path/to/tor-browser/") as scraper:
    if scraper.start():
        tweets = scraper.search_tweets("AI", max_tweets=5)
        print(f"Found {len(tweets)} tweets")
```

### Command Line

```bash
# Set Tor Browser path
export TBB_PATH=/path/to/tor-browser/

# Run scraper
uv run python -m src.main
```

## Data Structures

### Tweet
```python
@dataclass
class Tweet:
    id: Optional[str] = None
    text: str = ""
    author: str = ""
    timestamp: Optional[str] = None
    likes: int = 0
    retweets: int = 0
    replies: int = 0
    url: Optional[str] = None
```

### UserProfile
```python
@dataclass  
class UserProfile:
    username: str = ""
    display_name: str = ""
    bio: str = ""
    followers_count: Optional[int] = None
    following_count: Optional[int] = None
```

## Utility Functions

The `utils.py` module provides helper functions for:

- **Selenium operations**: Safe element interaction, waiting, scrolling
- **Text processing**: Cleaning, URL extraction, timestamp formatting
- **X-specific validation**: Username validation, URL parsing
- **File operations**: Safe filename creation
- **Rate limiting**: Random delays, retry decorators

## Testing

Run tests with:
```bash
# All tests
uv run pytest

# Specific test file
uv run pytest tests/test_utils.py

# With coverage
uv run pytest --cov=src --cov-report=html
```

## Configuration

### Environment Variables

- `TBB_PATH`: Path to Tor Browser directory (required)
- `HEADLESS`: Run in headless mode (default: true)

### Scraper Options

```python
scraper = XScraper(
    tbb_path="/path/to/tor-browser/",
    headless=True,           # Run headlessly
    use_stem=True,           # Use Stem to manage Tor process
    socks_port=9150,         # SOCKS proxy port
    control_port=9151,       # Tor control port
    data_dir="./data"        # Directory for output files
)
```

## Anti-Detection Features

- **Tor anonymization**: All requests go through Tor network
- **Random delays**: Between actions to avoid detection
- **Human-like scrolling**: Gradual page scrolling
- **Realistic user agent**: Mimics real browser behavior
- **Error handling**: Graceful handling of rate limits and blocks

## Troubleshooting

### Common Issues

1. **"TBB_PATH not set"**: Set the environment variable to your Tor Browser path
2. **"Tor connection failed"**: Ensure Tor Browser is properly installed and not blocked
3. **"Element not found"**: X frequently changes their UI; selectors may need updates
4. **Rate limiting**: Add longer delays or reduce request frequency

### Debug Mode

Enable debug logging:
```python
import sys
from loguru import logger

logger.remove()
logger.add(sys.stderr, level="DEBUG")
```

## Legal Notice

This tool is for educational and research purposes only. Users are responsible for:
- Complying with X's Terms of Service
- Following applicable laws and regulations  
- Respecting rate limits and robots.txt
- Not violating privacy or copyright

## Dependencies

- `tbselenium>=0.7.0`: Tor Browser automation
- `selenium>=4.15.0`: Web browser automation
- `stem>=1.8.0`: Tor network control
- `loguru>=0.7.0`: Enhanced logging
- `httpx>=0.25.0`: HTTP client

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes with tests
4. Run linting: `uv run ruff check .`
5. Submit pull request

## License

MIT License - see LICENSE file for details.

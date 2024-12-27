# utils/__init__.py

"""
Twitter Trends Scraper Package
This package contains utilities for scraping Twitter trends using Selenium with free proxy rotation
and MongoDB storage.

Components:
- FreeProxyRotator: Handles IP rotation using free proxy services
- TwitterScraper: Manages the web scraping process
- MongoDB: Handles database operations
"""

from .proxy import FreeProxyRotator
from .scraper import TwitterScraper
from .database import MongoDB

__all__ = ['FreeProxyRotator', 'TwitterScraper', 'MongoDB']

# Version of the utils package
__version__ = '1.0.1'

# Process Flow Documentation
"""
Complete Process Flow:

1. Web Interface Initialization:
   - Flask app starts and serves the index.html page
   - User sees a button to trigger scraping

2. When Scrape Button is Clicked:
   a. Frontend makes AJAX call to /scrape endpoint
   b. Backend process begins

3. Free Proxy Rotation (proxy.py):
   a. FreeProxyRotator maintains pool of validated proxies
   b. get_next_proxy() is called to:
      - Get next proxy from pool
      - Validate proxy is still working
      - Refresh proxy pool if needed
      - Return proxy details and current IP

4. Web Scraping (scraper.py):
   a. TwitterScraper initializes with free proxy
   b. Selenium WebDriver starts with proxy configuration
   c. Login process:
      - Navigate to Twitter login
      - Enter credentials
      - Wait for authentication
   d. Scraping process:
      - Wait for trends section to load
      - Extract top 5 trending topics
      - Close browser session

5. Database Operations (database.py):
   a. MongoDB connection established
   b. New document created with:
      - Unique ID (UUID)
      - 5 trending topics
      - Timestamp
      - IP address used
   c. Document inserted into trends collection

6. Response Handling:
   a. Success/failure status determined
   b. Data returned to frontend
   c. Frontend updates UI with results

Error Handling at Each Stage:
- Proxy errors: Retry with different proxy from pool
- Validation errors: Refresh proxy pool
- Scraping errors: Clean up WebDriver and report error
- Database errors: Log error and inform user
- Network errors: Timeout handling and retry logic

Data Flow:
User → Flask → FreeProxyRotator → TwitterScraper → MongoDB → User

Directory Structure:
twitter-trends-scraper/
├── config/
│   └── config.py           # Configuration settings
├── static/
│   └── styles.css         # Frontend styles
├── templates/
│   └── index.html         # Web interface
├── utils/
│   ├── __init__.py        # This file
│   ├── database.py        # MongoDB operations
│   ├── proxy.py          # Free proxy rotation
│   └── scraper.py        # Selenium scraping
├── .env                   # Environment variables
└── app.py                # Main Flask application
"""

def check_configuration():
    """
    Verify that all required configuration is present.
    Returns tuple of (bool, list of missing items)
    """
    from config.config import (
        TWITTER_USERNAME, 
        TWITTER_PASSWORD,
        MONGODB_URI,
        DB_NAME
    )
    
    required_configs = {
        'TWITTER_USERNAME': TWITTER_USERNAME,
        'TWITTER_PASSWORD': TWITTER_PASSWORD,
        'MONGODB_URI': MONGODB_URI,
        'DB_NAME': DB_NAME
    }
    
    missing = [k for k, v in required_configs.items() if not v]
    return (len(missing) == 0, missing)

def get_proxy_stats():
    """
    Get current proxy pool statistics
    Returns dict with proxy pool information
    """
    try:
        rotator = FreeProxyRotator()
        return {
            'working_proxies': len(rotator.working_proxies),
            'last_refresh': getattr(rotator, 'last_refresh', None),
            'status': 'active' if rotator.working_proxies else 'inactive'
        }
    except Exception as e:
        return {
            'working_proxies': 0,
            'last_refresh': None,
            'status': f'error: {str(e)}'
        }

def validate_environment():
    """
    Validate the complete environment setup
    Returns tuple of (bool, dict of status items)
    """
    status = {
        'config': check_configuration()[0],
        'proxy': get_proxy_stats()['status'] == 'active',
        'database': False,
        'selenium': False
    }
    
    # Check MongoDB connection
    try:
        db = MongoDB()
        db.collection.find_one()
        status['database'] = True
    except:
        pass
    
    # Check Selenium setup
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.service import Service
        from webdriver_manager.chrome import ChromeDriverManager
        webdriver.Chrome(service=Service(ChromeDriverManager().install()))
        status['selenium'] = True
    except:
        pass
    
    return (all(status.values()), status)
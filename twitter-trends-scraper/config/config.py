# config/config.py

import os
from dotenv import load_dotenv

load_dotenv()

# Twitter credentials
TWITTER_USERNAME = os.getenv('TWITTER_USERNAME')
TWITTER_PASSWORD = os.getenv('TWITTER_PASSWORD')

# MongoDB settings
MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')
DB_NAME = os.getenv('DB_NAME', 'twitter_trends')

# Application settings
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from utils.proxy import FreeProxyRotator
from utils.database import MongoDB
import time
import logging
import random
import uuid
from datetime import datetime
from config.config import TWITTER_USERNAME, TWITTER_PASSWORD

class TwitterScraper:
    def __init__(self):
        self.setup_logging()
        try:
            self.db = MongoDB()
            self.proxy_rotator = FreeProxyRotator()
            self.current_ip = None
            self.logger.info("Successfully initialized TwitterScraper with MongoDB connection")
        except Exception as e:
            self.logger.error(f"Failed to initialize TwitterScraper: {str(e)}")
            raise

    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger('TwitterScraper')

    def setup_driver(self):
        """Set up Chrome driver with anti-detection options"""
        chrome_options = Options()

        # Basic options
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--proxy-bypass-list=*')

        # Anti-detection options
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
        chrome_options.add_experimental_option('useAutomationExtension', False)

        # Additional stealth options
        chrome_options.add_argument('--lang=en-US,en')
        chrome_options.add_argument('--disable-notifications')
        chrome_options.add_argument(f'--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

        chrome_options.page_load_strategy = 'eager'

        # Add proxy if available
        try:
            proxy = self.proxy_rotator.get_next_proxy()
            self.current_ip = proxy['ip']
            chrome_options.add_argument(f'--proxy-server={proxy["proxy_host"]}')
        except Exception as e:
            self.logger.warning(f"Failed to get proxy, continuing without proxy: {str(e)}")
            self.current_ip = 'direct'

        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=chrome_options
        )

        # Additional anti-detection measures
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        return driver

    def human_like_delay(self, min_seconds=2, max_seconds=4):
        """Add random delay to simulate human behavior"""
        time.sleep(random.uniform(min_seconds, max_seconds))

    def check_login_success(self, driver):
        """Check if login was successful"""
        try:
            indicators = [
                '[data-testid="SideNav_AccountSwitcher_Button"]',
                '[data-testid="AppTabBar_Profile_Link"]',
                '[aria-label="Profile"]'
            ]

            for indicator in indicators:
                try:
                    WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, indicator))
                    )
                    self.logger.info("Login successful")
                    return True
                except:
                    continue

            self.logger.warning("Could not verify login success")
            return False

        except Exception as e:
            self.logger.error(f"Error checking login status: {str(e)}")
            return False

    def get_trends(self, max_retries=3):
        for attempt in range(max_retries):
            driver = None
            try:
                self.logger.info(f"Attempt {attempt + 1} of {max_retries}")
                driver = self.setup_driver()
                driver.set_page_load_timeout(30)

                self.logger.info("Navigating to X.com login page")
                driver.get('https://twitter.com/i/flow/login')
                self.human_like_delay(3, 5)

                self.logger.info("Attempting to log in")
                username_input = WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'input[autocomplete="username"]'))
                )

                for char in TWITTER_USERNAME:
                    username_input.send_keys(char)
                    time.sleep(random.uniform(0.1, 0.3))

                self.human_like_delay()

                next_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//span[text()='Next']"))
                )
                next_button.click()


                self.human_like_delay()

                password_input = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'input[name="password"]'))
                )

                for char in TWITTER_PASSWORD:
                    password_input.send_keys(char)
                    time.sleep(random.uniform(0.1, 0.3))

                self.human_like_delay()

                login_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//span[text()='Log in']"))
                )
                login_button.click()

                self.human_like_delay(4, 6)

                if not self.check_login_success(driver):
                    raise Exception("Login verification failed")

                self.logger.info("Navigating to home page")
                driver.get('https://twitter.com/home')
                self.human_like_delay(3, 5)

                self.logger.info("Locating 'Search' section")
                search_container = WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located((By.XPATH, "//span[text()='Search']/ancestor::div"))
                )

                self.logger.info("Locating 'What's happening' near 'Search'")
                whats_happening_label = search_container.find_element(By.XPATH, ".//span[text()=\"What's happening\"]")

                trends_container = whats_happening_label.find_element(By.XPATH, "./ancestor::div/following-sibling::div")

                trend_elements = trends_container.find_elements(By.CSS_SELECTOR, "div[dir='auto']")
                trends = [trend.text.strip() for trend in trend_elements if trend.text.strip()]

                if trends:
                    self.logger.info(f"Successfully retrieved {len(trends[:5])} trends")

                    trend_data = {
                        'unique_id': str(uuid.uuid4()),
                        'timestamp': datetime.now(),
                        'ip_address': self.current_ip
                    }

                    for i, trend in enumerate(trends[:5], 1):
                        trend_data[f'trend{i}'] = trend

                    self.db.insert_trends(trend_data)
                    self.logger.info("Successfully stored trends in MongoDB")

                    return trends[:5]

                else:
                    raise Exception("No trends found in the 'What's happening' section")

            except Exception as e:
                self.logger.error(f"Error during scraping (attempt {attempt + 1}): {str(e)}")
                if attempt < max_retries - 1:
                    self.logger.info("Retrying...")
                    self.human_like_delay(5, 8)
                else:
                    self.logger.error("Max retries reached")
                    raise

            finally:
                if driver:
                    try:
                        driver.quit()
                    except Exception as e:
                        self.logger.error(f"Error closing driver: {str(e)}")

        return []

if __name__ == '__main__':
    try:
        scraper = TwitterScraper()
        trends = scraper.get_trends()
        print("Retrieved and stored trends:", trends)

        latest_trends = scraper.db.get_latest_trends(limit=1)
        print("Latest trends from database:", latest_trends[0] if latest_trends else "No trends found")

    except Exception as e:
        print(f"Error: {str(e)}")

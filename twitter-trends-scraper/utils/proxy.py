# utils/proxy.py

import requests
from bs4 import BeautifulSoup
from itertools import cycle
import logging
import random
import concurrent.futures
from typing import List, Dict
import time

class FreeProxyRotator:
    """
    A class to handle proxy rotation using free proxies.
    Includes proxy validation and automatic rotation.
    """
    
    def __init__(self, min_proxies: int = 5):
        """
        Initialize the proxy rotator
        Args:
            min_proxies: Minimum number of working proxies to maintain
        """
        self.min_proxies = min_proxies
        self.working_proxies: List[Dict] = []
        self.proxy_cycle = None
        self.setup_logging()
        self.refresh_proxies()
    
    def setup_logging(self):
        """Set up logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger('FreeProxyRotator')

    def fetch_proxy_list(self) -> List[Dict]:
        """
        Fetch free proxies from multiple sources
        Returns:
            List of proxy dictionaries
        """
        proxies = []
        
        # Source 1: free-proxy-list.net
        try:
            response = requests.get('https://free-proxy-list.net/')
            soup = BeautifulSoup(response.text, 'html.parser')
            proxy_table = soup.find('table')
            
            for row in proxy_table.find_all('tr')[1:]:  # Skip header
                cols = row.find_all('td')
                if len(cols) >= 7:  # Ensure row has enough columns
                    ip = cols[0].text.strip()
                    port = cols[1].text.strip()
                    https = cols[6].text.strip()
                    
                    if https == 'yes':  # Only use HTTPS proxies
                        proxy = {
                            'ip': ip,
                            'port': port,
                            'proxy_url': f'http://{ip}:{port}'
                        }
                        proxies.append(proxy)
        except Exception as e:
            self.logger.error(f"Error fetching from free-proxy-list.net: {str(e)}")

        # Source 2: geonode free proxies
        try:
            response = requests.get('https://proxylist.geonode.com/api/proxy-list?limit=100&page=1&sort_by=lastChecked&sort_type=desc&protocols=http%2Chttps')
            data = response.json()
            
            for proxy in data.get('data', []):
                if proxy.get('protocols') and 'https' in proxy['protocols']:
                    proxy_dict = {
                        'ip': proxy['ip'],
                        'port': proxy['port'],
                        'proxy_url': f'http://{proxy["ip"]}:{proxy["port"]}'
                    }
                    proxies.append(proxy_dict)
        except Exception as e:
            self.logger.error(f"Error fetching from geonode: {str(e)}")

        return proxies

    def validate_proxy(self, proxy: Dict) -> bool:
        """
        Validate if a proxy is working
        Args:
            proxy: Proxy dictionary containing proxy information
        Returns:
            bool: True if proxy is working, False otherwise
        """
        try:
            # Test proxy with timeout
            test_url = 'https://httpbin.org/ip'
            proxies = {
                'http': proxy['proxy_url'],
                'https': proxy['proxy_url']
            }
            
            response = requests.get(
                test_url,
                proxies=proxies,
                timeout=10
            )
            
            if response.status_code == 200:
                # Verify we're actually using the proxy
                response_ip = response.json().get('origin', '').split(',')[0]
                if response_ip and response_ip != requests.get('https://httpbin.org/ip').json()['origin']:
                    return True
            return False
        except:
            return False

    def refresh_proxies(self):
        """Refresh the list of working proxies"""
        self.logger.info("Refreshing proxy list...")
        all_proxies = self.fetch_proxy_list()
        working_proxies = []
        
        # Validate proxies in parallel
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            future_to_proxy = {
                executor.submit(self.validate_proxy, proxy): proxy 
                for proxy in all_proxies
            }
            
            for future in concurrent.futures.as_completed(future_to_proxy):
                proxy = future_to_proxy[future]
                try:
                    if future.result():
                        working_proxies.append(proxy)
                        self.logger.info(f"Found working proxy: {proxy['ip']}:{proxy['port']}")
                        
                        # Break if we have enough working proxies
                        if len(working_proxies) >= self.min_proxies:
                            break
                except Exception as e:
                    self.logger.error(f"Error validating proxy: {str(e)}")

        self.working_proxies = working_proxies
        self.proxy_cycle = cycle(working_proxies)
        self.logger.info(f"Found {len(working_proxies)} working proxies")

    def get_next_proxy(self) -> Dict:
        """
        Get the next working proxy from the rotation
        Returns:
            Dict containing proxy information
        """
        if not self.working_proxies:
            self.refresh_proxies()
        
        if not self.working_proxies:
            raise Exception("No working proxies available")
        
        proxy = next(self.proxy_cycle)
        
        # Verify proxy still works, if not refresh list
        if not self.validate_proxy(proxy):
            self.refresh_proxies()
            if not self.working_proxies:
                raise Exception("No working proxies available")
            proxy = next(self.proxy_cycle)
        
        return {
            'proxy': proxy['proxy_url'],
            'ip': proxy['ip'],
            'proxy_host': f"{proxy['ip']}:{proxy['port']}"
        }

    def get_proxy_for_selenium(self) -> Dict:
        """
        Get proxy settings formatted for Selenium WebDriver
        Returns:
            Dict containing proxy settings for Selenium
        """
        proxy_info = self.get_next_proxy()
        return {
            'proxy': {
                'httpProxy': proxy_info['proxy_host'],
                'sslProxy': proxy_info['proxy_host'],
                'proxyType': 'MANUAL',
            },
            'ip': proxy_info['ip']
        }

if __name__ == '__main__':
    # Test the proxy rotator
    rotator = FreeProxyRotator(min_proxies=3)
    
    for _ in range(3):
        try:
            proxy = rotator.get_next_proxy()
            print(f"Successfully connected through proxy: {proxy['proxy_host']}")
            print(f"Current IP: {proxy['ip']}")
            time.sleep(2)  # Wait between tests
        except Exception as e:
            print(f"Error: {str(e)}")
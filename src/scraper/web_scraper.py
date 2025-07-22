"""Web scraping functionality for the Egypt Exporters Scraper."""

import requests
import time
from typing import Optional, Dict, Any, List
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.logger import Logger


class WebScraper:
    """Handles web scraping operations with proper session management."""
    
    def __init__(self, config: Dict[str, Any], logger: Logger):
        """Initialize WebScraper with configuration and logger."""
        self.config = config
        self.logger = logger
        self.session = None
        self.base_url = config.get('base_url', '')
        self.user_agent = config.get('user_agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        self.timeout = config.get('timeout', 30)
        self.request_delay_min = config.get('request_delay_min', 2)
        self.request_delay_max = config.get('request_delay_max', 5)
        
        self._initialize_session()
    
    def _initialize_session(self) -> None:
        """Initialize requests session with proper headers and retry strategy."""
        self.session = requests.Session()
        
        # Set headers
        self.session.headers.update({
            'User-Agent': self.user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ar,en-US;q=0.7,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        self.logger.info("WebScraper session initialized successfully")
    
    def fetch_page(self, url: str, max_retries: Optional[int] = None) -> Optional[str]:
        """Fetch webpage content with retry logic and error handling."""
        if max_retries is None:
            max_retries = self.config.get('retry_attempts', 3)
        
        for attempt in range(max_retries + 1):
            try:
                self.logger.info(f"Fetching page: {url} (Attempt {attempt + 1}/{max_retries + 1})")
                
                response = self.session.get(url, timeout=self.timeout)
                
                # Handle rate limiting
                if response.status_code == 429:
                    self.logger.warning(f"Rate limited on {url}, waiting longer...")
                    self._handle_rate_limiting(attempt)
                    continue
                
                response.raise_for_status()
                
                # Check if response is HTML
                content_type = response.headers.get('content-type', '').lower()
                if 'text/html' not in content_type:
                    self.logger.warning(f"Non-HTML content received from {url}: {content_type}")
                    return None
                
                self.logger.info(f"Successfully fetched page: {url} (Status: {response.status_code})")
                return response.text
                
            except requests.exceptions.Timeout as e:
                self.logger.warning(f"Timeout on attempt {attempt + 1} for {url}: {e}")
                if attempt < max_retries:
                    self._exponential_backoff(attempt)
                    continue
                    
            except requests.exceptions.ConnectionError as e:
                self.logger.warning(f"Connection error on attempt {attempt + 1} for {url}: {e}")
                if attempt < max_retries:
                    self._exponential_backoff(attempt)
                    continue
                    
            except requests.exceptions.HTTPError as e:
                status_code = e.response.status_code if e.response else None
                self.logger.error(f"HTTP error {status_code} for {url}: {e}")
                
                # Don't retry for client errors (4xx except 429)
                if status_code and 400 <= status_code < 500 and status_code != 429:
                    return None
                    
                if attempt < max_retries:
                    self._exponential_backoff(attempt)
                    continue
                    
            except requests.exceptions.RequestException as e:
                self.logger.error(f"Request error on attempt {attempt + 1} for {url}: {e}")
                if attempt < max_retries:
                    self._exponential_backoff(attempt)
                    continue
                    
            except Exception as e:
                self.logger.error(f"Unexpected error on attempt {attempt + 1} for {url}: {e}")
                if attempt < max_retries:
                    self._exponential_backoff(attempt)
                    continue
        
        self.logger.error(f"Failed to fetch page after {max_retries + 1} attempts: {url}")
        return None
    
    def _exponential_backoff(self, attempt: int) -> None:
        """Implement exponential backoff for retries."""
        delay = min(2 ** attempt, 60)  # Cap at 60 seconds
        self.logger.info(f"Waiting {delay} seconds before retry...")
        time.sleep(delay)
    
    def _handle_rate_limiting(self, attempt: int) -> None:
        """Handle rate limiting with adaptive delays."""
        base_delay = self.request_delay_max * 2
        delay = base_delay * (2 ** attempt)
        delay = min(delay, 300)  # Cap at 5 minutes
        self.logger.info(f"Rate limited - waiting {delay} seconds...")
        time.sleep(delay)
    
    def discover_all_pages(self, start_url: str) -> List[str]:
        """Discover all available pages from the website."""
        all_urls = []
        visited_urls = set()
        urls_to_visit = [start_url]
        
        self.logger.info(f"Starting page discovery from: {start_url}")
        
        while urls_to_visit:
            current_url = urls_to_visit.pop(0)
            
            if current_url in visited_urls:
                continue
                
            visited_urls.add(current_url)
            self.logger.info(f"Discovering pages from: {current_url}")
            
            # Respect rate limits
            self.respect_rate_limits()
            
            html_content = self.fetch_page(current_url)
            if not html_content:
                continue
                
            all_urls.append(current_url)
            
            # Parse HTML to find more pages
            soup = BeautifulSoup(html_content, 'lxml')
            new_urls = self._extract_navigation_urls(soup, current_url)
            
            for url in new_urls:
                if url not in visited_urls and url not in urls_to_visit:
                    urls_to_visit.append(url)
        
        self.logger.info(f"Page discovery completed. Found {len(all_urls)} pages")
        return all_urls
    
    def _extract_navigation_urls(self, soup: BeautifulSoup, current_url: str) -> List[str]:
        """Extract navigation URLs from HTML content."""
        urls = []
        base_domain = urlparse(self.base_url).netloc
        
        # Look for pagination links
        pagination_selectors = [
            'a[href*="page"]',
            'a[href*="Page"]',
            'a[href*="p="]',
            'a[href*="pagenum"]',
            '.pagination a',
            '.pager a',
            '.page-numbers a',
            'a:contains("Next")',
            'a:contains("التالي")',
            'a:contains(">")',
            'a:contains("»")'
        ]
        
        for selector in pagination_selectors:
            try:
                links = soup.select(selector)
                for link in links:
                    href = link.get('href')
                    if href:
                        full_url = urljoin(current_url, href)
                        if self._is_valid_url(full_url, base_domain):
                            urls.append(full_url)
            except Exception as e:
                self.logger.debug(f"Error with selector {selector}: {e}")
        
        # Look for category/section links
        category_selectors = [
            'a[href*="category"]',
            'a[href*="section"]',
            'a[href*="type"]',
            'a[href*="filter"]',
            '.menu a',
            '.nav a',
            '.categories a'
        ]
        
        for selector in category_selectors:
            try:
                links = soup.select(selector)
                for link in links:
                    href = link.get('href')
                    if href:
                        full_url = urljoin(current_url, href)
                        if self._is_valid_url(full_url, base_domain):
                            urls.append(full_url)
            except Exception as e:
                self.logger.debug(f"Error with selector {selector}: {e}")
        
        return list(set(urls))  # Remove duplicates
    
    def _is_valid_url(self, url: str, base_domain: str) -> bool:
        """Check if URL is valid and belongs to the target domain."""
        try:
            parsed = urlparse(url)
            
            # Must be same domain
            if parsed.netloc != base_domain:
                return False
            
            # Skip certain file types
            skip_extensions = ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.zip', '.rar', '.jpg', '.png', '.gif']
            if any(url.lower().endswith(ext) for ext in skip_extensions):
                return False
            
            # Skip certain paths
            skip_paths = ['mailto:', 'tel:', 'javascript:', '#']
            if any(url.lower().startswith(path) for path in skip_paths):
                return False
            
            return True
            
        except Exception:
            return False
    
    def navigate_pagination(self, html_content: str, current_url: str) -> Optional[str]:
        """Find and return the next page URL from current page."""
        soup = BeautifulSoup(html_content, 'lxml')
        
        # Common pagination patterns
        next_selectors = [
            'a[rel="next"]',
            'a:contains("Next")',
            'a:contains("التالي")',
            'a:contains(">")',
            'a:contains("»")',
            '.pagination .next',
            '.pager .next',
            '.page-numbers .next'
        ]
        
        for selector in next_selectors:
            try:
                next_link = soup.select_one(selector)
                if next_link and next_link.get('href'):
                    next_url = urljoin(current_url, next_link.get('href'))
                    if self._is_valid_url(next_url, urlparse(self.base_url).netloc):
                        return next_url
            except Exception as e:
                self.logger.debug(f"Error with next selector {selector}: {e}")
        
        return None
    
    def respect_rate_limits(self) -> None:
        """Implement delay between requests to respect rate limits."""
        import random
        delay = random.uniform(self.request_delay_min, self.request_delay_max)
        self.logger.debug(f"Waiting {delay:.2f} seconds before next request")
        time.sleep(delay)
    
    def close_session(self) -> None:
        """Close the requests session."""
        if self.session:
            self.session.close()
            self.logger.info("WebScraper session closed")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close_session()
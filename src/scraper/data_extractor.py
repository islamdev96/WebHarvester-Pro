"""Data extraction functionality for the Egypt Exporters Scraper."""

from bs4 import BeautifulSoup
from typing import Dict, Any, List, Optional
import re
from datetime import datetime

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.logger import Logger
from utils.validators import Validators


class DataExtractor:
    """Extracts structured data from HTML content."""
    
    def __init__(self, logger: Logger):
        """Initialize DataExtractor with logger."""
        self.logger = logger
        self.validators = Validators()
    
    def extract_companies_from_page(self, html_content: str, source_url: str) -> List[Dict[str, Any]]:
        """Extract all company data from a single page."""
        if not html_content:
            return []
        
        soup = BeautifulSoup(html_content, 'lxml')
        companies = []
        
        # Try different patterns to find company listings
        company_containers = self._find_company_containers(soup)
        
        self.logger.info(f"Found {len(company_containers)} potential company containers on page")
        
        for i, container in enumerate(company_containers):
            try:
                company_data = self._extract_single_company(container, source_url)
                # Check if company has either English or Arabic name
                if company_data and (company_data.get('company_name') or company_data.get('company_name_arabic')):
                    companies.append(company_data)
                    name = company_data.get('company_name') or company_data.get('company_name_arabic', 'Unknown')
                    self.logger.debug(f"Extracted company {i+1}: {name}")
                else:
                    self.logger.debug(f"Skipped company {i+1}: No valid name found")
            except Exception as e:
                self.logger.error(f"Error extracting company {i+1}: {e}")
                continue
        
        self.logger.info(f"Successfully extracted {len(companies)} companies from page")
        return companies
    
    def _find_company_containers(self, soup: BeautifulSoup) -> List:
        """Find HTML containers that likely contain company information."""
        containers = []
        
        # First, try specific selectors for this website
        specific_selectors = [
            '.co_node',  # Main company container
            'div.co_node',
            '.exporter_directory .co_node'
        ]
        
        for selector in specific_selectors:
            try:
                elements = soup.select(selector)
                if elements:
                    self.logger.info(f"Found {len(elements)} companies using selector: {selector}")
                    containers.extend(elements)
            except Exception as e:
                self.logger.debug(f"Error with selector {selector}: {e}")
        
        # If no specific containers found, try generic patterns
        if not containers:
            generic_selectors = [
                '.company',
                '.exporter',
                '.listing',
                '.item',
                '.entry',
                '.record',
                'tr',  # Table rows
                '.row',
                'div[class*="company"]',
                'div[class*="exporter"]',
                'div[class*="business"]',
                'li',  # List items
                'article',
                '.card',
                '.box'
            ]
            
            for selector in generic_selectors:
                try:
                    elements = soup.select(selector)
                    # Filter elements that likely contain company data
                    for element in elements:
                        if self._looks_like_company_container(element):
                            containers.append(element)
                except Exception as e:
                    self.logger.debug(f"Error with selector {selector}: {e}")
        
        # Remove duplicates while preserving order
        seen = set()
        unique_containers = []
        for container in containers:
            container_id = id(container)
            if container_id not in seen:
                seen.add(container_id)
                unique_containers.append(container)
        
        return unique_containers
    
    def _looks_like_company_container(self, element) -> bool:
        """Check if an element looks like it contains company information."""
        text = element.get_text().strip()
        
        # Must have some text
        if len(text) < 10:
            return False
        
        # Look for indicators of company information
        company_indicators = [
            'شركة',  # Company in Arabic
            'مؤسسة',  # Institution in Arabic
            'company',
            'corp',
            'ltd',
            'inc',
            'co.',
            'tel:',
            'phone:',
            'email:',
            '@',
            'www.',
            'http',
            'fax:',
            'address:',
            'عنوان',  # Address in Arabic
            'تليفون',  # Phone in Arabic
            'فاكس',  # Fax in Arabic
            'بريد'  # Email in Arabic
        ]
        
        text_lower = text.lower()
        indicator_count = sum(1 for indicator in company_indicators if indicator in text_lower)
        
        # Must have at least 2 indicators or be long enough to likely contain company info
        return indicator_count >= 2 or len(text) > 100
    
    def _extract_single_company(self, container, source_url: str) -> Dict[str, Any]:
        """Extract data from a single company container."""
        company_data = {
            'id': self._generate_company_id(container),
            'company_name': '',
            'company_name_arabic': '',
            'contact_info': {},
            'business_info': {},
            'registration_info': {},
            'extraction_metadata': {
                'extracted_at': datetime.now().isoformat(),
                'source_url': source_url
            }
        }
        
        # Extract company names
        company_data['company_name'], company_data['company_name_arabic'] = self._extract_company_names(container)
        
        # Extract contact information
        company_data['contact_info'] = self._extract_contact_info(container)
        
        # Extract business information
        company_data['business_info'] = self._extract_business_info(container)
        
        # Extract registration information
        company_data['registration_info'] = self._extract_registration_info(container)
        
        return company_data
    
    def _generate_company_id(self, container) -> str:
        """Generate a unique ID for the company."""
        # Use a combination of text content hash and position
        text = container.get_text().strip()[:100]  # First 100 chars
        import hashlib
        return hashlib.md5(text.encode('utf-8')).hexdigest()[:12]
    
    def _extract_company_names(self, container) -> tuple:
        """Extract company names in English and Arabic."""
        english_name = ""
        arabic_name = ""
        
        # First, try specific selectors for this website
        specific_selectors = [
            '.co_title',  # Main company title
            'div.co_title',
            '.company-name',
            '.name'
        ]
        
        for selector in specific_selectors:
            try:
                elements = container.select(selector)
                for element in elements:
                    text = element.get_text().strip()
                    if text and len(text) > 3:
                        if self._is_arabic_text(text):
                            if not arabic_name or len(text) > len(arabic_name):
                                arabic_name = text
                        else:
                            if not english_name or len(text) > len(english_name):
                                english_name = text
            except Exception:
                continue
        
        # If no names found with specific selectors, try generic ones
        if not english_name and not arabic_name:
            generic_selectors = [
                'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
                '.title',
                'strong', 'b',
                'td:first-child',  # First column in table
                '.first',
                'a[href*="/co/"]'  # Links to company pages
            ]
            
            for selector in generic_selectors:
                try:
                    elements = container.select(selector)
                    for element in elements:
                        text = element.get_text().strip()
                        if text and len(text) > 3:
                            if self._is_arabic_text(text):
                                if not arabic_name or len(text) > len(arabic_name):
                                    arabic_name = text
                            else:
                                if not english_name or len(text) > len(english_name):
                                    english_name = text
                except Exception:
                    continue
        
        # If still no names found, try to extract from full text
        if not english_name and not arabic_name:
            all_text = container.get_text()
            lines = all_text.split('\n')
            for line in lines[:5]:  # Check first 5 lines
                line = line.strip()
                if len(line) > 5 and not any(indicator in line.lower() for indicator in ['tel', 'phone', 'email', 'fax', 'address', 'القطاع', 'محافظة']):
                    if self._is_arabic_text(line):
                        if not arabic_name:
                            arabic_name = line
                    else:
                        if not english_name:
                            english_name = line
                    
                    if english_name and arabic_name:
                        break
        
        return self.validators.clean_text(english_name), self.validators.clean_text(arabic_name)
    
    def _extract_contact_info(self, container) -> Dict[str, str]:
        """Extract contact information from container."""
        contact_info = {}
        text = container.get_text()
        
        # Extract email
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text)
        if emails:
            contact_info['email'] = emails[0]
        
        # Extract phone numbers
        phone_patterns = [
            r'(?:tel|phone|تليفون|هاتف)[\s:]*([+\d\s\-\(\)]{7,20})',
            r'(\+20\d{9,10})',
            r'(20\d{9,10})',
            r'(0\d{9,10})',
            r'(\d{3,4}[-\s]?\d{3,4}[-\s]?\d{3,4})'
        ]
        
        for pattern in phone_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                clean_phone = re.sub(r'[^\d+]', '', match)
                if len(clean_phone) >= 7:
                    contact_info['phone'] = match.strip()
                    break
            if 'phone' in contact_info:
                break
        
        # Extract fax
        fax_patterns = [
            r'(?:fax|فاكس)[\s:]*([+\d\s\-\(\)]{7,20})',
        ]
        
        for pattern in fax_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                contact_info['fax'] = matches[0].strip()
                break
        
        # Extract website
        website_patterns = [
            r'(?:www\.|http[s]?://)([\w\.-]+\.[a-zA-Z]{2,})',
            r'(www\.[\w\.-]+\.[a-zA-Z]{2,})'
        ]
        
        for pattern in website_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                website = matches[0]
                if not website.startswith('http'):
                    website = 'http://' + website
                contact_info['website'] = website
                break
        
        # Extract address (basic extraction)
        address_indicators = ['address', 'عنوان', 'addr']
        for indicator in address_indicators:
            pattern = rf'{indicator}[\s:]*([^\n\r]+)'
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                address = matches[0].strip()
                if len(address) > 10:
                    if self._is_arabic_text(address):
                        contact_info['address_arabic'] = address
                    else:
                        contact_info['address'] = address
                    break
        
        return contact_info
    
    def _is_arabic_text(self, text: str) -> bool:
        """Check if text contains Arabic characters."""
        arabic_pattern = r'[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]'
        return bool(re.search(arabic_pattern, text))
    
    def _extract_business_info(self, container) -> Dict[str, Any]:
        """Extract business information from container."""
        business_info = {
            'categories': [],
            'products': [],
            'export_markets': []
        }
        
        text = container.get_text()
        
        # Extract business categories
        category_indicators = [
            'category', 'categories', 'sector', 'industry', 'field',
            'نشاط', 'قطاع', 'مجال', 'تخصص', 'فئة'
        ]
        
        for indicator in category_indicators:
            pattern = rf'{indicator}[\s:]*([^\n\r]+)'
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                categories = self._parse_list_items(match)
                business_info['categories'].extend(categories)
        
        # Extract products
        product_indicators = [
            'product', 'products', 'goods', 'items', 'manufacture',
            'منتج', 'منتجات', 'سلع', 'بضائع', 'تصنيع'
        ]
        
        for indicator in product_indicators:
            pattern = rf'{indicator}[\s:]*([^\n\r]+)'
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                products = self._parse_list_items(match)
                business_info['products'].extend(products)
        
        # Extract export markets
        market_indicators = [
            'export', 'market', 'markets', 'countries', 'destination',
            'تصدير', 'أسواق', 'سوق', 'دول', 'وجهة'
        ]
        
        for indicator in market_indicators:
            pattern = rf'{indicator}[\s:]*([^\n\r]+)'
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                markets = self._parse_list_items(match)
                business_info['export_markets'].extend(markets)
        
        # Remove duplicates and clean
        business_info['categories'] = list(set([self.validators.clean_text(cat) for cat in business_info['categories'] if cat]))
        business_info['products'] = list(set([self.validators.clean_text(prod) for prod in business_info['products'] if prod]))
        business_info['export_markets'] = list(set([self.validators.clean_text(market) for market in business_info['export_markets'] if market]))
        
        return business_info
    
    def _extract_registration_info(self, container) -> Dict[str, str]:
        """Extract registration information from container."""
        registration_info = {}
        text = container.get_text()
        
        # Extract registration number
        reg_patterns = [
            r'(?:reg|registration|license|رقم[\s]*التسجيل|رخصة)[\s#:]*([A-Z0-9\-/]{5,20})',
            r'(?:commercial|تجاري)[\s#:]*([A-Z0-9\-/]{5,20})',
            r'(?:tax|ضريبي)[\s#:]*([A-Z0-9\-/]{5,20})'
        ]
        
        for pattern in reg_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                registration_info['registration_number'] = matches[0].strip()
                break
        
        # Extract registration date
        date_patterns = [
            r'(?:established|founded|تأسست|أنشئت)[\s:]*(\d{4})',
            r'(?:since|منذ)[\s:]*(\d{4})',
            r'(\d{1,2}[/-]\d{1,2}[/-]\d{4})',
            r'(\d{4}[/-]\d{1,2}[/-]\d{1,2})'
        ]
        
        for pattern in date_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                registration_info['registration_date'] = matches[0].strip()
                break
        
        return registration_info
    
    def _parse_list_items(self, text: str) -> List[str]:
        """Parse comma-separated or line-separated list items."""
        if not text:
            return []
        
        # Try different separators
        separators = [',', '،', ';', '؛', '|', '\n', '-']
        
        items = []
        for separator in separators:
            if separator in text:
                parts = text.split(separator)
                items = [part.strip() for part in parts if part.strip()]
                break
        
        # If no separator found, treat as single item
        if not items:
            items = [text.strip()]
        
        # Filter out very short or very long items
        filtered_items = []
        for item in items:
            if 3 <= len(item) <= 100:
                filtered_items.append(item)
        
        return filtered_items
    
    def normalize_and_clean_data(self, companies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Normalize and clean extracted company data."""
        cleaned_companies = []
        
        for company in companies:
            try:
                # Validate and clean the company data
                cleaned_company = self.validators.validate_company_data(company)
                
                # Only keep companies with meaningful data
                if (cleaned_company.get('company_name') or cleaned_company.get('company_name_arabic')):
                    cleaned_companies.append(cleaned_company)
                    
            except Exception as e:
                self.logger.warning(f"Failed to clean company data: {e}")
                continue
        
        self.logger.info(f"Cleaned {len(cleaned_companies)} companies from {len(companies)} raw extractions")
        return cleaned_companies
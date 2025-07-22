"""JSON conversion functionality for the Egypt Exporters Scraper."""

import json
from typing import Dict, Any, List
from datetime import datetime

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.logger import Logger
from utils.file_handler import FileHandler


class JSONConverter:
    """Converts extracted data to properly formatted JSON."""
    
    def __init__(self, logger: Logger):
        """Initialize JSONConverter with logger."""
        self.logger = logger
        self.file_handler = FileHandler()
    
    def convert_to_json(self, companies: List[Dict[str, Any]], session_info: Dict[str, Any] = None) -> Dict[str, Any]:
        """Convert company data to structured JSON format."""
        if session_info is None:
            session_info = {
                'start_time': datetime.now().isoformat(),
                'end_time': datetime.now().isoformat(),
                'total_pages_scraped': 0,
                'total_companies_extracted': len(companies),
                'errors_encountered': 0
            }
        
        json_data = {
            'metadata': {
                'scraper_version': '1.0.0',
                'extraction_date': datetime.now().isoformat(),
                'source_website': 'http://www.expoegypt.gov.eg/exporters',
                'total_companies': len(companies),
                'data_format': 'Egypt Exporters Directory'
            },
            'session_info': session_info,
            'companies': companies
        }
        
        self.logger.info(f"Converted {len(companies)} companies to JSON format")
        return json_data
    
    def validate_json_format(self, json_data: Dict[str, Any]) -> bool:
        """Validate JSON data structure and content."""
        try:
            # Check required top-level keys
            required_keys = ['metadata', 'session_info', 'companies']
            for key in required_keys:
                if key not in json_data:
                    self.logger.error(f"Missing required JSON key: {key}")
                    return False
            
            # Validate metadata
            metadata = json_data['metadata']
            required_metadata = ['scraper_version', 'extraction_date', 'source_website', 'total_companies']
            for key in required_metadata:
                if key not in metadata:
                    self.logger.error(f"Missing required metadata key: {key}")
                    return False
            
            # Validate companies array
            companies = json_data['companies']
            if not isinstance(companies, list):
                self.logger.error("Companies data must be a list")
                return False
            
            # Validate individual company records
            for i, company in enumerate(companies):
                if not self._validate_company_record(company, i):
                    return False
            
            # Check data consistency
            if len(companies) != metadata['total_companies']:
                self.logger.warning(f"Company count mismatch: metadata says {metadata['total_companies']}, actual count is {len(companies)}")
                # Update metadata to match actual count
                json_data['metadata']['total_companies'] = len(companies)
            
            self.logger.info("JSON format validation passed")
            return True
            
        except Exception as e:
            self.logger.error(f"JSON validation error: {e}")
            return False
    
    def _validate_company_record(self, company: Dict[str, Any], index: int) -> bool:
        """Validate individual company record structure."""
        required_keys = ['id', 'contact_info', 'business_info', 'extraction_metadata']
        
        for key in required_keys:
            if key not in company:
                self.logger.error(f"Company {index}: Missing required key '{key}'")
                return False
        
        # Validate that at least one name exists
        if not company.get('company_name') and not company.get('company_name_arabic'):
            self.logger.error(f"Company {index}: Must have at least one company name")
            return False
        
        # Ensure ID exists
        if not company.get('id'):
            self.logger.error(f"Company {index}: Missing required key 'id'")
            return False
        
        # Validate nested structures
        if not isinstance(company.get('contact_info'), dict):
            self.logger.error(f"Company {index}: contact_info must be a dictionary")
            return False
        
        if not isinstance(company.get('business_info'), dict):
            self.logger.error(f"Company {index}: business_info must be a dictionary")
            return False
        
        return True
    
    def handle_arabic_encoding(self, data: Any) -> str:
        """Handle UTF-8 encoding for Arabic text in JSON."""
        try:
            # Convert to JSON string with proper Arabic encoding
            json_string = json.dumps(
                data,
                ensure_ascii=False,  # Allow non-ASCII characters (Arabic)
                indent=2,
                separators=(',', ': '),
                sort_keys=False
            )
            
            # Verify the string can be properly encoded/decoded
            json_string.encode('utf-8').decode('utf-8')
            
            self.logger.debug("Arabic encoding handled successfully")
            return json_string
            
        except UnicodeEncodeError as e:
            self.logger.error(f"Unicode encoding error: {e}")
            # Fallback: use ASCII-safe encoding
            return json.dumps(data, ensure_ascii=True, indent=2)
        except Exception as e:
            self.logger.error(f"JSON encoding error: {e}")
            raise
    
    def save_json_file(self, json_data: Dict[str, Any], file_path: str) -> bool:
        """Save JSON data to file with proper encoding."""
        try:
            # Validate before saving
            if not self.validate_json_format(json_data):
                self.logger.error("JSON validation failed, not saving file")
                return False
            
            # Save with UTF-8 encoding
            self.file_handler.save_json(json_data, file_path, encoding='utf-8', indent=2)
            
            # Verify file was saved correctly
            file_size = self.file_handler.get_file_size(file_path)
            self.logger.info(f"JSON file saved successfully: {file_path} ({file_size} bytes)")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save JSON file: {e}")
            return False
    
    def load_and_merge_json(self, file_path: str, new_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Load existing JSON file and merge with new data."""
        try:
            if self.file_handler.file_exists(file_path):
                existing_data = self.file_handler.load_json(file_path)
                
                # Merge companies
                existing_companies = existing_data.get('companies', [])
                all_companies = existing_companies + new_data
                
                # Update metadata
                existing_data['companies'] = all_companies
                existing_data['metadata']['total_companies'] = len(all_companies)
                existing_data['metadata']['last_updated'] = datetime.now().isoformat()
                
                self.logger.info(f"Merged {len(new_data)} new companies with {len(existing_companies)} existing companies")
                return existing_data
            else:
                # Create new structure
                return self.convert_to_json(new_data)
                
        except Exception as e:
            self.logger.error(f"Failed to load and merge JSON: {e}")
            # Return new data as fallback
            return self.convert_to_json(new_data)
    
    def create_summary_report(self, json_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a summary report of the extracted data."""
        companies = json_data.get('companies', [])
        
        summary = {
            'total_companies': len(companies),
            'companies_with_email': sum(1 for c in companies if c.get('contact_info', {}).get('email')),
            'companies_with_phone': sum(1 for c in companies if c.get('contact_info', {}).get('phone')),
            'companies_with_website': sum(1 for c in companies if c.get('contact_info', {}).get('website')),
            'companies_with_arabic_name': sum(1 for c in companies if c.get('company_name_arabic')),
            'companies_with_english_name': sum(1 for c in companies if c.get('company_name')),
            'total_business_categories': 0,
            'total_products': 0,
            'total_export_markets': 0
        }
        
        # Count business information
        all_categories = set()
        all_products = set()
        all_markets = set()
        
        for company in companies:
            business_info = company.get('business_info', {})
            categories = business_info.get('categories', [])
            products = business_info.get('products', [])
            markets = business_info.get('export_markets', [])
            
            all_categories.update(categories)
            all_products.update(products)
            all_markets.update(markets)
        
        summary['total_business_categories'] = len(all_categories)
        summary['total_products'] = len(all_products)
        summary['total_export_markets'] = len(all_markets)
        summary['unique_categories'] = list(all_categories)[:10]  # Top 10
        summary['unique_products'] = list(all_products)[:10]  # Top 10
        summary['unique_markets'] = list(all_markets)[:10]  # Top 10
        
        return summary  
  
    def remove_duplicates(self, companies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate companies from the list."""
        if not companies:
            return companies
        
        unique_companies = []
        seen_companies = set()
        duplicate_count = 0
        
        for company in companies:
            # Create a signature for the company
            signature = self._create_company_signature(company)
            
            if signature not in seen_companies:
                seen_companies.add(signature)
                unique_companies.append(company)
            else:
                duplicate_count += 1
                self.logger.debug(f"Duplicate company detected: {company.get('company_name', 'Unknown')}")
        
        self.logger.info(f"Removed {duplicate_count} duplicate companies. {len(unique_companies)} unique companies remain.")
        return unique_companies
    
    def _create_company_signature(self, company: Dict[str, Any]) -> str:
        """Create a unique signature for a company to detect duplicates."""
        # Use company name, phone, and email to create signature
        name = company.get('company_name', '').lower().strip()
        name_arabic = company.get('company_name_arabic', '').lower().strip()
        
        contact_info = company.get('contact_info', {})
        phone = contact_info.get('phone', '').strip()
        email = contact_info.get('email', '').lower().strip()
        
        # Clean phone number for comparison
        clean_phone = ''.join(filter(str.isdigit, phone))
        
        # Create signature from available data
        signature_parts = []
        
        if name:
            signature_parts.append(name)
        if name_arabic:
            signature_parts.append(name_arabic)
        if clean_phone and len(clean_phone) >= 7:
            signature_parts.append(clean_phone[-7:])  # Last 7 digits
        if email:
            signature_parts.append(email)
        
        signature = '|'.join(signature_parts)
        
        # If no meaningful signature, use ID
        if not signature:
            signature = company.get('id', '')
        
        return signature
    
    def validate_data_quality(self, companies: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate data quality and return quality metrics."""
        if not companies:
            return {'total_companies': 0, 'quality_score': 0}
        
        quality_metrics = {
            'total_companies': len(companies),
            'companies_with_name': 0,
            'companies_with_contact': 0,
            'companies_with_business_info': 0,
            'companies_with_complete_data': 0,
            'data_completeness_score': 0,
            'quality_issues': []
        }
        
        for i, company in enumerate(companies):
            has_name = bool(company.get('company_name') or company.get('company_name_arabic'))
            has_contact = bool(
                company.get('contact_info', {}).get('phone') or 
                company.get('contact_info', {}).get('email') or
                company.get('contact_info', {}).get('address')
            )
            has_business_info = bool(
                company.get('business_info', {}).get('categories') or
                company.get('business_info', {}).get('products')
            )
            
            if has_name:
                quality_metrics['companies_with_name'] += 1
            else:
                quality_metrics['quality_issues'].append(f"Company {i+1}: Missing company name")
            
            if has_contact:
                quality_metrics['companies_with_contact'] += 1
            
            if has_business_info:
                quality_metrics['companies_with_business_info'] += 1
            
            if has_name and has_contact and has_business_info:
                quality_metrics['companies_with_complete_data'] += 1
        
        # Calculate completeness score (0-100)
        total = len(companies)
        completeness_score = (
            (quality_metrics['companies_with_name'] / total * 40) +
            (quality_metrics['companies_with_contact'] / total * 35) +
            (quality_metrics['companies_with_business_info'] / total * 25)
        )
        
        quality_metrics['data_completeness_score'] = round(completeness_score, 2)
        
        self.logger.info(f"Data quality validation completed. Completeness score: {quality_metrics['data_completeness_score']}%")
        
        return quality_metrics
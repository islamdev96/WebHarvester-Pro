"""Data validation utilities for the Egypt Exporters Scraper."""

import re
from typing import Any, Dict, List, Optional


class Validators:
    """Data validation functions for scraped data."""
    
    @staticmethod
    def is_valid_email(email: str) -> bool:
        """Validate email format."""
        if not email or not isinstance(email, str):
            return False
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    @staticmethod
    def is_valid_phone(phone: str) -> bool:
        """Validate phone number format (Egyptian format)."""
        if not phone or not isinstance(phone, str):
            return False
        # Remove spaces, dashes, and parentheses
        clean_phone = re.sub(r'[\s\-\(\)]', '', phone)
        # Egyptian phone patterns
        patterns = [
            r'^\+20\d{9,10}$',  # +20 followed by 9-10 digits
            r'^20\d{9,10}$',    # 20 followed by 9-10 digits
            r'^0\d{9,10}$',     # 0 followed by 9-10 digits
            r'^\d{7,11}$'       # 7-11 digits
        ]
        return any(re.match(pattern, clean_phone) for pattern in patterns)
    
    @staticmethod
    def is_valid_url(url: str) -> bool:
        """Validate URL format."""
        if not url or not isinstance(url, str):
            return False
        pattern = r'^https?://[^\s/$.?#].[^\s]*$'
        return bool(re.match(pattern, url))
    
    @staticmethod
    def clean_text(text: str) -> str:
        """Clean and normalize text data."""
        if not text or not isinstance(text, str):
            return ""
        # Remove extra whitespace and normalize
        cleaned = re.sub(r'\s+', ' ', text.strip())
        return cleaned
    
    @staticmethod
    def validate_company_data(company_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and clean company data."""
        validated_data = {}
        
        # Check if at least one name exists (English or Arabic)
        if not company_data.get('company_name') and not company_data.get('company_name_arabic'):
            raise ValueError("Missing required field: company_name or company_name_arabic")
        
        # Clean company name
        validated_data['company_name'] = Validators.clean_text(company_data.get('company_name', ''))
        validated_data['company_name_arabic'] = Validators.clean_text(company_data.get('company_name_arabic', ''))
        
        # Validate contact info
        contact_info = company_data.get('contact_info', {})
        validated_contact = {}
        
        if 'email' in contact_info and contact_info['email']:
            email = Validators.clean_text(contact_info['email'])
            if Validators.is_valid_email(email):
                validated_contact['email'] = email
        
        if 'phone' in contact_info and contact_info['phone']:
            phone = Validators.clean_text(contact_info['phone'])
            if Validators.is_valid_phone(phone):
                validated_contact['phone'] = phone
        
        if 'website' in contact_info and contact_info['website']:
            website = Validators.clean_text(contact_info['website'])
            if Validators.is_valid_url(website):
                validated_contact['website'] = website
        
        # Clean address fields
        for field in ['address', 'address_arabic', 'fax']:
            if field in contact_info:
                validated_contact[field] = Validators.clean_text(contact_info[field])
        
        validated_data['contact_info'] = validated_contact
        
        # Clean business info
        business_info = company_data.get('business_info', {})
        validated_business = {}
        
        for field in ['categories', 'products', 'export_markets']:
            if field in business_info and isinstance(business_info[field], list):
                validated_business[field] = [
                    Validators.clean_text(item) for item in business_info[field] 
                    if item and isinstance(item, str)
                ]
        
        validated_data['business_info'] = validated_business
        
        # Clean registration info
        registration_info = company_data.get('registration_info', {})
        validated_registration = {}
        
        for field in ['registration_number', 'registration_date']:
            if field in registration_info:
                validated_registration[field] = Validators.clean_text(registration_info[field])
        
        validated_data['registration_info'] = validated_registration
        
        return validated_data
    
    @staticmethod
    def detect_duplicates(companies: List[Dict[str, Any]]) -> List[int]:
        """Detect duplicate companies based on name similarity."""
        duplicates = []
        seen_names = set()
        
        for i, company in enumerate(companies):
            name = company.get('company_name', '').lower().strip()
            if name in seen_names:
                duplicates.append(i)
            else:
                seen_names.add(name)
        
        return duplicates
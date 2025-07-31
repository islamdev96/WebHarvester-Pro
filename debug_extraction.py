"""Debug script to test data extraction."""

import requests
from bs4 import BeautifulSoup
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.utils.logger import Logger
from src.scraper.data_extractor import DataExtractor

def debug_extraction():
    """Debug the data extraction process."""
    url = "http://www.expoegypt.gov.eg/exporters"
    



    # Fetch the page   
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        # Initialize logger and extractor
        logger = Logger("DebugExtractor", "logs/debug.log", "DEBUG")
        extractor = DataExtractor(logger)
        
        print("=== EXTRACTION DEBUG ===")
        
        # Extract companies
        companies = extractor.extract_companies_from_page(response.text, url)
        
        print(f"Total companies extracted: {len(companies)}")
        
        if companies:
            for i, company in enumerate(companies):
                print(f"\nCompany {i+1}:")
                print(f"  ID: {company.get('id', 'N/A')}")
                print(f"  Name: {company.get('company_name', 'N/A')}")
                print(f"  Arabic Name: {company.get('company_name_arabic', 'N/A')}")
                print(f"  Contact Info: {company.get('contact_info', {})}")
                print(f"  Business Info: {company.get('business_info', {})}")
        else:
            # Debug why no companies were extracted
            soup = BeautifulSoup(response.text, 'lxml')
            
            # Find containers manually
            co_nodes = soup.select('.co_node')
            print(f"\nFound {len(co_nodes)} .co_node elements")
            
            for i, node in enumerate(co_nodes[:3]):  # Check first 3
                print(f"\nNode {i+1}:")
                print(f"  Text length: {len(node.get_text())}")
                print(f"  First 200 chars: {node.get_text()[:200]}...")
                
                # Try to extract company name manually
                co_title = node.select_one('.co_title')
                if co_title:
                    print(f"  Co_title found: {co_title.get_text().strip()}")
                else:
                    print("  No co_title found")
                
                # Check if it passes the validation
                company_data = extractor._extract_single_company(node, url)
                print(f"  Extracted data: {company_data}")
                
                # Check validation
                if company_data.get('company_name') or company_data.get('company_name_arabic'):
                    print("  ✅ Company has valid name")
                else:
                    print("  ❌ Company has no valid name")
        
    except Exception as e:
        print(f"Error in debug extraction: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_extraction()
"""Debug script to analyze the page structure."""

import requests
from bs4 import BeautifulSoup
import json

def analyze_page_structure():
    """Analyze the structure of the Egypt exporters page."""
    url = "http://www.expoegypt.gov.eg/exporters"
    
    # Fetch the page
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'lxml')
        
        print("=== PAGE ANALYSIS ===")
        print(f"Page title: {soup.title.string if soup.title else 'No title'}")
        print(f"Page length: {len(response.text)} characters")
        
        # Save full HTML for inspection
        with open('page_sample.html', 'w', encoding='utf-8') as f:
            f.write(response.text)
        
        print(f"Full HTML saved to page_sample.html")
        
        # Look for API endpoints or AJAX calls in JavaScript
        scripts = soup.find_all('script')
        print(f"\nScript tags found: {len(scripts)}")
        
        api_endpoints = []
        for script in scripts:
            if script.string:
                script_content = script.string.lower()
                # Look for common API patterns
                if 'api' in script_content or 'ajax' in script_content or 'fetch' in script_content:
                    print("  ⚠️  Dynamic content loading detected")
                    # Try to extract API endpoints
                    import re
                    urls = re.findall(r'["\']([^"\']*(?:api|exporters|companies)[^"\']*)["\']', script.string)
                    api_endpoints.extend(urls)
        
        if api_endpoints:
            print("\nPotential API endpoints found:")
            for endpoint in set(api_endpoints):
                print(f"  - {endpoint}")
        
        # Look for data attributes or hidden content
        data_elements = soup.find_all(attrs={'data-url': True})
        if data_elements:
            print(f"\nElements with data-url found: {len(data_elements)}")
            for elem in data_elements:
                print(f"  - {elem.get('data-url')}")
        
        # Look for forms that might submit to get data
        forms = soup.find_all('form')
        print(f"\nForms found: {len(forms)}")
        for i, form in enumerate(forms):
            action = form.get('action', 'No action')
            method = form.get('method', 'GET')
            print(f"  Form {i+1}: {method} {action}")
            
            # Look for inputs that might be search parameters
            inputs = form.find_all('input')
            for inp in inputs:
                name = inp.get('name')
                input_type = inp.get('type', 'text')
                if name:
                    print(f"    Input: {name} ({input_type})")
        
        # Try to find the actual exporters data
        # Look for specific patterns that might contain company data
        potential_data_containers = [
            'div[id*="exporter"]',
            'div[class*="exporter"]',
            'div[id*="company"]',
            'div[class*="company"]',
            'div[id*="result"]',
            'div[class*="result"]',
            'div[id*="list"]',
            'div[class*="list"]'
        ]
        
        print("\n=== LOOKING FOR DATA CONTAINERS ===")
        for selector in potential_data_containers:
            elements = soup.select(selector)
            if elements:
                print(f"Found {len(elements)} elements with selector: {selector}")
                for i, elem in enumerate(elements[:2]):
                    text = elem.get_text().strip()[:200]
                    print(f"  Element {i+1}: {text}...")
        
        # Check if there's a search functionality
        search_inputs = soup.find_all('input', {'type': 'search'}) + soup.find_all('input', {'name': re.compile(r'search|query', re.I)})
        if search_inputs:
            print(f"\nSearch inputs found: {len(search_inputs)}")
            for inp in search_inputs:
                print(f"  - {inp.get('name', 'unnamed')} ({inp.get('placeholder', 'no placeholder')})")
        
    except Exception as e:
        print(f"Error analyzing page: {e}")

if __name__ == "__main__":
    analyze_page_structure()
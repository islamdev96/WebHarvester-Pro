"""Quick scraper to extract data from a single page."""

import requests
from bs4 import BeautifulSoup
import json
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.utils.logger import Logger
from src.scraper.data_extractor import DataExtractor
from src.scraper.json_converter import JSONConverter

def quick_scrape():
    """Quickly scrape data from the first page."""
    url = "http://www.expoegypt.gov.eg/exporters"
    
    # Fetch the page
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        print("🚀 جاري استخراج البيانات من الصفحة الأولى...")
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        # Initialize components
        logger = Logger("QuickScraper", "logs/quick_scraper.log", "INFO")
        extractor = DataExtractor(logger)
        converter = JSONConverter(logger)
        
        # Extract companies
        companies = extractor.extract_companies_from_page(response.text, url)
        
        print(f"✅ تم استخراج {len(companies)} شركة من الصفحة الأولى")
        
        if companies:
            # Clean and process data
            cleaned_companies = extractor.normalize_and_clean_data(companies)
            unique_companies = converter.remove_duplicates(cleaned_companies)
            
            # Convert to JSON
            session_info = {
                'start_time': '2025-07-22T03:05:00',
                'end_time': '2025-07-22T03:05:30',
                'total_pages_scraped': 1,
                'total_companies_extracted': len(unique_companies),
                'errors_encountered': 0
            }
            
            json_data = converter.convert_to_json(unique_companies, session_info)
            
            # Save to file
            output_file = "output/sample_exporters_data.json"
            success = converter.save_json_file(json_data, output_file)
            
            if success:
                print(f"💾 تم حفظ البيانات في: {output_file}")
                
                # Show sample data
                print("\n📊 عينة من البيانات المستخرجة:")
                for i, company in enumerate(unique_companies[:3]):
                    name = company.get('company_name_arabic') or company.get('company_name', 'غير محدد')
                    phone = company.get('contact_info', {}).get('phone', 'غير متوفر')
                    email = company.get('contact_info', {}).get('email', 'غير متوفر')
                    sector = company.get('business_info', {}).get('categories', ['غير محدد'])
                    
                    print(f"\n{i+1}. {name}")
                    print(f"   📞 الهاتف: {phone}")
                    print(f"   📧 الإيميل: {email}")
                    print(f"   🏭 القطاع: {', '.join(sector[:2])}")
                
                # Create summary
                summary = converter.create_summary_report(json_data)
                print(f"\n📈 ملخص البيانات:")
                print(f"   إجمالي الشركات: {summary['total_companies']}")
                print(f"   شركات لها إيميل: {summary['companies_with_email']}")
                print(f"   شركات لها هاتف: {summary['companies_with_phone']}")
                print(f"   شركات لها موقع: {summary['companies_with_website']}")
                
                return True
            else:
                print("❌ فشل في حفظ البيانات")
                return False
        else:
            print("⚠️ لم يتم العثور على أي شركات")
            return False
            
    except Exception as e:
        print(f"❌ خطأ في استخراج البيانات: {e}")
        return False

if __name__ == "__main__":
    quick_scrape()
"""Simple extractor to show results quickly."""

import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime

def simple_extract():
    """Extract data simply without complex validation."""
    url = "http://www.expoegypt.gov.eg/exporters"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        print("🚀 جاري استخراج البيانات...")
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'lxml')
        
        # Find company containers
        co_nodes = soup.select('.co_node')
        print(f"✅ تم العثور على {len(co_nodes)} شركة")
        
        companies = []
        
        for i, node in enumerate(co_nodes):
            try:
                # Extract company name
                co_title = node.select_one('.co_title')
                company_name = co_title.get_text().strip() if co_title else f"شركة {i+1}"
                
                # Extract contact info
                contact_info = {}
                
                # Phone
                phone_elem = node.select_one('.co_phone')
                if phone_elem:
                    phone = phone_elem.get_text().strip()
                    if phone:
                        contact_info['phone'] = phone
                
                # Email and website
                co_net = node.select_one('.co_net')
                if co_net:
                    links = co_net.find_all('a')
                    for link in links:
                        href = link.get('href', '')
                        text = link.get_text().strip()
                        if 'mailto:' in href:
                            contact_info['email'] = href.replace('mailto:', '')
                        elif 'www.' in href or 'http' in href:
                            contact_info['website'] = href
                
                # Address
                co_address = node.select_one('.co_address')
                if co_address:
                    address = co_address.get_text().strip()
                    if address:
                        contact_info['address'] = address
                
                # Business sector
                business_info = {}
                ind_sector = node.select_one('.ind_sector')
                if ind_sector:
                    sector_text = ind_sector.get_text().strip()
                    if 'القطاع الصناعى:' in sector_text:
                        sector = sector_text.replace('القطاع الصناعى:', '').strip()
                        if sector:
                            business_info['sector'] = sector
                
                company_data = {
                    'id': f"company_{i+1}",
                    'company_name_arabic': company_name,
                    'contact_info': contact_info,
                    'business_info': business_info,
                    'extracted_at': datetime.now().isoformat()
                }
                
                companies.append(company_data)
                
            except Exception as e:
                print(f"⚠️ خطأ في استخراج الشركة {i+1}: {e}")
                continue
        
        # Create JSON output
        result = {
            'metadata': {
                'extraction_date': datetime.now().isoformat(),
                'source_url': url,
                'total_companies': len(companies)
            },
            'companies': companies
        }
        
        # Save to file
        output_file = "output/simple_results.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        print(f"💾 تم حفظ البيانات في: {output_file}")
        
        # Show sample results
        print(f"\n📊 تم استخراج {len(companies)} شركة بنجاح!")
        print("\n🏢 عينة من الشركات:")
        
        for i, company in enumerate(companies[:5]):
            name = company.get('company_name_arabic', 'غير محدد')
            phone = company.get('contact_info', {}).get('phone', 'غير متوفر')
            email = company.get('contact_info', {}).get('email', 'غير متوفر')
            sector = company.get('business_info', {}).get('sector', 'غير محدد')
            
            print(f"\n{i+1}. {name}")
            print(f"   📞 الهاتف: {phone}")
            print(f"   📧 الإيميل: {email}")
            print(f"   🏭 القطاع: {sector}")
        
        # Statistics
        companies_with_phone = sum(1 for c in companies if c.get('contact_info', {}).get('phone'))
        companies_with_email = sum(1 for c in companies if c.get('contact_info', {}).get('email'))
        companies_with_website = sum(1 for c in companies if c.get('contact_info', {}).get('website'))
        
        print(f"\n📈 إحصائيات:")
        print(f"   إجمالي الشركات: {len(companies)}")
        print(f"   شركات لها هاتف: {companies_with_phone}")
        print(f"   شركات لها إيميل: {companies_with_email}")
        print(f"   شركات لها موقع: {companies_with_website}")
        
        return True
        
    except Exception as e:
        print(f"❌ خطأ في الاستخراج: {e}")
        return False

if __name__ == "__main__":
    simple_extract()
"""Extract data from multiple pages and save results."""

import requests
from bs4 import BeautifulSoup
import json
import time
from datetime import datetime
import os

def extract_from_multiple_pages(max_pages=5):
    """Extract data from multiple pages."""
    
    base_url = "http://www.expoegypt.gov.eg/exporters"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    all_companies = []
    successful_pages = 0
    
    print(f"🚀 بدء استخراج البيانات من {max_pages} صفحات...")
    
    for page_num in range(1, max_pages + 1):
        try:
            # Build URL for current page
            if page_num == 1:
                url = base_url
            else:
                url = f"{base_url}?page={page_num}"
            
            print(f"\n📄 جاري استخراج الصفحة {page_num}...")
            print(f"🔗 الرابط: {url}")
            
            # Fetch page
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'lxml')
            co_nodes = soup.select('.co_node')
            
            print(f"✅ تم العثور على {len(co_nodes)} شركة في الصفحة {page_num}")
            
            # Extract companies from current page
            page_companies = []
            
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
                        'id': f"page_{page_num}_company_{i+1}",
                        'company_name_arabic': company_name,
                        'contact_info': contact_info,
                        'business_info': business_info,
                        'source_page': page_num,
                        'source_url': url,
                        'extracted_at': datetime.now().isoformat()
                    }
                    
                    page_companies.append(company_data)
                    
                except Exception as e:
                    print(f"⚠️ خطأ في استخراج الشركة {i+1} من الصفحة {page_num}: {e}")
                    continue
            
            all_companies.extend(page_companies)
            successful_pages += 1
            
            print(f"✅ تم استخراج {len(page_companies)} شركة من الصفحة {page_num}")
            
            # Wait between requests to be respectful
            if page_num < max_pages:
                print("⏳ انتظار 3 ثوان...")
                time.sleep(3)
                
        except Exception as e:
            print(f"❌ خطأ في استخراج الصفحة {page_num}: {e}")
            continue
    
    # Create results
    result = {
        'metadata': {
            'extraction_date': datetime.now().isoformat(),
            'total_pages_extracted': successful_pages,
            'total_companies': len(all_companies),
            'pages_requested': max_pages,
            'base_url': base_url
        },
        'companies': all_companies
    }
    
    # Save main results file
    output_file = "output/multiple_pages_results.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    # Create a summary file
    summary_file = "output/extraction_summary.txt"
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write("=== ملخص استخراج البيانات ===\n\n")
        f.write(f"تاريخ الاستخراج: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"عدد الصفحات المطلوبة: {max_pages}\n")
        f.write(f"عدد الصفحات المستخرجة بنجاح: {successful_pages}\n")
        f.write(f"إجمالي الشركات المستخرجة: {len(all_companies)}\n\n")
        
        # Statistics
        companies_with_phone = sum(1 for c in all_companies if c.get('contact_info', {}).get('phone'))
        companies_with_email = sum(1 for c in all_companies if c.get('contact_info', {}).get('email'))
        companies_with_website = sum(1 for c in all_companies if c.get('contact_info', {}).get('website'))
        
        f.write("=== الإحصائيات ===\n")
        f.write(f"شركات لها هاتف: {companies_with_phone}\n")
        f.write(f"شركات لها إيميل: {companies_with_email}\n")
        f.write(f"شركات لها موقع: {companies_with_website}\n\n")
        
        # Sample companies
        f.write("=== عينة من الشركات ===\n")
        for i, company in enumerate(all_companies[:10]):
            name = company.get('company_name_arabic', 'غير محدد')
            phone = company.get('contact_info', {}).get('phone', 'غير متوفر')
            email = company.get('contact_info', {}).get('email', 'غير متوفر')
            sector = company.get('business_info', {}).get('sector', 'غير محدد')
            page = company.get('source_page', 'غير محدد')
            
            f.write(f"\n{i+1}. {name} (صفحة {page})\n")
            f.write(f"   الهاتف: {phone}\n")
            f.write(f"   الإيميل: {email}\n")
            f.write(f"   القطاع: {sector}\n")
    
    # Create Excel-like CSV file
    csv_file = "output/companies_data.csv"
    with open(csv_file, 'w', encoding='utf-8-sig') as f:
        f.write("الرقم,اسم الشركة,الهاتف,الإيميل,الموقع,العنوان,القطاع,رقم الصفحة\n")
        
        for i, company in enumerate(all_companies):
            name = company.get('company_name_arabic', '').replace(',', '،')
            phone = company.get('contact_info', {}).get('phone', '')
            email = company.get('contact_info', {}).get('email', '')
            website = company.get('contact_info', {}).get('website', '')
            address = company.get('contact_info', {}).get('address', '').replace(',', '،').replace('\n', ' ')
            sector = company.get('business_info', {}).get('sector', '')
            page = company.get('source_page', '')
            
            f.write(f"{i+1},{name},{phone},{email},{website},{address},{sector},{page}\n")
    
    print(f"\n🎉 تم الانتهاء من الاستخراج!")
    print(f"📊 إجمالي الشركات: {len(all_companies)}")
    print(f"📄 الصفحات المستخرجة: {successful_pages} من {max_pages}")
    
    print(f"\n📁 الملفات المحفوظة:")
    print(f"   📋 البيانات الكاملة: {output_file}")
    print(f"   📝 الملخص: {summary_file}")
    print(f"   📊 ملف CSV: {csv_file}")
    
    # Show sample results
    print(f"\n🏢 عينة من الشركات المستخرجة:")
    for i, company in enumerate(all_companies[:5]):
        name = company.get('company_name_arabic', 'غير محدد')
        phone = company.get('contact_info', {}).get('phone', 'غير متوفر')
        email = company.get('contact_info', {}).get('email', 'غير متوفر')
        sector = company.get('business_info', {}).get('sector', 'غير محدد')
        page = company.get('source_page', 'غير محدد')
        
        print(f"\n{i+1}. {name} (صفحة {page})")
        print(f"   📞 الهاتف: {phone}")
        print(f"   📧 الإيميل: {email}")
        print(f"   🏭 القطاع: {sector}")
    
    return len(all_companies)

if __name__ == "__main__":
    # Extract from 10 pages (you can change this number)
    pages_to_extract = 10
    print(f"سيتم استخراج البيانات من {pages_to_extract} صفحات")
    print("يمكنك تغيير هذا الرقم في الكود إذا كنت تريد أكثر أو أقل")
    
    total_companies = extract_from_multiple_pages(pages_to_extract)
    
    print(f"\n✅ تم استخراج {total_companies} شركة بنجاح!")
    print("🔍 يمكنك الآن فتح الملفات في مجلد output لرؤية النتائج")
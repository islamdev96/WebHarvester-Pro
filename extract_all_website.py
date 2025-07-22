"""Extract ALL data from the entire website."""

import requests
from bs4 import BeautifulSoup
import json
import time
from datetime import datetime
import os

def extract_all_website_data():
    """Extract data from ALL pages in the website."""
    
    base_url = "http://www.expoegypt.gov.eg/exporters"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    all_companies = []
    successful_pages = 0
    failed_pages = 0
    current_page = 1
    max_consecutive_failures = 5
    consecutive_failures = 0
    
    print("🚀 بدء استخراج كل البيانات من الموقع بالكامل...")
    print("⚠️  هذا قد يستغرق وقتاً طويلاً (30-60 دقيقة)")
    print("💡 يمكنك إيقاف البرنامج بـ Ctrl+C في أي وقت وستحتفظ بالبيانات المستخرجة")
    
    start_time = datetime.now()
    
    while consecutive_failures < max_consecutive_failures:
        try:
            # Build URL for current page
            if current_page == 1:
                url = base_url
            else:
                url = f"{base_url}?page={current_page}"
            
            print(f"\n📄 جاري استخراج الصفحة {current_page}...")
            
            # Fetch page
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'lxml')
            co_nodes = soup.select('.co_node')
            
            # If no companies found, might be end of pages
            if len(co_nodes) == 0:
                print(f"⚠️ لم يتم العثور على شركات في الصفحة {current_page}")
                consecutive_failures += 1
                failed_pages += 1
                
                if consecutive_failures >= max_consecutive_failures:
                    print(f"🛑 تم الوصول لنهاية الصفحات المتاحة")
                    break
                    
                current_page += 1
                continue
            
            print(f"✅ تم العثور على {len(co_nodes)} شركة في الصفحة {current_page}")
            
            # Reset consecutive failures counter
            consecutive_failures = 0
            
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
                        'id': f"page_{current_page}_company_{i+1}",
                        'company_name_arabic': company_name,
                        'contact_info': contact_info,
                        'business_info': business_info,
                        'source_page': current_page,
                        'source_url': url,
                        'extracted_at': datetime.now().isoformat()
                    }
                    
                    page_companies.append(company_data)
                    
                except Exception as e:
                    print(f"⚠️ خطأ في استخراج الشركة {i+1} من الصفحة {current_page}: {e}")
                    continue
            
            all_companies.extend(page_companies)
            successful_pages += 1
            
            print(f"✅ تم استخراج {len(page_companies)} شركة من الصفحة {current_page}")
            print(f"📊 إجمالي الشركات حتى الآن: {len(all_companies)}")
            
            # Save progress every 10 pages
            if current_page % 10 == 0:
                save_progress(all_companies, current_page, successful_pages, start_time)
            
            # Wait between requests to be respectful
            time.sleep(2)  # 2 seconds delay
            current_page += 1
                
        except KeyboardInterrupt:
            print(f"\n⚠️ تم إيقاف البرنامج بواسطة المستخدم")
            print(f"📊 تم استخراج {len(all_companies)} شركة من {successful_pages} صفحة")
            break
            
        except Exception as e:
            print(f"❌ خطأ في استخراج الصفحة {current_page}: {e}")
            consecutive_failures += 1
            failed_pages += 1
            
            if consecutive_failures >= max_consecutive_failures:
                print(f"🛑 تم تجاوز الحد الأقصى للأخطاء المتتالية")
                break
                
            current_page += 1
            time.sleep(5)  # Wait longer after error
            continue
    
    # Final save
    end_time = datetime.now()
    duration = end_time - start_time
    
    print(f"\n🎉 تم الانتهاء من الاستخراج!")
    print(f"⏱️ الوقت المستغرق: {duration}")
    print(f"📊 إجمالي الشركات: {len(all_companies)}")
    print(f"📄 الصفحات المستخرجة بنجاح: {successful_pages}")
    print(f"❌ الصفحات الفاشلة: {failed_pages}")
    
    # Save final results
    save_final_results(all_companies, successful_pages, failed_pages, start_time, end_time)
    
    return len(all_companies)

def save_progress(companies, current_page, successful_pages, start_time):
    """Save progress periodically."""
    print(f"💾 حفظ التقدم... (الصفحة {current_page})")
    
    progress_file = f"output/progress_page_{current_page}.json"
    progress_data = {
        'progress_info': {
            'current_page': current_page,
            'successful_pages': successful_pages,
            'total_companies': len(companies),
            'start_time': start_time.isoformat(),
            'last_update': datetime.now().isoformat()
        },
        'companies': companies
    }
    
    with open(progress_file, 'w', encoding='utf-8') as f:
        json.dump(progress_data, f, ensure_ascii=False, indent=2)

def save_final_results(companies, successful_pages, failed_pages, start_time, end_time):
    """Save final comprehensive results."""
    
    # Create results
    result = {
        'metadata': {
            'extraction_date': end_time.isoformat(),
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat(),
            'duration_seconds': (end_time - start_time).total_seconds(),
            'total_pages_extracted': successful_pages,
            'failed_pages': failed_pages,
            'total_companies': len(companies),
            'base_url': "http://www.expoegypt.gov.eg/exporters",
            'extraction_type': 'FULL_WEBSITE'
        },
        'companies': companies
    }
    
    # Save main results file
    output_file = "output/FULL_WEBSITE_DATA.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    # Create comprehensive summary
    summary_file = "output/FULL_EXTRACTION_SUMMARY.txt"
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write("=== استخراج كامل لبيانات الموقع ===\n\n")
        f.write(f"تاريخ البدء: {start_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"تاريخ الانتهاء: {end_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"الوقت المستغرق: {end_time - start_time}\n")
        f.write(f"عدد الصفحات المستخرجة بنجاح: {successful_pages}\n")
        f.write(f"عدد الصفحات الفاشلة: {failed_pages}\n")
        f.write(f"إجمالي الشركات المستخرجة: {len(companies)}\n\n")
        
        # Statistics
        companies_with_phone = sum(1 for c in companies if c.get('contact_info', {}).get('phone'))
        companies_with_email = sum(1 for c in companies if c.get('contact_info', {}).get('email'))
        companies_with_website = sum(1 for c in companies if c.get('contact_info', {}).get('website'))
        
        f.write("=== الإحصائيات التفصيلية ===\n")
        f.write(f"شركات لها هاتف: {companies_with_phone} ({companies_with_phone/len(companies)*100:.1f}%)\n")
        f.write(f"شركات لها إيميل: {companies_with_email} ({companies_with_email/len(companies)*100:.1f}%)\n")
        f.write(f"شركات لها موقع: {companies_with_website} ({companies_with_website/len(companies)*100:.1f}%)\n\n")
        
        # Sector analysis
        sectors = {}
        for company in companies:
            sector = company.get('business_info', {}).get('sector', 'غير محدد')
            sectors[sector] = sectors.get(sector, 0) + 1
        
        f.write("=== توزيع القطاعات ===\n")
        for sector, count in sorted(sectors.items(), key=lambda x: x[1], reverse=True):
            f.write(f"{sector}: {count} شركة\n")
        
        f.write(f"\n=== عينة من الشركات (أول 20) ===\n")
        for i, company in enumerate(companies[:20]):
            name = company.get('company_name_arabic', 'غير محدد')
            phone = company.get('contact_info', {}).get('phone', 'غير متوفر')
            email = company.get('contact_info', {}).get('email', 'غير متوفر')
            sector = company.get('business_info', {}).get('sector', 'غير محدد')
            page = company.get('source_page', 'غير محدد')
            
            f.write(f"\n{i+1}. {name} (صفحة {page})\n")
            f.write(f"   الهاتف: {phone}\n")
            f.write(f"   الإيميل: {email}\n")
            f.write(f"   القطاع: {sector}\n")
    
    # Create comprehensive CSV file
    csv_file = "output/FULL_COMPANIES_DATABASE.csv"
    with open(csv_file, 'w', encoding='utf-8-sig') as f:
        f.write("الرقم,اسم الشركة,الهاتف,الإيميل,الموقع,العنوان,القطاع,رقم الصفحة,تاريخ الاستخراج\n")
        
        for i, company in enumerate(companies):
            name = company.get('company_name_arabic', '').replace(',', '،')
            phone = company.get('contact_info', {}).get('phone', '')
            email = company.get('contact_info', {}).get('email', '')
            website = company.get('contact_info', {}).get('website', '')
            address = company.get('contact_info', {}).get('address', '').replace(',', '،').replace('\n', ' ')
            sector = company.get('business_info', {}).get('sector', '')
            page = company.get('source_page', '')
            extracted_at = company.get('extracted_at', '')
            
            f.write(f"{i+1},{name},{phone},{email},{website},{address},{sector},{page},{extracted_at}\n")
    
    print(f"\n📁 الملفات النهائية:")
    print(f"   📋 البيانات الكاملة: {output_file}")
    print(f"   📝 الملخص الشامل: {summary_file}")
    print(f"   📊 قاعدة البيانات CSV: {csv_file}")

if __name__ == "__main__":
    print("🌐 استخراج كامل لبيانات موقع المصدرين المصريين")
    print("=" * 50)
    
    try:
        total_companies = extract_all_website_data()
        print(f"\n✅ تم استخراج {total_companies} شركة بنجاح من الموقع بالكامل!")
        print("🔍 تحقق من مجلد output للحصول على جميع الملفات")
        
    except KeyboardInterrupt:
        print(f"\n⚠️ تم إيقاف البرنامج بواسطة المستخدم")
        print("💾 البيانات المستخرجة حتى الآن محفوظة في مجلد output")
        
    except Exception as e:
        print(f"\n❌ خطأ عام في البرنامج: {e}")
        print("💾 تحقق من مجلد output للبيانات المحفوظة")
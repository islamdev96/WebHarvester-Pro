"""Universal Web Scraper - يعمل مع أي موقع"""

import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime

class UniversalScraper:
    """مستخرج بيانات عام يعمل مع أي موقع"""
    
    def __init__(self, config):
        """
        config = {
            'base_url': 'https://example.com',
            'selectors': {
                'container': '.item',           # حاوي كل عنصر
                'title': '.title',             # العنوان
                'description': '.description', # الوصف
                'link': 'a',                   # الرابط
                'image': 'img',                # الصورة
                'price': '.price',             # السعر (اختياري)
                'date': '.date'                # التاريخ (اختياري)
            },
            'pagination': {
                'type': 'page_number',         # أو 'next_button'
                'pattern': '?page={}'          # أو selector للزر التالي
            }
        }
        """
        self.config = config
        self.base_url = config['base_url']
        self.selectors = config['selectors']
        self.pagination = config.get('pagination', {})
        
    def scrape_page(self, url):
        """استخراج البيانات من صفحة واحدة"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'lxml')
            
            # العثور على حاويات العناصر
            containers = soup.select(self.selectors['container'])
            
            items = []
            for i, container in enumerate(containers):
                item = self.extract_item_data(container, i+1)
                if item:
                    items.append(item)
            
            return items
            
        except Exception as e:
            print(f"خطأ في استخراج الصفحة {url}: {e}")
            return []
    
    def extract_item_data(self, container, index):
        """استخراج بيانات عنصر واحد"""
        item = {
            'id': f"item_{index}",
            'extracted_at': datetime.now().isoformat()
        }
        
        # استخراج كل حقل حسب المحددات
        for field_name, selector in self.selectors.items():
            if field_name == 'container':
                continue
                
            try:
                element = container.select_one(selector)
                if element:
                    if field_name == 'link':
                        item[field_name] = element.get('href', '')
                    elif field_name == 'image':
                        item[field_name] = element.get('src', '')
                    else:
                        item[field_name] = element.get_text().strip()
            except Exception as e:
                print(f"خطأ في استخراج {field_name}: {e}")
                item[field_name] = ""
        
        return item
    
    def scrape_all_pages(self, max_pages=None):
        """استخراج كل الصفحات"""
        all_items = []
        page_num = 1
        
        while True:
            if max_pages and page_num > max_pages:
                break
                
            # بناء رابط الصفحة
            if page_num == 1:
                url = self.base_url
            else:
                if self.pagination.get('type') == 'page_number':
                    pattern = self.pagination.get('pattern', '?page={}')
                    url = self.base_url + pattern.format(page_num)
                else:
                    break  # لا يدعم أنواع أخرى من التصفح حالياً
            
            print(f"📄 استخراج الصفحة {page_num}: {url}")
            
            items = self.scrape_page(url)
            
            if not items:
                print(f"⚠️ لا توجد عناصر في الصفحة {page_num}")
                break
            
            all_items.extend(items)
            print(f"✅ تم استخراج {len(items)} عنصر من الصفحة {page_num}")
            
            page_num += 1
            
            # تأخير بين الطلبات
            import time
            time.sleep(2)
        
        return all_items

# مثال للاستخدام مع مواقع مختلفة:

# 1. موقع أخبار
news_config = {
    'base_url': 'https://example-news.com',
    'selectors': {
        'container': '.article',
        'title': '.article-title',
        'description': '.article-summary',
        'link': 'a',
        'date': '.publish-date'
    },
    'pagination': {
        'type': 'page_number',
        'pattern': '/page/{}'
    }
}

# 2. موقع تجارة إلكترونية
ecommerce_config = {
    'base_url': 'https://example-shop.com/products',
    'selectors': {
        'container': '.product',
        'title': '.product-name',
        'description': '.product-description',
        'price': '.price',
        'image': '.product-image img',
        'link': 'a'
    },
    'pagination': {
        'type': 'page_number',
        'pattern': '?page={}'
    }
}

# 3. موقع وظائف
jobs_config = {
    'base_url': 'https://example-jobs.com',
    'selectors': {
        'container': '.job-listing',
        'title': '.job-title',
        'description': '.job-description',
        'company': '.company-name',
        'location': '.job-location',
        'date': '.posted-date'
    },
    'pagination': {
        'type': 'page_number',
        'pattern': '?page={}'
    }
}

def demo_usage():
    """مثال على الاستخدام"""
    
    # اختر الإعدادات حسب نوع الموقع
    config = news_config  # أو ecommerce_config أو jobs_config
    
    # إنشاء المستخرج
    scraper = UniversalScraper(config)
    
    # استخراج البيانات
    items = scraper.scrape_all_pages(max_pages=5)
    
    # حفظ النتائج
    result = {
        'metadata': {
            'extraction_date': datetime.now().isoformat(),
            'total_items': len(items),
            'source_url': config['base_url']
        },
        'items': items
    }
    
    with open('universal_results.json', 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"✅ تم استخراج {len(items)} عنصر وحفظها في universal_results.json")

if __name__ == "__main__":
    print("🌐 المستخرج العام - يعمل مع أي موقع")
    print("💡 عدل الإعدادات في الكود ليناسب موقعك")
    # demo_usage()  # ألغ التعليق لتشغيل المثال
"""
إطار عمل مختلط - الأفضل من العالمين
Framework مشترك + تخصيص لكل موقع
"""

from abc import ABC, abstractmethod
import requests
from bs4 import BeautifulSoup
import json
import time
from datetime import datetime
from typing import Dict, List, Any, Optional

class BaseScraper(ABC):
    """الفئة الأساسية المشتركة لكل المواقع"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.base_url = config['base_url']
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        self.delay = config.get('delay', 2)
        self.timeout = config.get('timeout', 30)
        self.max_retries = config.get('max_retries', 3)
    
    def fetch_page(self, url: str) -> Optional[str]:
        """جلب صفحة مع إعادة المحاولة - مشترك لكل المواقع"""
        for attempt in range(self.max_retries):
            try:
                response = requests.get(url, headers=self.headers, timeout=self.timeout)
                response.raise_for_status()
                return response.text
            except Exception as e:
                print(f"محاولة {attempt + 1} فشلت: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)  # تأخير متزايد
        return None
    
    def save_results(self, data: List[Dict], filename: str):
        """حفظ النتائج - مشترك لكل المواقع"""
        result = {
            'metadata': {
                'extraction_date': datetime.now().isoformat(),
                'total_items': len(data),
                'source': self.base_url,
                'scraper_type': self.__class__.__name__
            },
            'data': data
        }
        
        with open(f"output/{filename}.json", 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        print(f"✅ تم حفظ {len(data)} عنصر في {filename}.json")
    
    def respect_rate_limits(self):
        """احترام حدود المعدل - مشترك"""
        time.sleep(self.delay)
    
    # الوظائف المجردة - يجب تنفيذها في كل موقع
    @abstractmethod
    def extract_items_from_page(self, html: str, page_url: str) -> List[Dict[str, Any]]:
        """استخراج العناصر من صفحة - مخصص لكل موقع"""
        pass
    
    @abstractmethod
    def get_next_page_url(self, current_url: str, page_num: int) -> Optional[str]:
        """الحصول على رابط الصفحة التالية - مخصص لكل موقع"""
        pass
    
    @abstractmethod
    def is_valid_item(self, item: Dict[str, Any]) -> bool:
        """التحقق من صحة العنصر - مخصص لكل موقع"""
        pass
    
    def scrape_all_pages(self, max_pages: Optional[int] = None) -> List[Dict[str, Any]]:
        """استخراج كل الصفحات - مشترك مع تخصيص"""
        all_items = []
        page_num = 1
        current_url = self.base_url
        
        while True:
            if max_pages and page_num > max_pages:
                break
            
            print(f"📄 استخراج الصفحة {page_num}: {current_url}")
            
            html = self.fetch_page(current_url)
            if not html:
                print(f"❌ فشل في جلب الصفحة {page_num}")
                break
            
            # استخراج مخصص لكل موقع
            items = self.extract_items_from_page(html, current_url)
            
            if not items:
                print(f"⚠️ لا توجد عناصر في الصفحة {page_num}")
                break
            
            # تصفية العناصر الصحيحة
            valid_items = [item for item in items if self.is_valid_item(item)]
            all_items.extend(valid_items)
            
            print(f"✅ تم استخراج {len(valid_items)} عنصر صحيح من الصفحة {page_num}")
            
            # الحصول على الصفحة التالية
            next_url = self.get_next_page_url(current_url, page_num + 1)
            if not next_url:
                break
            
            current_url = next_url
            page_num += 1
            self.respect_rate_limits()
        
        return all_items

# تطبيق مخصص لموقع المصدرين المصريين
class EgyptExportersScraper(BaseScraper):
    """مستخرج مخصص لموقع المصدرين المصريين"""
    
    def extract_items_from_page(self, html: str, page_url: str) -> List[Dict[str, Any]]:
        """استخراج الشركات من الصفحة"""
        soup = BeautifulSoup(html, 'lxml')
        companies = []
        
        co_nodes = soup.select('.co_node')
        
        for i, node in enumerate(co_nodes):
            try:
                # اسم الشركة
                co_title = node.select_one('.co_title')
                company_name = co_title.get_text().strip() if co_title else ""
                
                # معلومات الاتصال
                contact_info = {}
                
                # الهاتف
                phone_elem = node.select_one('.co_phone')
                if phone_elem:
                    phone = phone_elem.get_text().strip()
                    if phone:
                        contact_info['phone'] = phone
                
                # الإيميل والموقع
                co_net = node.select_one('.co_net')
                if co_net:
                    links = co_net.find_all('a')
                    for link in links:
                        href = link.get('href', '')
                        if 'mailto:' in href:
                            contact_info['email'] = href.replace('mailto:', '')
                        elif 'www.' in href or 'http' in href:
                            contact_info['website'] = href
                
                # العنوان
                co_address = node.select_one('.co_address')
                if co_address:
                    contact_info['address'] = co_address.get_text().strip()
                
                # القطاع
                sector = ""
                ind_sector = node.select_one('.ind_sector')
                if ind_sector:
                    sector_text = ind_sector.get_text().strip()
                    if 'القطاع الصناعى:' in sector_text:
                        sector = sector_text.replace('القطاع الصناعى:', '').strip()
                
                company = {
                    'id': f"company_{i+1}",
                    'name': company_name,
                    'contact_info': contact_info,
                    'sector': sector,
                    'source_page': page_url,
                    'extracted_at': datetime.now().isoformat()
                }
                
                companies.append(company)
                
            except Exception as e:
                print(f"خطأ في استخراج الشركة {i+1}: {e}")
                continue
        
        return companies
    
    def get_next_page_url(self, current_url: str, page_num: int) -> Optional[str]:
        """الحصول على رابط الصفحة التالية"""
        if page_num == 1:
            return self.base_url
        else:
            return f"{self.base_url}?page={page_num}"
    
    def is_valid_item(self, item: Dict[str, Any]) -> bool:
        """التحقق من صحة الشركة"""
        return bool(item.get('name') and item['name'].strip())

# تطبيق مخصص لموقع أخبار
class NewsScraper(BaseScraper):
    """مستخرج مخصص لمواقع الأخبار"""
    
    def extract_items_from_page(self, html: str, page_url: str) -> List[Dict[str, Any]]:
        """استخراج الأخبار من الصفحة"""
        soup = BeautifulSoup(html, 'lxml')
        articles = []
        
        # محددات مرنة للأخبار
        selectors = self.config.get('selectors', {
            'container': '.article, .news-item, .post',
            'title': 'h1, h2, h3, .title, .headline',
            'summary': '.summary, .excerpt, .description',
            'date': '.date, .published, .timestamp',
            'link': 'a'
        })
        
        containers = soup.select(selectors['container'])
        
        for i, container in enumerate(containers):
            try:
                title_elem = container.select_one(selectors['title'])
                title = title_elem.get_text().strip() if title_elem else ""
                
                summary_elem = container.select_one(selectors['summary'])
                summary = summary_elem.get_text().strip() if summary_elem else ""
                
                date_elem = container.select_one(selectors['date'])
                date = date_elem.get_text().strip() if date_elem else ""
                
                link_elem = container.select_one(selectors['link'])
                link = link_elem.get('href', '') if link_elem else ""
                
                article = {
                    'id': f"article_{i+1}",
                    'title': title,
                    'summary': summary,
                    'date': date,
                    'link': link,
                    'source_page': page_url,
                    'extracted_at': datetime.now().isoformat()
                }
                
                articles.append(article)
                
            except Exception as e:
                print(f"خطأ في استخراج المقال {i+1}: {e}")
                continue
        
        return articles
    
    def get_next_page_url(self, current_url: str, page_num: int) -> Optional[str]:
        """الحصول على رابط الصفحة التالية"""
        pattern = self.config.get('pagination_pattern', '/page/{}')
        return self.base_url + pattern.format(page_num)
    
    def is_valid_item(self, item: Dict[str, Any]) -> bool:
        """التحقق من صحة المقال"""
        return bool(item.get('title') and len(item['title']) > 10)

# تطبيق مخصص للمتاجر الإلكترونية
class EcommerceScraper(BaseScraper):
    """مستخرج مخصص للمتاجر الإلكترونية"""
    
    def extract_items_from_page(self, html: str, page_url: str) -> List[Dict[str, Any]]:
        """استخراج المنتجات من الصفحة"""
        soup = BeautifulSoup(html, 'lxml')
        products = []
        
        selectors = self.config.get('selectors', {
            'container': '.product, .item, .product-card',
            'title': '.product-name, .title, h3',
            'price': '.price, .cost, .amount',
            'image': 'img',
            'rating': '.rating, .stars',
            'link': 'a'
        })
        
        containers = soup.select(selectors['container'])
        
        for i, container in enumerate(containers):
            try:
                title_elem = container.select_one(selectors['title'])
                title = title_elem.get_text().strip() if title_elem else ""
                
                price_elem = container.select_one(selectors['price'])
                price = price_elem.get_text().strip() if price_elem else ""
                
                image_elem = container.select_one(selectors['image'])
                image = image_elem.get('src', '') if image_elem else ""
                
                rating_elem = container.select_one(selectors['rating'])
                rating = rating_elem.get_text().strip() if rating_elem else ""
                
                link_elem = container.select_one(selectors['link'])
                link = link_elem.get('href', '') if link_elem else ""
                
                product = {
                    'id': f"product_{i+1}",
                    'title': title,
                    'price': price,
                    'image': image,
                    'rating': rating,
                    'link': link,
                    'source_page': page_url,
                    'extracted_at': datetime.now().isoformat()
                }
                
                products.append(product)
                
            except Exception as e:
                print(f"خطأ في استخراج المنتج {i+1}: {e}")
                continue
        
        return products
    
    def get_next_page_url(self, current_url: str, page_num: int) -> Optional[str]:
        """الحصول على رابط الصفحة التالية"""
        pattern = self.config.get('pagination_pattern', '?page={}')
        return self.base_url + pattern.format(page_num)
    
    def is_valid_item(self, item: Dict[str, Any]) -> bool:
        """التحقق من صحة المنتج"""
        return bool(item.get('title') and item.get('price'))

# مصنع لإنشاء المستخرجات
class ScraperFactory:
    """مصنع لإنشاء المستخرج المناسب لكل موقع"""
    
    @staticmethod
    def create_scraper(website_type: str, config: Dict[str, Any]) -> BaseScraper:
        """إنشاء المستخرج المناسب"""
        scrapers = {
            'egypt_exporters': EgyptExportersScraper,
            'news': NewsScraper,
            'ecommerce': EcommerceScraper
        }
        
        scraper_class = scrapers.get(website_type)
        if not scraper_class:
            raise ValueError(f"نوع الموقع غير مدعوم: {website_type}")
        
        return scraper_class(config)

# أمثلة للاستخدام
def example_usage():
    """أمثلة على الاستخدام"""
    
    # 1. موقع المصدرين المصريين
    egypt_config = {
        'base_url': 'http://www.expoegypt.gov.eg/exporters',
        'delay': 2,
        'timeout': 30
    }
    
    egypt_scraper = ScraperFactory.create_scraper('egypt_exporters', egypt_config)
    companies = egypt_scraper.scrape_all_pages(max_pages=5)
    egypt_scraper.save_results(companies, 'egypt_companies')
    
    # 2. موقع أخبار
    news_config = {
        'base_url': 'https://example-news.com',
        'pagination_pattern': '/page/{}',
        'selectors': {
            'container': '.article',
            'title': '.article-title',
            'summary': '.article-summary',
            'date': '.publish-date'
        }
    }
    
    news_scraper = ScraperFactory.create_scraper('news', news_config)
    articles = news_scraper.scrape_all_pages(max_pages=3)
    news_scraper.save_results(articles, 'news_articles')
    
    # 3. متجر إلكتروني
    shop_config = {
        'base_url': 'https://example-shop.com/products',
        'pagination_pattern': '?page={}',
        'selectors': {
            'container': '.product',
            'title': '.product-name',
            'price': '.price',
            'image': '.product-image img'
        }
    }
    
    shop_scraper = ScraperFactory.create_scraper('ecommerce', shop_config)
    products = shop_scraper.scrape_all_pages(max_pages=2)
    shop_scraper.save_results(products, 'shop_products')

if __name__ == "__main__":
    print("🏗️ إطار العمل المختلط - الأفضل من العالمين")
    print("=" * 50)
    # example_usage()  # ألغ التعليق للتشغيل
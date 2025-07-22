"""مثال عملي لاستخراج البيانات من أي موقع"""

from universal_scraper import UniversalScraper
import json

def scrape_quotes_website():
    """مثال: استخراج الاقتباسات من موقع quotes.toscrape.com"""
    
    config = {
        'base_url': 'http://quotes.toscrape.com',
        'selectors': {
            'container': '.quote',           # كل اقتباس
            'text': '.text',                 # نص الاقتباس
            'author': '.author',             # المؤلف
            'tags': '.tags .tag'             # العلامات
        },
        'pagination': {
            'type': 'page_number',
            'pattern': '/page/{}'
        }
    }
    
    scraper = UniversalScraper(config)
    quotes = scraper.scrape_all_pages(max_pages=3)
    
    # حفظ النتائج
    with open('output/quotes_data.json', 'w', encoding='utf-8') as f:
        json.dump({
            'total_quotes': len(quotes),
            'quotes': quotes
        }, f, ensure_ascii=False, indent=2)
    
    print(f"✅ تم استخراج {len(quotes)} اقتباس")
    return quotes

def scrape_news_website():
    """مثال: استخراج الأخبار (تحتاج تعديل الرابط والمحددات)"""
    
    config = {
        'base_url': 'https://example-news.com',
        'selectors': {
            'container': '.news-item',
            'title': 'h2',
            'summary': '.summary',
            'date': '.date',
            'link': 'a'
        },
        'pagination': {
            'type': 'page_number',
            'pattern': '?page={}'
        }
    }
    
    scraper = UniversalScraper(config)
    news = scraper.scrape_all_pages(max_pages=2)
    
    print(f"✅ تم استخراج {len(news)} خبر")
    return news

def scrape_products_website():
    """مثال: استخراج المنتجات من موقع تجاري"""
    
    config = {
        'base_url': 'https://example-shop.com/products',
        'selectors': {
            'container': '.product-card',
            'title': '.product-name',
            'price': '.price',
            'image': 'img',
            'rating': '.rating',
            'link': 'a'
        },
        'pagination': {
            'type': 'page_number',
            'pattern': '?page={}'
        }
    }
    
    scraper = UniversalScraper(config)
    products = scraper.scrape_all_pages(max_pages=5)
    
    print(f"✅ تم استخراج {len(products)} منتج")
    return products

if __name__ == "__main__":
    print("🌐 أمثلة لاستخراج البيانات من مواقع مختلفة")
    print("=" * 50)
    
    # جرب استخراج الاقتباسات (موقع حقيقي للتجربة)
    try:
        quotes = scrape_quotes_website()
        print("✅ نجح استخراج الاقتباسات")
    except Exception as e:
        print(f"❌ فشل استخراج الاقتباسات: {e}")
    
    print("\n💡 لاستخراج من مواقع أخرى:")
    print("1. غير base_url للموقع المطلوب")
    print("2. افحص HTML الموقع واستخرج المحددات الصحيحة")
    print("3. عدل selectors في الإعدادات")
    print("4. شغل البرنامج!")
"""Main application for the Egypt Exporters Scraper."""

import argparse
import signal
import sys
from datetime import datetime
from typing import List, Dict, Any

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scraper.config import Configuration
from scraper.web_scraper import WebScraper
from scraper.data_extractor import DataExtractor
from scraper.json_converter import JSONConverter
from utils.logger import Logger


class EgyptExportersScraper:
    """Main scraper application orchestrator."""
    
    def __init__(self, config_path: str = "config/scraper_config.json"):
        """Initialize the scraper application."""
        self.config = Configuration(config_path)
        self.logger = Logger("EgyptExportersScraper", 
                           self.config.get('logging', 'file_path'),
                           self.config.get('logging', 'level'))
        
        self.web_scraper = None
        self.data_extractor = DataExtractor(self.logger)
        self.json_converter = JSONConverter(self.logger)
        
        self.session_info = {
            'start_time': datetime.now().isoformat(),
            'end_time': None,
            'total_pages_scraped': 0,
            'total_companies_extracted': 0,
            'errors_encountered': 0
        }
        
        self.interrupted = False
        self._setup_signal_handlers()
    
    def _setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown."""
        def signal_handler(signum, frame):
            self.logger.info("Received interrupt signal. Shutting down gracefully...")
            self.interrupted = True
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    def run(self, resume: bool = False) -> bool:
        """Run the complete scraping workflow with comprehensive error handling."""
        try:
            self.logger.info("Starting Egypt Exporters Scraper")
            self.logger.info(f"Target website: {self.config.get('scraping', 'base_url')}")
            
            # Validate configuration
            if not self._validate_configuration():
                return False
            
            # Initialize web scraper with error handling
            try:
                scraping_config = self.config.get_scraping_config()
                self.web_scraper = WebScraper(scraping_config, self.logger)
            except Exception as e:
                self.logger.error(f"Failed to initialize web scraper: {e}")
                return False
            
            # Discover all pages to scrape
            base_url = scraping_config['base_url']
            all_urls = self._discover_pages(base_url)
            
            if not all_urls:
                self.logger.error("No pages discovered. This could indicate:")
                self.logger.error("1. Website is down or inaccessible")
                self.logger.error("2. Website structure has changed")
                self.logger.error("3. Network connectivity issues")
                return False
            
            # Scrape all discovered pages
            all_companies = self._scrape_all_pages(all_urls)
            
            if not all_companies:
                self.logger.warning("No companies extracted from any pages. This could indicate:")
                self.logger.warning("1. Website structure has changed")
                self.logger.warning("2. No company data is available")
                self.logger.warning("3. Extraction patterns need updating")
                
                # Save empty result with session info for debugging
                self._save_empty_result()
                return False
            
            # Process and save data
            success = self._process_and_save_data(all_companies)
            
            # Update session info
            self.session_info['end_time'] = datetime.now().isoformat()
            self.session_info['total_companies_extracted'] = len(all_companies)
            
            self.logger.info(f"Scraping completed. Extracted {len(all_companies)} companies from {self.session_info['total_pages_scraped']} pages")
            
            return success
            
        except KeyboardInterrupt:
            self.logger.info("Scraping interrupted by user")
            self.session_info['errors_encountered'] += 1
            self._save_partial_results()
            return False
        except MemoryError:
            self.logger.error("Out of memory error. Try reducing batch size or available system memory.")
            self.session_info['errors_encountered'] += 1
            return False
        except Exception as e:
            self.logger.error(f"Fatal error in scraper: {e}")
            self.logger.error(f"Error type: {type(e).__name__}")
            import traceback
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            self.session_info['errors_encountered'] += 1
            return False
        finally:
            self._cleanup_resources()
    
    def _validate_configuration(self) -> bool:
        """Validate configuration before starting scraping."""
        try:
            # Check required configuration sections
            required_sections = ['scraping', 'output', 'logging']
            for section in required_sections:
                if not self.config.get(section):
                    self.logger.error(f"Missing configuration section: {section}")
                    return False
            
            # Validate scraping configuration
            scraping_config = self.config.get('scraping')
            if not scraping_config.get('base_url'):
                self.logger.error("Missing base_url in scraping configuration")
                return False
            
            # Validate output configuration
            output_config = self.config.get('output')
            if not output_config.get('file_path'):
                self.logger.error("Missing file_path in output configuration")
                return False
            
            # Test write permissions for output directory
            import os
            output_dir = os.path.dirname(output_config['file_path'])
            if output_dir and not os.access(output_dir, os.W_OK):
                self.logger.error(f"No write permission for output directory: {output_dir}")
                return False
            
            self.logger.info("Configuration validation passed")
            return True
            
        except Exception as e:
            self.logger.error(f"Configuration validation error: {e}")
            return False
    
    def _save_empty_result(self):
        """Save empty result with session info for debugging."""
        try:
            empty_data = self.json_converter.convert_to_json([], self.session_info)
            output_config = self.config.get_output_config()
            output_file = output_config['file_path'].replace('.json', '_empty.json')
            self.json_converter.save_json_file(empty_data, output_file)
            self.logger.info(f"Empty result saved to: {output_file}")
        except Exception as e:
            self.logger.error(f"Failed to save empty result: {e}")
    
    def _save_partial_results(self):
        """Save partial results when scraping is interrupted."""
        try:
            # This would be implemented if we were tracking partial results
            self.logger.info("Partial results saving not implemented yet")
        except Exception as e:
            self.logger.error(f"Failed to save partial results: {e}")
    
    def _cleanup_resources(self):
        """Clean up resources and close connections."""
        try:
            if self.web_scraper:
                self.web_scraper.close_session()
            self.logger.info("Resources cleaned up successfully")
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
    
    def _discover_pages(self, base_url: str) -> List[str]:
        """Discover all pages to scrape."""
        self.logger.info("Discovering pages to scrape...")
        
        try:
            all_urls = self.web_scraper.discover_all_pages(base_url)
            self.logger.info(f"Discovered {len(all_urls)} pages to scrape")
            return all_urls
        except Exception as e:
            self.logger.error(f"Error discovering pages: {e}")
            self.session_info['errors_encountered'] += 1
            # Fallback to just the base URL
            return [base_url]
    
    def _scrape_all_pages(self, urls: List[str]) -> List[Dict[str, Any]]:
        """Scrape all discovered pages."""
        all_companies = []
        
        for i, url in enumerate(urls):
            if self.interrupted:
                self.logger.info("Scraping interrupted by user")
                break
            
            self.logger.info(f"Scraping page {i+1}/{len(urls)}: {url}")
            
            try:
                # Fetch page content
                html_content = self.web_scraper.fetch_page(url)
                if not html_content:
                    self.logger.warning(f"Failed to fetch content from {url}")
                    self.session_info['errors_encountered'] += 1
                    continue
                
                # Extract companies from page
                companies = self.data_extractor.extract_companies_from_page(html_content, url)
                if companies:
                    all_companies.extend(companies)
                    self.logger.info(f"Extracted {len(companies)} companies from page {i+1}")
                else:
                    self.logger.warning(f"No companies found on page {i+1}")
                
                self.session_info['total_pages_scraped'] += 1
                
                # Respect rate limits
                if i < len(urls) - 1:  # Don't wait after the last page
                    self.web_scraper.respect_rate_limits()
                
            except Exception as e:
                self.logger.error(f"Error scraping page {url}: {e}")
                self.session_info['errors_encountered'] += 1
                continue
        
        return all_companies
    
    def _process_and_save_data(self, companies: List[Dict[str, Any]]) -> bool:
        """Process extracted data and save to JSON file."""
        try:
            self.logger.info(f"Processing {len(companies)} extracted companies...")
            
            # Clean and normalize data
            cleaned_companies = self.data_extractor.normalize_and_clean_data(companies)
            self.logger.info(f"Cleaned data: {len(cleaned_companies)} valid companies")
            
            # Remove duplicates
            unique_companies = self.json_converter.remove_duplicates(cleaned_companies)
            self.logger.info(f"After duplicate removal: {len(unique_companies)} unique companies")
            
            # Validate data quality
            quality_metrics = self.json_converter.validate_data_quality(unique_companies)
            self.logger.info(f"Data quality score: {quality_metrics['data_completeness_score']}%")
            
            # Convert to JSON format
            json_data = self.json_converter.convert_to_json(unique_companies, self.session_info)
            
            # Add quality metrics to metadata
            json_data['metadata']['quality_metrics'] = quality_metrics
            
            # Save to file
            output_config = self.config.get_output_config()
            output_file = output_config['file_path']
            
            success = self.json_converter.save_json_file(json_data, output_file)
            
            if success:
                self.logger.info(f"Data saved successfully to: {output_file}")
                
                # Create and log summary report
                summary = self.json_converter.create_summary_report(json_data)
                self._log_summary_report(summary)
                
                return True
            else:
                self.logger.error("Failed to save data to file")
                return False
                
        except Exception as e:
            self.logger.error(f"Error processing and saving data: {e}")
            return False
    
    def _log_summary_report(self, summary: Dict[str, Any]):
        """Log summary report of extracted data."""
        self.logger.info("=== EXTRACTION SUMMARY REPORT ===")
        self.logger.info(f"Total companies extracted: {summary['total_companies']}")
        self.logger.info(f"Companies with email: {summary['companies_with_email']}")
        self.logger.info(f"Companies with phone: {summary['companies_with_phone']}")
        self.logger.info(f"Companies with website: {summary['companies_with_website']}")
        self.logger.info(f"Companies with Arabic names: {summary['companies_with_arabic_name']}")
        self.logger.info(f"Companies with English names: {summary['companies_with_english_name']}")
        self.logger.info(f"Unique business categories: {summary['total_business_categories']}")
        self.logger.info(f"Unique products: {summary['total_products']}")
        self.logger.info(f"Unique export markets: {summary['total_export_markets']}")
        
        if summary.get('unique_categories'):
            self.logger.info(f"Top categories: {', '.join(summary['unique_categories'][:5])}")
        
        self.logger.info("=== END SUMMARY REPORT ===")


def main():
    """Main entry point for the application."""
    parser = argparse.ArgumentParser(description='Egypt Exporters Data Scraper')
    parser.add_argument('--config', '-c', default='config/scraper_config.json',
                       help='Path to configuration file')
    parser.add_argument('--resume', '-r', action='store_true',
                       help='Resume from previous scraping session')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose logging')
    
    args = parser.parse_args()
    
    try:
        # Create and run scraper
        scraper = EgyptExportersScraper(args.config)
        
        if args.verbose:
            scraper.logger.logger.setLevel('DEBUG')
        
        success = scraper.run(resume=args.resume)
        
        if success:
            print("✅ Scraping completed successfully!")
            sys.exit(0)
        else:
            print("❌ Scraping failed. Check logs for details.")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⚠️  Scraping interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
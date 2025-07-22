# Design Document

## Overview

The Egypt Exporters Scraper is a Python-based web scraping application that systematically extracts company data from the Egyptian Ministry of Trade and Industry's exporters directory. The system uses modern web scraping techniques with proper error handling, rate limiting, and data validation to ensure reliable data extraction.

## Architecture

The application follows a modular architecture with clear separation of concerns:

```
egypt-exporters-scraper/
├── src/
│   ├── scraper/
│   │   ├── __init__.py
│   │   ├── web_scraper.py      # Main scraping logic
│   │   ├── data_extractor.py   # Data extraction and parsing
│   │   ├── json_converter.py   # JSON formatting and validation
│   │   └── config.py           # Configuration management
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── logger.py           # Logging utilities
│   │   ├── validators.py       # Data validation
│   │   └── file_handler.py     # File I/O operations
│   └── main.py                 # Entry point
├── config/
│   └── scraper_config.json     # Configuration file
├── output/
│   └── exporters_data.json     # Output JSON file
├── logs/
│   └── scraper.log            # Application logs
├── requirements.txt
└── README.md
```

## Components and Interfaces

### WebScraper Class

- **Purpose**: Handles HTTP requests, session management, and website navigation
- **Key Methods**:
  - `initialize_session()`: Sets up requests session with headers and cookies
  - `fetch_page(url)`: Retrieves webpage content with retry logic
  - `navigate_pagination()`: Handles automatic page navigation
  - `respect_rate_limits()`: Implements delays between requests

### DataExtractor Class

- **Purpose**: Parses HTML content and extracts structured data
- **Key Methods**:
  - `extract_company_data(html)`: Parses company information from HTML
  - `extract_contact_info(html)`: Extracts contact details
  - `extract_business_categories(html)`: Gets business classification data
  - `validate_extracted_data(data)`: Ensures data completeness

### JSONConverter Class

- **Purpose**: Converts extracted data to properly formatted JSON
- **Key Methods**:
  - `convert_to_json(data)`: Transforms data to JSON structure
  - `validate_json_format(json_data)`: Ensures valid JSON formatting
  - `handle_arabic_encoding()`: Manages UTF-8 encoding for Arabic text
  - `remove_duplicates(data)`: Identifies and handles duplicate records

### Configuration Manager

- **Purpose**: Manages application settings and scraping parameters
- **Configuration Options**:
  - Request delays (default: 2-5 seconds)
  - Retry attempts (default: 3)
  - Timeout settings (default: 30 seconds)
  - Output file paths
  - Logging levels

## Data Models

### Company Data Structure

```json
{
  "id": "unique_identifier",
  "company_name": "string",
  "company_name_arabic": "string",
  "contact_info": {
    "address": "string",
    "address_arabic": "string",
    "phone": "string",
    "fax": "string",
    "email": "string",
    "website": "string"
  },
  "business_info": {
    "categories": ["string"],
    "products": ["string"],
    "export_markets": ["string"]
  },
  "registration_info": {
    "registration_number": "string",
    "registration_date": "string"
  },
  "extraction_metadata": {
    "extracted_at": "ISO_timestamp",
    "source_url": "string"
  }
}
```

### Scraping Session Data

```json
{
  "session_info": {
    "start_time": "ISO_timestamp",
    "end_time": "ISO_timestamp",
    "total_pages_scraped": "number",
    "total_companies_extracted": "number",
    "errors_encountered": "number"
  },
  "companies": [
    // Array of company objects
  ]
}
```

## Error Handling

### Network Error Handling

- **Connection Timeouts**: Implement exponential backoff retry strategy
- **HTTP Errors**: Handle 4xx and 5xx status codes with appropriate responses
- **Rate Limiting**: Detect rate limiting responses and implement adaptive delays
- **DNS Resolution**: Handle network connectivity issues gracefully

### Data Validation Errors

- **Missing Required Fields**: Log warnings and continue with available data
- **Invalid Data Formats**: Sanitize and normalize data where possible
- **Encoding Issues**: Ensure proper UTF-8 handling for Arabic text
- **Duplicate Detection**: Implement fuzzy matching for similar company names

### Application Errors

- **Configuration Errors**: Validate configuration file on startup
- **File I/O Errors**: Handle permissions and disk space issues
- **Memory Management**: Implement batch processing for large datasets
- **Graceful Shutdown**: Allow interruption and resume capability

## Testing Strategy

### Unit Testing

- **Data Extraction Tests**: Verify parsing logic with sample HTML
- **JSON Conversion Tests**: Validate output format and encoding
- **Configuration Tests**: Ensure proper configuration loading
- **Validation Tests**: Test data validation rules

### Integration Testing

- **End-to-End Scraping**: Test complete scraping workflow with limited data
- **Error Scenario Testing**: Simulate network errors and website changes
- **Performance Testing**: Measure scraping speed and resource usage
- **Data Quality Testing**: Verify extracted data accuracy

### Mock Testing

- **Website Response Mocking**: Use saved HTML responses for consistent testing
- **Network Error Simulation**: Test error handling without affecting live website
- **Rate Limiting Simulation**: Test adaptive delay mechanisms

## Implementation Considerations

### Technical Stack

- **Python 3.8+**: Core programming language
- **requests**: HTTP client library
- **BeautifulSoup4**: HTML parsing
- **lxml**: Fast XML/HTML parser
- **json**: JSON handling (built-in)
- **logging**: Application logging (built-in)
- **time**: Rate limiting delays (built-in)

### Performance Optimization

- **Session Reuse**: Maintain persistent HTTP sessions
- **Concurrent Processing**: Consider threading for I/O-bound operations
- **Memory Efficiency**: Process data in batches to manage memory usage
- **Caching**: Cache parsed data to avoid re-processing

### Compliance and Ethics

- **robots.txt Compliance**: Check and respect robots.txt directives
- **Rate Limiting**: Implement respectful request intervals
- **User-Agent**: Use appropriate user-agent strings
- **Terms of Service**: Ensure compliance with website terms

"""Configuration management for the Egypt Exporters Scraper."""

import json
import os
from typing import Dict, Any


class Configuration:
    """Manages scraper configuration settings."""
    
    def __init__(self, config_path: str = "config/scraper_config.json"):
        """Initialize configuration with default path."""
        self.config_path = config_path
        self.config = self._load_config()
        self._validate_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from JSON file."""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in configuration file: {e}")
    
    def _validate_config(self) -> None:
        """Validate required configuration parameters."""
        required_sections = ['scraping', 'output', 'logging']
        for section in required_sections:
            if section not in self.config:
                raise ValueError(f"Missing required configuration section: {section}")
        
        # Validate scraping section
        scraping_config = self.config['scraping']
        required_scraping_keys = ['base_url', 'request_delay_min', 'request_delay_max', 'retry_attempts', 'timeout']
        for key in required_scraping_keys:
            if key not in scraping_config:
                raise ValueError(f"Missing required scraping configuration: {key}")
        
        # Validate output section
        output_config = self.config['output']
        if 'file_path' not in output_config:
            raise ValueError("Missing required output configuration: file_path")
        
        # Create output directory if it doesn't exist
        output_dir = os.path.dirname(output_config['file_path'])
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
    
    def get(self, section: str, key: str = None) -> Any:
        """Get configuration value by section and optional key."""
        if section not in self.config:
            raise KeyError(f"Configuration section not found: {section}")
        
        if key is None:
            return self.config[section]
        
        if key not in self.config[section]:
            raise KeyError(f"Configuration key not found: {section}.{key}")
        
        return self.config[section][key]
    
    def get_scraping_config(self) -> Dict[str, Any]:
        """Get scraping configuration."""
        return self.get('scraping')
    
    def get_output_config(self) -> Dict[str, Any]:
        """Get output configuration."""
        return self.get('output')
    
    def get_logging_config(self) -> Dict[str, Any]:
        """Get logging configuration."""
        return self.get('logging')
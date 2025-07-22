"""File handling utilities for the Egypt Exporters Scraper."""

import json
import os
from typing import Any, Dict, List


class FileHandler:
    """Handles file I/O operations for the scraper."""
    
    @staticmethod
    def save_json(data: Any, file_path: str, encoding: str = 'utf-8', indent: int = 2) -> None:
        """Save data to JSON file with proper encoding."""
        try:
            # Create directory if it doesn't exist
            directory = os.path.dirname(file_path)
            if directory and not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)
            
            with open(file_path, 'w', encoding=encoding) as f:
                json.dump(data, f, ensure_ascii=False, indent=indent)
        except Exception as e:
            raise IOError(f"Failed to save JSON file {file_path}: {e}")
    
    @staticmethod
    def load_json(file_path: str, encoding: str = 'utf-8') -> Any:
        """Load data from JSON file."""
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                return json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"JSON file not found: {file_path}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in file {file_path}: {e}")
    
    @staticmethod
    def file_exists(file_path: str) -> bool:
        """Check if file exists."""
        return os.path.exists(file_path)
    
    @staticmethod
    def create_directory(directory: str) -> None:
        """Create directory if it doesn't exist."""
        if not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
    
    @staticmethod
    def get_file_size(file_path: str) -> int:
        """Get file size in bytes."""
        if os.path.exists(file_path):
            return os.path.getsize(file_path)
        return 0
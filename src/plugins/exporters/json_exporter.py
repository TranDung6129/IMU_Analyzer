# File: src/plugins/exporters/json_exporter.py
# Purpose: Export data to JSON format
# Target Lines: ≤150

"""
Methods to implement:
- init(): Initialize the exporter
- export(): Export data to JSON format
- destroy(): Clean up resources
"""

import os
import json
import logging
from datetime import datetime
from src.plugins.exporters.base_exporter import BaseExporter


class JSONExporter(BaseExporter):
    """
    Exporter for JSON (JavaScript Object Notation) format.
    
    Exports processed data, analyzed data, or raw data to JSON files.
    """
    
    def __init__(self, config=None):
        """
        Initialize the JSON exporter with optional configuration.
        
        Args:
            config (dict, optional): Configuration dictionary with options:
                - export_path: Path where to save the JSON file
                - indent: Number of spaces for indentation (default: 2)
                - ensure_ascii: Whether to escape non-ASCII characters (default: False)
                - sort_keys: Whether to sort keys (default: True)
                - extension: File extension (default: .json)
                - datetime_format: Format for datetime fields (default: "%Y-%m-%d %H:%M:%S.%f")
                - array_mode: Whether to export data as a JSON array (default: False)
        """
        super().__init__(config)
        
    def init(self, config):
        """
        Initialize or re-initialize the exporter with the specified configuration.
        
        Args:
            config (dict): Configuration dictionary
            
        Returns:
            bool: True if successful, False otherwise
        """
        self.config = config
        
        # Set default values if not provided
        if 'indent' not in self.config:
            self.config['indent'] = 2
        if 'ensure_ascii' not in self.config:
            self.config['ensure_ascii'] = False
        if 'sort_keys' not in self.config:
            self.config['sort_keys'] = True
        if 'extension' not in self.config:
            self.config['extension'] = '.json'
        if 'datetime_format' not in self.config:
            self.config['datetime_format'] = "%Y-%m-%d %H:%M:%S.%f"
        if 'array_mode' not in self.config:
            self.config['array_mode'] = False
        
        # Validate the configuration
        if not self.validate_config(self.config):
            return False
        
        self.initialized = True
        return True
        
    def export(self, data, config=None):
        """
        Export data to JSON format.
        
        Args:
            data (dict or list): Data to export
            config (dict, optional): Export-specific configuration
            
        Returns:
            str: Path to the exported file
            
        Raises:
            ValueError: If the data cannot be exported
        """
        if not self.initialized:
            raise RuntimeError("Exporter not initialized")
        
        # Use provided config or instance config
        export_config = config or self.config
        
        try:
            # Get export path
            export_path = export_config.get('export_path')
            if not export_path:
                # Generate a default filename if none provided
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                export_path = f"export_{timestamp}{export_config.get('extension', '.json')}"
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(os.path.abspath(export_path)), exist_ok=True)
            
            # Prepare data for export
            prepared_data = self._prepare_data(data, export_config)
            
            # Write data to file
            with open(export_path, 'w', encoding='utf-8') as json_file:
                json.dump(
                    prepared_data,
                    json_file,
                    indent=export_config.get('indent', 2),
                    ensure_ascii=export_config.get('ensure_ascii', False),
                    sort_keys=export_config.get('sort_keys', True),
                    default=self._json_serializer
                )
            
            # Update export count
            self.export_count += 1
            self.logger.info(f"Data exported to JSON: {export_path}")
            
            return export_path
            
        except Exception as e:
            error_msg = f"Failed to export data to JSON: {str(e)}"
            self.set_error(error_msg)
            raise ValueError(error_msg)
    
    def _prepare_data(self, data, config):
        """
        Prepare data for JSON export.
        
        Args:
            data (dict or list): Data to prepare
            config (dict): Export configuration
            
        Returns:
            dict or list: Prepared data for JSON export
        """
        # Handle array mode
        if config.get('array_mode', False) and isinstance(data, dict):
            return [data]
        
        # Handle timestamp wrapping
        if config.get('wrap_with_timestamp', False):
            return {
                'timestamp': datetime.now().strftime(config.get('datetime_format', "%Y-%m-%d %H:%M:%S.%f")),
                'data': data
            }
        
        return data
    
    def _json_serializer(self, obj):
        """
        Custom JSON serializer for objects not serializable by default.
        
        Args:
            obj: Object to serialize
            
        Returns:
            Serializable object
        
        Raises:
            TypeError: If object cannot be serialized
        """
        # Handle datetime objects
        if isinstance(obj, datetime):
            return obj.strftime(self.config.get('datetime_format', "%Y-%m-%d %H:%M:%S.%f"))
        
        # Handle bytes objects
        if isinstance(obj, bytes):
            return obj.hex()
        
        # Handle custom objects with to_dict() method
        if hasattr(obj, 'to_dict') and callable(getattr(obj, 'to_dict')):
            return obj.to_dict()
        
        # Handle sets
        if isinstance(obj, set):
            return list(obj)
        
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
    
    def destroy(self):
        """
        Clean up any resources used by the exporter.
        
        Returns:
            bool: True if successful, False otherwise
        """
        self.initialized = False
        self.clear_error()
        return True


# How to extend and modify:
# 1. Add compression: Add option to compress JSON files
# 2. Add streaming export: Extend export() to handle large datasets in a streaming manner
# 3. Add schema validation: Add option to validate data against JSON schema
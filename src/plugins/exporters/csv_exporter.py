# File: src/plugins/exporters/csv_exporter.py
# Purpose: Export data to CSV format
# Target Lines: ≤150

"""
Methods to implement:
- init(): Initialize the exporter
- export(): Export data to CSV format
- destroy(): Clean up resources
"""

import os
import csv
import logging
import time
from datetime import datetime
from src.plugins.exporters.base_exporter import BaseExporter


class CSVExporter(BaseExporter):
    """
    Exporter for CSV (Comma Separated Values) format.
    
    Exports processed data, analyzed data, or raw data to CSV files.
    """
    
    def __init__(self, config=None):
        """
        Initialize the CSV exporter with optional configuration.
        
        Args:
            config (dict, optional): Configuration dictionary with options:
                - export_path: Path where to save the CSV file
                - delimiter: CSV delimiter character (default: ',')
                - quotechar: CSV quote character (default: '"')
                - datetime_format: Format for datetime fields (default: "%Y-%m-%d %H:%M:%S.%f")
                - include_header: Whether to include a header row (default: True)
                - extension: File extension (default: .csv)
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
        if 'delimiter' not in self.config:
            self.config['delimiter'] = ','
        if 'quotechar' not in self.config:
            self.config['quotechar'] = '"'
        if 'datetime_format' not in self.config:
            self.config['datetime_format'] = "%Y-%m-%d %H:%M:%S.%f"
        if 'include_header' not in self.config:
            self.config['include_header'] = True
        if 'extension' not in self.config:
            self.config['extension'] = '.csv'
        
        # Validate the configuration
        if not self.validate_config(self.config):
            return False
        
        self.initialized = True
        return True
        
    def export(self, data, config=None):
        """
        Export data to CSV format.
        
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
                export_path = f"export_{timestamp}{export_config.get('extension', '.csv')}"
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(os.path.abspath(export_path)), exist_ok=True)
            
            # Prepare data for export
            rows = self._prepare_data(data)
            
            # Write data to file
            with open(export_path, 'w', newline='') as csvfile:
                writer = csv.writer(
                    csvfile,
                    delimiter=export_config.get('delimiter', ','),
                    quotechar=export_config.get('quotechar', '"'),
                    quoting=csv.QUOTE_MINIMAL
                )
                
                # Write rows
                for row in rows:
                    writer.writerow(row)
            
            # Update export count
            self.export_count += 1
            self.logger.info(f"Data exported to CSV: {export_path}")
            
            return export_path
            
        except Exception as e:
            error_msg = f"Failed to export data to CSV: {str(e)}"
            self.set_error(error_msg)
            raise ValueError(error_msg)
    
    def _prepare_data(self, data):
        """
        Prepare data for CSV export.
        
        Args:
            data (dict or list): Data to prepare
            
        Returns:
            list: List of rows ready for CSV export
        """
        rows = []
        
        # Handle list of dictionaries
        if isinstance(data, list) and all(isinstance(item, dict) for item in data):
            # Get all unique keys for the header
            all_keys = set()
            for item in data:
                all_keys.update(item.keys())
            
            # Sort keys for consistent ordering
            header = sorted(list(all_keys))
            
            # Add header row if configured
            if self.config.get('include_header', True):
                rows.append(header)
            
            # Add data rows
            for item in data:
                row = [self._format_value(item.get(key, "")) for key in header]
                rows.append(row)
        
        # Handle single dictionary
        elif isinstance(data, dict):
            # Add header row if configured
            if self.config.get('include_header', True):
                rows.append(list(data.keys()))
            
            # Add data row
            rows.append([self._format_value(value) for value in data.values()])
        
        # Handle other cases (e.g., nested dictionaries)
        else:
            # Convert to flat structure
            flat_data = self._flatten_data(data)
            
            # Add header row if configured
            if self.config.get('include_header', True):
                rows.append(list(flat_data.keys()))
            
            # Add data row
            rows.append([self._format_value(value) for value in flat_data.values()])
        
        return rows
    
    def _format_value(self, value):
        """
        Format a value for CSV export.
        
        Args:
            value: Value to format
            
        Returns:
            str: Formatted value
        """
        # Format datetime objects
        if isinstance(value, datetime):
            return value.strftime(self.config.get('datetime_format', "%Y-%m-%d %H:%M:%S.%f"))
        
        # Convert dictionaries to JSON string
        if isinstance(value, dict):
            import json
            return json.dumps(value)
        
        # Convert lists to string
        if isinstance(value, list):
            import json
            return json.dumps(value)
        
        return value
    
    def _flatten_data(self, data, parent_key='', sep='.'):
        """
        Flatten nested dictionaries.
        
        Args:
            data (dict): Dictionary to flatten
            parent_key (str): Key for parent items
            sep (str): Separator for nested keys
            
        Returns:
            dict: Flattened dictionary
        """
        items = {}
        for key, value in data.items() if isinstance(data, dict) else enumerate(data):
            new_key = f"{parent_key}{sep}{key}" if parent_key else key
            
            if isinstance(value, (dict, list)) and value:
                items.update(self._flatten_data(value, new_key, sep=sep))
            else:
                items[new_key] = value
                
        return items
    
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
# 1. Add formatting options: Extend _format_value() to handle specific data types
# 2. Add compression: Add option to compress CSV files
# 3. Add streaming export: Extend export() to handle large datasets in a streaming manner
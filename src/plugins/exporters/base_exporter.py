# File: src/plugins/exporters/base_exporter.py
# Purpose: Abstract base class for all data exporters
# Target Lines: ≤150

"""
Methods to implement in derived classes:
- __init__(self, config=None): Initialize with optional configuration
- init(self, config): Initialize or re-initialize with new configuration
- export(self, data, config=None): Export data to specified format
- destroy(self): Clean up resources
"""

from abc import ABC, abstractmethod
import logging
import os


class BaseExporter(ABC):
    """
    Abstract base class for all data exporters.
    
    Exporters are responsible for exporting data to various formats,
    such as CSV, JSON, etc.
    """
    
    def __init__(self, config=None):
        """
        Initialize the exporter with optional configuration.
        
        Args:
            config (dict, optional): Configuration dictionary for the exporter
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        self.config = config or {}
        self.initialized = False
        self.error_state = False
        self.error_message = None
        self.export_count = 0
        self.export_errors = 0
        
        if config:
            self.init(config)
    
    @abstractmethod
    def init(self, config):
        """
        Initialize or re-initialize the exporter with the specified configuration.
        
        Args:
            config (dict): Configuration dictionary for the exporter
            
        Returns:
            bool: True if successful, False otherwise
        """
        self.config = config
        self.initialized = True
        return True
    
    @abstractmethod
    def export(self, data, config=None):
        """
        Export data to the specified format.
        
        Args:
            data (dict or list): Data to export
            config (dict, optional): Export-specific configuration, overrides instance config
            
        Returns:
            str: Path to the exported file, or export result identifier
            
        Raises:
            ValueError: If the data cannot be exported
        """
        if not self.initialized:
            raise RuntimeError("Exporter not initialized")
        
        # Use provided config or instance config
        export_config = config or self.config
        
        # Ensure export directory exists
        export_path = export_config.get("export_path")
        if export_path:
            os.makedirs(os.path.dirname(export_path), exist_ok=True)
        
        self.export_count += 1
        return None
    
    @abstractmethod
    def destroy(self):
        """
        Clean up any resources used by the exporter.
        
        Returns:
            bool: True if successful, False otherwise
        """
        self.initialized = False
        return True
    
    def get_status(self):
        """
        Get the current status of the exporter.
        
        Returns:
            dict: A dictionary containing status information:
                - initialized (bool): Whether the exporter is initialized
                - error_state (bool): Whether there's an error
                - error_message (str): Error message, if any
                - export_count (int): Total number of export operations
                - export_errors (int): Total number of export errors
        """
        return {
            "initialized": self.initialized,
            "error_state": self.error_state,
            "error_message": self.error_message,
            "export_count": self.export_count,
            "export_errors": self.export_errors
        }
    
    def set_error(self, message):
        """
        Set the exporter in error state with the specified message.
        
        Args:
            message (str): Error message
        """
        self.error_state = True
        self.error_message = message
        self.export_errors += 1
        self.logger.error(f"Exporter error: {message}")
    
    def clear_error(self):
        """
        Clear any error state.
        """
        self.error_state = False
        self.error_message = None
    
    def validate_config(self, config):
        """
        Validate the export configuration.
        
        Args:
            config (dict): Configuration to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        # Base validation just checks for export_path
        if "export_path" not in config:
            self.set_error("Missing export_path in config")
            return False
        return True


# How to extend and modify:
# 1. Add more export formats: Create new derived classes for different formats
# 2. Add export options: Add methods to configure export options (headers, delimiter, etc.)
# 3. Add batch export: Add methods to export multiple datasets at once
# 4. Add data transformations: Add methods to transform data before exporting
# 5. Add compression options: Add methods to compress exported data
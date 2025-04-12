# File: src/io/readers/base_reader.py
# Purpose: Abstract base class for all data readers (File, Serial, Bluetooth)
# Target Lines: ≤150

"""
Methods to implement in derived classes:
- __init__(self, config): Initialize with configuration
- open(self): Open the data source
- read(self): Read data from the source
- close(self): Close the data source
- get_status(self): Get current status of the reader
"""

from abc import ABC, abstractmethod
import logging


class BaseReader(ABC):
    """
    Abstract base class for all data readers.
    
    Readers are responsible for reading data from various sources such as
    files, serial ports, Bluetooth devices, etc.
    """
    
    def __init__(self, config):
        """
        Initialize the reader with configuration.
        
        Args:
            config (dict): Configuration dictionary for the reader
        """
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        self.is_open = False
        self.error_state = False
        self.error_message = None
        self.metadata = {}
    
    @abstractmethod
    def open(self):
        """
        Open the data source for reading.
        
        Returns:
            bool: True if successful, False otherwise
            
        Raises:
            RuntimeError: If there's an error opening the data source
        """
        pass
    
    @abstractmethod
    def read(self):
        """
        Read data from the source.
        
        Returns:
            bytes or str or dict: Data read from the source
            
        Raises:
            RuntimeError: If there's an error reading from the data source
            IOError: If the source is not open
        """
        if not self.is_open:
            raise IOError("Cannot read: data source is not open")
    
    @abstractmethod
    def close(self):
        """
        Close the data source.
        
        Returns:
            bool: True if successful, False otherwise
        """
        pass
    
    def get_status(self):
        """
        Get the current status of the reader.
        
        Returns:
            dict: A dictionary containing status information:
                - is_open (bool): Whether the source is open
                - error_state (bool): Whether there's an error
                - error_message (str): Error message, if any
                - metadata (dict): Any additional metadata about the source
        """
        return {
            "is_open": self.is_open,
            "error_state": self.error_state,
            "error_message": self.error_message,
            "metadata": self.metadata
        }
    
    def set_error(self, message):
        """
        Set the reader in error state with the specified message.
        
        Args:
            message (str): Error message
        """
        self.error_state = True
        self.error_message = message
        self.logger.error(f"Reader error: {message}")
    
    def clear_error(self):
        """
        Clear any error state.
        """
        self.error_state = False
        self.error_message = None


# How to extend and modify:
# 1. Add more common methods: You can add more common methods here that all readers might need
# 2. Add more status information: Extend the get_status() method to include more information
# 3. Add data validation: Add methods to validate the data before returning it
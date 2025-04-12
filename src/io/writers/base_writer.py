# File: src/io/writers/base_writer.py
# Purpose: Abstract base class for all data writers (File, Serial, Bluetooth)
# Target Lines: ≤150

"""
Methods to implement in derived classes:
- __init__(self, config): Initialize with configuration
- open(self): Open the data destination
- write(self, data): Write data to the destination
- close(self): Close the data destination
- get_status(self): Get current status of the writer
"""

from abc import ABC, abstractmethod
import logging


class BaseWriter(ABC):
    """
    Abstract base class for all data writers.
    
    Writers are responsible for writing data to various destinations such as
    files, serial ports, Bluetooth devices, etc.
    """
    
    def __init__(self, config):
        """
        Initialize the writer with configuration.
        
        Args:
            config (dict): Configuration dictionary for the writer
        """
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        self.is_open = False
        self.error_state = False
        self.error_message = None
        self.bytes_written = 0
        self.write_count = 0
    
    @abstractmethod
    def open(self):
        """
        Open the data destination for writing.
        
        Returns:
            bool: True if successful, False otherwise
            
        Raises:
            RuntimeError: If there's an error opening the data destination
        """
        pass
    
    @abstractmethod
    def write(self, data):
        """
        Write data to the destination.
        
        Args:
            data (bytes or str or dict): Data to write to the destination
            
        Returns:
            int: Number of bytes written
            
        Raises:
            RuntimeError: If there's an error writing to the data destination
            IOError: If the destination is not open
        """
        if not self.is_open:
            raise IOError("Cannot write: data destination is not open")
    
    @abstractmethod
    def close(self):
        """
        Close the data destination.
        
        Returns:
            bool: True if successful, False otherwise
        """
        pass
    
    def get_status(self):
        """
        Get the current status of the writer.
        
        Returns:
            dict: A dictionary containing status information:
                - is_open (bool): Whether the destination is open
                - error_state (bool): Whether there's an error
                - error_message (str): Error message, if any
                - bytes_written (int): Total bytes written
                - write_count (int): Total number of write operations
        """
        return {
            "is_open": self.is_open,
            "error_state": self.error_state,
            "error_message": self.error_message,
            "bytes_written": self.bytes_written,
            "write_count": self.write_count
        }
    
    def set_error(self, message):
        """
        Set the writer in error state with the specified message.
        
        Args:
            message (str): Error message
        """
        self.error_state = True
        self.error_message = message
        self.logger.error(f"Writer error: {message}")
    
    def clear_error(self):
        """
        Clear any error state.
        """
        self.error_state = False
        self.error_message = None
    
    def update_stats(self, bytes_written):
        """
        Update the writing statistics.
        
        Args:
            bytes_written (int): Number of bytes written in the last operation
        """
        self.bytes_written += bytes_written
        self.write_count += 1


# How to extend and modify:
# 1. Add flush mechanism: Add a flush() method to ensure data is written to the destination
# 2. Add buffering: Implement a buffer to improve write performance
# 3. Add more statistics: Extend the get_status() method to include more information
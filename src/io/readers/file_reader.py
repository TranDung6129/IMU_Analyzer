# File: src/io/readers/file_reader.py
# Purpose: Read data from files
# Target Lines: ≤150

"""
Methods to implement:
- __init__(self, config): Initialize with configuration
- open(self): Open the file
- read(self): Read data from the file
- close(self): Close the file
- get_status(self): Get current status of the reader
"""

import os
import logging
from src.io.readers.base_reader import BaseReader


class FileReader(BaseReader):
    """
    Reader for file data sources.
    
    Reads data from files in various formats (CSV, TXT, binary, etc.)
    """
    
    def __init__(self, config):
        """
        Initialize the file reader with configuration.
        
        Args:
            config (dict): Configuration dictionary for the file reader
                - file_path (str): Path to the file to read
                - chunk_size (int): Size of chunks to read at once
                - mode (str): File open mode ('r', 'rb', etc.)
                - encoding (str): File encoding (for text files)
        """
        super().__init__(config)
        
        # Extract configuration
        self.file_path = config.get('file_path')
        self.chunk_size = config.get('chunk_size', 1024)
        self.mode = config.get('mode', 'r')
        self.encoding = config.get('encoding', 'utf-8')
        
        # Initialize file handle
        self.file = None
        self.file_size = 0
        self.current_position = 0
        
        # Validate configuration
        if not self.file_path:
            self.set_error("No file path specified in configuration")
    
    def open(self):
        """
        Open the file for reading.
        
        Returns:
            bool: True if successful, False otherwise
            
        Raises:
            RuntimeError: If there's an error opening the file
        """
        if self.is_open:
            self.logger.warning(f"File already open: {self.file_path}")
            return True
        
        try:
            # Check if file exists
            if not os.path.exists(self.file_path):
                raise FileNotFoundError(f"File not found: {self.file_path}")
            
            # Open the file
            self.file = open(self.file_path, self.mode, encoding=self.encoding if 'b' not in self.mode else None)
            self.is_open = True
            
            # Get file size
            self.file_size = os.path.getsize(self.file_path)
            self.current_position = 0
            
            # Update metadata
            self.metadata = {
                'file_path': self.file_path,
                'file_size': self.file_size,
                'mode': self.mode,
                'encoding': self.encoding if 'b' not in self.mode else None
            }
            
            self.logger.info(f"Opened file: {self.file_path}")
            self.clear_error()
            return True
            
        except Exception as e:
            self.set_error(f"Error opening file: {str(e)}")
            raise RuntimeError(f"Error opening file {self.file_path}: {str(e)}")
    
    def read(self):
        """
        Read data from the file.
        
        Returns:
            str or bytes: Data read from the file
            
        Raises:
            RuntimeError: If there's an error reading from the file
            IOError: If the file is not open
        """
        super().read()  # This will raise if not open
        
        try:
            # Read chunk of data
            data = self.file.read(self.chunk_size)
            
            # Update position
            if self.file:
                self.current_position = self.file.tell()
            
            # Return None if end of file
            if not data:
                return None
                
            return data
            
        except Exception as e:
            self.set_error(f"Error reading file: {str(e)}")
            raise RuntimeError(f"Error reading file {self.file_path}: {str(e)}")
    
    def close(self):
        """
        Close the file.
        
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.is_open:
            return True
        
        try:
            if self.file:
                self.file.close()
                self.file = None
            
            self.is_open = False
            self.logger.info(f"Closed file: {self.file_path}")
            return True
            
        except Exception as e:
            self.set_error(f"Error closing file: {str(e)}")
            return False
    
    def get_status(self):
        """
        Get the current status of the file reader.
        
        Returns:
            dict: Status information including base reader status and:
                - file_path (str): Path to the file
                - file_size (int): Size of the file in bytes
                - current_position (int): Current position in the file
                - progress (float): Reading progress as percentage
        """
        status = super().get_status()
        
        # Add file-specific status
        status.update({
            'file_path': self.file_path,
            'file_size': self.file_size,
            'current_position': self.current_position,
            'progress': (self.current_position / self.file_size * 100) if self.file_size else 0
        })
        
        return status


# How to extend and modify:
# 1. Add support for compressed files: Extend open() and read() to handle gzip, zip, etc.
# 2. Add seek capability: Add seek() method to jump to a specific position in the file
# 3. Add line-by-line reading: Add read_line() method for text files
# 4. Add file filtering: Add filter_data() method to preprocess data before returning
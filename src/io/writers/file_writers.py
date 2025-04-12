# File: src/io/writers/file_writer.py
# Purpose: Write data to files
# Target Lines: ≤150

"""
Methods to implement:
- __init__(self, config): Initialize with configuration
- open(self): Open the file for writing
- write(self, data): Write data to the file
- close(self): Close the file
- get_status(self): Get current status of the writer
"""

import os
import logging
import json
from src.io.writers.base_writer import BaseWriter


class FileWriter(BaseWriter):
    """
    Writer for file data destinations.
    
    Writes data to files in various formats (text, CSV, JSON, binary, etc.)
    """
    
    def __init__(self, config):
        """
        Initialize the file writer with configuration.
        
        Args:
            config (dict): Configuration dictionary for the file writer
                - output_path (str): Path to the output file
                - mode (str): File open mode ('w', 'a', 'wb', 'ab', etc.)
                - encoding (str): File encoding (for text files)
                - append (bool): Whether to append to the file (if it exists)
                - format (str): Format for structured data (e.g., 'json', 'csv')
                - delimiter (str): Delimiter for CSV format
        """
        super().__init__(config)
        
        # Extract configuration
        self.output_path = config.get('output_path')
        self.append = config.get('append', True)
        self.mode = config.get('mode')
        self.encoding = config.get('encoding', 'utf-8')
        self.format = config.get('format', 'text')  # text, csv, json, binary
        self.delimiter = config.get('delimiter', ',')
        
        # Set mode based on format and append if not specified
        if not self.mode:
            if self.format == 'binary':
                self.mode = 'ab' if self.append else 'wb'
            else:
                self.mode = 'a' if self.append else 'w'
        
        # Initialize file handle
        self.file = None
        
        # Validate configuration
        if not self.output_path:
            self.set_error("No output path specified in configuration")
    
    def open(self):
        """
        Open the file for writing.
        
        Returns:
            bool: True if successful, False otherwise
            
        Raises:
            RuntimeError: If there's an error opening the file
        """
        if self.is_open:
            self.logger.warning(f"File already open: {self.output_path}")
            return True
        
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(os.path.abspath(self.output_path)), exist_ok=True)
            
            # Open the file
            self.file = open(
                self.output_path, 
                self.mode, 
                encoding=self.encoding if 'b' not in self.mode else None
            )
            
            self.is_open = True
            self.logger.info(f"Opened file for writing: {self.output_path} (mode: {self.mode})")
            self.clear_error()
            return True
            
        except Exception as e:
            self.set_error(f"Error opening file for writing: {str(e)}")
            raise RuntimeError(f"Error opening file {self.output_path}: {str(e)}")
    
    def write(self, data):
        """
        Write data to the file.
        
        Args:
            data (bytes, str, dict, list): Data to write to the file
            
        Returns:
            int: Number of bytes written
            
        Raises:
            RuntimeError: If there's an error writing to the file
            IOError: If the file is not open
        """
        super().write(data)  # This will raise if not open
        
        try:
            bytes_written = 0
            
            # Process data based on format
            if self.format == 'json' and not isinstance(data, (bytes, str)):
                # Convert to JSON
                json_data = json.dumps(data)
                bytes_written = self.file.write(json_data + '\n')
                
            elif self.format == 'csv' and isinstance(data, dict):
                # Convert dict to CSV row
                csv_row = self.delimiter.join(str(value) for value in data.values())
                bytes_written = self.file.write(csv_row + '\n')
                
            elif isinstance(data, bytes) and 'b' not in self.mode:
                # Convert bytes to string if file is in text mode
                str_data = data.decode(self.encoding)
                bytes_written = self.file.write(str_data)
                
            elif isinstance(data, str) and 'b' in self.mode:
                # Convert string to bytes if file is in binary mode
                bytes_data = data.encode(self.encoding)
                bytes_written = self.file.write(bytes_data)
                
            else:
                # Write data as is
                bytes_written = self.file.write(data)
            
            # Flush to ensure data is written
            self.file.flush()
            
            # Update stats
            self.update_stats(bytes_written)
            
            return bytes_written
            
        except Exception as e:
            self.set_error(f"Error writing to file: {str(e)}")
            raise RuntimeError(f"Error writing to file {self.output_path}: {str(e)}")
    
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
            self.logger.info(f"Closed file: {self.output_path}")
            return True
            
        except Exception as e:
            self.set_error(f"Error closing file: {str(e)}")
            return False
    
    def get_status(self):
        """
        Get the current status of the file writer.
        
        Returns:
            dict: Status information including base writer status and file-specific info
        """
        status = super().get_status()
        
        # Add file-specific status
        status.update({
            'output_path': self.output_path,
            'mode': self.mode,
            'format': self.format
        })
        
        return status


# How to extend and modify:
# 1. Add support for compressed files: Extend to write to gzip, zip, etc.
# 2. Add batched writing: Add buffer to collect data and write in batches
# 3. Add rotation support: Add file rotation based on size or time
# 4. Add more formats: Extend to support more structured formats like XML, YAML, etc.
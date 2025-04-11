# src/io/readers/file_reader.py
import os
import csv
import time
from typing import Dict, Any, Generator, Optional
from src.io.readers.base_reader import IDataReader

class FileReader(IDataReader):
    """
    Reader for file-based data sources.
    
    Reads data from files (binary, CSV, etc.) and provides it as raw bytes
    to the pipeline.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the file reader.
        
        Args:
            config: Dictionary containing configuration parameters:
                - file_path (str): Path to the file to read
                - chunk_size (int, optional): Size of chunks to read in bytes (for binary files)
                - delimiter (str, optional): Delimiter for CSV files (default: ',')
                - encoding (str, optional): File encoding (default: 'utf-8')
                - simulate_realtime (bool, optional): Whether to simulate real-time data flow (default: False)
                - simulation_speed (float, optional): Speed multiplier for real-time simulation (default: 1.0)
        """
        super().__init__(config)
        
        # Required parameter
        self.file_path = config.get('file_path')
        if not self.file_path:
            raise ValueError("file_path must be specified in the configuration")
        
        # Optional parameters with defaults
        self.chunk_size = config.get('chunk_size', 4096)
        self.delimiter = config.get('delimiter', ',')
        self.encoding = config.get('encoding', 'utf-8')
        self.simulate_realtime = config.get('simulate_realtime', False)
        self.simulation_speed = config.get('simulation_speed', 1.0)
        
        # Internal state
        self.file = None
        self.csv_reader = None
        self.is_binary = self._is_binary_file(self.file_path)
        self.is_csv = self._is_csv_file(self.file_path)
        self.last_read_time = 0
        
        print(f"FileReader initialized for {self.file_path} (binary: {self.is_binary}, CSV: {self.is_csv})")
    
    def _is_binary_file(self, file_path: str) -> bool:
        """
        Determine if the file is binary based on extension.
        
        Args:
            file_path: Path to the file
            
        Returns:
            True if the file is likely binary, False otherwise
        """
        binary_extensions = ['.bin', '.dat', '.raw', '.imu']
        _, ext = os.path.splitext(file_path)
        return ext.lower() in binary_extensions
    
    def _is_csv_file(self, file_path: str) -> bool:
        """
        Determine if the file is CSV based on extension.
        
        Args:
            file_path: Path to the file
            
        Returns:
            True if the file is likely CSV, False otherwise
        """
        csv_extensions = ['.csv', '.tsv', '.txt']
        _, ext = os.path.splitext(file_path)
        return ext.lower() in csv_extensions
    
    def open(self):
        """Open the file for reading."""
        try:
            mode = 'rb' if self.is_binary else 'r'
            self.file = open(self.file_path, mode, encoding=None if self.is_binary else self.encoding)
            
            # If it's a CSV file, create a CSV reader
            if self.is_csv and not self.is_binary:
                self.csv_reader = csv.reader(self.file, delimiter=self.delimiter)
            
            print(f"Opened file: {self.file_path}")
            return self
        except Exception as e:
            raise IOError(f"Failed to open file {self.file_path}: {e}")
    
    def close(self):
        """Close the file."""
        if self.file:
            self.file.close()
            self.file = None
            self.csv_reader = None
            print(f"Closed file: {self.file_path}")
    
    def read(self) -> Generator[bytes, None, None]:
        """
        Read data from the file.
        
        For binary files: Yields chunks of raw bytes.
        For CSV files: Reads each row, converts to string, and yields as bytes.
        
        If simulate_realtime is True, adds delays between chunks to simulate
        real-time data acquisition.
        
        Yields:
            Chunks of data as bytes
        """
        if not self.file:
            raise IOError("File is not open. Call open() before reading.")
        
        try:
            # For binary files, read in chunks
            if self.is_binary:
                while True:
                    if self.simulate_realtime:
                        self._simulate_delay()
                    
                    chunk = self.file.read(self.chunk_size)
                    if not chunk:
                        # End of file
                        break
                    
                    yield chunk
            
            # For CSV files, read row by row
            elif self.csv_reader:
                # Read and yield header row first if needed
                # (In a real implementation, you might want to handle this differently)
                if self.simulate_realtime:
                    self._simulate_delay()
                
                # Read and yield each data row
                for row in self.csv_reader:
                    if self.simulate_realtime:
                        self._simulate_delay()
                    
                    # Convert row to string and then to bytes
                    row_str = self.delimiter.join(row) + "\n"
                    yield row_str.encode(self.encoding)
            
            # For text files that are not CSV
            else:
                while True:
                    if self.simulate_realtime:
                        self._simulate_delay()
                    
                    line = self.file.readline()
                    if not line:
                        # End of file
                        break
                    
                    # Convert line to bytes if it's not already
                    if isinstance(line, str):
                        line = line.encode(self.encoding)
                    
                    yield line
                    
        except Exception as e:
            raise IOError(f"Error reading from file {self.file_path}: {e}")
    
    def _simulate_delay(self):
        """
        Add a delay to simulate real-time data acquisition.
        
        The delay is calculated to simulate the specified simulation_speed.
        """
        current_time = time.time()
        
        if self.last_read_time > 0:
            # Calculate the time to wait
            elapsed = current_time - self.last_read_time
            target_delay = 1.0 / self.simulation_speed  # seconds per chunk
            
            # If we need to wait more
            if elapsed < target_delay:
                time.sleep(target_delay - elapsed)
        
        self.last_read_time = time.time()
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get the current status of the reader.
        
        Returns:
            Dictionary with status information
        """
        return {
            "status": "open" if self.file else "closed",
            "file_path": self.file_path,
            "is_binary": self.is_binary,
            "is_csv": self.is_csv,
            "simulate_realtime": self.simulate_realtime,
            "simulation_speed": self.simulation_speed
        }
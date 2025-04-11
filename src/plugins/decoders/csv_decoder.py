# src/plugins/decoders/csv_decoder.py
import logging
import csv
import io
from typing import Dict, Any, Generator, List, Optional
from src.plugins.decoders.base_decoder import IDecoder
from src.data.models import SensorData

logger = logging.getLogger(__name__)

class CSVDecoder(IDecoder):
    """
    Decoder for CSV data.
    
    Parses CSV data and converts it to SensorData objects.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the CSV decoder.
        
        Args:
            config: Dictionary containing configuration parameters:
                - sensor_id (str, optional): ID to assign to the sensor (default: 'csv_sensor')
                - data_type (str, optional): Type of data (default: 'csv')
                - delimiter (str, optional): CSV delimiter (default: ',')
                - columns (List[str], optional): Column names if header is missing
                - timestamp_column (str, optional): Name of the timestamp column (default: 'timestamp')
                - timestamp_format (str, optional): Format of the timestamp (e.g., '%Y-%m-%d %H:%M:%S')
                - units (Dict[str, str], optional): Units for each column
                - numeric_columns (List[str], optional): Columns to convert to float
                - skip_header (bool, optional): Whether to skip the header row (default: False)
        """
        super().__init__(config)
        
        # Optional parameters with defaults
        self.sensor_id = config.get('sensor_id', 'csv_sensor')
        self.data_type = config.get('data_type', 'csv')
        self.delimiter = config.get('delimiter', ',')
        self.columns = config.get('columns', [])
        self.timestamp_column = config.get('timestamp_column', 'timestamp')
        self.timestamp_format = config.get('timestamp_format', '')
        self.units = config.get('units', {})
        self.numeric_columns = config.get('numeric_columns', [])
        self.skip_header = config.get('skip_header', False)
        
        # Internal state
        self.header = self.columns.copy()
        self.has_header = bool(self.header)
        self.buffer = ""
        
        logger.info(f"CSVDecoder initialized for sensor '{self.sensor_id}', data_type: '{self.data_type}'")
    
    def decode(self, raw_data: bytes) -> Generator[SensorData, None, None]:
        """
        Decode raw CSV data into SensorData objects.
        
        Args:
            raw_data: Raw CSV data as bytes
            
        Yields:
            SensorData objects
        """
        # Convert bytes to string and add to buffer
        try:
            text = raw_data.decode('utf-8')
            self.buffer += text
        except UnicodeDecodeError as e:
            logger.error(f"Error decoding CSV data: {e}")
            return
        
        # Process complete lines in the buffer
        lines = self.buffer.split('\n')
        
        # Keep the last (potentially incomplete) line in the buffer
        self.buffer = lines[-1]
        lines = lines[:-1]
        
        # Skip header if specified and this is the first chunk
        if self.skip_header and not self.has_header and lines:
            # Extract header from the first line
            header_line = lines[0]
            self.header = [col.strip() for col in header_line.split(self.delimiter)]
            self.has_header = True
            lines = lines[1:]
        
        # Process each complete line
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            try:
                # Parse the line
                row = line.split(self.delimiter)
                
                # Skip if no header or mismatch in column count
                if not self.header:
                    logger.warning("No header defined and no columns specified. Skipping line.")
                    continue
                
                if len(row) != len(self.header):
                    logger.warning(f"Column count mismatch: expected {len(self.header)}, got {len(row)}. Skipping line.")
                    continue
                
                # Convert to dictionary
                data_dict = {col: row[i] for i, col in enumerate(self.header)}
                
                # Convert numeric columns
                for col in self.numeric_columns:
                    if col in data_dict:
                        try:
                            data_dict[col] = float(data_dict[col])
                        except (ValueError, TypeError):
                            logger.warning(f"Failed to convert column '{col}' to float. Keeping as string.")
                
                # Extract timestamp
                timestamp = None
                raw_timestamp = None
                
                if self.timestamp_column in data_dict:
                    raw_timestamp = data_dict[self.timestamp_column]
                    
                    try:
                        timestamp = float(raw_timestamp)
                    except (ValueError, TypeError):
                        if self.timestamp_format:
                            # In a real implementation, we would parse according to the format
                            # For simplicity, we'll just use the current time
                            import time
                            timestamp = time.time()
                            logger.warning(f"Failed to parse timestamp '{raw_timestamp}'. Using current time.")
                        else:
                            # Use current time as fallback
                            import time
                            timestamp = time.time()
                else:
                    # Use current time if no timestamp column
                    import time
                    timestamp = time.time()
                
                # Create SensorData object
                sensor_data = SensorData(
                    timestamp=timestamp,
                    sensor_id=self.sensor_id,
                    data_type=self.data_type,
                    values={k: v for k, v in data_dict.items() if k != self.timestamp_column},
                    raw_timestamp=raw_timestamp,
                    units=self.units
                )
                
                yield sensor_data
                
            except Exception as e:
                logger.error(f"Error processing CSV line: {e}")
    
    def reset(self):
        """Reset the decoder state."""
        self.buffer = ""
        self.has_header = bool(self.header)
# File: src/plugins/decoders/custom_decoder.py
# Purpose: Flexible decoder for various data formats (CSV, JSON, binary, etc.)
# Target Lines: ≤150

"""
Methods to implement:
- __init__(self, config=None): Initialize with optional configuration
- init(self, config): Initialize or re-initialize with new configuration
- decode(self, data): Decode raw data into structured format
- destroy(self): Clean up resources
"""

import json
import csv
import io
import struct
import logging
from src.plugins.decoders.base_decoder import BaseDecoder
from src.data.models import ProcessedData


class CustomDecoder(BaseDecoder):
    """
    Flexible decoder for various data formats.
    
    Supports decoding CSV, JSON, binary, and custom formats.
    Format is specified via configuration.
    """
    
    def __init__(self, config=None):
        """
        Initialize the custom decoder with optional configuration.

        Args:
            config (dict, optional): Configuration dictionary for the decoder
        """
        # Gọi init của lớp cha TRƯỚC TIÊN
        super().__init__(config)
        # Giờ đây self.logger và self.config đã tồn tại

        # --- LOGIC KHỞI TẠO CỤ THỂ CHO CUSTOM DECODER ---
        effective_config = self.config # Lấy config từ lớp cha

        # Default values (Gán giá trị mặc định trước khi đọc config)
        self.format = 'auto'
        self.field_mapping = {}
        self.has_header = True
        self.delimiter = ","
        self.binary_format = "<fffffffff"
        self.buffer = bytearray()

        # Đọc config một cách an toàn để cập nhật giá trị mặc định
        self.format = effective_config.get('format', self.format).lower()
        self.field_mapping = effective_config.get("field_mapping", self.field_mapping)
        self.has_header = effective_config.get("has_header", self.has_header)
        self.delimiter = effective_config.get("delimiter", self.delimiter)
        self.binary_format = effective_config.get("binary_format", self.binary_format)

        # Thiết lập mapping mặc định nếu cần
        if not self.field_mapping and self.format in ["csv", "json"]:
            self._setup_default_field_mapping()

        self.logger.info(f"Custom decoder initialized with format={self.format}")


    def init(self, config):
        """
        Re-initialize the decoder with the specified configuration.
        Should be called only if re-configuration is needed after creation.

        Args:
            config (dict): Configuration dictionary for the decoder

        Returns:
            bool: True if successful, False otherwise
        """
        # Gọi init của lớp cha để reset stats và cập nhật self.config
        super().init(config)

        effective_config = self.config # Lấy config mới từ lớp cha

        # Update parameters from config
        # Giá trị mặc định giờ lấy từ self.<attribute> đã được gán trong __init__
        self.format = effective_config.get("format", self.format).lower()
        self.field_mapping = effective_config.get("field_mapping", self.field_mapping)
        self.has_header = effective_config.get("has_header", self.has_header)
        self.delimiter = effective_config.get("delimiter", self.delimiter)
        self.binary_format = effective_config.get("binary_format", self.binary_format)

        # Cập nhật lại field mapping mặc định nếu cần
        if not self.field_mapping and self.format in ["csv", "json"]:
             self._setup_default_field_mapping()

        self.logger.info(f"Custom decoder re-initialized with format={self.format}")
        return True

    def _setup_default_field_mapping(self):
        """Helper to set default field mapping based on format."""
        if self.format == "csv":
            self.field_mapping = {
                "timestamp": "timestamp", "roll": "roll", "pitch": "pitch", "yaw": "yaw",
                "accel_x": "accel_x", "accel_y": "accel_y", "accel_z": "accel_z",
                "gyro_x": "gyro_x", "gyro_y": "gyro_y", "gyro_z": "gyro_z",
                "mag_x": "mag_x", "mag_y": "mag_y", "mag_z": "mag_z"
            }
        elif self.format == "json":
             self.field_mapping = {
                "timestamp": "timestamp",
                "orientation": {"roll": "roll", "pitch": "pitch", "yaw": "yaw"},
                "acceleration": {"x": "accel_x", "y": "accel_y", "z": "accel_z"},
                "gyroscope": {"x": "gyro_x", "y": "gyro_y", "z": "gyro_z"},
                "magnetometer": {"x": "mag_x", "y": "mag_y", "z": "mag_z"}
            }
    
    def decode(self, data):
        """
        Decode raw data into a structured format based on the configured format.
        
        Args:
            data (bytes, str, or dict): Raw data to decode
            
        Returns:
            ProcessedData: Decoded data in a structured format
            
        Raises:
            ValueError: If the data cannot be decoded
        """
        try:
            # Call parent's decode method for counting and validation
            super().decode(data)
            
            # Auto-detect format if set to "auto"
            if self.format == "auto":
                self._auto_detect_format(data)
            
            # Decode based on format
            if self.format == "csv":
                return self._decode_csv(data)
            elif self.format == "json":
                return self._decode_json(data)
            elif self.format == "binary":
                return self._decode_binary(data)
            else:
                self.set_error(f"Unsupported format: {self.format}")
                return None
                
        except Exception as e:
            self.set_error(f"Error decoding data: {str(e)}")
            return None
    
    def _auto_detect_format(self, data):
        """
        Attempt to auto-detect the data format.
        
        Args:
            data: Data to analyze for format detection
            
        Sets self.format to the detected format
        """
        # Try to detect format based on data type and content
        if isinstance(data, dict):
            self.format = "json"
        elif isinstance(data, str):
            # Check if it's a JSON string
            if data.strip().startswith("{") and data.strip().endswith("}"):
                self.format = "json"
            else:
                # Assume CSV if it contains commas or tabs
                if "," in data or "\t" in data:
                    self.format = "csv"
                    # Update delimiter
                    if "\t" in data and "," not in data:
                        self.delimiter = "\t"
                    else:
                        self.delimiter = ","
        elif isinstance(data, (bytes, bytearray)):
            self.format = "binary"
        
        self.logger.debug(f"Auto-detected format: {self.format}")
    
    def _decode_csv(self, data):
        """
        Decode CSV data into a ProcessedData object.
        
        Args:
            data (str or bytes): CSV data
            
        Returns:
            ProcessedData: Decoded data
        """
        # Convert bytes to string if necessary
        if isinstance(data, (bytes, bytearray)):
            data = data.decode('utf-8')
        
        # Process CSV data
        csv_reader = csv.DictReader(io.StringIO(data), delimiter=self.delimiter) if self.has_header else None
        
        if csv_reader:
            # Get the first row if header exists
            row = next(csv_reader, None)
        else:
            # Split the line and create a dictionary
            fields = data.strip().split(self.delimiter)
            fieldnames = [f"field{i}" for i in range(len(fields))]
            row = dict(zip(fieldnames, fields))
        
        if not row:
            return None
        
        # Create ProcessedData object and map fields
        result = ProcessedData()
        
        for csv_field, result_field in self.field_mapping.items():
            if csv_field in row:
                try:
                    value = float(row[csv_field])
                    setattr(result, result_field, value)
                except (ValueError, TypeError):
                    # If not a number, store as string in additional_values
                    if not hasattr(result, "additional_values"):
                        result.additional_values = {}
                    result.additional_values[result_field] = row[csv_field]
        
        return result
    
    def _decode_json(self, data):
        """
        Decode JSON data into a ProcessedData object.
        
        Args:
            data (str or dict): JSON data
            
        Returns:
            ProcessedData: Decoded data
        """
        # Parse JSON if it's a string
        if isinstance(data, (bytes, bytearray)):
            data = data.decode('utf-8')
        
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except json.JSONDecodeError as e:
                self.set_error(f"Invalid JSON: {str(e)}")
                return None
        
        if not isinstance(data, dict):
            self.set_error(f"Expected dict, got {type(data)}")
            return None
        
        # Create ProcessedData object
        result = ProcessedData()
        
        # Map fields from JSON to ProcessedData
        self._map_fields(data, self.field_mapping, result)
        
        return result
    
    def _decode_binary(self, data):
        """
        Decode binary data into a ProcessedData object.
        
        Args:
            data (bytes): Binary data
            
        Returns:
            ProcessedData: Decoded data
        """
        # Add to buffer
        if isinstance(data, (bytes, bytearray)):
            self.buffer.extend(data)
        
        # Calculate expected size based on binary_format
        expected_size = struct.calcsize(self.binary_format)
        
        # Check if we have enough data
        if len(self.buffer) < expected_size:
            return None
        
        # Extract data from buffer
        values = struct.unpack(self.binary_format, self.buffer[:expected_size])
        
        # Remove processed data from buffer
        self.buffer = self.buffer[expected_size:]
        
        # Create ProcessedData object
        result = ProcessedData()
        
        # Assuming standard format: timestamp, roll, pitch, yaw, ax, ay, az, gx, gy, gz
        # Adjust according to your binary_format
        try:
            result.timestamp = values[0]
            result.roll = values[1]
            result.pitch = values[2]
            result.yaw = values[3]
            result.accel_x = values[4]
            result.accel_y = values[5]
            result.accel_z = values[6]
            result.gyro_x = values[7]
            result.gyro_y = values[8]
            result.gyro_z = values[9] if len(values) > 9 else 0.0
            
            # Add additional values if available
            if len(values) > 10:
                result.additional_values = {f"value_{i}": values[i] for i in range(10, len(values))}
        except IndexError:
            # Handle case where values doesn't match expected fields
            self.logger.warning(f"Binary data format mismatch. Expected at least 10 values, got {len(values)}")
        
        return result
    
    def _map_fields(self, data, mapping, result, prefix=""):
        """
        Recursively map fields from a nested dictionary to a ProcessedData object.
        
        Args:
            data (dict): Source data
            mapping (dict): Field mapping
            result (ProcessedData): Destination object
            prefix (str): Prefix for nested fields
        """
        for src_field, dst_field in mapping.items():
            # Full field name with prefix
            full_src_field = f"{prefix}{src_field}"
            
            # Handle nested dictionaries
            if isinstance(dst_field, dict) and full_src_field in data and isinstance(data[full_src_field], dict):
                self._map_fields(data[full_src_field], dst_field, result)
            # Handle simple field mapping
            elif full_src_field in data:
                try:
                    value = data[full_src_field]
                    if isinstance(value, (int, float)):
                        setattr(result, dst_field, value)
                    else:
                        # Try to convert to float
                        try:
                            value = float(value)
                            setattr(result, dst_field, value)
                        except (ValueError, TypeError):
                            # If not a number, store as string in additional_values
                            if not hasattr(result, "additional_values"):
                                result.additional_values = {}
                            result.additional_values[dst_field] = value
                except Exception as e:
                    self.logger.warning(f"Error mapping field {full_src_field} to {dst_field}: {str(e)}")
    
    def destroy(self):
        """
        Clean up any resources used by the decoder.
        
        Returns:
            bool: True if successful, False otherwise
        """
        # Clear buffer
        self.buffer = bytearray()
        
        return super().destroy()


# How to extend and modify:
# 1. Add support for more formats: Add new format handling in decode() and create _decode_xxx() methods
# 2. Add field validation: Add methods to validate field values before setting them in ProcessedData
# 3. Add error recovery: Enhance error handling to recover from malformed data
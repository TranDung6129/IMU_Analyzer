# File: src/plugins/decoders/witmotion_decoder.py
# Purpose: Decoder for WitMotion IMU sensor data
# Target Lines: ≤150

"""
Methods to implement:
- __init__(self, config=None): Initialize with optional configuration
- init(self, config): Initialize or re-initialize with new configuration
- decode(self, data): Decode WitMotion raw data into structured format
- destroy(self): Clean up resources
"""

import struct
import logging
from src.plugins.decoders.base_decoder import BaseDecoder
from src.data.models import ProcessedData


class WitMotionDecoder(BaseDecoder):
    """
    Decoder for WitMotion IMU sensors.
    
    Decodes binary data from WitMotion sensors into structured data.
    Supports acceleration, gyroscope, and orientation data.
    """
    
    def __init__(self, config=None):
        """
        Initialize the WitMotion decoder with optional configuration.

        Args:
            config (dict, optional): Configuration dictionary for the decoder
        """
        # Gọi init của lớp cha TRƯỚC TIÊN
        super().__init__(config)
        # Giờ đây self.logger và self.config đã tồn tại

        # --- LOGIC KHỞI TẠO CỤ THỂ CHO WITMOTION ---
        effective_config = self.config # Lấy config từ lớp cha

        # Default ranges (Gán giá trị mặc định trước khi đọc config)
        self.acc_range = 16.0
        self.gyro_range = 2000.0
        self.angle_range = 180.0

        # Update ranges if provided in config
        self.acc_range = effective_config.get("acc_range", self.acc_range)
        self.gyro_range = effective_config.get("gyro_range", self.gyro_range)
        self.angle_range = effective_config.get("angle_range", self.angle_range)

        # Frame markers
        self.frame_markers = {
            0x51: "acceleration",
            0x52: "angular_velocity",
            0x53: "orientation",
            0x54: "magnetometer"
        }

        # Buffer
        self.buffer = bytearray()

        self.logger.info(f"WitMotion decoder initialized with acc_range={self.acc_range}g, "
                         f"gyro_range={self.gyro_range}°/s, angle_range={self.angle_range}°")

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

        # Cập nhật lại các tham số từ config mới
        # Giá trị mặc định giờ lấy từ self.<attribute> đã được gán trong __init__
        self.acc_range = effective_config.get("acc_range", self.acc_range)
        self.gyro_range = effective_config.get("gyro_range", self.gyro_range)
        self.angle_range = effective_config.get("angle_range", self.angle_range)

        self.logger.info(f"WitMotion decoder re-initialized with acc_range={self.acc_range}g, "
                         f"gyro_range={self.gyro_range}°/s, angle_range={self.angle_range}°")

        return True
    
    def decode(self, data):
        """
        Decode WitMotion raw data into structured format.
        
        Args:
            data (bytes or bytearray): Raw data from the sensor
            
        Returns:
            ProcessedData: Decoded data in a structured format
            
        Raises:
            ValueError: If the data cannot be decoded
        """
        try:
            # Call parent's decode method for counting and validation
            super().decode(data)
            
            # Add data to buffer
            if isinstance(data, (bytes, bytearray)):
                self.buffer.extend(data)
            else:
                # If data is not bytes or bytearray, try to convert it
                try:
                    if isinstance(data, dict) and "raw_bytes" in data:
                        self.buffer.extend(data["raw_bytes"])
                    else:
                        self.logger.warning(f"Unexpected data type: {type(data)}")
                        return None
                except Exception as e:
                    self.set_error(f"Failed to convert data to bytes: {str(e)}")
                    return None
            
            # Process packets in buffer
            result = self._process_buffer()
            
            return result
            
        except Exception as e:
            self.set_error(f"Error decoding data: {str(e)}")
            return None
    
    def _process_buffer(self):
        """
        Process the data buffer to extract complete packets.
        
        Returns:
            ProcessedData: Decoded data or None if no complete packet
        """
        # Need at least 11 bytes for a complete packet (1 header + 1 frame marker + 8 data + 1 checksum)
        while len(self.buffer) >= 11:
            # Find packet start (0x55 is the header byte for WitMotion)
            if self.buffer[0] != 0x55:
                # Discard bytes until we find a header
                for i in range(1, len(self.buffer)):
                    if self.buffer[i] == 0x55:
                        self.buffer = self.buffer[i:]
                        break
                else:
                    # No header found, clear buffer
                    self.buffer.clear()
                    return None
            
            # Check if we still have enough bytes for a packet
            if len(self.buffer) < 11:
                return None
                
            # Extract frame marker (data type)
            frame_marker = self.buffer[1]
            
            # Check if frame marker is valid
            if frame_marker not in self.frame_markers:
                # Invalid frame marker, discard this byte and continue
                self.buffer = self.buffer[1:]
                continue
            
            # Extract data bytes (8 bytes)
            data_bytes = self.buffer[2:10]
            
            # Calculate checksum (sum of all bytes except checksum)
            calculated_checksum = sum(self.buffer[0:10]) & 0xFF
            received_checksum = self.buffer[10]
            
            # Verify checksum
            if calculated_checksum != received_checksum:
                self.logger.warning(f"Checksum mismatch: expected {calculated_checksum}, got {received_checksum}")
                # Discard this packet and continue
                self.buffer = self.buffer[11:]
                continue
            
            # Decode data based on frame marker
            result = self._decode_packet(frame_marker, data_bytes)
            
            # Remove processed packet from buffer
            self.buffer = self.buffer[11:]
            
            return result
        
        # Not enough data for a complete packet
        return None
    
    def _decode_packet(self, frame_marker, data_bytes):
        """
        Decode a single packet based on its frame marker.
        
        Args:
            frame_marker (int): Frame marker indicating data type
            data_bytes (bytes): Data bytes to decode
            
        Returns:
            ProcessedData: Decoded data
        """
        # Create a empty ProcessedData object
        result = ProcessedData()
        
        # Decode based on frame marker
        if frame_marker == 0x51:  # Acceleration
            # WitMotion format: 3 int16 values for ax, ay, az
            ax, ay, az = struct.unpack('<hhh', data_bytes[0:6])
            
            # Convert to g (±self.acc_range)
            factor = self.acc_range / 32768.0
            result.accel_x = ax * factor
            result.accel_y = ay * factor
            result.accel_z = az * factor
            
        elif frame_marker == 0x52:  # Angular velocity
            # WitMotion format: 3 int16 values for gx, gy, gz
            gx, gy, gz = struct.unpack('<hhh', data_bytes[0:6])
            
            # Convert to °/s (±self.gyro_range)
            factor = self.gyro_range / 32768.0
            result.gyro_x = gx * factor
            result.gyro_y = gy * factor
            result.gyro_z = gz * factor
            
        elif frame_marker == 0x53:  # Orientation
            # WitMotion format: 3 int16 values for roll, pitch, yaw
            roll, pitch, yaw = struct.unpack('<hhh', data_bytes[0:6])
            
            # Convert to degrees (±self.angle_range)
            factor = self.angle_range / 32768.0
            result.roll = roll * factor
            result.pitch = pitch * factor
            result.yaw = yaw * factor
            
        elif frame_marker == 0x54:  # Magnetometer
            # WitMotion format: 3 int16 values for mx, my, mz
            mx, my, mz = struct.unpack('<hhh', data_bytes[0:6])
            
            # Magnetometer values already in proper units
            result.mag_x = mx
            result.mag_y = my
            result.mag_z = mz
        
        return result
    
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
# 1. Add support for more data types: Add new frame markers in self.frame_markers and handle them in _decode_packet()
# 2. Add support for different WitMotion models: Adjust the parsing logic in _decode_packet() for different data formats
# 3. Add calibration support: Implement methods to calibrate sensor data based on reference measurements
# File: src/io/readers/serial_reader.py
# Purpose: Read data from serial ports
# Target Lines: ≤150

"""
Methods to implement:
- __init__(self, config): Initialize with configuration
- open(self): Open the serial port
- read(self): Read data from the serial port
- close(self): Close the serial port
- get_status(self): Get current status of the reader
"""

import logging
import time
from src.io.readers.base_reader import BaseReader

# Use try/except for pyserial import to handle cases where it's not installed
try:
    import serial
    import serial.tools.list_ports
    SERIAL_AVAILABLE = True
except ImportError:
    SERIAL_AVAILABLE = False


class SerialReader(BaseReader):
    """
    Reader for serial port data sources.
    
    Reads data from serial ports (USB, COM ports, etc.)
    """
    
    def __init__(self, config):
        """
        Initialize the serial reader with configuration.
        
        Args:
            config (dict): Configuration dictionary for the serial reader
                - port (str): Serial port name (e.g., 'COM3', '/dev/ttyUSB0')
                - baudrate (int): Baud rate (e.g., 9600, 115200)
                - timeout (float): Read timeout in seconds
                - bytesize (int): Byte size (5-8)
                - parity (str): Parity ('N', 'E', 'O', 'M', 'S')
                - stopbits (float): Stop bits (1, 1.5, 2)
        """
        super().__init__(config)
        
        if not SERIAL_AVAILABLE:
            self.set_error("pyserial module not available. Install with 'pip install pyserial'")
            return
        
        # Extract configuration
        self.port = config.get('port')
        self.baudrate = config.get('baudrate', 9600)
        self.timeout = config.get('timeout', 1.0)
        self.bytesize = config.get('bytesize', serial.EIGHTBITS)
        self.parity = config.get('parity', serial.PARITY_NONE)
        self.stopbits = config.get('stopbits', serial.STOPBITS_ONE)
        
        # Initialize serial handle
        self.serial = None
        self.bytes_read = 0
        self.read_count = 0
        
        # Validate configuration
        if not self.port:
            self.set_error("No port specified in configuration")
    
    def open(self):
        """
        Open the serial port for reading.
        
        Returns:
            bool: True if successful, False otherwise
            
        Raises:
            RuntimeError: If there's an error opening the serial port
        """
        if not SERIAL_AVAILABLE:
            self.set_error("pyserial module not available")
            raise RuntimeError("pyserial module not available")
        
        if self.is_open:
            self.logger.warning(f"Serial port already open: {self.port}")
            return True
        
        try:
            # Open the serial port
            self.serial = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                bytesize=self.bytesize,
                parity=self.parity,
                stopbits=self.stopbits,
                timeout=self.timeout
            )
            
            # Wait for port to open
            time.sleep(0.1)
            self.is_open = True
            
            # Update metadata
            self.metadata = {
                'port': self.port,
                'baudrate': self.baudrate,
                'bytesize': self.bytesize,
                'parity': self.parity,
                'stopbits': self.stopbits,
                'timeout': self.timeout
            }
            
            self.logger.info(f"Opened serial port: {self.port} at {self.baudrate} baud")
            self.clear_error()
            return True
            
        except Exception as e:
            self.set_error(f"Error opening serial port: {str(e)}")
            raise RuntimeError(f"Error opening serial port {self.port}: {str(e)}")
    
    def read(self):
        """
        Read data from the serial port.
        
        Returns:
            bytes: Data read from the serial port
            
        Raises:
            RuntimeError: If there's an error reading from the serial port
            IOError: If the serial port is not open
        """
        super().read()  # This will raise if not open
        
        try:
            if self.serial.in_waiting > 0:
                # Read available data
                data = self.serial.read(self.serial.in_waiting)
                
                # Update stats
                self.bytes_read += len(data)
                self.read_count += 1
                
                return data
            else:
                # Read with timeout
                data = self.serial.read(1)
                if data:
                    # Update stats
                    self.bytes_read += len(data)
                    self.read_count += 1
                    
                    return data
                return None
            
        except Exception as e:
            self.set_error(f"Error reading serial port: {str(e)}")
            raise RuntimeError(f"Error reading serial port {self.port}: {str(e)}")
    
    def close(self):
        """
        Close the serial port.
        
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.is_open:
            return True
        
        try:
            if self.serial:
                self.serial.close()
                self.serial = None
            
            self.is_open = False
            self.logger.info(f"Closed serial port: {self.port}")
            return True
            
        except Exception as e:
            self.set_error(f"Error closing serial port: {str(e)}")
            return False
    
    def get_status(self):
        """
        Get the current status of the serial reader.
        
        Returns:
            dict: Status information including base reader status and:
                - port (str): Serial port name
                - baudrate (int): Baud rate
                - bytes_read (int): Total bytes read
                - read_count (int): Total number of read operations
        """
        status = super().get_status()
        
        # Add serial-specific status
        status.update({
            'port': self.port,
            'baudrate': self.baudrate,
            'bytes_read': self.bytes_read,
            'read_count': self.read_count
        })
        
        return status

    @staticmethod
    def list_ports():
        """
        List available serial ports.
        
        Returns:
            list: List of available serial ports
        """
        if not SERIAL_AVAILABLE:
            return []
        
        try:
            ports = []
            for port in serial.tools.list_ports.comports():
                ports.append({
                    'device': port.device,
                    'description': port.description,
                    'hwid': port.hwid
                })
            return ports
        except Exception:
            return []


# How to extend and modify:
# 1. Add data buffering: Add a buffer to collect data until a complete message is received
# 2. Add line reading mode: Add a read_line() method to read until newline character
# 3. Add data validation: Add check_data_validity() method to validate received data
# 4. Add automatic port detection: Extend to auto-detect the correct port based on device ID
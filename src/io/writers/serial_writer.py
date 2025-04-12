# File: src/io/writers/serial_writer.py
# Purpose: Write data to serial ports
# Target Lines: ≤150

"""
Methods to implement:
- __init__(self, config): Initialize with configuration
- open(self): Open the serial port
- write(self, data): Write data to the serial port
- close(self): Close the serial port
- get_status(self): Get current status of the writer
"""

import logging
import time
from src.io.writers.base_writer import BaseWriter

# Use try/except for pyserial import to handle cases where it's not installed
try:
    import serial
    import serial.tools.list_ports
    SERIAL_AVAILABLE = True
except ImportError:
    SERIAL_AVAILABLE = False


class SerialWriter(BaseWriter):
    """
    Writer for serial port data destinations.
    
    Writes data to serial ports (USB, COM ports, etc.)
    """
    
    def __init__(self, config):
        """
        Initialize the serial writer with configuration.
        
        Args:
            config (dict): Configuration dictionary for the serial writer
                - port (str): Serial port name (e.g., 'COM3', '/dev/ttyUSB0')
                - baudrate (int): Baud rate (e.g., 9600, 115200)
                - bytesize (int): Byte size (5-8)
                - parity (str): Parity ('N', 'E', 'O', 'M', 'S')
                - stopbits (float): Stop bits (1, 1.5, 2)
                - write_timeout (float): Write timeout in seconds
                - terminator (str): Line terminator for string data
        """
        super().__init__(config)
        
        if not SERIAL_AVAILABLE:
            self.set_error("pyserial module not available. Install with 'pip install pyserial'")
            return
        
        # Extract configuration
        self.port = config.get('port')
        self.baudrate = config.get('baudrate', 9600)
        self.bytesize = config.get('bytesize', serial.EIGHTBITS)
        self.parity = config.get('parity', serial.PARITY_NONE)
        self.stopbits = config.get('stopbits', serial.STOPBITS_ONE)
        self.write_timeout = config.get('write_timeout', 1.0)
        self.terminator = config.get('terminator', '\n')
        
        # Initialize serial handle
        self.serial = None
        
        # Validate configuration
        if not self.port:
            self.set_error("No port specified in configuration")
    
    def open(self):
        """
        Open the serial port for writing.
        
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
                timeout=None,  # No read timeout needed for writer
                write_timeout=self.write_timeout
            )
            
            # Wait for port to open
            time.sleep(0.1)
            self.is_open = True
            self.logger.info(f"Opened serial port for writing: {self.port} at {self.baudrate} baud")
            self.clear_error()
            return True
            
        except Exception as e:
            self.set_error(f"Error opening serial port: {str(e)}")
            raise RuntimeError(f"Error opening serial port {self.port}: {str(e)}")
    
    def write(self, data):
        """
        Write data to the serial port.
        
        Args:
            data (bytes, str, dict): Data to write to the serial port
            
        Returns:
            int: Number of bytes written
            
        Raises:
            RuntimeError: If there's an error writing to the serial port
            IOError: If the serial port is not open
        """
        super().write(data)  # This will raise if not open
        
        try:
            bytes_written = 0
            
            # Convert data to appropriate format
            if isinstance(data, str):
                # Add terminator if not present and convert to bytes
                if not data.endswith(self.terminator):
                    data += self.terminator
                bytes_data = data.encode('utf-8')
                bytes_written = self.serial.write(bytes_data)
                
            elif isinstance(data, dict):
                # Convert dict to string, add terminator, and convert to bytes
                str_data = str(data)
                if not str_data.endswith(self.terminator):
                    str_data += self.terminator
                bytes_data = str_data.encode('utf-8')
                bytes_written = self.serial.write(bytes_data)
                
            elif isinstance(data, bytes):
                # Write bytes directly
                bytes_written = self.serial.write(data)
                
            else:
                # Convert to string, add terminator, and convert to bytes
                str_data = str(data)
                if not str_data.endswith(self.terminator):
                    str_data += self.terminator
                bytes_data = str_data.encode('utf-8')
                bytes_written = self.serial.write(bytes_data)
            
            # Update stats
            self.update_stats(bytes_written)
            
            return bytes_written
            
        except Exception as e:
            self.set_error(f"Error writing to serial port: {str(e)}")
            raise RuntimeError(f"Error writing to serial port {self.port}: {str(e)}")
    
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
        Get the current status of the serial writer.
        
        Returns:
            dict: Status information including base writer status and serial-specific info
        """
        status = super().get_status()
        
        # Add serial-specific status
        status.update({
            'port': self.port,
            'baudrate': self.baudrate
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
# 1. Add data buffering: Add a buffer to collect data and send in larger chunks
# 2. Add data formatting: Add methods to format data in specific protocols
# 3. Add flow control: Add support for hardware and software flow control
# 4. Add command mode: Add methods to switch between command and data modes
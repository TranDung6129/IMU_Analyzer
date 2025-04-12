# File: src/io/writers/bluetooth_writer.py
# Purpose: Write data to Bluetooth devices
# Target Lines: ≤150

"""
Methods to implement:
- __init__(self, config): Initialize with configuration
- open(self): Open the Bluetooth connection
- write(self, data): Write data to the Bluetooth device
- close(self): Close the Bluetooth connection
- get_status(self): Get current status of the writer
"""

import logging
import time
from src.io.writers.base_writer import BaseWriter

# Use try/except for PyBluez import to handle cases where it's not installed
try:
    import bluetooth
    BLUETOOTH_AVAILABLE = True
except ImportError:
    BLUETOOTH_AVAILABLE = False


class BluetoothWriter(BaseWriter):
    """
    Writer for Bluetooth data destinations.
    
    Writes data to Bluetooth devices, especially useful for wireless IMUs.
    """
    
    def __init__(self, config):
        """
        Initialize the Bluetooth writer with configuration.
        
        Args:
            config (dict): Configuration dictionary for the Bluetooth writer
                - device (str): Bluetooth device name or MAC address
                - port (int): Bluetooth port/channel (default: 1)
                - terminator (str): Line terminator for string data
                - retry_count (int): Number of retries for connection
                - retry_delay (float): Delay between retries in seconds
        """
        super().__init__(config)
        
        if not BLUETOOTH_AVAILABLE:
            self.set_error("PyBluez module not available. Install with 'pip install pybluez'")
            return
        
        # Extract configuration
        self.device = config.get('device')
        self.port = config.get('port', 1)
        self.terminator = config.get('terminator', '\n')
        self.retry_count = config.get('retry_count', 3)
        self.retry_delay = config.get('retry_delay', 1.0)
        
        # Initialize socket
        self.socket = None
        self.device_address = None
        
        # Validate configuration
        if not self.device:
            self.set_error("No device specified in configuration")
    
    def open(self):
        """
        Open the Bluetooth connection for writing.
        
        Returns:
            bool: True if successful, False otherwise
            
        Raises:
            RuntimeError: If there's an error opening the Bluetooth connection
        """
        if not BLUETOOTH_AVAILABLE:
            self.set_error("PyBluez module not available")
            raise RuntimeError("PyBluez module not available")
        
        if self.is_open:
            self.logger.warning(f"Bluetooth connection already open: {self.device}")
            return True
        
        retry = 0
        last_error = None
        
        while retry <= self.retry_count:
            try:
                # Find the device address if a name was provided
                if not self._is_mac_address(self.device):
                    self.logger.info(f"Searching for Bluetooth device: {self.device}")
                    
                    # Discover devices
                    nearby_devices = bluetooth.discover_devices(lookup_names=True)
                    device_found = False
                    
                    for addr, name in nearby_devices:
                        if name == self.device:
                            self.device_address = addr
                            device_found = True
                            self.logger.info(f"Found device {self.device} at address {addr}")
                            break
                    
                    if not device_found:
                        raise RuntimeError(f"Bluetooth device {self.device} not found")
                else:
                    # Device address was provided directly
                    self.device_address = self.device
                
                # Create socket and connect
                self.socket = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
                self.socket.connect((self.device_address, self.port))
                
                self.is_open = True
                self.logger.info(f"Connected to Bluetooth device: {self.device}")
                self.clear_error()
                return True
                
            except Exception as e:
                last_error = str(e)
                retry += 1
                
                if retry <= self.retry_count:
                    self.logger.warning(f"Connection attempt {retry} failed: {last_error}. Retrying in {self.retry_delay} seconds...")
                    time.sleep(self.retry_delay)
                else:
                    break
        
        # All retries failed
        self.set_error(f"Error connecting to Bluetooth device after {self.retry_count} attempts: {last_error}")
        raise RuntimeError(f"Error connecting to Bluetooth device {self.device}: {last_error}")
    
    def write(self, data):
        """
        Write data to the Bluetooth device.
        
        Args:
            data (bytes, str, dict): Data to write to the Bluetooth device
            
        Returns:
            int: Number of bytes written
            
        Raises:
            RuntimeError: If there's an error writing to the Bluetooth device
            IOError: If the Bluetooth connection is not open
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
                bytes_written = self.socket.send(bytes_data)
                
            elif isinstance(data, dict):
                # Convert dict to string, add terminator, and convert to bytes
                str_data = str(data)
                if not str_data.endswith(self.terminator):
                    str_data += self.terminator
                bytes_data = str_data.encode('utf-8')
                bytes_written = self.socket.send(bytes_data)
                
            elif isinstance(data, bytes):
                # Write bytes directly
                bytes_written = self.socket.send(data)
                
            else:
                # Convert to string, add terminator, and convert to bytes
                str_data = str(data)
                if not str_data.endswith(self.terminator):
                    str_data += self.terminator
                bytes_data = str_data.encode('utf-8')
                bytes_written = self.socket.send(bytes_data)
            
            # Update stats
            self.update_stats(bytes_written)
            
            return bytes_written
            
        except Exception as e:
            self.set_error(f"Error writing to Bluetooth device: {str(e)}")
            raise RuntimeError(f"Error writing to Bluetooth device {self.device}: {str(e)}")
    
    def close(self):
        """
        Close the Bluetooth connection.
        
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.is_open:
            return True
        
        try:
            if self.socket:
                self.socket.close()
                self.socket = None
            
            self.is_open = False
            self.logger.info(f"Closed Bluetooth connection: {self.device}")
            return True
            
        except Exception as e:
            self.set_error(f"Error closing Bluetooth connection: {str(e)}")
            return False
    
    def get_status(self):
        """
        Get the current status of the Bluetooth writer.
        
        Returns:
            dict: Status information including base writer status and Bluetooth-specific info
        """
        status = super().get_status()
        
        # Add Bluetooth-specific status
        status.update({
            'device': self.device,
            'address': self.device_address,
            'port': self.port
        })
        
        return status
    
    def _is_mac_address(self, text):
        """
        Check if the provided string is a MAC address.
        
        Args:
            text (str): String to check
            
        Returns:
            bool: True if it's a MAC address, False otherwise
        """
        # Simple check - MAC addresses are usually in the format XX:XX:XX:XX:XX:XX
        if not text:
            return False
            
        parts = text.split(':')
        if len(parts) != 6:
            return False
            
        for part in parts:
            if len(part) != 2:
                return False
                
            try:
                int(part, 16)
            except ValueError:
                return False
                
        return True


# How to extend and modify:
# 1. Add support for Bluetooth Low Energy (BLE): Create a new BLEWriter class
# 2. Add command protocol: Add methods to format and send specific commands
# 3. Add data buffering: Add a buffer to collect data and send in larger chunks
# 4. Add GATT characteristics support: Add methods to write to specific characteristics for BLE
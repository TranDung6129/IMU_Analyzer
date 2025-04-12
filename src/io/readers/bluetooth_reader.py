# File: src/io/readers/bluetooth_reader.py
# Purpose: Read data from Bluetooth devices
# Target Lines: ≤150

"""
Methods to implement:
- __init__(self, config): Initialize with configuration
- open(self): Open the Bluetooth connection
- read(self): Read data from the Bluetooth device
- close(self): Close the Bluetooth connection
- get_status(self): Get current status of the reader
"""

import logging
import time
from src.io.readers.base_reader import BaseReader

# Use try/except for PyBluez import to handle cases where it's not installed
try:
    import bluetooth
    BLUETOOTH_AVAILABLE = True
except ImportError:
    BLUETOOTH_AVAILABLE = False


class BluetoothReader(BaseReader):
    """
    Reader for Bluetooth data sources.
    
    Reads data from Bluetooth devices, especially useful for wireless IMUs.
    """
    
    def __init__(self, config):
        """
        Initialize the Bluetooth reader with configuration.
        
        Args:
            config (dict): Configuration dictionary for the Bluetooth reader
                - device (str): Bluetooth device name or MAC address
                - port (int): Bluetooth port/channel (default: 1)
                - timeout (float): Read timeout in seconds
                - buffer_size (int): Buffer size for reading
        """
        super().__init__(config)
        
        if not BLUETOOTH_AVAILABLE:
            self.set_error("PyBluez module not available. Install with 'pip install pybluez'")
            return
        
        # Extract configuration
        self.device = config.get('device')
        self.port = config.get('port', 1)
        self.timeout = config.get('timeout', 2.0)
        self.buffer_size = config.get('buffer_size', 1024)
        
        # Initialize socket
        self.socket = None
        self.device_address = None
        self.bytes_read = 0
        self.read_count = 0
        
        # Validate configuration
        if not self.device:
            self.set_error("No device specified in configuration")
    
    def open(self):
        """
        Open the Bluetooth connection for reading.
        
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
                    self.set_error(f"Bluetooth device {self.device} not found")
                    raise RuntimeError(f"Bluetooth device {self.device} not found")
            else:
                # Device address was provided directly
                self.device_address = self.device
            
            # Create socket and connect
            self.socket = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
            self.socket.settimeout(self.timeout)
            self.socket.connect((self.device_address, self.port))
            
            self.is_open = True
            
            # Update metadata
            self.metadata = {
                'device': self.device,
                'address': self.device_address,
                'port': self.port
            }
            
            self.logger.info(f"Connected to Bluetooth device: {self.device}")
            self.clear_error()
            return True
            
        except Exception as e:
            self.set_error(f"Error connecting to Bluetooth device: {str(e)}")
            raise RuntimeError(f"Error connecting to Bluetooth device {self.device}: {str(e)}")
    
    def read(self):
        """
        Read data from the Bluetooth device.
        
        Returns:
            bytes: Data read from the Bluetooth device
            
        Raises:
            RuntimeError: If there's an error reading from the Bluetooth device
            IOError: If the Bluetooth connection is not open
        """
        super().read()  # This will raise if not open
        
        try:
            # Read data with timeout
            data = self.socket.recv(self.buffer_size)
            
            if data:
                # Update stats
                self.bytes_read += len(data)
                self.read_count += 1
                
                return data
            return None
            
        except bluetooth.btcommon.BluetoothError as e:
            if str(e) == "timed out":
                # Timeout is not an error, just return None
                return None
            self.set_error(f"Error reading from Bluetooth device: {str(e)}")
            raise RuntimeError(f"Error reading from Bluetooth device {self.device}: {str(e)}")
        except Exception as e:
            self.set_error(f"Error reading from Bluetooth device: {str(e)}")
            raise RuntimeError(f"Error reading from Bluetooth device {self.device}: {str(e)}")
    
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
        Get the current status of the Bluetooth reader.
        
        Returns:
            dict: Status information including base reader status and:
                - device (str): Bluetooth device name
                - address (str): Bluetooth MAC address
                - bytes_read (int): Total bytes read
                - read_count (int): Total number of read operations
        """
        status = super().get_status()
        
        # Add Bluetooth-specific status
        status.update({
            'device': self.device,
            'address': self.device_address,
            'bytes_read': self.bytes_read,
            'read_count': self.read_count
        })
        
        return status
    
    @staticmethod
    def list_devices():
        """
        List available Bluetooth devices.
        
        Returns:
            list: List of available Bluetooth devices (name, address)
        """
        if not BLUETOOTH_AVAILABLE:
            return []
        
        try:
            devices = []
            nearby_devices = bluetooth.discover_devices(lookup_names=True)
            
            for addr, name in nearby_devices:
                devices.append({
                    'name': name,
                    'address': addr
                })
            
            return devices
        except Exception:
            return []
    
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
# 1. Add support for Bluetooth Low Energy (BLE): Create a new BLEReader class
# 2. Add service and characteristic discovery: Add methods to discover available services
# 3. Add pairing functionality: Add methods to handle device pairing
# 4. Add GATT profile support: Add methods to work with GATT profiles for BLE devices
# File: src/system/configurators/witmotion_configurator.py
# Purpose: Configurator for WitMotion IMU sensors
# Target Lines: ≤150

"""
Methods to implement:
- __init__(self, config): Initialize with configuration
- configure(): Send configuration to the WitMotion sensor
- reset(): Reset WitMotion sensor to default settings
- _parse_init_sequence(): Convert hex strings to bytes
- _send_command(command): Send command bytes to sensor
"""

import serial
import time
import logging
from src.plugins.configurators.base_configurator import BaseConfigurator


class WitMotionConfigurator(BaseConfigurator):
    """
    Configurator for WitMotion IMU sensors.
    
    Handles sending configuration commands to WitMotion sensors via serial port.
    """
    
    def __init__(self, config):
        """
        Initialize the WitMotion configurator with configuration.
        
        Args:
            config (dict): Configuration dictionary containing:
                - port (str): Serial port (e.g., "COM3")
                - baudrate (int): Baud rate (default: 9600)
                - timeout (float): Serial timeout in seconds (default: 1.0)
                - init_sequence (list): List of hex strings to send during configuration
        """
        super().__init__(config)
        self.port = config.get("port")
        self.baudrate = config.get("baudrate", 9600)
        self.timeout = config.get("timeout", 1.0)
        self.init_sequence = config.get("init_sequence", [])
        self.serial_conn = None
    
    def configure(self):
        """
        Send configuration commands to the WitMotion sensor.
        
        Returns:
            bool: True if successful, False otherwise
            
        Raises:
            RuntimeError: If there's an error configuring the sensor
        """
        if not self.port:
            self.set_error("No port specified in configuration")
            return False
        
        try:
            # Open serial connection
            self.serial_conn = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=self.timeout
            )
            
            # Send initialization sequence
            for cmd in self.init_sequence:
                command_bytes = self._parse_init_sequence(cmd)
                self._send_command(command_bytes)
                time.sleep(0.1)  # Small delay between commands
            
            # Set configured flag
            self.is_configured = True
            self.clear_error()
            self.logger.info(f"WitMotion sensor on {self.port} configured successfully")
            return True
            
        except serial.SerialException as e:
            self.set_error(f"Serial error: {str(e)}")
            return False
        except Exception as e:
            self.set_error(f"Configuration error: {str(e)}")
            return False
        finally:
            # Close serial connection if open
            if self.serial_conn and self.serial_conn.is_open:
                self.serial_conn.close()
                self.serial_conn = None
    
    def reset(self):
        """
        Reset the WitMotion sensor to default settings.
        
        Returns:
            bool: True if successful, False otherwise
            
        Raises:
            RuntimeError: If there's an error resetting the sensor
        """
        try:
            # Open serial connection
            self.serial_conn = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=self.timeout
            )
            
            # Send reset command (FF AA 00 for WitMotion)
            self._send_command(b'\xFF\xAA\x00')
            
            self.is_configured = False
            self.clear_error()
            self.logger.info(f"WitMotion sensor on {self.port} reset successfully")
            return True
            
        except serial.SerialException as e:
            self.set_error(f"Serial error: {str(e)}")
            return False
        except Exception as e:
            self.set_error(f"Reset error: {str(e)}")
            return False
        finally:
            # Close serial connection if open
            if self.serial_conn and self.serial_conn.is_open:
                self.serial_conn.close()
                self.serial_conn = None
    
    def _parse_init_sequence(self, hex_string):
        """
        Convert a hex string to bytes.
        
        Args:
            hex_string (str): Hex string (e.g., "FF AA 69")
            
        Returns:
            bytes: Parsed bytes
        """
        # Remove spaces and convert to bytes
        clean_hex = hex_string.replace(" ", "")
        return bytes.fromhex(clean_hex)
    
    def _send_command(self, command):
        """
        Send command bytes to the sensor.
        
        Args:
            command (bytes): Command to send
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.serial_conn or not self.serial_conn.is_open:
            self.set_error("Serial connection not open")
            return False
        
        try:
            bytes_written = self.serial_conn.write(command)
            self.logger.debug(f"Sent command: {command.hex(' ').upper()}, {bytes_written} bytes written")
            return True
        except Exception as e:
            self.set_error(f"Error sending command: {str(e)}")
            return False


# How to extend and modify:
# 1. Add support for advanced configurations: Adding methods for configuring specific WitMotion settings
# 2. Add response handling: Parse and validate responses from the sensor
# 3. Add automatic detection: Detect WitMotion sensors and their settings automatically
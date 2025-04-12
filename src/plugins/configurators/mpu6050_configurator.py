# File: src/plugins/configurators/mpu6050_configurator.py
# Purpose: Configurator for MPU6050 IMU sensors
# Target Lines: ≤150

"""
Methods to implement:
- __init__(self, config): Initialize with configuration
- configure(): Send configuration to the MPU6050 sensor
- reset(): Reset MPU6050 sensor to default settings
- _send_register(register, value): Send register/value pair to sensor
"""

import serial
import time
import logging
from src.plugins.configurators.base_configurator import BaseConfigurator

class MPU6050Configurator(BaseConfigurator):
    """
    Configurator for MPU6050 IMU sensors.
    
    Handles sending configuration commands to MPU6050 sensors via I2C or Serial adapter.
    """
    
    # MPU6050 register addresses
    PWR_MGMT_1 = 0x6B
    GYRO_CONFIG = 0x1B
    ACCEL_CONFIG = 0x1C
    SMPLRT_DIV = 0x19
    CONFIG = 0x1A
    
    def __init__(self, config):
        """
        Initialize the MPU6050 configurator with configuration.
        
        Args:
            config (dict): Configuration dictionary containing:
                - interface (str): "i2c" or "serial"
                - address (int): I2C address (default: 0x68) or serial port (e.g., "COM3")
                - baudrate (int): Baud rate for serial interface (default: 9600)
                - timeout (float): Serial timeout in seconds (default: 1.0)
                - gyro_range (int): Gyroscope range (0-3, default: 0)
                - accel_range (int): Accelerometer range (0-3, default: 0)
                - sample_rate (int): Sample rate divider (0-255, default: 0)
        """
        super().__init__(config)
        self.interface = config.get("interface", "i2c")
        self.address = config.get("address", 0x68 if self.interface == "i2c" else "COM3")
        self.baudrate = config.get("baudrate", 9600) if self.interface == "serial" else None
        self.timeout = config.get("timeout", 1.0) if self.interface == "serial" else None
        
        # Configuration values
        self.gyro_range = config.get("gyro_range", 0)  # 0: ±250°/s, 1: ±500°/s, 2: ±1000°/s, 3: ±2000°/s
        self.accel_range = config.get("accel_range", 0)  # 0: ±2g, 1: ±4g, 2: ±8g, 3: ±16g
        self.sample_rate = config.get("sample_rate", 0)  # Sample Rate = 8kHz / (1 + sample_rate)
        
        # Communication handle
        self.i2c_bus = None
        self.serial_conn = None
    
    def configure(self):
        """
        Send configuration commands to the MPU6050 sensor.
        
        Returns:
            bool: True if successful, False otherwise
            
        Raises:
            RuntimeError: If there's an error configuring the sensor
        """
        try:
            # Open communication interface
            if self.interface == "i2c":
                self._open_i2c()
            else:  # serial
                self._open_serial()
            
            # Reset device first
            self._send_register(self.PWR_MGMT_1, 0x80)  # Reset MPU6050
            time.sleep(0.1)
            
            # Wake up device
            self._send_register(self.PWR_MGMT_1, 0x00)  # Wake up
            time.sleep(0.01)
            
            # Configure gyroscope range
            self._send_register(self.GYRO_CONFIG, self.gyro_range << 3)
            
            # Configure accelerometer range
            self._send_register(self.ACCEL_CONFIG, self.accel_range << 3)
            
            # Configure sample rate
            self._send_register(self.SMPLRT_DIV, self.sample_rate)
            
            # Configure DLPF
            self._send_register(self.CONFIG, 0x03)  # DLPF_CFG = 3: 44Hz Gyro, 42Hz Accel
            
            # Set configured flag
            self.is_configured = True
            self.clear_error()
            self.logger.info(f"MPU6050 sensor configured successfully via {self.interface}")
            return True
            
        except Exception as e:
            self.set_error(f"Configuration error: {str(e)}")
            return False
        finally:
            # Close communication interface
            self._close_interface()
    
    def reset(self):
        """
        Reset the MPU6050 sensor to default settings.
        
        Returns:
            bool: True if successful, False otherwise
            
        Raises:
            RuntimeError: If there's an error resetting the sensor
        """
        try:
            # Open communication interface
            if self.interface == "i2c":
                self._open_i2c()
            else:  # serial
                self._open_serial()
            
            # Reset device
            self._send_register(self.PWR_MGMT_1, 0x80)  # Reset MPU6050
            time.sleep(0.1)
            
            self.is_configured = False
            self.clear_error()
            self.logger.info(f"MPU6050 sensor reset successfully via {self.interface}")
            return True
            
        except Exception as e:
            self.set_error(f"Reset error: {str(e)}")
            return False
        finally:
            # Close communication interface
            self._close_interface()
    
    def _open_i2c(self):
        """Open I2C communication interface."""
        try:
            # For now, let's assume SMBus is available
            # This would need to be adjusted based on the actual I2C library used
            import smbus
            self.i2c_bus = smbus.SMBus(1)  # 1 indicates /dev/i2c-1
            self.logger.debug(f"Opened I2C interface to MPU6050 at address 0x{self.address:02X}")
        except ImportError:
            raise RuntimeError("smbus module not available for I2C communication")
        except Exception as e:
            raise RuntimeError(f"Failed to open I2C interface: {str(e)}")
    
    def _open_serial(self):
        """Open serial communication interface."""
        try:
            self.serial_conn = serial.Serial(
                port=self.address,
                baudrate=self.baudrate,
                timeout=self.timeout
            )
            self.logger.debug(f"Opened serial interface to MPU6050 at {self.address}")
        except Exception as e:
            raise RuntimeError(f"Failed to open serial interface: {str(e)}")
    
    def _send_register(self, register, value):
        """
        Send a register/value pair to the sensor.
        
        Args:
            register (int): Register address
            value (int): Value to write
            
        Raises:
            RuntimeError: If communication fails
        """
        try:
            if self.interface == "i2c" and self.i2c_bus:
                self.i2c_bus.write_byte_data(self.address, register, value)
            elif self.interface == "serial" and self.serial_conn:
                # Simple protocol: first byte is register, second is value
                # This would need to be adjusted based on the actual protocol used by the serial adapter
                command = bytes([register, value])
                self.serial_conn.write(command)
            else:
                raise RuntimeError("No communication interface open")
                
            self.logger.debug(f"Sent register 0x{register:02X} = 0x{value:02X}")
        except Exception as e:
            raise RuntimeError(f"Failed to send register: {str(e)}")
    
    def _close_interface(self):
        """Close the communication interface."""
        if self.interface == "i2c" and self.i2c_bus:
            # SMBus doesn't have a close method, but if using another I2C library, close here
            self.i2c_bus = None
        elif self.interface == "serial" and self.serial_conn:
            if self.serial_conn.is_open:
                self.serial_conn.close()
            self.serial_conn = None


# How to extend and modify:
# 1. Add more configuration options: Add methods to configure additional MPU6050 registers
# 2. Add data reading functionality: Add methods to read data from the sensor for testing
# 3. Add more interface types: Support additional interfaces like SPI
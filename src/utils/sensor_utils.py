# File: src/utils/sensor_utils.py
# Purpose: Sensor management utilities
# Target Lines: ≤150

"""
Methods to implement:
- scan_serial_ports(): Scan for available serial ports
- scan_bluetooth_devices(): Scan for available Bluetooth devices
- assign_sensor_id(sensor_config): Generate a unique ID for a sensor
"""

import logging
import random
import string
import uuid


def scan_serial_ports():
    """
    Scan for available serial ports on the system.
    
    Returns:
        list: List of available serial port names
    """
    ports = []
    
    try:
        import serial.tools.list_ports
        ports = [port.device for port in serial.tools.list_ports.comports()]
    except ImportError:
        logging.error("pyserial not installed, cannot scan serial ports")
    except Exception as e:
        logging.error(f"Error scanning serial ports: {str(e)}")
    
    return ports


def scan_bluetooth_devices():
    """
    Scan for available Bluetooth devices.
    
    Returns:
        list: List of (address, name) tuples for available Bluetooth devices
    """
    devices = []
    
    try:
        import bluetooth
        nearby_devices = bluetooth.discover_devices(lookup_names=True)
        devices = nearby_devices
    except ImportError:
        logging.error("pybluez not installed, cannot scan Bluetooth devices")
    except Exception as e:
        logging.error(f"Error scanning Bluetooth devices: {str(e)}")
    
    return devices


def assign_sensor_id(sensor_config):
    """
    Generate a unique ID for a sensor based on its configuration.
    
    Args:
        sensor_config (dict): Sensor configuration
        
    Returns:
        str: Unique sensor ID
    """
    # If sensor already has an ID, return it
    if 'id' in sensor_config and sensor_config['id']:
        return sensor_config['id']
    
    # Generate ID based on type and available identifiers
    sensor_type = sensor_config.get('type', 'unknown')
    
    # For serial devices, use port
    if sensor_type.lower() == 'serial' and 'port' in sensor_config:
        port = sensor_config['port'].replace('/', '_').replace('\\', '_')
        return f"serial_{port}"
    
    # For Bluetooth devices, use address
    elif sensor_type.lower() == 'bluetooth' and 'address' in sensor_config:
        address = sensor_config['address'].replace(':', '')
        return f"bt_{address}"
    
    # For file sources, use filename
    elif sensor_type.lower() == 'file' and 'file_path' in sensor_config:
        import os
        filename = os.path.basename(sensor_config['file_path'])
        return f"file_{filename}"
    
    # If no specific info available, generate random ID
    else:
        return f"{sensor_type}_{uuid.uuid4().hex[:8]}"


# Additional utility functions (not implemented yet, just signatures)

# TODO: Implement sensor validation function
# def validate_sensor_config(sensor_config):
#     pass

# TODO: Implement sensor health check
# def check_sensor_health(sensor_id, connection):
#     pass

# TODO: Implement sensor data rate estimation
# def estimate_data_rate(sensor_data, time_window=10.0):
#     pass

# How to extend and modify:
# 1. Add more sensor types: Add support for new sensor connection types
# 2. Add sensor auto-discovery: Add functionality to auto-discover sensors
# 3. Add sensor calibration: Add calibration utilities for different sensors
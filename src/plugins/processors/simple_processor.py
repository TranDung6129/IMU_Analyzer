# File: src/plugins/processors/simple_processor.py
# Purpose: Process decoded data with basic filters
# Target Lines: ≤150

"""
Methods to implement:
- __init__(self, config=None): Initialize with optional configuration
- init(self, config): Initialize or re-initialize with new configuration
- process(self, data): Process decoded data
- destroy(self): Clean up resources
"""

import logging
import numpy as np
from src.plugins.processors.base_processor import BaseProcessor
from src.data.models import ProcessedData


class SimpleProcessor(BaseProcessor):
    """
    Simple processor for basic data processing.
    
    Provides basic filtering (lowpass, highpass, none) and unit conversion.
    """
    
    def __init__(self, config=None):
        """
        Initialize the processor with optional configuration.
        
        Args:
            config (dict, optional): Configuration dictionary for the processor
        """
        super().__init__(config)
        
        # Initialize filter parameters
        self.filter_type = "none"
        self.cutoff_freq = 10.0  # Hz
        self.alpha = 0.0  # Filter coefficient (calculated in init)
        
        # Data buffers for filtering
        self.last_values = {}
        
        if config:
            self.init(config)
    
    def init(self, config):
        """
        Initialize or re-initialize the processor with the specified configuration.
        
        Args:
            config (dict): Configuration dictionary with the following options:
                - filter_type (str): Type of filter to apply ("lowpass", "highpass", "none")
                - cutoff_freq (float): Cutoff frequency in Hz
                - sample_rate (float, optional): Sample rate in Hz, defaults to 100Hz
                
        Returns:
            bool: True if successful, False otherwise
        """
        self.config = config
        
        # Get filter settings
        self.filter_type = config.get("filter_type", "none").lower()
        self.cutoff_freq = config.get("cutoff_freq", 10.0)
        sample_rate = config.get("sample_rate", 100.0)
        
        # Calculate filter coefficient for lowpass/highpass (RC filter approximation)
        if self.filter_type in ["lowpass", "highpass"]:
            dt = 1.0 / sample_rate
            rc = 1.0 / (2.0 * np.pi * self.cutoff_freq)
            self.alpha = dt / (dt + rc)
            
            # Log filter info
            self.logger.info(f"Initialized {self.filter_type} filter with cutoff: {self.cutoff_freq}Hz, alpha: {self.alpha}")
        
        # Reset filter state
        self.last_values = {}
        
        self.initialized = True
        return True
    
    def process(self, data):
        """
        Process decoded data.
        
        Applies configured filter to sensor data.
        
        Args:
            data (dict): Decoded data to process
            
        Returns:
            ProcessedData: Processed data object
            
        Raises:
            ValueError: If the data cannot be processed
        """
        if not self.initialized:
            raise RuntimeError("Processor not initialized")
        
        try:
            # If data is already a ProcessedData object, use it as is
            if isinstance(data, ProcessedData):
                processed_data = data
            else:
                # Create a new ProcessedData object
                processed_data = ProcessedData(
                    sensor_data_id=data.get("id", ""),
                    sensor_id=data.get("sensor_id", ""),
                    timestamp=data.get("timestamp", 0.0),
                    roll=data.get("roll", 0.0),
                    pitch=data.get("pitch", 0.0),
                    yaw=data.get("yaw", 0.0),
                    accel_x=data.get("accel_x", 0.0),
                    accel_y=data.get("accel_y", 0.0),
                    accel_z=data.get("accel_z", 0.0),
                    gyro_x=data.get("gyro_x", 0.0),
                    gyro_y=data.get("gyro_y", 0.0),
                    gyro_z=data.get("gyro_z", 0.0),
                    mag_x=data.get("mag_x", 0.0),
                    mag_y=data.get("mag_y", 0.0),
                    mag_z=data.get("mag_z", 0.0),
                    additional_values=data.get("additional_values", {}),
                    processing_metadata={"filter_type": self.filter_type, "cutoff_freq": self.cutoff_freq}
                )
            
            # Apply filtering if needed
            if self.filter_type == "lowpass":
                processed_data = self._apply_lowpass_filter(processed_data)
            elif self.filter_type == "highpass":
                processed_data = self._apply_highpass_filter(processed_data)
            
            self.process_count += 1
            return processed_data
            
        except Exception as e:
            self.set_error(f"Error processing data: {str(e)}")
            self.process_errors += 1
            raise ValueError(f"Could not process data: {str(e)}")
    
    def _apply_lowpass_filter(self, data):
        """
        Apply a simple low-pass filter to the data.
        
        Args:
            data (ProcessedData): Data to filter
            
        Returns:
            ProcessedData: Filtered data
        """
        sensor_id = data.sensor_id
        
        # Initialize last values for this sensor if not already
        if sensor_id not in self.last_values:
            self.last_values[sensor_id] = {
                "roll": data.roll, "pitch": data.pitch, "yaw": data.yaw,
                "accel_x": data.accel_x, "accel_y": data.accel_y, "accel_z": data.accel_z,
                "gyro_x": data.gyro_x, "gyro_y": data.gyro_y, "gyro_z": data.gyro_z
            }
            return data
        
        # Apply low-pass filter: y[n] = alpha * x[n] + (1 - alpha) * y[n-1]
        # Where y[n] is the filtered output and x[n] is the current input
        last = self.last_values[sensor_id]
        
        # Apply filter to each value
        data.roll = self.alpha * data.roll + (1 - self.alpha) * last["roll"]
        data.pitch = self.alpha * data.pitch + (1 - self.alpha) * last["pitch"]
        data.yaw = self.alpha * data.yaw + (1 - self.alpha) * last["yaw"]
        
        data.accel_x = self.alpha * data.accel_x + (1 - self.alpha) * last["accel_x"]
        data.accel_y = self.alpha * data.accel_y + (1 - self.alpha) * last["accel_y"]
        data.accel_z = self.alpha * data.accel_z + (1 - self.alpha) * last["accel_z"]
        
        data.gyro_x = self.alpha * data.gyro_x + (1 - self.alpha) * last["gyro_x"]
        data.gyro_y = self.alpha * data.gyro_y + (1 - self.alpha) * last["gyro_y"]
        data.gyro_z = self.alpha * data.gyro_z + (1 - self.alpha) * last["gyro_z"]
        
        # Update last values
        self.last_values[sensor_id] = {
            "roll": data.roll, "pitch": data.pitch, "yaw": data.yaw,
            "accel_x": data.accel_x, "accel_y": data.accel_y, "accel_z": data.accel_z,
            "gyro_x": data.gyro_x, "gyro_y": data.gyro_y, "gyro_z": data.gyro_z
        }
        
        return data
    
    def _apply_highpass_filter(self, data):
        """
        Apply a simple high-pass filter to the data.
        
        Args:
            data (ProcessedData): Data to filter
            
        Returns:
            ProcessedData: Filtered data
        """
        sensor_id = data.sensor_id
        
        # Initialize last values for this sensor if not already
        if sensor_id not in self.last_values:
            self.last_values[sensor_id] = {
                "roll": data.roll, "pitch": data.pitch, "yaw": data.yaw,
                "accel_x": data.accel_x, "accel_y": data.accel_y, "accel_z": data.accel_z,
                "gyro_x": data.gyro_x, "gyro_y": data.gyro_y, "gyro_z": data.gyro_z,
                "filtered_roll": 0, "filtered_pitch": 0, "filtered_yaw": 0,
                "filtered_accel_x": 0, "filtered_accel_y": 0, "filtered_accel_z": 0,
                "filtered_gyro_x": 0, "filtered_gyro_y": 0, "filtered_gyro_z": 0
            }
            return data
        
        # Apply high-pass filter: y[n] = alpha * (y[n-1] + x[n] - x[n-1])
        # Where y[n] is the filtered output and x[n] is the current input
        last = self.last_values[sensor_id]
        
        # Calculate filtered values
        filtered_roll = self.alpha * (last["filtered_roll"] + data.roll - last["roll"])
        filtered_pitch = self.alpha * (last["filtered_pitch"] + data.pitch - last["pitch"])
        filtered_yaw = self.alpha * (last["filtered_yaw"] + data.yaw - last["yaw"])
        
        filtered_accel_x = self.alpha * (last["filtered_accel_x"] + data.accel_x - last["accel_x"])
        filtered_accel_y = self.alpha * (last["filtered_accel_y"] + data.accel_y - last["accel_y"])
        filtered_accel_z = self.alpha * (last["filtered_accel_z"] + data.accel_z - last["accel_z"])
        
        filtered_gyro_x = self.alpha * (last["filtered_gyro_x"] + data.gyro_x - last["gyro_x"])
        filtered_gyro_y = self.alpha * (last["filtered_gyro_y"] + data.gyro_y - last["gyro_y"])
        filtered_gyro_z = self.alpha * (last["filtered_gyro_z"] + data.gyro_z - last["gyro_z"])
        
        # Update data with filtered values
        data.roll = filtered_roll
        data.pitch = filtered_pitch
        data.yaw = filtered_yaw
        
        data.accel_x = filtered_accel_x
        data.accel_y = filtered_accel_y
        data.accel_z = filtered_accel_z
        
        data.gyro_x = filtered_gyro_x
        data.gyro_y = filtered_gyro_y
        data.gyro_z = filtered_gyro_z
        
        # Update last values
        self.last_values[sensor_id] = {
            "roll": data.roll, "pitch": data.pitch, "yaw": data.yaw,
            "accel_x": data.accel_x, "accel_y": data.accel_y, "accel_z": data.accel_z,
            "gyro_x": data.gyro_x, "gyro_y": data.gyro_y, "gyro_z": data.gyro_z,
            "filtered_roll": filtered_roll, "filtered_pitch": filtered_pitch, "filtered_yaw": filtered_yaw,
            "filtered_accel_x": filtered_accel_x, "filtered_accel_y": filtered_accel_y, "filtered_accel_z": filtered_accel_z,
            "filtered_gyro_x": filtered_gyro_x, "filtered_gyro_y": filtered_gyro_y, "filtered_gyro_z": filtered_gyro_z
        }
        
        return data
    
    def destroy(self):
        """
        Clean up any resources used by the processor.
        
        Returns:
            bool: True if successful, False otherwise
        """
        # Clear filter state
        self.last_values = {}
        self.initialized = False
        return True


# How to extend and modify:
# 1. Add more filter types: Add new methods like _apply_kalman_filter() and update process() to use them
# 2. Add data normalization: Add methods to normalize or scale data values
# 3. Add unit conversion: Add methods to convert between different unit systems
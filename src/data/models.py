# File: src/data/models.py
# Purpose: Define data structures for the system
# Target Lines: ≤150

"""
Classes to implement:
- SensorData: Raw data from sensors
- ProcessedData: Processed data from raw sensor data
- AnalysisResult: Results from data analysis
"""

import time
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Union
import numpy as np


@dataclass
class SensorData:
    """
    Container for raw sensor data.
    
    Represents the raw, unprocessed data coming directly from sensors.
    Includes timestamp and sensor metadata.
    """
    # Unique ID for this data point
    id: str = field(default_factory=lambda: f"data_{time.time()}")
    
    # Sensor identification
    sensor_id: str = ""
    
    # Timestamp when data was collected (seconds since epoch)
    timestamp: float = field(default_factory=time.time)
    
    # Raw values from the sensor (can be bytes, string, or parsed values)
    raw_values: Any = None
    
    # Raw byte data if available
    raw_bytes: Optional[bytes] = None
    
    # Data format description (e.g., "csv", "binary", "json")
    format: str = "unknown"
    
    # Sensor metadata (additional information about the sensor)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __str__(self):
        """String representation of sensor data"""
        return f"SensorData(id={self.id}, sensor_id={self.sensor_id}, timestamp={self.timestamp}, format={self.format})"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        result = {
            "id": self.id,
            "sensor_id": self.sensor_id,
            "timestamp": self.timestamp,
            "format": self.format,
            "metadata": self.metadata
        }
        
        # Include raw_values if they are serializable
        if isinstance(self.raw_values, (dict, list, str, int, float, bool)) or self.raw_values is None:
            result["raw_values"] = self.raw_values
            
        return result


@dataclass
class ProcessedData:
    """
    Container for processed sensor data.
    
    Represents data after it has been decoded and processed,
    typically containing structured values like orientation and acceleration.
    """
    # Unique ID for this data point
    id: str = field(default_factory=lambda: f"proc_{time.time()}")
    
    # ID of the original sensor data
    sensor_data_id: str = ""
    
    # Sensor identification
    sensor_id: str = ""
    
    # Timestamp when data was collected (seconds since epoch)
    timestamp: float = field(default_factory=time.time)
    
    # Orientation values (in degrees)
    roll: float = 0.0
    pitch: float = 0.0
    yaw: float = 0.0
    
    # Acceleration values (in g, typically ±2g or ±4g)
    accel_x: float = 0.0
    accel_y: float = 0.0
    accel_z: float = 0.0
    
    # Gyroscope values (in degrees per second)
    gyro_x: float = 0.0
    gyro_y: float = 0.0
    gyro_z: float = 0.0
    
    # Magnetometer values (if available)
    mag_x: float = 0.0
    mag_y: float = 0.0
    mag_z: float = 0.0
    
    # Additional processed values (sensor-specific)
    additional_values: Dict[str, Any] = field(default_factory=dict)
    
    # Processing metadata (e.g., filter settings used)
    processing_metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __str__(self):
        """String representation of processed data"""
        return (f"ProcessedData(id={self.id}, sensor_id={self.sensor_id}, "
                f"timestamp={self.timestamp}, orientation=({self.roll}, {self.pitch}, {self.yaw}))")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "id": self.id,
            "sensor_data_id": self.sensor_data_id,
            "sensor_id": self.sensor_id,
            "timestamp": self.timestamp,
            "orientation": {
                "roll": self.roll,
                "pitch": self.pitch,
                "yaw": self.yaw
            },
            "acceleration": {
                "x": self.accel_x,
                "y": self.accel_y,
                "z": self.accel_z
            },
            "gyroscope": {
                "x": self.gyro_x,
                "y": self.gyro_y,
                "z": self.gyro_z
            },
            "magnetometer": {
                "x": self.mag_x,
                "y": self.mag_y,
                "z": self.mag_z
            },
            "additional_values": self.additional_values,
            "processing_metadata": self.processing_metadata
        }


@dataclass
class AnalysisResult:
    """
    Container for analysis results.
    
    Represents the results of data analysis, including anomaly detection,
    pattern recognition, or machine learning inference.
    """
    # Unique ID for this analysis result
    id: str = field(default_factory=lambda: f"analysis_{time.time()}")
    
    # ID of the processed data
    processed_data_id: str = ""
    
    # Sensor identification
    sensor_id: str = ""
    
    # Timestamp when analysis was performed
    timestamp: float = field(default_factory=time.time)
    
    # Anomaly detection score (0.0 to 1.0, higher means more anomalous)
    anomaly_score: float = 0.0
    
    # Prediction label (if applicable)
    prediction: Optional[str] = None
    
    # Prediction confidence (0.0 to 1.0)
    confidence: float = 0.0
    
    # Additional analysis results
    results: Dict[str, Any] = field(default_factory=dict)
    
    # Analysis metadata (e.g., model version, parameters)
    analysis_metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __str__(self):
        """String representation of analysis result"""
        result_str = f"AnalysisResult(id={self.id}, sensor_id={self.sensor_id}, timestamp={self.timestamp}"
        
        if self.anomaly_score > 0:
            result_str += f", anomaly_score={self.anomaly_score:.3f}"
            
        if self.prediction:
            result_str += f", prediction={self.prediction}, confidence={self.confidence:.3f}"
            
        result_str += ")"
        return result_str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "id": self.id,
            "processed_data_id": self.processed_data_id,
            "sensor_id": self.sensor_id,
            "timestamp": self.timestamp,
            "anomaly_score": self.anomaly_score,
            "prediction": self.prediction,
            "confidence": self.confidence,
            "results": self.results,
            "analysis_metadata": self.analysis_metadata
        }


# How to extend and modify:
# 1. Add new data classes: Create additional classes for specific data types
# 2. Add serialization methods: Add methods for JSON, CSV, or binary serialization
# 3. Add validation methods: Add methods to validate data integrity
# 4. Add transformation methods: Add methods to convert between different formats
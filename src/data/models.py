# src/data/models.py
from dataclasses import dataclass, field
from typing import Dict, Any, Optional
import time

@dataclass
class SensorData:
    """
    Standard data structure for sensor data after decoding.

    Attributes:
        timestamp (float): Normalized timestamp as UNIX timestamp (float seconds since epoch).
                         This is the main timestamp field used within the system.
        sensor_id (str): Unique identifier for the sensor or data source.
        data_type (str): Main data type (e.g., 'imu', 'gps', 'image', 'temperature').
        values (Dict[str, Any]): Dictionary containing the actual data values.
                               Keys are channel names (e.g., 'accX', 'gyroY', 'latitude').
                               Values are the corresponding values.
        raw_timestamp (Optional[Any]): Original timestamp from the sensor or data source (if available).
                                    Can be a string, integer, or datetime object.
                                    Useful for debugging or reference.
        units (Dict[str, str]): Dictionary containing units for each value in 'values'.
                             Keys match keys in 'values'.
                             Values are string representations of units (e.g., 'm/s²', 'deg/s', 'deg').
                             Important for consistent processing and display.
        metadata (Dict[str, Any]): (Optional) Dictionary containing additional metadata if needed.
    """
    timestamp: float
    sensor_id: str
    data_type: str
    values: Dict[str, Any] = field(default_factory=dict)
    raw_timestamp: Optional[Any] = None
    units: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict) 

    def __post_init__(self):
        # Perform basic validation or conversion after initialization
        # Example: ensure timestamp is a float
        if not isinstance(self.timestamp, float):
            try:
                # Try to convert timestamp to float
                self.timestamp = float(self.timestamp)
            except (ValueError, TypeError):
                print(f"Warning: Could not convert timestamp {self.timestamp} for sensor {self.sensor_id} to float. Using current time.")
                # Provide a default value or log a more serious error
                self.timestamp = time.time()

    def get_value(self, key: str, default: Any = None) -> Any:
        """Safely get a value from the 'values' field."""
        return self.values.get(key, default)

    def get_unit(self, key: str, default: str = "") -> str:
        """Get the unit for a specific value."""
        return self.units.get(key, default)
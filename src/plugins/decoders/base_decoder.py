# src/plugins/decoders/base_decoder.py
from abc import ABC, abstractmethod
from typing import Any, Generator, Dict
# Import the standard SensorData class
from src.data.models import SensorData

class IDecoder(ABC):
    """
    Interface for all data decoders.
    
    Decoders receive RAW data (bytes) from a Reader and convert it
    to structured data (SensorData objects).
    """
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the decoder with a specific configuration.
        
        Args:
            config: Dictionary containing configuration parameters
                  for this decoder (e.g., 'acc_range', 'gyro_range',
                                     'timestamp_mode', 'sensor_id').
        """
        self.config = config
        self.sensor_id = config.get('sensor_id', 'default_sensor')  # Get sensor_id from config
        print(f"Initializing {self.__class__.__name__} for sensor '{self.sensor_id}' with config: {config}")

    @abstractmethod
    def decode(self, raw_data: bytes) -> Generator[SensorData, None, None]:
        """
        Core method to decode raw data.
        
        This method MUST be implemented by subclasses.
        It receives a block of raw data (`raw_data`) from a Reader.
        The decoder may need to manage an internal buffer to handle
        incomplete packets from `raw_data`.
        
        It should return a generator (using `yield`). Each yield returns
        a fully decoded and normalized `SensorData` object.
        A block of `raw_data` may contain 0, 1, or multiple complete
        packets, so this generator may yield 0, 1, or multiple times
        per call.
        
        Args:
            raw_data: Raw data as bytes from a Reader
            
        Returns:
            Generator[SensorData, None, None]: A generator yielding SensorData objects
        """
        pass
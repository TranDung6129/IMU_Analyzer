# src/plugins/processors/simple_processor.py
import logging
from typing import Any, Generator, Dict, List, Optional
from src.plugins.processors.base_processor import IProcessor
from src.data.models import SensorData

logger = logging.getLogger(__name__)

class SimpleProcessor(IProcessor):
    """
    A simple processor that logs data to the console and performs basic operations.
    
    This processor can:
    1. Log data values to the console
    2. Filter data based on thresholds
    3. Apply simple scaling to values
    4. Pass through data without modifications
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the simple processor.
        
        Args:
            config: Dictionary containing configuration parameters:
                - channels (List[str], optional): List of channels to process (default: all)
                - log_level (str, optional): Logging level ('DEBUG', 'INFO', etc., default: 'INFO')
                - log_format (str, optional): Format for logging (default: simple format)
                - min_threshold (float, optional): Minimum threshold for values (below this, data is filtered out)
                - max_threshold (float, optional): Maximum threshold for values (above this, data is filtered out)
                - scale_factor (Dict[str, float], optional): Scaling factors for each channel
                - pass_through (bool, optional): If True, pass data through without modification (default: True)
        """
        super().__init__(config)
        
        # Optional parameters with defaults
        self.channels = config.get('channels', [])
        self.log_level = config.get('log_level', 'INFO')
        self.log_format = config.get('log_format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        self.min_threshold = config.get('min_threshold', float('-inf'))
        self.max_threshold = config.get('max_threshold', float('inf'))
        self.scale_factor = config.get('scale_factor', {})
        self.pass_through = config.get('pass_through', True)
        
        # Configure logging
        self._configure_logging()
        
        logger.info(f"SimpleProcessor initialized with channels: {self.channels or 'all'}")
    
    def _configure_logging(self):
        """Configure the logger for this processor."""
        numeric_level = getattr(logging, self.log_level.upper(), None)
        if not isinstance(numeric_level, int):
            numeric_level = logging.INFO
        
        # Configure the logger
        handler = logging.StreamHandler()
        formatter = logging.Formatter(self.log_format)
        handler.setFormatter(formatter)
        
        logger.setLevel(numeric_level)
        
        # Remove existing handlers to avoid duplicates
        for hdlr in logger.handlers:
            logger.removeHandler(hdlr)
        
        logger.addHandler(handler)
    
    def process(self, data: Any) -> Generator[Any, None, None]:
        """
        Process the input data.
        
        Args:
            data: Input data to process (expected to be a SensorData object)
            
        Yields:
            Processed data (modified SensorData or pass-through)
        """
        if not isinstance(data, SensorData):
            logger.warning(f"Expected SensorData, got {type(data)}. Skipping.")
            return
        
        # Log the input data
        self._log_data(data)
        
        # Filter data based on thresholds
        if not self._should_process(data):
            logger.debug(f"Data filtered out based on thresholds: {data.sensor_id}")
            return
        
        # Apply scaling if configured
        output_data = self._apply_scaling(data)
        
        # Yield the processed data
        if self.pass_through or output_data != data:
            yield output_data
    
    def _log_data(self, data: SensorData):
        """
        Log data to the console.
        
        Args:
            data: SensorData to log
        """
        # For specific channels
        if self.channels:
            values_str = ", ".join(f"{ch}={data.get_value(ch)} {data.get_unit(ch)}" 
                                 for ch in self.channels if ch in data.values)
        # For all channels
        else:
            values_str = ", ".join(f"{ch}={val} {data.get_unit(ch)}" 
                                 for ch, val in data.values.items())
        
        logger.info(f"[{data.timestamp:.3f}] {data.sensor_id} ({data.data_type}): {values_str}")
    
    def _should_process(self, data: SensorData) -> bool:
        """
        Determine if the data should be processed based on thresholds.
        
        Args:
            data: SensorData to check
            
        Returns:
            True if the data should be processed, False otherwise
        """
        # Apply thresholds to specified channels or all channels
        channels_to_check = self.channels if self.channels else data.values.keys()
        
        for channel in channels_to_check:
            if channel in data.values:
                value = data.get_value(channel)
                
                # Skip non-numeric values
                if not isinstance(value, (int, float)):
                    continue
                
                # Check thresholds
                if value < self.min_threshold or value > self.max_threshold:
                    return False
        
        return True
    
    def _apply_scaling(self, data: SensorData) -> SensorData:
        """
        Apply scaling to the data values.
        
        Args:
            data: SensorData to scale
            
        Returns:
            Scaled SensorData
        """
        # If no scaling is configured, return the original data
        if not self.scale_factor:
            return data
        
        # Create a new SensorData object to avoid modifying the original
        scaled_data = SensorData(
            timestamp=data.timestamp,
            sensor_id=data.sensor_id,
            data_type=data.data_type,
            raw_timestamp=data.raw_timestamp,
            units=data.units.copy(),
            metadata=data.metadata.copy()
        )
        
        # Copy the values and apply scaling
        scaled_values = data.values.copy()
        
        for channel, scale in self.scale_factor.items():
            if channel in scaled_values:
                value = scaled_values[channel]
                
                # Apply scaling to numeric values
                if isinstance(value, (int, float)):
                    scaled_values[channel] = value * scale
        
        scaled_data.values = scaled_values
        return scaled_data
    
    def setup(self):
        """Set up the processor before processing begins."""
        logger.info("SimpleProcessor setup complete")
    
    def teardown(self):
        """Clean up the processor after processing is done."""
        logger.info("SimpleProcessor teardown complete")
# src/plugins/processors/base_processor.py
from abc import ABC, abstractmethod
from typing import Any, Generator, Dict
from src.data.models import SensorData  # Typically, processors will handle SensorData

class IProcessor(ABC):
    """
    Interface for all data processors.
    
    Processors receive normalized data (typically SensorData) from a Decoder
    or another Processor, perform some transformation or analysis,
    and return the result.
    """
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the processor with a specific configuration.
        
        Args:
            config: Dictionary containing configuration parameters
                  for this processor (e.g., 'cutoff_freq', 'window_size', 'target_channels').
        """
        self.config = config
        print(f"Initializing {self.__class__.__name__} with config: {config}")

    @abstractmethod
    def process(self, data: Any) -> Generator[Any, None, None]:
        """
        Core method to process data.
        
        This method MUST be implemented by subclasses.
        It takes an input data unit (typically a `SensorData` object).
        It should return a generator (using `yield`). Each yield returns
        a processed data unit.
        
        A processor may:
        - Return modified data (yield once).
        - Return nothing (no yield) if data is filtered out.
        - Return multiple new results (yield multiple times).
        - Change the data type returned (e.g., from SensorData to some analysis result type).
        
        Args:
            data: Input data, typically a SensorData object.
            
        Returns:
            Generator[Any, None, None]: A generator yielding the processing result(s).
        """
        pass

    def setup(self):
        """
        (Optional) Perform any initialization needed before processing begins.
        Examples: Initialize buffers, load models, etc.
        """
        pass

    def teardown(self):
        """
        (Optional) Clean up resources after processing is done.
        Examples: Close files, free memory, etc.
        """
        pass
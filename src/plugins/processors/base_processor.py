# File: src/plugins/processors/base_processor.py
# Purpose: Abstract base class for all data processors
# Target Lines: ≤150

"""
Methods to implement in derived classes:
- __init__(self, config=None): Initialize with optional configuration
- init(self, config): Initialize or re-initialize with new configuration
- process(self, data): Process decoded data
- destroy(self): Clean up resources
"""

from abc import ABC, abstractmethod
import logging


class BaseProcessor(ABC):
    """
    Abstract base class for all data processors.
    
    Processors are responsible for transforming decoded data into
    processed data, such as filtering, converting units, or calculating
    derived values.
    """
    
    def __init__(self, config=None):
        """
        Initialize the processor with optional configuration.
        
        Args:
            config (dict, optional): Configuration dictionary for the processor
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        self.config = config or {}
        self.initialized = False
        self.error_state = False
        self.error_message = None
        self.process_count = 0
        self.process_errors = 0
        
        if config:
            self.init(config)
    
    @abstractmethod
    def init(self, config):
        """
        Initialize or re-initialize the processor with the specified configuration.
        
        Args:
            config (dict): Configuration dictionary for the processor
            
        Returns:
            bool: True if successful, False otherwise
        """
        self.config = config
        self.initialized = True
        return True
    
    @abstractmethod
    def process(self, data):
        """
        Process decoded data.
        
        Args:
            data (dict): Decoded data to process
            
        Returns:
            dict: Processed data
            
        Raises:
            ValueError: If the data cannot be processed
        """
        if not self.initialized:
            raise RuntimeError("Processor not initialized")
        
        self.process_count += 1
        return None
    
    @abstractmethod
    def destroy(self):
        """
        Clean up any resources used by the processor.
        
        Returns:
            bool: True if successful, False otherwise
        """
        self.initialized = False
        return True
    
    def get_status(self):
        """
        Get the current status of the processor.
        
        Returns:
            dict: A dictionary containing status information:
                - initialized (bool): Whether the processor is initialized
                - error_state (bool): Whether there's an error
                - error_message (str): Error message, if any
                - process_count (int): Total number of process operations
                - process_errors (int): Total number of process errors
        """
        return {
            "initialized": self.initialized,
            "error_state": self.error_state,
            "error_message": self.error_message,
            "process_count": self.process_count,
            "process_errors": self.process_errors
        }
    
    def set_error(self, message):
        """
        Set the processor in error state with the specified message.
        
        Args:
            message (str): Error message
        """
        self.error_state = True
        self.error_message = message
        self.process_errors += 1
        self.logger.error(f"Processor error: {message}")
    
    def clear_error(self):
        """
        Clear any error state.
        """
        self.error_state = False
        self.error_message = None
    
    def reset(self):
        """
        Reset the processor state.
        
        Returns:
            bool: True if successful, False otherwise
        """
        self.clear_error()
        return True


# How to extend and modify:
# 1. Add more common processing methods: Add utility methods for filtering, smoothing, etc.
# 2. Add state management: Add methods to save and restore the processing state
# 3. Add batch processing: Add methods to process multiple data points at once
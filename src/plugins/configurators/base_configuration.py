# File: src/system/configurators/base_configurator.py
# Purpose: Abstract base class for all sensor configurators
# Target Lines: ≤150

"""
Methods to implement in derived classes:
- __init__(self, config): Initialize with configuration
- configure(): Send configuration to the sensor
- reset(): Reset sensor to default settings
- get_status(): Get current status of the configurator
"""

from abc import ABC, abstractmethod
import logging


class BaseConfigurator(ABC):
    """
    Abstract base class for all sensor configurators.
    
    Configurators are responsible for configuring sensors with specific
    initialization sequences, sampling rates, and other settings.
    """
    
    def __init__(self, config):
        """
        Initialize the configurator with configuration.
        
        Args:
            config (dict): Configuration dictionary for the configurator
        """
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        self.is_configured = False
        self.error_state = False
        self.error_message = None
    
    @abstractmethod
    def configure(self):
        """
        Send configuration to the sensor.
        
        Returns:
            bool: True if successful, False otherwise
            
        Raises:
            RuntimeError: If there's an error configuring the sensor
        """
        pass
    
    @abstractmethod
    def reset(self):
        """
        Reset the sensor to default settings.
        
        Returns:
            bool: True if successful, False otherwise
            
        Raises:
            RuntimeError: If there's an error resetting the sensor
        """
        pass
    
    def get_status(self):
        """
        Get the current status of the configurator.
        
        Returns:
            dict: A dictionary containing status information:
                - is_configured (bool): Whether the sensor is configured
                - error_state (bool): Whether there's an error
                - error_message (str): Error message, if any
        """
        return {
            "is_configured": self.is_configured,
            "error_state": self.error_state,
            "error_message": self.error_message
        }
    
    def set_error(self, message):
        """
        Set the configurator in error state with the specified message.
        
        Args:
            message (str): Error message
        """
        self.error_state = True
        self.error_message = message
        self.logger.error(f"Configurator error: {message}")
    
    def clear_error(self):
        """
        Clear any error state.
        """
        self.error_state = False
        self.error_message = None


# How to extend and modify:
# 1. Add more common methods: Additional methods all configurators might need
# 2. Add validation methods: Methods to validate configuration parameters
# 3. Add protocol-specific methods: Implement protocol-specific configuration patterns
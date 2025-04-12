# File: src/plugins/visualizers/base_visualizer.py
# Purpose: Abstract base class for all data visualizers
# Target Lines: ≤150

"""
Methods to implement in derived classes:
- __init__(self, config=None): Initialize with optional configuration
- init(self, config): Initialize or re-initialize with new configuration
- visualize(self, data): Visualize processed or analyzed data
- destroy(self): Clean up resources
"""

from abc import ABC, abstractmethod
import logging


class BaseVisualizer(ABC):
    """
    Abstract base class for all data visualizers.
    
    Visualizers are responsible for creating visual representations of
    processed or analyzed data, such as graphs, charts, or 3D visualizations.
    """
    
    def __init__(self, config=None):
        """
        Initialize the visualizer with optional configuration.

        Args:
            config (dict, optional): Configuration dictionary for the visualizer
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        self.config = config or {}
        self.initialized = False
        self.error_state = False
        self.error_message = None
        self.visualize_count = 0
        self.visualize_errors = 0
        self.data_buffer = None
        self.logger.debug(f"{self.__class__.__name__} base initialized.")
    
    @abstractmethod
    def init(self, config):
        """
        Initialize or re-initialize the visualizer with the specified configuration.
        """
        self.config = config or {} # Cập nhật config
        # Không đặt self.initialized ở đây, lớp con sẽ quản lý
        # self.initialized = True # Xóa dòng này
        self.logger.info(f"{self.__class__.__name__} configuration updated.")
        return True
    
    @abstractmethod
    def visualize(self, data):
        """
        Visualize processed or analyzed data.
        
        Args:
            data (dict): Data to visualize
            
        Returns:
            object: Visualization object (e.g., figure, plot, etc.)
            
        Raises:
            ValueError: If the data cannot be visualized
        """
        if not self.initialized:
            raise RuntimeError("Visualizer not initialized")
        
        self.visualize_count += 1
        # Store the latest data in the buffer
        self.data_buffer = data
        return None
    
    @abstractmethod
    def destroy(self):
        """
        Clean up any resources used by the visualizer.
        
        Returns:
            bool: True if successful, False otherwise
        """
        self.initialized = False
        self.data_buffer = None
        return True
    
    def get_status(self):
        """
        Get the current status of the visualizer.
        
        Returns:
            dict: A dictionary containing status information:
                - initialized (bool): Whether the visualizer is initialized
                - error_state (bool): Whether there's an error
                - error_message (str): Error message, if any
                - visualize_count (int): Total number of visualize operations
                - visualize_errors (int): Total number of visualize errors
                - has_data (bool): Whether there's data in the buffer
        """
        return {
            "initialized": self.initialized,
            "error_state": self.error_state,
            "error_message": self.error_message,
            "visualize_count": self.visualize_count,
            "visualize_errors": self.visualize_errors,
            "has_data": self.data_buffer is not None
        }
    
    def set_error(self, message):
        """
        Set the visualizer in error state with the specified message.
        
        Args:
            message (str): Error message
        """
        self.error_state = True
        self.error_message = message
        self.visualize_errors += 1
        self.logger.error(f"Visualizer error: {message}")
    
    def clear_error(self):
        """
        Clear any error state.
        """
        self.error_state = False
        self.error_message = None
    
    def get_latest_data(self):
        """
        Get the latest data from the buffer.
        
        Returns:
            dict: Latest data
        """
        return self.data_buffer


# How to extend and modify:
# 1. Add render target capabilities: Add methods to render to different targets (UI, file, etc.)
# 2. Add animation support: Add methods to create animated visualizations
# 3. Add interactive elements: Add methods to create interactive visualizations
# 4. Add theme support: Add methods to apply different visual themes
# File: src/plugins/analyzers/base_analyzer.py
# Purpose: Abstract base class for all data analyzers
# Target Lines: ≤150

"""
Methods to implement in derived classes:
- __init__(self, config=None): Initialize with optional configuration
- analyze(self, data): Analyze processed data
- reset(self): Reset analyzer state
- update_config(self, new_config): Update analyzer configuration
"""

from abc import ABC, abstractmethod
import logging


class BaseAnalyzer(ABC):
    """
    Abstract base class for all data analyzers.
    
    Analyzers are responsible for performing complex analysis on processed data,
    such as anomaly detection, pattern recognition, or machine learning inference.
    """
    
    def __init__(self, config=None):
        """
        Initialize the analyzer with optional configuration.

        Args:
            config (dict, optional): Configuration dictionary for the analyzer
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        # Lưu config gốc để lớp con truy cập sau super().__init__
        self.config = config or {}
        self.initialized = False # Sẽ được đặt thành True bởi lớp con
        self.error_state = False
        self.error_message = None
        self.analyze_count = 0
        self.analyze_errors = 0

        # --- SỬA ĐỔI BẮT ĐẦU ---
        # Không gọi update_config từ đây nữa.
        # Lớp con sẽ tự gọi nó trong __init__ của mình nếu cần.
        # if config:
        #     self.update_config(config)
        # --- SỬA ĐỔI KẾT THÚC ---
        self.logger.debug(f"{self.__class__.__name__} base initialized.")
    
    @abstractmethod
    def analyze(self, data):
        """
        Analyze processed data.
        
        Args:
            data (dict): Processed data to analyze
            
        Returns:
            dict: Analysis results
            
        Raises:
            ValueError: If the data cannot be analyzed
        """
        if not self.initialized:
            raise RuntimeError("Analyzer not initialized")
        
        self.analyze_count += 1
        return None
    
    @abstractmethod
    def reset(self):
        """
        Reset the analyzer state.
        
        Returns:
            bool: True if successful, False otherwise
        """
        self.clear_error()
        return True
    
    @abstractmethod
    def update_config(self, new_config):
        """
        Update the analyzer configuration.
        
        Args:
            new_config (dict): New configuration dictionary
            
        Returns:
            bool: True if successful, False otherwise
        """
        self.config.update(new_config)
        self.config.update(new_config)
        self.logger.info(f"{self.__class__.__name__} configuration updated.")
        return True
    
    def get_status(self):
        """
        Get the current status of the analyzer.
        
        Returns:
            dict: A dictionary containing status information:
                - initialized (bool): Whether the analyzer is initialized
                - error_state (bool): Whether there's an error
                - error_message (str): Error message, if any
                - analyze_count (int): Total number of analyze operations
                - analyze_errors (int): Total number of analyze errors
        """
        return {
            "initialized": self.initialized,
            "error_state": self.error_state,
            "error_message": self.error_message,
            "analyze_count": self.analyze_count,
            "analyze_errors": self.analyze_errors
        }
    
    def set_error(self, message):
        """
        Set the analyzer in error state with the specified message.
        
        Args:
            message (str): Error message
        """
        self.error_state = True
        self.error_message = message
        self.analyze_errors += 1
        self.logger.error(f"Analyzer error: {message}")
    
    def clear_error(self):
        """
        Clear any error state.
        """
        self.error_state = False
        self.error_message = None


# How to extend and modify:
# 1. Add model management: Add methods to load and save ML models
# 2. Add training capability: Add methods to train or fine-tune ML models
# 3. Add ensemble methods: Add methods to combine multiple analyses
# 4. Add incremental analysis: Add methods for online or streaming analysis
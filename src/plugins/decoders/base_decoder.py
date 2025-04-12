# File: src/plugins/decoders/base_decoder.py
# Purpose: Base class for all decoders
# Target Lines: ≤150

"""
Methods to implement:
- __init__(self, config=None): Initialize with optional configuration
- init(self, config): Initialize or re-initialize with new configuration
- decode(self, data): Abstract method to decode raw data
- get_status(self): Get status information
- destroy(self): Clean up resources
"""

import logging
import time
from abc import ABC, abstractmethod


class BaseDecoder(ABC):
    """
    Base class for all sensor data decoders.
    
    Provides common functionalities like logging, status tracking,
    and defines the interface for decoding data.
    """
    
    def __init__(self, config=None):
        """
        Initialize the base decoder with optional configuration.
        
        Args:
            config (dict, optional): Configuration dictionary for the decoder
        """
        self.config = config if config is not None else {}
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Statistics
        self.packets_received = 0
        self.bytes_received = 0
        self.packets_decoded = 0
        self.last_decode_time = None
        self.errors = []
        self.is_initialized = False

        # --- SỬA ĐỔI BẮT ĐẦU ---
        # Không gọi self.init(config) từ đây nữa.
        # Logic khởi tạo cụ thể nên nằm trong __init__ của lớp con,
        # sau khi gọi super().__init__.
        # self.init(self.config) # Xóa hoặc comment dòng này
        self.is_initialized = True # Đánh dấu base init hoàn thành
        self.logger.debug("BaseDecoder initialized.")
        # --- SỬA ĐỔI KẾT THÚC ---

    def init(self, config):
        """
        Initialize or re-initialize the decoder with the specified configuration.
        This method is intended for re-configuration after initial creation.

        Args:
            config (dict): Configuration dictionary for the decoder

        Returns:
            bool: True if successful, False otherwise
        """
        self.config = config if config is not None else {}
        self.logger.info(f"Re-initializing {self.__class__.__name__} with new config.")
        # Reset stats or other relevant states if needed
        self.packets_received = 0
        self.bytes_received = 0
        self.packets_decoded = 0
        self.errors = []
        self.is_initialized = True
        return True

    @abstractmethod
    def decode(self, data):
        """
        Decode raw data into a structured format. Must be implemented by subclasses.

        Args:
            data (bytes, str, or dict): Raw data to decode

        Returns:
            ProcessedData or list[ProcessedData]: Decoded data, or None if decoding fails
        """
        # Basic tracking common to all decoders
        self.packets_received += 1
        if isinstance(data, (bytes, bytearray)):
            self.bytes_received += len(data)
        elif isinstance(data, str):
             self.bytes_received += len(data.encode('utf-8')) # Ước tính

        self.last_decode_time = time.time()
        # Subclasses should implement the actual decoding logic

    def get_status(self):
        """
        Get the current status and statistics of the decoder.

        Returns:
            dict: Status information
        """
        return {
            'decoder_type': self.__class__.__name__,
            'packets_received': self.packets_received,
            'bytes_received': self.bytes_received,
            'packets_decoded': self.packets_decoded,
            'last_decode_time': self.last_decode_time,
            'is_initialized': self.is_initialized,
            'errors': self.errors
        }

    def set_error(self, error_message):
        """
        Log an error and add it to the error list.

        Args:
            error_message (str): The error message to log
        """
        self.logger.error(error_message)
        self.errors.append(error_message)
        # Optionally limit the size of the error list
        max_errors = self.config.get("max_error_log", 100)
        if len(self.errors) > max_errors:
            self.errors.pop(0)

    def clear_errors(self):
        """Clear the list of recorded errors."""
        self.errors = []

    def destroy(self):
        """
        Clean up any resources used by the decoder.

        Returns:
            bool: True if successful, False otherwise
        """
        self.logger.info(f"Destroying {self.__class__.__name__}.")
        self.is_initialized = False
        # Subclasses can override to add specific cleanup logic
        return True
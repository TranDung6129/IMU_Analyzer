# src/io/readers/base_reader.py
from abc import ABC, abstractmethod
from typing import Any, Generator, Dict

class IDataReader(ABC):
    """
    Interface for all data readers.
    
    DataReaders are responsible for reading RAW data from a specific source
    (e.g., file, serial port, network stream) and providing it to the decoder.
    """
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the reader with a specific configuration.
        
        Args:
            config: Dictionary containing configuration parameters
                  for this reader (e.g., 'file_path', 'port', 'baudrate').
        """
        self.config = config
        print(f"Initializing {self.__class__.__name__} with config: {config}")

    @abstractmethod
    def read(self) -> Generator[bytes, None, None]:
        """
        Core method to read raw data from the source.
        
        This method MUST be implemented by subclasses.
        It should return a generator (using `yield`).
        Each yield returns a chunk of raw data as `bytes`.
        
        - For real-time sources (serial, network): yield data as it becomes available.
        - For file sources (post-processing): yield data in chunks.
        
        The generator should terminate (return or raise StopIteration) when there's no more data.
        
        Returns:
            Generator[bytes, None, None]: A generator that yields blocks of bytes.
        """
        pass

    def open(self):
        """
        (Optional) Set up or open the connection/resource.
        Example: Open a file, connect to a serial port.
        Usually called when used with a `with` statement.
        """
        pass

    def close(self):
        """
        (Optional) Close the connection or free resources.
        Example: Close a file, close a serial port.
        Usually called at the end of a `with` statement or when the pipeline stops.
        """
        pass

    def __enter__(self):
        """Support for context manager (`with` statement)."""
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Support for context manager (`with` statement). Ensures close() is called."""
        self.close()

    def get_status(self) -> Dict[str, Any]:
        """(Optional) Return the current status of the reader (e.g., connected, error)."""
        return {"status": "unknown"}
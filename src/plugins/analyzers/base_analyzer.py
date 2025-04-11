# src/plugins/analyzers/base_analyzer.py
from abc import ABC, abstractmethod
from typing import Any, Dict, Generator, Optional
from src.data.models import SensorData

class IAnalyzer(ABC):
    """
    Interface for all data analyzers.
    
    Analyzers perform more complex analysis on processed data,
    potentially using machine learning, statistical analysis,
    or other advanced techniques. They typically run asynchronously
    to avoid blocking the main processing pipeline.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the analyzer with a specific configuration.
        
        Args:
            config: Dictionary containing configuration parameters
                  for this analyzer (e.g., 'model_path', 'threshold_values',
                                     'window_size', 'feature_columns').
        """
        self.config = config
        print(f"Initializing {self.__class__.__name__} with config: {config}")
    
    @abstractmethod
    def analyze(self, data: Any) -> Generator[Any, None, None]:
        """
        Core method to analyze data.
        
        This method MUST be implemented by subclasses.
        It takes input data (often SensorData or processed data)
        and returns a generator of analysis results.
        
        Analyzers are typically stateful and may collect data over time
        before producing results. The generator should yield results
        whenever meaningful analysis is available.
        
        Args:
            data: Input data to analyze
            
        Returns:
            Generator yielding analysis results
        """
        pass
    
    def setup(self):
        """
        Set up resources needed for analysis.
        
        This method should be called before analysis starts.
        Examples: Load ML models, initialize data structures,
        allocate memory for data buffers, etc.
        """
        pass
    
    def teardown(self):
        """
        Clean up resources after analysis is complete.
        
        This method should be called when analysis is finished.
        Examples: Free memory, close open files, etc.
        """
        pass
    
    def reset(self):
        """
        Reset the analyzer state.
        
        This method should reset the internal state of the analyzer
        without requiring a full reinitialization. Useful for clearing
        data buffers while keeping loaded models, etc.
        """
        pass
    
    def update_config(self, config: Dict[str, Any]):
        """
        Update the analyzer configuration.
        
        This method allows changing analyzer parameters without
        reinitializing the entire analyzer. Should be implemented
        by stateful analyzers that need to adjust their behavior
        based on external inputs.
        
        Args:
            config: Updated configuration dictionary
        """
        self.config.update(config)
# src/plugins/visualizers/base_visualizer.py
from abc import ABC, abstractmethod
from typing import Any, Dict
from src.data.models import SensorData  # Typically, visualizers will display SensorData

class IVisualizer(ABC):
    """
    Interface for all data visualizers.
    
    Visualizers receive data (typically SensorData or results from a Processor)
    and display it to the user (e.g., plots, console output, UI updates).
    """
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the visualizer with a specific configuration.
        
        Args:
            config: Dictionary containing configuration parameters
                  for this visualizer (e.g., 'output_dir', 'plot_title', 'update_interval').
        """
        self.config = config
        print(f"Initializing {self.__class__.__name__} with config: {config}")

    @abstractmethod
    def visualize(self, data: Any) -> None:
        """
        Core method to visualize data.
        
        This method MUST be implemented by subclasses.
        It takes a data unit as input.
        Its responsibility is to perform the visualization action. It does not return a value.
        
        - For real-time: This method may be called continuously to update the display.
        - For post-processing: May be called once per result or accumulate data and display at the end.
        
        Args:
            data: Data to visualize.
        """
        pass

    def setup(self):
        """
        (Optional) Perform any initial setup needed for visualization.
        Examples: Create plot windows, initialize GUI libraries.
        Usually called once before the pipeline starts processing data.
        """
        pass

    def teardown(self):
        """
        (Optional) Clean up after visualization is complete.
        Examples: Save final plots, close windows, free GUI resources.
        Usually called once after the pipeline has processed all data.
        """
        pass
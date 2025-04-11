# src/plugins/visualizers/time_series_visualizer.py
import logging
import time
from collections import deque
from typing import Dict, Any, List, Optional, Deque
from src.plugins.visualizers.base_visualizer import IVisualizer
from src.data.models import SensorData

logger = logging.getLogger(__name__)

class TimeSeriesVisualizer(IVisualizer):
    """
    Visualizer for time series data.
    
    This simple implementation logs data to the console and 
    provides a mock ASCII visualization of the time series data.
    In a real implementation, this would use a plotting library
    like Matplotlib, PyQtGraph, or a web-based plotting tool.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the time series visualizer.
        
        Args:
            config: Dictionary containing configuration parameters:
                - channels (List[str], optional): List of channels to visualize (default: all)
                - window_size (int, optional): Number of data points to keep in memory (default: 100)
                - update_interval (float, optional): Minimum time between visualization updates in seconds (default: 0.5)
                - ascii_plot (bool, optional): Whether to show ASCII plots in the console (default: True)
                - ascii_width (int, optional): Width of ASCII plots in characters (default: 50)
                - ascii_height (int, optional): Height of ASCII plots in characters (default: 10)
        """
        super().__init__(config)
        
        # Optional parameters with defaults
        self.channels = config.get('channels', [])
        self.window_size = config.get('window_size', 100)
        self.update_interval = config.get('update_interval', 0.5)
        self.ascii_plot = config.get('ascii_plot', True)
        self.ascii_width = config.get('ascii_width', 50)
        self.ascii_height = config.get('ascii_height', 10)
        
        # Data storage
        self.data_buffers: Dict[str, Dict[str, Deque]] = {}  # {channel_name: {'timestamps': deque, 'values': deque}}
        
        # Visualization state
        self.last_update_time = 0
        
        logger.info(f"TimeSeriesVisualizer initialized with channels: {self.channels or 'all'}, window_size: {self.window_size}")
    
    def setup(self):
        """Set up the visualizer before visualization begins."""
        logger.info("TimeSeriesVisualizer setup complete")
    
    def teardown(self):
        """Clean up the visualizer after visualization is done."""
        logger.info("TimeSeriesVisualizer teardown complete")
        
        # In a real implementation, we might save plots to files here
        
        # Final visualization of all data
        if self.ascii_plot:
            logger.info("Final state of data buffers:")
            for channel, buffer in self.data_buffers.items():
                self._draw_ascii_plot(channel, buffer['timestamps'], buffer['values'])
    
    def visualize(self, data: Any) -> None:
        """
        Visualize the input data.
        
        Args:
            data: Input data to visualize (expected to be a SensorData object)
        """
        if not isinstance(data, SensorData):
            logger.warning(f"Expected SensorData, got {type(data)}. Skipping.")
            return
        
        # Update data buffers
        self._update_buffers(data)
        
        # Check if we should update the visualization
        current_time = time.time()
        if current_time - self.last_update_time >= self.update_interval:
            self._update_visualization()
            self.last_update_time = current_time
    
    def _update_buffers(self, data: SensorData):
        """
        Update data buffers with new data.
        
        Args:
            data: SensorData to add to buffers
        """
        # Determine which channels to process
        channels_to_process = self.channels if self.channels else data.values.keys()
        
        for channel in channels_to_process:
            if channel in data.values:
                value = data.get_value(channel)
                
                # Skip non-numeric values
                if not isinstance(value, (int, float)):
                    continue
                
                # Create buffer for this channel if it doesn't exist
                if channel not in self.data_buffers:
                    self.data_buffers[channel] = {
                        'timestamps': deque(maxlen=self.window_size),
                        'values': deque(maxlen=self.window_size)
                    }
                
                # Add data to buffers
                self.data_buffers[channel]['timestamps'].append(data.timestamp)
                self.data_buffers[channel]['values'].append(value)
    
    def _update_visualization(self):
        """Update the visualization with current data."""
        # In a real implementation, we would update plots here
        
        # For this mock implementation, log the current state
        for channel, buffer in self.data_buffers.items():
            if len(buffer['values']) > 0:
                latest_value = buffer['values'][-1]
                unit = ""  # In a real implementation, we would get this from the data
                logger.info(f"Channel {channel}: Current value = {latest_value} {unit}, Buffer size = {len(buffer['values'])}")
                
                # Draw ASCII plot if enabled
                if self.ascii_plot:
                    self._draw_ascii_plot(channel, buffer['timestamps'], buffer['values'])
    
    def _draw_ascii_plot(self, channel: str, timestamps: Deque, values: Deque):
        """
        Draw a simple ASCII plot of the data.
        
        Args:
            channel: Channel name
            timestamps: Deque of timestamps
            values: Deque of values
        """
        if not values:
            return
        
        # Convert to lists for easier processing
        timestamps_list = list(timestamps)
        values_list = list(values)
        
        # Calculate min and max values
        min_value = min(values_list)
        max_value = max(values_list)
        
        # Ensure we have a non-zero range
        if max_value == min_value:
            max_value += 1
        
        # Calculate the time range
        time_range = max(timestamps_list) - min(timestamps_list)
        time_unit = "s"
        
        logger.info(f"\nASCII Plot for {channel} ({len(values_list)} points, range: {min_value:.2f} to {max_value:.2f}):")
        logger.info(f"Time span: {time_range:.2f} {time_unit}")
        
        # Create the plot
        plot = []
        for _ in range(self.ascii_height):
            plot.append([' '] * self.ascii_width)
        
        # Fill in the plot
        for i in range(min(len(values_list), self.ascii_width)):
            # Calculate the x position (time)
            x = i
            
            # Calculate the y position (value)
            normalized = (values_list[i] - min_value) / (max_value - min_value)
            y = self.ascii_height - 1 - int(normalized * (self.ascii_height - 1))
            
            # Ensure y is within bounds
            y = max(0, min(self.ascii_height - 1, y))
            
            # Add the point to the plot
            plot[y][x] = '*'
        
        # Draw the plot
        for row in plot:
            logger.info(''.join(row))
        
        # Draw the axis
        logger.info('-' * self.ascii_width)
        
        # Add a blank line after the plot
        logger.info("")
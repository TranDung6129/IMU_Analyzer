# File: src/plugins/visualizers/time_series_visualizer.py
# Purpose: Visualize time series data from sensors
# Target Lines: ≤150

"""
Methods to implement:
- __init__(self, config=None): Initialize with optional configuration
- init(self, config): Initialize or re-initialize with new configuration
- visualize(self, data): Process and prepare data for visualization
- destroy(self): Clean up resources
"""

import logging
import time
import numpy as np
from collections import deque
from src.plugins.visualizers.base_visualizer import BaseVisualizer


class TimeSeriesVisualizer(BaseVisualizer):
    """
    Visualizer for time series data from sensors.
    
    Stores and prepares time series data for visualization in the UI.
    Supports tracking multiple fields over time and maintaining a scrolling
    window of recent values.
    """
    
    def __init__(self, config=None):
        """
        Initialize the time series visualizer with optional configuration.
        
        Args:
            config (dict, optional): Configuration with the following keys:
                - fields (list): List of fields to visualize (default: ['roll', 'pitch', 'yaw'])
                - max_points (int): Maximum number of points to keep (default: 500)
                - time_window (float): Time window to display in seconds (default: 10.0)
                - auto_range (bool): Auto-adjust Y-axis range (default: True)
                - y_min (float): Minimum Y value if not auto_range (default: -180)
                - y_max (float): Maximum Y value if not auto_range (default: 180)
                - line_colors (dict): Colors for each field (default: auto-generated)
        """
        super().__init__(config)
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Initialize with default settings
        self.fields = ['roll', 'pitch', 'yaw']
        self.max_points = 500
        self.time_window = 10.0  # seconds
        self.auto_range = True
        self.y_min = -180
        self.y_max = 180
        self.line_colors = {}
        
        # Initialize data storage
        self.timestamps = deque(maxlen=self.max_points)
        self.data_series = {}
        self.last_update_time = time.time()
        
        # Default color palette
        self.default_colors = [
            '#1f77b4',  # blue
            '#ff7f0e',  # orange
            '#2ca02c',  # green
            '#d62728',  # red
            '#9467bd',  # purple
            '#8c564b',  # brown
            '#e377c2',  # pink
            '#7f7f7f',  # gray
            '#bcbd22',  # olive
            '#17becf'   # teal
        ]
        
        # Statistics
        self.stats = {field: {'min': None, 'max': None, 'mean': 0, 'std': 0} for field in self.fields}
        
        # Update with provided configuration
        if config:
            self.init(config)
    
    def init(self, config):
        """
        Initialize or re-initialize the visualizer with the specified configuration.
        
        Args:
            config (dict): Configuration dictionary
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not isinstance(config, dict):
            self.set_error("Configuration must be a dictionary")
            return False
        
        # Update fields to visualize
        if 'fields' in config and isinstance(config['fields'], list):
            self.fields = config['fields']
        
        # Update max points
        if 'max_points' in config:
            try:
                max_points = int(config['max_points'])
                if max_points < 10:
                    self.logger.warning(f"max_points too small, using minimum of 10")
                    max_points = 10
                
                # If the max_points changed, we need to recreate our deques
                if max_points != self.max_points:
                    self.max_points = max_points
                    self.timestamps = deque(maxlen=self.max_points)
                    # Keep existing data truncated to new length
                    for field in self.data_series:
                        old_data = list(self.data_series[field])[-self.max_points:] if self.data_series[field] else []
                        self.data_series[field] = deque(old_data, maxlen=self.max_points)
            except (ValueError, TypeError):
                self.logger.warning("Invalid max_points value, using default")
        
        # Update time window
        if 'time_window' in config:
            try:
                time_window = float(config['time_window'])
                if time_window <= 0:
                    self.logger.warning("time_window must be positive, using default")
                else:
                    self.time_window = time_window
            except (ValueError, TypeError):
                self.logger.warning("Invalid time_window value, using default")
        
        # Update auto range
        if 'auto_range' in config:
            self.auto_range = bool(config['auto_range'])
        
        # Update Y-axis range if not auto
        if not self.auto_range:
            if 'y_min' in config:
                try:
                    self.y_min = float(config['y_min'])
                except (ValueError, TypeError):
                    self.logger.warning("Invalid y_min value, using default")
            
            if 'y_max' in config:
                try:
                    self.y_max = float(config['y_max'])
                    if self.y_max <= self.y_min:
                        self.logger.warning("y_max must be greater than y_min, adjusting")
                        self.y_max = self.y_min + 1.0
                except (ValueError, TypeError):
                    self.logger.warning("Invalid y_max value, using default")
        
        # Update line colors
        if 'line_colors' in config and isinstance(config['line_colors'], dict):
            self.line_colors = config['line_colors']
        
        # Initialize data series for each field
        for field in self.fields:
            if field not in self.data_series:
                self.data_series[field] = deque(maxlen=self.max_points)
            
            # Initialize statistics
            if field not in self.stats:
                self.stats[field] = {'min': None, 'max': None, 'mean': 0, 'std': 0}
            
            # Assign default color if not specified
            if field not in self.line_colors:
                color_idx = len(self.line_colors) % len(self.default_colors)
                self.line_colors[field] = self.default_colors[color_idx]
        
        self.initialized = True
        self.clear_error()
        return True
    
    def visualize(self, data):
        """
        Process and prepare data for visualization.
        
        Args:
            data (dict): Processed data with fields to visualize
            
        Returns:
            dict: Visualization data ready for the UI
            
        Raises:
            RuntimeError: If the visualizer is not initialized
            ValueError: If the data is not a dictionary
        """
        if not self.initialized:
            raise RuntimeError("Visualizer not initialized")
        
        if not isinstance(data, dict):
            self.set_error("Data must be a dictionary")
            return None
        
        # Get current timestamp
        current_time = time.time()
        timestamp = data.get('timestamp', current_time)
        
        # Try to convert string timestamp to float if needed
        if isinstance(timestamp, str):
            try:
                # Handle ISO format timestamp
                from datetime import datetime
                timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00')).timestamp()
            except (ValueError, TypeError):
                # Fall back to current time if parsing fails
                timestamp = current_time
        
        # Add timestamp to the timestamps queue
        self.timestamps.append(timestamp)
        
        # Process each field
        for field in self.fields:
            # Skip fields not in data
            if field not in data:
                # Add None to maintain alignment with timestamps
                self.data_series.setdefault(field, deque(maxlen=self.max_points)).append(None)
                continue
            
            try:
                # Get the data value, convert to float
                value = float(data[field])
                
                # Add to data series
                self.data_series.setdefault(field, deque(maxlen=self.max_points)).append(value)
                
                # Update statistics
                values = [v for v in self.data_series[field] if v is not None]
                if values:
                    self.stats[field]['min'] = min(values)
                    self.stats[field]['max'] = max(values)
                    self.stats[field]['mean'] = sum(values) / len(values)
                    
                    # Calculate standard deviation
                    if len(values) > 1:
                        mean = self.stats[field]['mean']
                        variance = sum((x - mean) ** 2 for x in values) / len(values)
                        self.stats[field]['std'] = variance ** 0.5
                    else:
                        self.stats[field]['std'] = 0.0
            
            except (ValueError, TypeError) as e:
                self.logger.debug(f"Error processing field {field}: {str(e)}")
                # Add None to maintain alignment with timestamps
                self.data_series.setdefault(field, deque(maxlen=self.max_points)).append(None)
        
        # Prepare visualization data for UI
        viz_data = {
            'type': 'time_series',
            'timestamps': list(self.timestamps),
            'series': {},
            'fields': self.fields,
            'colors': self.line_colors,
            'auto_range': self.auto_range,
            'fixed_range': [self.y_min, self.y_max] if not self.auto_range else None,
            'stats': self.stats
        }
        
        # Add each data series to visualization data
        for field in self.fields:
            if field in self.data_series:
                viz_data['series'][field] = list(self.data_series[field])
        
        # Set the time range
        if len(self.timestamps) > 1:
            last_timestamp = self.timestamps[-1]
            viz_data['time_range'] = [last_timestamp - self.time_window, last_timestamp]
        else:
            current_time = time.time()
            viz_data['time_range'] = [current_time - self.time_window, current_time]
        
        # Update the data buffer for access by UI
        self.data_buffer = viz_data
        
        # Update last update time
        self.last_update_time = current_time
        
        # Update visualize count
        super().visualize(data)
        
        return viz_data
    
    def destroy(self):
        """
        Clean up resources used by the visualizer.
        
        Returns:
            bool: True if successful, False otherwise
        """
        # Clear all data
        self.timestamps.clear()
        for field in self.data_series:
            self.data_series[field].clear()
        
        self.initialized = False
        self.clear_error()
        return True
    
    def get_time_range(self):
        """
        Get the current time range of the visualization.
        
        Returns:
            tuple: (start_time, end_time) in seconds
        """
        if not self.timestamps:
            current_time = time.time()
            return (current_time - self.time_window, current_time)
        
        end_time = self.timestamps[-1]
        start_time = end_time - self.time_window
        return (start_time, end_time)
    
    def get_value_range(self, field=None):
        """
        Get the current value range for a specific field or all fields.
        
        Args:
            field (str, optional): Field to get range for, or None for all fields
            
        Returns:
            tuple: (min_value, max_value)
        """
        if self.auto_range:
            # Calculate range based on data
            if field:
                # For a specific field
                if field in self.stats and self.stats[field]['min'] is not None:
                    min_val = self.stats[field]['min']
                    max_val = self.stats[field]['max']
                    # Add 10% padding
                    range_size = max(max_val - min_val, 1e-6)
                    return (min_val - range_size * 0.1, max_val + range_size * 0.1)
                return (self.y_min, self.y_max)
            else:
                # For all fields
                all_min = self.y_min
                all_max = self.y_max
                has_data = False
                
                for field in self.fields:
                    if field in self.stats and self.stats[field]['min'] is not None:
                        all_min = min(all_min, self.stats[field]['min'])
                        all_max = max(all_max, self.stats[field]['max'])
                        has_data = True
                
                if has_data:
                    # Add 10% padding
                    range_size = max(all_max - all_min, 1e-6)
                    return (all_min - range_size * 0.1, all_max + range_size * 0.1)
        
        # Use fixed range
        return (self.y_min, self.y_max)
    
    def clear_data(self):
        """
        Clear all data series but keep settings.
        
        Returns:
            bool: True if successful
        """
        self.timestamps.clear()
        for field in self.data_series:
            self.data_series[field].clear()
        
        # Reset statistics
        for field in self.stats:
            self.stats[field] = {'min': None, 'max': None, 'mean': 0, 'std': 0}
        
        self.data_buffer = None  # Clear visualization buffer
        return True
    
    def add_annotation(self, timestamp, text, color="#ff0000"):
        """
        Add an annotation to the time series.
        
        Args:
            timestamp (float): Time point for annotation
            text (str): Annotation text
            color (str, optional): Annotation color
            
        Returns:
            bool: True if successful, False otherwise
        """
        # This is just a placeholder. In a real implementation,
        # we would store annotations and add them to viz_data.
        self.logger.info(f"Annotation added at {timestamp}: {text}")
        return True


# How to extend and modify:
# 1. Add more visualization options: Modify init() to support line styles, markers, etc.
# 2. Add data filtering: Modify visualize() to apply filters (e.g., moving average) before visualization
# 3. Add annotations: Add support for marking events or anomalies on the time series
# 4. Add multiple Y-axes: Support different scales for different fields
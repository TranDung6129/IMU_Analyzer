# src/plugins/visualizers/fft_visualizer.py
import logging
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from collections import deque
import time

# Import base visualizer interface
from src.plugins.visualizers.base_visualizer import IVisualizer

# Import SensorData model
from src.data.models import SensorData

# Import analyzer results if available
try:
    from src.plugins.analyzers.simple_analyzer import AnalysisResult
    ANALYSIS_RESULTS_AVAILABLE = True
except ImportError:
    ANALYSIS_RESULTS_AVAILABLE = False

logger = logging.getLogger(__name__)

# Check if matplotlib is available (for plotting)
try:
    import matplotlib
    matplotlib.use('Agg')  # Non-interactive backend
    import matplotlib.pyplot as plt
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    logger.warning("Matplotlib not available, FFTVisualizer will use text output only")
    MATPLOTLIB_AVAILABLE = False

class FFTVisualizer(IVisualizer):
    """
    Visualizer for frequency domain data.
    
    Displays frequency-domain representations of sensor data,
    typically the output of an FFT (Fast Fourier Transform) 
    processor or analyzer.
    
    In GUI mode, renders plots using matplotlib.
    In console mode, renders ASCII plots.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the FFT visualizer.
        
        Args:
            config: Visualization configuration:
                - channels (List[str], optional): Channels to visualize (default: all)
                - window_size (int, optional): Number of data points to display (default: 100)
                - update_interval (float, optional): Update interval in seconds (default: 0.5)
                - frequency_range (List[float], optional): Min and max frequency to display (default: [0, 50])
                - amplitude_range (List[float], optional): Min and max amplitude to display (default: auto)
                - plot_type (str, optional): Plot type (default: 'line', options: 'line', 'bar')
                - log_scale (bool, optional): Use logarithmic scale for frequency axis (default: True)
                - gui_mode (bool, optional): Use GUI or text mode (default: MATPLOTLIB_AVAILABLE)
                - output_file (str, optional): Save plot to file path (default: None)
                - ascii_width (int, optional): Width of ASCII plots (default: 80)
                - ascii_height (int, optional): Height of ASCII plots (default: 15)
        """
        super().__init__(config)
        
        # Extract configuration
        self.channels = config.get('channels', [])
        self.window_size = config.get('window_size', 100)
        self.update_interval = config.get('update_interval', 0.5)
        self.frequency_range = config.get('frequency_range', [0, 50])
        self.amplitude_range = config.get('amplitude_range', None)
        self.plot_type = config.get('plot_type', 'line')
        self.log_scale = config.get('log_scale', True)
        self.gui_mode = config.get('gui_mode', MATPLOTLIB_AVAILABLE)
        self.output_file = config.get('output_file', None)
        self.ascii_width = config.get('ascii_width', 80)
        self.ascii_height = config.get('ascii_height', 15)
        
        # Data buffers for each channel
        # {channel_name: {'frequencies': deque, 'amplitudes': deque, 'timestamp': last_timestamp}}
        self.data_buffers = {}
        
        # Plotting resources
        self.figure = None
        self.canvas = None
        self.axes = None
        
        # Time tracking
        self.last_update_time = 0
        
        logger.info(f"FFTVisualizer initialized with window_size={self.window_size}, "
                   f"channels={self.channels or 'all'}")
    
    def setup(self):
        """Set up the visualizer."""
        # Initialize matplotlib figure if using GUI mode
        if self.gui_mode and MATPLOTLIB_AVAILABLE:
            self.figure = Figure(figsize=(8, 6), dpi=100)
            self.canvas = FigureCanvas(self.figure)
            self.axes = self.figure.add_subplot(111)
            
            # Configure plot
            if self.log_scale:
                self.axes.set_xscale('log')
            
            self.axes.set_xlabel('Frequency (Hz)')
            self.axes.set_ylabel('Amplitude')
            self.axes.set_title('FFT Visualization')
            
            # Set frequency range if specified
            if self.frequency_range:
                self.axes.set_xlim(self.frequency_range)
            
            # Set amplitude range if specified
            if self.amplitude_range:
                self.axes.set_ylim(self.amplitude_range)
            
            # Add grid
            self.axes.grid(True)
            
            # Add legend
            self.axes.legend()
            
            self.figure.tight_layout()
        
        logger.info("FFTVisualizer setup complete")
    
    def teardown(self):
        """Clean up resources."""
        # Save final plot if output file is specified
        if self.output_file and self.figure:
            try:
                self.figure.savefig(self.output_file)
                logger.info(f"Final FFT plot saved to {self.output_file}")
            except Exception as e:
                logger.error(f"Error saving FFT plot to {self.output_file}: {e}")
        
        # Clear data buffers
        self.data_buffers.clear()
        
        logger.info("FFTVisualizer teardown complete")
    
    def visualize(self, data: Any) -> None:
        """
        Visualize FFT data.
        
        Args:
            data: Data to visualize (SensorData or AnalysisResult)
        """
        # Handle different data types
        if isinstance(data, SensorData):
            self._visualize_sensor_data(data)
        elif ANALYSIS_RESULTS_AVAILABLE and isinstance(data, AnalysisResult):
            self._visualize_analysis_result(data)
        else:
            # Try to handle as a generic data structure
            self._visualize_generic_data(data)
    
    def _visualize_sensor_data(self, data: SensorData):
        """
        Visualize sensor data.
        
        Args:
            data: Sensor data to visualize
        """
        # Skip if not FFT data (no frequencies)
        if 'frequencies' not in data.metadata:
            return
        
        # Extract FFT data
        frequencies = data.metadata['frequencies']
        
        # Get timestamp
        timestamp = data.timestamp
        
        # Process channels
        channels_to_process = self.channels if self.channels else data.values.keys()
        
        # Update data buffers for each channel
        for channel in channels_to_process:
            if channel in data.values:
                amplitudes = data.get_value(channel)
                if not isinstance(amplitudes, (list, np.ndarray)):
                    continue
                
                # Create buffer for this channel if it doesn't exist
                if channel not in self.data_buffers:
                    self.data_buffers[channel] = {
                        'frequencies': frequencies,
                        'amplitudes': amplitudes,
                        'timestamp': timestamp,
                        'unit': data.get_unit(channel) or ''
                    }
                else:
                    # Update buffer
                    self.data_buffers[channel]['frequencies'] = frequencies
                    self.data_buffers[channel]['amplitudes'] = amplitudes
                    self.data_buffers[channel]['timestamp'] = timestamp
                    self.data_buffers[channel]['unit'] = data.get_unit(channel) or ''
        
        # Update visualization if enough time has passed
        current_time = timestamp  # Use data timestamp
        if current_time - self.last_update_time >= self.update_interval:
            self._update_visualization()
            self.last_update_time = current_time
    
    def _visualize_analysis_result(self, data: 'AnalysisResult'):
        """
        Visualize analysis result.
        
        Args:
            data: Analysis result to visualize
        """
        # Skip if not a frequency-domain analysis
        if data.analysis_type not in ('fft', 'spectrum', 'frequency'):
            return
        
        # Extract data
        timestamp = data.timestamp
        channel = data.sensor_id
        
        # Get frequencies and amplitudes from values
        if 'frequencies' in data.values and 'amplitudes' in data.values:
            frequencies = data.values['frequencies']
            amplitudes = data.values['amplitudes']
            
            # Create or update buffer
            if channel not in self.data_buffers:
                self.data_buffers[channel] = {
                    'frequencies': frequencies,
                    'amplitudes': amplitudes,
                    'timestamp': timestamp,
                    'unit': data.metadata.get('unit', '')
                }
            else:
                # Update buffer
                self.data_buffers[channel]['frequencies'] = frequencies
                self.data_buffers[channel]['amplitudes'] = amplitudes
                self.data_buffers[channel]['timestamp'] = timestamp
                self.data_buffers[channel]['unit'] = data.metadata.get('unit', '')
        
        # Update visualization if enough time has passed
        current_time = timestamp  # Use data timestamp
        if current_time - self.last_update_time >= self.update_interval:
            self._update_visualization()
            self.last_update_time = current_time
    
    def _visualize_generic_data(self, data: Any):
        """
        Try to visualize generic data.
        
        Args:
            data: Generic data to visualize
        """
        # Skip if data format not recognized
        if not hasattr(data, 'get') and not hasattr(data, '__getitem__'):
            return
        
        try:
            # Try to extract relevant fields
            frequencies = None
            amplitudes = None
            channel = None
            timestamp = getattr(data, 'timestamp', None) or time.time()
            
            # Try different attribute/key patterns
            if hasattr(data, 'get'):
                # Dictionary-like
                if 'frequencies' in data and 'amplitudes' in data:
                    frequencies = data['frequencies']
                    amplitudes = data['amplitudes']
                    channel = data.get('channel', 'unknown')
                elif 'fft' in data:
                    fft_data = data['fft']
                    if isinstance(fft_data, dict):
                        frequencies = fft_data.get('frequencies')
                        amplitudes = fft_data.get('amplitudes')
                        channel = fft_data.get('channel', 'unknown')
            
            # Skip if required data not found
            if frequencies is None or amplitudes is None:
                return
            
            # Create or update buffer
            if channel not in self.data_buffers:
                self.data_buffers[channel] = {
                    'frequencies': frequencies,
                    'amplitudes': amplitudes,
                    'timestamp': timestamp,
                    'unit': getattr(data, 'unit', '') or ''
                }
            else:
                # Update buffer
                self.data_buffers[channel]['frequencies'] = frequencies
                self.data_buffers[channel]['amplitudes'] = amplitudes
                self.data_buffers[channel]['timestamp'] = timestamp
            
            # Update visualization if enough time has passed
            current_time = timestamp
            if current_time - self.last_update_time >= self.update_interval:
                self._update_visualization()
                self.last_update_time = current_time
                
        except Exception as e:
            logger.warning(f"Error visualizing generic data: {e}")
    
    def _update_visualization(self):
        """Update the visualization."""
        if self.gui_mode and MATPLOTLIB_AVAILABLE and self.figure and self.axes:
            self._update_matplotlib_plot()
        else:
            self._update_ascii_plot()
    
    def _update_matplotlib_plot(self):
        """Update the matplotlib plot."""
        if not MATPLOTLIB_AVAILABLE or not self.figure or not self.axes:
            return
        
        # Clear previous plot
        self.axes.clear()
        
        # Plot each channel
        for channel, buffer in self.data_buffers.items():
            frequencies = buffer['frequencies']
            amplitudes = buffer['amplitudes']
            unit = buffer.get('unit', '')
            
            # Skip if no data
            if len(frequencies) == 0 or len(amplitudes) == 0:
                continue
            
            # Plot based on plot type
            if self.plot_type == 'bar':
                self.axes.bar(frequencies, amplitudes, alpha=0.5, label=channel)
            else:  # Default to line
                self.axes.plot(frequencies, amplitudes, label=f"{channel} {unit}")
        
        # Configure plot
        if self.log_scale:
            self.axes.set_xscale('log')
        
        self.axes.set_xlabel('Frequency (Hz)')
        self.axes.set_ylabel('Amplitude')
        self.axes.set_title('FFT Visualization')
        
        # Set frequency range if specified
        if self.frequency_range:
            self.axes.set_xlim(self.frequency_range)
        
        # Set amplitude range if specified
        if self.amplitude_range:
            self.axes.set_ylim(self.amplitude_range)
        
        # Add grid
        self.axes.grid(True)
        
        # Add legend if multiple channels
        if len(self.data_buffers) > 1:
            self.axes.legend()
        
        self.figure.tight_layout()
        
        # Redraw canvas
        self.canvas.draw()
        
        # Save to file if specified
        if self.output_file:
            try:
                self.figure.savefig(self.output_file)
            except Exception as e:
                logger.error(f"Error saving FFT plot to {self.output_file}: {e}")
    
    def _update_ascii_plot(self):
        """Update the ASCII plot."""
        # Log the current state
        logger.info("\nFFT Visualization (ASCII):")
        
        for channel, buffer in self.data_buffers.items():
            frequencies = buffer['frequencies']
            amplitudes = buffer['amplitudes']
            unit = buffer.get('unit', '')
            
            # Skip if no data
            if len(frequencies) == 0 or len(amplitudes) == 0:
                continue
            
            # Get timestamp
            timestamp = buffer.get('timestamp', 0)
            
            # Create header
            logger.info(f"Channel: {channel} {unit} (Timestamp: {timestamp:.3f})")
            
            # Find peak frequency
            peak_idx = np.argmax(amplitudes)
            peak_freq = frequencies[peak_idx]
            peak_amp = amplitudes[peak_idx]
            
            logger.info(f"Peak Frequency: {peak_freq:.2f} Hz, Amplitude: {peak_amp:.4f}")
            
            # Create simple ASCII plot
            self._draw_ascii_plot(channel, frequencies, amplitudes)
    
    def _draw_ascii_plot(self, channel: str, frequencies: List[float], amplitudes: List[float]):
        """
        Draw an ASCII plot.
        
        Args:
            channel: Channel name
            frequencies: Frequency values
            amplitudes: Amplitude values
        """
        # Skip if no data
        if len(frequencies) == 0 or len(amplitudes) == 0:
            return
        
        # Convert to numpy arrays if needed
        frequencies = np.array(frequencies)
        amplitudes = np.array(amplitudes)
        
        # Apply frequency range filter
        if self.frequency_range:
            mask = (frequencies >= self.frequency_range[0]) & (frequencies <= self.frequency_range[1])
            frequencies = frequencies[mask]
            amplitudes = amplitudes[mask]
        
        # Skip if no data after filtering
        if len(frequencies) == 0 or len(amplitudes) == 0:
            return
        
        # Create ASCII plot
        width = self.ascii_width
        height = self.ascii_height
        
        # Find min/max values
        amp_min = np.min(amplitudes)
        amp_max = np.max(amplitudes)
        
        # Ensure non-zero range
        if amp_max == amp_min:
            amp_max = amp_min + 1.0
        
        # Create empty plot
        plot = [[' ' for _ in range(width)] for _ in range(height)]
        
        # Calculate frequency bins
        if self.log_scale and frequencies[0] > 0:
            # Logarithmic binning
            freq_min = np.log10(frequencies[0])
            freq_max = np.log10(frequencies[-1])
            bin_edges = np.logspace(freq_min, freq_max, width + 1)
        else:
            # Linear binning
            freq_min = frequencies[0]
            freq_max = frequencies[-1]
            bin_edges = np.linspace(freq_min, freq_max, width + 1)
        
        # Create histogram
        hist, _ = np.histogram(frequencies, bins=bin_edges, weights=amplitudes)
        
        # Normalize histogram
        hist_min = np.min(hist)
        hist_max = np.max(hist)
        if hist_max == hist_min:
            hist_max = hist_min + 1.0
        
        # Plot histogram
        for i, val in enumerate(hist):
            if i >= width:
                break
                
            # Calculate bar height
            normalized = (val - hist_min) / (hist_max - hist_min)
            bar_height = int(normalized * (height - 1))
            
            # Draw bar
            for j in range(height - 1, height - 1 - bar_height - 1, -1):
                if j >= 0:
                    plot[j][i] = '*'
        
        # Draw plot
        for row in plot:
            logger.info(''.join(row))
        
        # Draw x-axis labels
        x_labels = ['|']
        
        # Add frequency labels
        if self.log_scale:
            # Logarithmic scale labels
            decades = np.floor(np.log10(freq_max)) - np.ceil(np.log10(freq_min)) + 1
            if decades <= 10:
                # One label per decade
                label_values = [10 ** exp for exp in range(int(np.ceil(np.log10(freq_min))), 
                                                         int(np.floor(np.log10(freq_max))) + 1)]
            else:
                # Fewer labels for many decades
                step = int(decades / 5) + 1
                label_values = [10 ** exp for exp in range(int(np.ceil(np.log10(freq_min))), 
                                                         int(np.floor(np.log10(freq_max))) + 1, 
                                                         step)]
        else:
            # Linear scale labels
            num_labels = 5
            step = (freq_max - freq_min) / num_labels
            label_values = [freq_min + i * step for i in range(num_labels + 1)]
        
        # Convert frequency values to positions
        for val in label_values:
            if self.log_scale:
                pos = int(width * (np.log10(val) - np.log10(freq_min)) / (np.log10(freq_max) - np.log10(freq_min)))
            else:
                pos = int(width * (val - freq_min) / (freq_max - freq_min))
            
            # Skip if out of range
            if pos < 0 or pos >= width:
                continue
            
            # Add label
            label = f"{val:.1f}"
            x_labels.append(f"{' ' * (pos - len(x_labels))}|")
        
        # Print axis labels
        logger.info(''.join(x_labels))
        
        # Add footer
        logger.info(f"Frequency (Hz): {freq_min:.1f} - {freq_max:.1f}")
        logger.info(f"Amplitude: {amp_min:.4f} - {amp_max:.4f}")
        logger.info("")  # Add blank line after plot
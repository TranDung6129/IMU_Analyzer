# src/plugins/analyzers/simple_analyzer.py
import logging
import statistics
import time
from collections import deque
from typing import Any, Dict, Generator, List, Optional, Deque, Tuple
from src.plugins.analyzers.base_analyzer import IAnalyzer
from src.data.models import SensorData

logger = logging.getLogger(__name__)

class AnalysisResult:
    """Container for analysis results."""
    
    def __init__(self, 
                 sensor_id: str, 
                 timestamp: float, 
                 analysis_type: str, 
                 values: Dict[str, Any], 
                 metadata: Optional[Dict[str, Any]] = None):
        """
        Initialize an analysis result.
        
        Args:
            sensor_id: ID of the sensor that produced the data
            timestamp: Timestamp of the analysis
            analysis_type: Type of analysis performed
            values: Analysis result values
            metadata: Additional metadata
        """
        self.sensor_id = sensor_id
        self.timestamp = timestamp
        self.analysis_type = analysis_type
        self.values = values
        self.metadata = metadata or {}
    
    def __str__(self):
        """Return a string representation of the analysis result."""
        values_str = ", ".join(f"{k}={v}" for k, v in self.values.items())
        return f"AnalysisResult({self.analysis_type}, {self.sensor_id}, {self.timestamp:.3f}): {values_str}"

class SimpleAnalyzer(IAnalyzer):
    """
    A simple data analyzer that performs basic statistical analysis.
    
    Features:
    - Rolling window statistics (mean, min, max, std dev)
    - Threshold detection (value exceeds min/max thresholds)
    - Simple trend detection (increasing/decreasing trends)
    - Data rate monitoring
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the simple analyzer.
        
        Args:
            config: Dictionary containing configuration parameters:
                - channels (List[str], optional): Channels to analyze (default: all)
                - window_size (int, optional): Size of the analysis window (default: 50)
                - min_threshold (Dict[str, float], optional): Min thresholds by channel
                - max_threshold (Dict[str, float], optional): Max thresholds by channel
                - trigger_interval (float, optional): Min time between analyses (default: 0.5s)
                - trend_sensitivity (float, optional): Trend detection sensitivity (default: 0.5)
        """
        super().__init__(config)
        
        # Configuration parameters
        self.channels = config.get('channels', [])
        self.window_size = config.get('window_size', 50)
        self.min_thresholds = config.get('min_threshold', {})
        self.max_thresholds = config.get('max_threshold', {})
        self.trigger_interval = config.get('trigger_interval', 0.5)
        self.trend_sensitivity = config.get('trend_sensitivity', 0.5)
        
        # Data buffers: {channel: deque of (timestamp, value) tuples}
        self.data_buffers: Dict[str, Deque[Tuple[float, float]]] = {}
        
        # State tracking
        self.last_analysis_time = 0
        self.data_rates: Dict[str, float] = {}  # Data points per second by channel
        self.trend_directions: Dict[str, str] = {}  # 'increasing', 'decreasing', or 'stable'
        
        logger.info(f"SimpleAnalyzer initialized with window_size={self.window_size}, "
                   f"channels={self.channels or 'all'}")
    
    def setup(self):
        """Set up the analyzer."""
        logger.info("SimpleAnalyzer setup")
        self.reset()
    
    def teardown(self):
        """Clean up the analyzer."""
        logger.info("SimpleAnalyzer teardown")
        self.data_buffers.clear()
    
    def reset(self):
        """Reset the analyzer state."""
        logger.info("SimpleAnalyzer reset")
        self.data_buffers.clear()
        self.last_analysis_time = 0
        self.data_rates.clear()
        self.trend_directions.clear()
    
    def update_config(self, config: Dict[str, Any]):
        """
        Update the analyzer configuration.
        
        Args:
            config: Updated configuration dictionary
        """
        # Update config
        super().update_config(config)
        
        # Extract updated parameters
        if 'channels' in config:
            self.channels = config['channels']
        if 'window_size' in config:
            self.window_size = config['window_size']
        if 'min_threshold' in config:
            self.min_thresholds = config['min_threshold']
        if 'max_threshold' in config:
            self.max_thresholds = config['max_threshold']
        if 'trigger_interval' in config:
            self.trigger_interval = config['trigger_interval']
        if 'trend_sensitivity' in config:
            self.trend_sensitivity = config['trend_sensitivity']
        
        logger.info(f"SimpleAnalyzer configuration updated: {config}")
    
    def analyze(self, data: Any) -> Generator[AnalysisResult, None, None]:
        """
        Analyze incoming data.
        
        Args:
            data: Input data to analyze (expected to be a SensorData object)
            
        Yields:
            AnalysisResult objects
        """
        if not isinstance(data, SensorData):
            logger.warning(f"Expected SensorData, got {type(data)}. Skipping.")
            return
        
        # Update data buffers
        self._update_buffers(data)
        
        # Check if it's time to perform analysis
        current_time = time.time()
        if current_time - self.last_analysis_time < self.trigger_interval:
            return
        
        # Perform analysis if we have enough data
        for channel, buffer in self.data_buffers.items():
            if len(buffer) >= self.window_size:
                # Extract values for analysis
                timestamps = [t for t, _ in buffer]
                values = [v for _, v in buffer]
                
                # Perform statistical analysis
                stats_result = self._analyze_statistics(channel, timestamps, values)
                if stats_result:
                    yield stats_result
                
                # Check thresholds
                threshold_result = self._check_thresholds(channel, timestamps, values)
                if threshold_result:
                    yield threshold_result
                
                # Detect trends
                trend_result = self._detect_trend(channel, timestamps, values)
                if trend_result:
                    yield trend_result
                
                # Calculate data rate
                rate_result = self._calculate_data_rate(channel, timestamps)
                if rate_result:
                    yield rate_result
        
        # Update last analysis time
        self.last_analysis_time = current_time
    
    def _update_buffers(self, data: SensorData):
        """
        Update data buffers with new data.
        
        Args:
            data: SensorData to add to buffers
        """
        # Determine which channels to process
        channels_to_process = self.channels if self.channels else data.values.keys()
        
        # Add data to buffers
        for channel in channels_to_process:
            if channel in data.values:
                value = data.get_value(channel)
                
                # Skip non-numeric values
                if not isinstance(value, (int, float)):
                    continue
                
                # Create buffer for this channel if it doesn't exist
                if channel not in self.data_buffers:
                    self.data_buffers[channel] = deque(maxlen=self.window_size)
                
                # Add data point to buffer
                self.data_buffers[channel].append((data.timestamp, value))
    
    def _analyze_statistics(self, channel: str, timestamps: List[float], values: List[float]) -> Optional[AnalysisResult]:
        """
        Perform statistical analysis on a channel.
        
        Args:
            channel: Channel name
            timestamps: List of timestamps
            values: List of values
            
        Returns:
            AnalysisResult or None
        """
        try:
            # Calculate statistics
            stats = {
                'mean': statistics.mean(values),
                'min': min(values),
                'max': max(values),
                'std_dev': statistics.stdev(values) if len(values) > 1 else 0,
                'median': statistics.median(values),
                'range': max(values) - min(values)
            }
            
            # Create result
            return AnalysisResult(
                sensor_id=channel,
                timestamp=timestamps[-1],
                analysis_type='statistics',
                values=stats
            )
        except Exception as e:
            logger.error(f"Error calculating statistics for {channel}: {e}")
            return None
    
    def _check_thresholds(self, channel: str, timestamps: List[float], values: List[float]) -> Optional[AnalysisResult]:
        """
        Check if values exceed configured thresholds.
        
        Args:
            channel: Channel name
            timestamps: List of timestamps
            values: List of values
            
        Returns:
            AnalysisResult or None
        """
        # Check if we have thresholds for this channel
        min_threshold = self.min_thresholds.get(channel)
        max_threshold = self.max_thresholds.get(channel)
        
        if min_threshold is None and max_threshold is None:
            return None
        
        # Check latest value against thresholds
        latest_value = values[-1]
        latest_timestamp = timestamps[-1]
        
        threshold_results = {}
        
        if min_threshold is not None and latest_value < min_threshold:
            threshold_results['below_min'] = True
            threshold_results['min_threshold'] = min_threshold
            threshold_results['value'] = latest_value
            threshold_results['delta'] = min_threshold - latest_value
        
        if max_threshold is not None and latest_value > max_threshold:
            threshold_results['above_max'] = True
            threshold_results['max_threshold'] = max_threshold
            threshold_results['value'] = latest_value
            threshold_results['delta'] = latest_value - max_threshold
        
        if threshold_results:
            return AnalysisResult(
                sensor_id=channel,
                timestamp=latest_timestamp,
                analysis_type='threshold',
                values=threshold_results
            )
        
        return None
    
    def _detect_trend(self, channel: str, timestamps: List[float], values: List[float]) -> Optional[AnalysisResult]:
        """
        Detect trends in the data.
        
        Args:
            channel: Channel name
            timestamps: List of timestamps
            values: List of values
            
        Returns:
            AnalysisResult or None
        """
        if len(values) < 5:  # Need enough points for a meaningful trend
            return None
        
        try:
            # Simple trend detection using linear regression slope
            n = len(values)
            sum_x = sum(range(n))
            sum_y = sum(values)
            sum_xx = sum(i*i for i in range(n))
            sum_xy = sum(i*values[i] for i in range(n))
            
            # Calculate slope
            slope = (n * sum_xy - sum_x * sum_y) / (n * sum_xx - sum_x * sum_x)
            
            # Determine trend direction based on slope and sensitivity
            prev_direction = self.trend_directions.get(channel, 'stable')
            
            if slope > self.trend_sensitivity:
                direction = 'increasing'
            elif slope < -self.trend_sensitivity:
                direction = 'decreasing'
            else:
                direction = 'stable'
            
            # Only report if direction changed
            if direction != prev_direction:
                self.trend_directions[channel] = direction
                
                return AnalysisResult(
                    sensor_id=channel,
                    timestamp=timestamps[-1],
                    analysis_type='trend',
                    values={
                        'direction': direction,
                        'slope': slope,
                        'previous_direction': prev_direction
                    }
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Error detecting trend for {channel}: {e}")
            return None
    
    def _calculate_data_rate(self, channel: str, timestamps: List[float]) -> Optional[AnalysisResult]:
        """
        Calculate data rate for a channel.
        
        Args:
            channel: Channel name
            timestamps: List of timestamps
            
        Returns:
            AnalysisResult or None
        """
        if len(timestamps) < 2:
            return None
        
        try:
            # Calculate time span
            time_span = timestamps[-1] - timestamps[0]
            
            if time_span <= 0:
                return None
            
            # Calculate data rate (points per second)
            data_rate = len(timestamps) / time_span
            
            # Check if data rate changed significantly
            prev_rate = self.data_rates.get(channel, 0)
            rate_change = abs(data_rate - prev_rate) / max(prev_rate, 0.1)
            
            # Update stored rate
            self.data_rates[channel] = data_rate
            
            # Only report if rate changed significantly or first calculation
            if prev_rate == 0 or rate_change > 0.1:  # 10% change threshold
                return AnalysisResult(
                    sensor_id=channel,
                    timestamp=timestamps[-1],
                    analysis_type='data_rate',
                    values={
                        'rate': data_rate,
                        'points': len(timestamps),
                        'timespan': time_span,
                        'unit': 'points/second',
                        'previous_rate': prev_rate,
                        'rate_change': rate_change
                    }
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Error calculating data rate for {channel}: {e}")
            return None
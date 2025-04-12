# File: src/system/monitor.py
# Purpose: Monitor system resources and performance
# Target Lines: ≤300

"""
Methods to implement:
- get_cpu_usage(): Get current CPU usage
- get_memory_usage(): Get current memory usage
- log_system_stats(): Log system statistics
- run_monitor(): Main monitor loop
"""

import os
import time
import logging
import threading
import psutil
from datetime import datetime


class SystemMonitor:
    """
    Monitor system resources and performance.
    
    Tracks CPU usage, memory usage, disk I/O, and process statistics.
    Can also monitor pipeline performance.
    """
    
    def __init__(self, interval=1.0, logger=True, log_interval=60.0):
        """
        Initialize the system monitor.
        
        Args:
            interval (float): Monitoring interval in seconds
            logger (bool): Whether to enable logging
            log_interval (float): Interval for logging statistics in seconds
        """
        self.interval = interval
        self.enable_logging = logger
        self.log_interval = log_interval
        self.logger = logging.getLogger("SystemMonitor")
        self.running = False
        self.monitor_thread = None
        self.last_log_time = 0
        
        # Monitoring data
        self.cpu_usage = 0.0
        self.memory_usage = 0.0
        self.memory_total = 0
        self.memory_available = 0
        self.disk_usage = 0.0
        self.process_cpu = 0.0
        self.process_memory = 0
        
        # Pipeline metrics
        self.pipelines = {}
        
        # Performance history
        self.history_size = 60  # Keep 1 minute of history by default
        self.cpu_history = []
        self.memory_history = []
        self.process_cpu_history = []
        self.process_memory_history = []
        
        # Initialize process information
        self.process = psutil.Process(os.getpid())
    
    def start(self):
        """
        Start the monitoring thread.
        
        Returns:
            bool: True if started successfully, False otherwise
        """
        if self.running:
            self.logger.warning("Monitor is already running")
            return False
        
        self.running = True
        self.monitor_thread = threading.Thread(
            target=self.run_monitor,
            name="SystemMonitorThread",
            daemon=True
        )
        self.monitor_thread.start()
        self.logger.info(f"System monitor started with interval {self.interval} seconds")
        return True
    
    def stop(self):
        """
        Stop the monitoring thread.
        
        Returns:
            bool: True if stopped successfully, False otherwise
        """
        if not self.running:
            self.logger.warning("Monitor is not running")
            return False
        
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2.0)
            if self.monitor_thread.is_alive():
                self.logger.warning("Monitor thread did not stop cleanly")
        
        self.logger.info("System monitor stopped")
        return True
    
    def run_monitor(self):
        """
        Main monitoring loop.
        
        Continuously collects system statistics at the specified interval.
        """
        self.logger.info("Monitor thread started")
        self.last_log_time = time.time()
        
        while self.running:
            try:
                # Update statistics
                self.get_cpu_usage()
                self.get_memory_usage()
                self.get_disk_usage()
                self.get_process_stats()
                
                # Update history
                self._update_history()
                
                # Log statistics periodically if logging is enabled
                current_time = time.time()
                if self.enable_logging and (current_time - self.last_log_time) >= self.log_interval:
                    self.log_system_stats()
                    self.last_log_time = current_time
                
                # Sleep for the monitoring interval
                time.sleep(self.interval)
                
            except Exception as e:
                self.logger.error(f"Error in monitor thread: {str(e)}")
                time.sleep(max(1.0, self.interval))  # Wait at least 1 second before trying again
        
        self.logger.info("Monitor thread stopped")
    
    def get_cpu_usage(self):
        """
        Get current CPU usage.
        
        Returns:
            float: CPU usage percentage (0-100)
        """
        try:
            self.cpu_usage = psutil.cpu_percent(interval=0.1)
            return self.cpu_usage
        except Exception as e:
            self.logger.error(f"Error getting CPU usage: {str(e)}")
            return 0.0
    
    def get_memory_usage(self):
        """
        Get current memory usage.
        
        Returns:
            float: Memory usage percentage (0-100)
        """
        try:
            mem = psutil.virtual_memory()
            self.memory_usage = mem.percent
            self.memory_total = mem.total
            self.memory_available = mem.available
            return self.memory_usage
        except Exception as e:
            self.logger.error(f"Error getting memory usage: {str(e)}")
            return 0.0
    
    def get_disk_usage(self):
        """
        Get current disk usage.
        
        Returns:
            float: Disk usage percentage (0-100)
        """
        try:
            disk = psutil.disk_usage('/')
            self.disk_usage = disk.percent
            return self.disk_usage
        except Exception as e:
            self.logger.error(f"Error getting disk usage: {str(e)}")
            return 0.0
    
    def get_process_stats(self):
        """
        Get current process statistics.
        
        Returns:
            tuple: (CPU usage percentage, memory usage in bytes)
        """
        try:
            self.process_cpu = self.process.cpu_percent(interval=0.1)
            self.process_memory = self.process.memory_info().rss
            return (self.process_cpu, self.process_memory)
        except Exception as e:
            self.logger.error(f"Error getting process stats: {str(e)}")
            return (0.0, 0)
    
    def log_system_stats(self):
        """
        Log system statistics.
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.logger.debug(
            f"[{timestamp}] CPU: {self.cpu_usage:.1f}%, "
            f"Memory: {self.memory_usage:.1f}%, "
            f"Process CPU: {self.process_cpu:.1f}%, "
            f"Process Memory: {self._format_bytes(self.process_memory)}"
        )
    
    def _update_history(self):
        """
        Update the performance history.
        """
        # Add new values
        self.cpu_history.append(self.cpu_usage)
        self.memory_history.append(self.memory_usage)
        self.process_cpu_history.append(self.process_cpu)
        self.process_memory_history.append(self.process_memory)
        
        # Trim history to the specified size
        if len(self.cpu_history) > self.history_size:
            self.cpu_history = self.cpu_history[-self.history_size:]
        if len(self.memory_history) > self.history_size:
            self.memory_history = self.memory_history[-self.history_size:]
        if len(self.process_cpu_history) > self.history_size:
            self.process_cpu_history = self.process_cpu_history[-self.history_size:]
        if len(self.process_memory_history) > self.history_size:
            self.process_memory_history = self.process_memory_history[-self.history_size:]
    
    def register_pipeline(self, pipeline_id, pipeline):
        """
        Register a pipeline for monitoring.
        
        Args:
            pipeline_id (str): ID of the pipeline
            pipeline: Pipeline object to monitor
        """
        self.pipelines[pipeline_id] = pipeline
        self.logger.info(f"Registered pipeline for monitoring: {pipeline_id}")
    
    def unregister_pipeline(self, pipeline_id):
        """
        Unregister a pipeline from monitoring.
        
        Args:
            pipeline_id (str): ID of the pipeline to unregister
        """
        if pipeline_id in self.pipelines:
            del self.pipelines[pipeline_id]
            self.logger.info(f"Unregistered pipeline from monitoring: {pipeline_id}")
    
    def get_pipeline_metrics(self, pipeline_id=None):
        """
        Get pipeline performance metrics.
        
        Args:
            pipeline_id (str, optional): ID of the pipeline to get metrics for
            
        Returns:
            dict: Pipeline metrics
        """
        if pipeline_id:
            if pipeline_id in self.pipelines:
                return self.pipelines[pipeline_id].get_metrics()
            else:
                return None
        
        # Return metrics for all pipelines
        return {pid: pipeline.get_metrics() for pid, pipeline in self.pipelines.items()}
    
    def get_pipeline_status(self, pipeline_id=None):
        """
        Get pipeline status.
        
        Args:
            pipeline_id (str, optional): ID of the pipeline to get status for
            
        Returns:
            dict: Pipeline status
        """
        if pipeline_id:
            if pipeline_id in self.pipelines:
                return self.pipelines[pipeline_id].get_status()
            else:
                return None
        
        # Return status for all pipelines
        return {pid: pipeline.get_status() for pid, pipeline in self.pipelines.items()}
    
    def get_system_stats(self):
        """
        Get the current system statistics.
        
        Returns:
            dict: Current system statistics
        """
        return {
            "timestamp": datetime.now().isoformat(),
            "cpu_usage": self.cpu_usage,
            "memory_usage": self.memory_usage,
            "memory_total": self.memory_total,
            "memory_available": self.memory_available,
            "disk_usage": self.disk_usage,
            "process_cpu": self.process_cpu,
            "process_memory": self.process_memory,
            "process_memory_formatted": self._format_bytes(self.process_memory),
            "history": {
                "cpu": self.cpu_history,
                "memory": self.memory_history,
                "process_cpu": self.process_cpu_history,
                "process_memory": [self._format_bytes(m) for m in self.process_memory_history]
            }
        }
    
    def _format_bytes(self, bytes_value):
        """
        Format bytes to human-readable format.
        
        Args:
            bytes_value (int): Bytes value
            
        Returns:
            str: Formatted string (e.g., "1.23 MB")
        """
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_value < 1024 or unit == 'TB':
                return f"{bytes_value:.2f} {unit}"
            bytes_value /= 1024


# How to extend and modify:
# 1. Add network monitoring: Add methods to track network usage
# 2. Add temperature monitoring: Add methods to track CPU/GPU temperature
# 3. Add alert thresholds: Add functionality to alert when resource usage exceeds thresholds
# 4. Add metrics storage: Add functionality to store metrics to file for later analysis
# File: src/ui/panels/monitor_panel.py
# Purpose: UI panel for displaying system performance metrics
# Target Lines: ≤150

"""
Methods to implement:
- _setup_ui(): Set up the UI components
- update_stats(): Update displayed statistics
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QProgressBar, QGroupBox, QScrollArea, 
                            QPushButton, QTabWidget, QFrame)
from PyQt6.QtCore import Qt, QTimer, pyqtSlot
from PyQt6.QtGui import QColor, QPalette

import pyqtgraph as pg
import numpy as np


class MonitorPanel(QWidget):
    """
    Panel for displaying system performance metrics in the IMU Analyzer.
    
    Shows CPU usage, memory usage, pipeline throughput, and other performance metrics.
    """
    
    def __init__(self, parent=None):
        """
        Initialize the monitor panel.
        
        Args:
            parent (QWidget, optional): Parent widget
        """
        super().__init__(parent)
        self.system_monitor = None
        self.update_interval = 1000  # Default to 1 second
        self.history_size = 60  # 60 data points on graph
        
        # Set up data structures for history
        self.cpu_history = np.zeros(self.history_size)
        self.memory_history = np.zeros(self.history_size)
        self.process_cpu_history = np.zeros(self.history_size)
        self.process_memory_history = np.zeros(self.history_size)
        
        # Set up UI components
        self._setup_ui()
        
        # Set up timer for updates
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update_stats)
    
    def set_system_monitor(self, system_monitor):
        """
        Set the system monitor for this panel.
        
        Args:
            system_monitor: SystemMonitor instance
        """
        self.system_monitor = system_monitor
        
        # Start update timer
        self.update_timer.start(self.update_interval)
    
    def set_update_interval(self, interval_ms):
        """
        Set the update interval for the panel.
        
        Args:
            interval_ms (int): Update interval in milliseconds
        """
        self.update_interval = interval_ms
        if self.update_timer.isActive():
            self.update_timer.stop()
            self.update_timer.start(interval_ms)
    
    def _setup_ui(self):
        """
        Set up the UI components of the monitor panel.
        """
        # Main layout
        main_layout = QVBoxLayout(self)
        
        # Header
        header_label = QLabel("System Monitor")
        header_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        main_layout.addWidget(header_label)
        
        # Tab widget for different monitor categories
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        # System Resources Tab
        sys_resources_widget = QWidget()
        sys_resources_layout = QVBoxLayout(sys_resources_widget)
        
        # CPU Usage Group
        cpu_group = QGroupBox("CPU Usage")
        cpu_layout = QVBoxLayout(cpu_group)
        
        # CPU progress bar
        self.cpu_progress = QProgressBar()
        self.cpu_progress.setRange(0, 100)
        self.cpu_progress.setValue(0)
        self.cpu_progress.setFormat("%v%")
        self.cpu_progress.setStyleSheet(self._get_progress_style())
        cpu_layout.addWidget(self.cpu_progress)
        
        # CPU label
        self.cpu_label = QLabel("CPU: 0.0%")
        cpu_layout.addWidget(self.cpu_label)
        
        # Process CPU label
        self.process_cpu_label = QLabel("Process CPU: 0.0%")
        cpu_layout.addWidget(self.process_cpu_label)
        
        # CPU Graph
        self.cpu_graph = pg.PlotWidget()
        self.cpu_graph.setBackground('w')
        self.cpu_graph.setTitle("CPU Usage History")
        self.cpu_graph.setLabel('left', 'Usage', '%')
        self.cpu_graph.setLabel('bottom', 'Time', 's')
        self.cpu_graph.showGrid(x=True, y=True)
        self.cpu_graph.setYRange(0, 100)
        
        # CPU plot lines
        self.cpu_plot = self.cpu_graph.plot(pen=pg.mkPen(color='b', width=2), name="System CPU")
        self.process_cpu_plot = self.cpu_graph.plot(pen=pg.mkPen(color='r', width=2), name="Process CPU")
        
        # Add legend
        self.cpu_graph.addLegend()
        
        cpu_layout.addWidget(self.cpu_graph)
        sys_resources_layout.addWidget(cpu_group)
        
        # Memory Usage Group
        memory_group = QGroupBox("Memory Usage")
        memory_layout = QVBoxLayout(memory_group)
        
        # Memory progress bar
        self.memory_progress = QProgressBar()
        self.memory_progress.setRange(0, 100)
        self.memory_progress.setValue(0)
        self.memory_progress.setFormat("%v%")
        self.memory_progress.setStyleSheet(self._get_progress_style())
        memory_layout.addWidget(self.memory_progress)
        
        # Memory label
        self.memory_label = QLabel("Memory: 0.0%")
        memory_layout.addWidget(self.memory_label)
        
        # Process Memory label
        self.process_memory_label = QLabel("Process Memory: 0 B")
        memory_layout.addWidget(self.process_memory_label)
        
        # Memory Available label
        self.memory_available_label = QLabel("Available Memory: 0 B")
        memory_layout.addWidget(self.memory_available_label)
        
        # Memory Graph
        self.memory_graph = pg.PlotWidget()
        self.memory_graph.setBackground('w')
        self.memory_graph.setTitle("Memory Usage History")
        self.memory_graph.setLabel('left', 'Usage', '%')
        self.memory_graph.setLabel('bottom', 'Time', 's')
        self.memory_graph.showGrid(x=True, y=True)
        self.memory_graph.setYRange(0, 100)
        
        # Memory plot line
        self.memory_plot = self.memory_graph.plot(pen=pg.mkPen(color='g', width=2), name="System Memory")
        
        memory_layout.addWidget(self.memory_graph)
        sys_resources_layout.addWidget(memory_group)
        
        # Add to tab widget
        self.tab_widget.addTab(sys_resources_widget, "System Resources")
        
        # Pipeline Performance Tab
        pipeline_widget = QWidget()
        pipeline_layout = QVBoxLayout(pipeline_widget)
        
        # Pipeline Group
        pipeline_group = QGroupBox("Pipeline Throughput")
        pipeline_inner_layout = QVBoxLayout(pipeline_group)
        
        # Placeholder for pipeline metrics
        self.pipeline_layout = QVBoxLayout()
        pipeline_inner_layout.addLayout(self.pipeline_layout)
        
        pipeline_layout.addWidget(pipeline_group)
        self.tab_widget.addTab(pipeline_widget, "Pipelines")
        
        # Add refresh button
        refresh_button = QPushButton("Refresh Now")
        refresh_button.clicked.connect(self.update_stats)
        main_layout.addWidget(refresh_button)
    
    def _get_progress_style(self):
        """
        Get the stylesheet for progress bars with color gradients.
        
        Returns:
            str: CSS stylesheet
        """
        return """
            QProgressBar {
                border: 1px solid #bbb;
                border-radius: 3px;
                text-align: center;
                height: 20px;
            }
            QProgressBar::chunk {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0078D7, stop:1 #5CB85C);
                width: 1px;
            }
        """
    
    @pyqtSlot()
    def update_stats(self):
        """
        Update the displayed statistics from the system monitor.
        """
        if not self.system_monitor:
            return
        
        # Get current stats
        stats = self.system_monitor.get_system_stats()
        
        # Update CPU display
        cpu_usage = stats.get("cpu_usage", 0.0)
        self.cpu_progress.setValue(int(cpu_usage))
        self.cpu_label.setText(f"CPU: {cpu_usage:.1f}%")
        
        process_cpu = stats.get("process_cpu", 0.0)
        self.process_cpu_label.setText(f"Process CPU: {process_cpu:.1f}%")
        
        # Update Memory display
        memory_usage = stats.get("memory_usage", 0.0)
        self.memory_progress.setValue(int(memory_usage))
        self.memory_label.setText(f"Memory: {memory_usage:.1f}%")
        
        process_memory_formatted = stats.get("process_memory_formatted", "0 B")
        self.process_memory_label.setText(f"Process Memory: {process_memory_formatted}")
        
        memory_available = stats.get("memory_available", 0)
        memory_available_formatted = self._format_bytes(memory_available)
        self.memory_available_label.setText(f"Available Memory: {memory_available_formatted}")
        
        # Update history data
        self.cpu_history = np.roll(self.cpu_history, -1)
        self.cpu_history[-1] = cpu_usage
        
        self.process_cpu_history = np.roll(self.process_cpu_history, -1)
        self.process_cpu_history[-1] = process_cpu
        
        self.memory_history = np.roll(self.memory_history, -1)
        self.memory_history[-1] = memory_usage
        
        # Update graphs
        self.cpu_plot.setData(self.cpu_history)
        self.process_cpu_plot.setData(self.process_cpu_history)
        self.memory_plot.setData(self.memory_history)
        
        # Update pipeline metrics
        self._update_pipeline_metrics()
    
    def _update_pipeline_metrics(self):
        """
        Update the pipeline performance metrics display.
        """
        if not self.system_monitor:
            return
            
        # Clear existing widgets
        while self.pipeline_layout.count():
            item = self.pipeline_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Get pipeline metrics
        pipeline_metrics = self.system_monitor.get_pipeline_metrics()
        if not pipeline_metrics:
            self.pipeline_layout.addWidget(QLabel("No active pipelines"))
            return
        
        # Add pipeline metrics
        for pipeline_id, metrics in pipeline_metrics.items():
            throughput = metrics.get("throughput", 0.0)
            read_count = metrics.get("read_count", 0)
            
            # Create pipeline metric widget
            pipeline_frame = QFrame()
            pipeline_frame.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Raised)
            pipeline_frame_layout = QVBoxLayout(pipeline_frame)
            
            # Pipeline header
            header_layout = QHBoxLayout()
            header_layout.addWidget(QLabel(f"Pipeline: {pipeline_id}"))
            header_layout.addStretch()
            header_layout.addWidget(QLabel(f"Throughput: {throughput:.2f} Hz"))
            pipeline_frame_layout.addLayout(header_layout)
            
            # Pipeline progress bar
            throughput_bar = QProgressBar()
            throughput_bar.setRange(0, 100)
            throughput_bar.setValue(min(int(throughput), 100))
            throughput_bar.setFormat("%v Hz")
            throughput_bar.setStyleSheet(self._get_progress_style())
            pipeline_frame_layout.addWidget(throughput_bar)
            
            # Pipeline counts
            counts_layout = QHBoxLayout()
            counts_layout.addWidget(QLabel(f"Read: {read_count}"))
            
            if "decode_count" in metrics:
                counts_layout.addWidget(QLabel(f"Decode: {metrics['decode_count']}"))
            
            if "process_count" in metrics:
                counts_layout.addWidget(QLabel(f"Process: {metrics['process_count']}"))
            
            if "analyze_count" in metrics:
                counts_layout.addWidget(QLabel(f"Analyze: {metrics['analyze_count']}"))
            
            if "visualize_count" in metrics:
                counts_layout.addWidget(QLabel(f"Visualize: {metrics['visualize_count']}"))
            
            if "write_count" in metrics:
                counts_layout.addWidget(QLabel(f"Write: {metrics['write_count']}"))
            
            pipeline_frame_layout.addLayout(counts_layout)
            
            # Add to pipeline layout
            self.pipeline_layout.addWidget(pipeline_frame)
        
        # Add stretch to push widgets to the top
        self.pipeline_layout.addStretch()
    
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
# 1. Add disk usage monitoring: Add display for disk usage metrics
# 2. Add network monitoring: Add display for network usage metrics
# 3. Add alerts: Add visual alerts for when metrics exceed thresholds
# 4. Add saving metrics: Add ability to save/export performance metrics
# File: src/ui/visualizers/time_series_widget.py
# Purpose: Widget to display time series data
# Target Lines: ≤150

"""
Methods to implement:
- __init__(self, parent=None, config=None): Initialize with optional parent and config
- update_data(self, data): Update widget with new time series data
- set_position(self, position): Set widget position
- set_size(self, size): Set widget size
- _setup_plot(self): Setup the plot area
- _update_plot(self): Update the plot with current data
"""

import logging
import numpy as np
from collections import deque
from PyQt6.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QCheckBox
from PyQt6.QtCore import Qt, QTimer
from PyQt6 import QtGui

try:
    import pyqtgraph as pg
    PYQTGRAPH_AVAILABLE = True
except ImportError:
    PYQTGRAPH_AVAILABLE = False

from src.ui.visualizers.base_widget import BaseWidget


class TimeSeriesWidget(BaseWidget):
    """
    Widget to display time series data from sensors.
    
    Supports multiple series, auto-scaling, and customization.
    """
    
    def __init__(self, parent=None, config=None):
        """
        Initialize the time series widget.
        
        Args:
            parent (QWidget, optional): Parent widget
            config (dict, optional): Widget configuration
        """
        default_config = {
            "title": "Time Series", "max_points": 100, "update_interval": 100,
            "show_legend": True, "show_grid": True, "auto_range": True,
            "y_range": [-10, 10], "channels": ["accel_x", "accel_y", "accel_z"],
            "colors": ["#4285F4", "#0F9D58", "#DB4437"]
        }
        if config: default_config.update(config)
        super().__init__(parent, default_config)

        self.data_buffers = {}
        self.time_buffer = deque(maxlen=self.config["max_points"])
        self.update_timer = QTimer()
        self.update_timer.setInterval(self.config["update_interval"])
        self.update_timer.timeout.connect(self._update_plot)
        for channel in self.config["channels"]:
            self.data_buffers[channel] = deque(maxlen=self.config["max_points"])

        self._setup_plot()

        # --- SỬA ĐỔI: Gọi _setup_controls() ---
        self._setup_controls()
        # --- KẾT THÚC SỬA ĐỔI ---

        self.update_timer.start()
        self.logger.info("TimeSeriesWidget initialized")
    
    def _setup_plot(self):
        """
        Setup the plot area with proper axes and grid.
        """
        # Check if pyqtgraph is available
        if not PYQTGRAPH_AVAILABLE:
             self.plot_widget = QLabel("PyQtGraph not available...")
             self.content_layout.addWidget(self.plot_widget)
             return
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground('w')
        self.plot_widget.showGrid(x=True, y=True, alpha=0.3)
        self.plot_widget.setLabel('left', 'Amplitude')
        self.plot_widget.setLabel('bottom', 'Time (samples)')
        self.plot_widget.getAxis('left').setPen(pg.mkPen(color='k', width=1))
        self.plot_widget.getAxis('bottom').setPen(pg.mkPen(color='k', width=1))
        self.plot_widget.setTitle(self.config.get("title", "Time Series")) # Lấy title từ config
        self.plot_lines = {}
        for i, channel in enumerate(self.config["channels"]):
            color = self.config["colors"][i % len(self.config["colors"])]
            plot_line = self.plot_widget.plot([], [], name=channel, pen=pg.mkPen(color=color, width=2))
            self.plot_lines[channel] = plot_line
        if self.config["show_legend"]:
            legend = self.plot_widget.addLegend(offset=(10, 10))
            legend.setBrush(pg.mkBrush(color='w', alpha=200))

        # Đặt plot_widget vào content_layout của BaseWidget
        self.content_layout.addWidget(self.plot_widget)

    def _setup_controls(self):
        """
        Setup control panel.
        """
        if not PYQTGRAPH_AVAILABLE:
            self.logger.warning("PyQtGraph not available, cannot setup controls.")
            # Khởi tạo các biến control là None để tránh lỗi sau này nếu được truy cập
            self.channel_selector = None
            self.auto_range_cb = None
            return # Không tạo control nếu không có đồ thị

        control_panel = QHBoxLayout()
        channel_label = QLabel("Channels:")
        self.channel_selector = QComboBox()
        self.channel_selector.addItem("All")
        for channel in self.config["channels"]:
            self.channel_selector.addItem(channel)
        self.channel_selector.currentIndexChanged.connect(self._on_channel_changed)

        self.auto_range_cb = QCheckBox("Auto Range")
        self.auto_range_cb.setChecked(self.config["auto_range"])
        self.auto_range_cb.stateChanged.connect(self._toggle_auto_range)

        control_panel.addWidget(channel_label)
        control_panel.addWidget(self.channel_selector)
        control_panel.addStretch(1)
        control_panel.addWidget(self.auto_range_cb)

        # Thêm control_panel vào layout chính của widget (layout từ BaseWidget)
        self.layout.addLayout(control_panel) # Thêm vào layout chính
    
    def update_data(self, data):
        """
        Update the widget with new time series data.
        
        Args:
            data (dict): New time series data point
        """
        # Call parent method
        super().update_data(data)
        if 'timestamp' in data:
            self.time_buffer.append(data['timestamp'])
        else:
            self.time_buffer.append(len(self.time_buffer))
        for channel in self.config["channels"]:
            value = data.get(channel) # Dùng get để tránh lỗi nếu channel không có
            self.data_buffers[channel].append(value) # Lưu cả None
    
    def _update_plot(self):
        """
        Update the plot with current data.
        """
        if not PYQTGRAPH_AVAILABLE or not self.plot_lines or self.channel_selector is None:
            # self.logger.debug("Plot update skipped: PyQtGraph not available or UI not fully set up.")
            return
        # --- KẾT THÚC SỬA ĐỔI ---

        selected = self.channel_selector.currentText()
        something_plotted = False # Cờ kiểm tra xem có gì được vẽ không

        for channel, plot_line in self.plot_lines.items():
            plot_line.setVisible(selected == "All" or selected == channel) # Ẩn/hiện đường kẻ
            if plot_line.isVisible():
                data = list(self.data_buffers[channel])
                # Tạo trục thời gian đơn giản bằng index
                time_indices = list(range(len(data)))

                # Lọc bỏ các điểm dữ liệu None CÙNG với index tương ứng
                valid_indices = [t for t, d in zip(time_indices, data) if d is not None]
                valid_data = [d for d in data if d is not None]

                if valid_data: # Chỉ vẽ nếu có dữ liệu hợp lệ
                    plot_line.setData(valid_indices, valid_data)
                    something_plotted = True
                else:
                    plot_line.setData([], []) # Xóa đường kẻ nếu không có dữ liệu

        # Chỉ bật auto range nếu đang hiển thị và có dữ liệu được vẽ
        if self.plot_widget and hasattr(self.plot_widget, 'enableAutoRange'):
             if self.config["auto_range"] and something_plotted:
                  self.plot_widget.enableAutoRange(axis=pg.ViewBox.YAxis) # Chỉ auto range trục Y
                  # Có thể cần giới hạn auto range trục X nếu index quá lớn
                  # self.plot_widget.enableAutoRange(axis=pg.ViewBox.XAxis)
             else:
                  self.plot_widget.disableAutoRange(axis=pg.ViewBox.YAxis)
                  # Set Y range thủ công nếu auto range tắt
                  if not self.config["auto_range"]:
                      yrange = self.config.get("y_range", [-10, 10])
                      self.plot_widget.setYRange(yrange[0], yrange[1], padding=0.1) # Thêm padding
    
    def set_position(self, position):
        """
        Set the widget position in the grid.
        
        Args:
            position (tuple): Grid position as (row, column)
        """
        super().set_position(position)
    
    def set_size(self, size):
        """
        Set the widget size in the grid.
        
        Args:
            size (tuple): Grid size as (row_span, column_span)
        """
        super().set_size(size)
        
        # Update plot if size changed
        # if PYQTGRAPH_AVAILABLE and hasattr(self, 'plot_widget'):
        #     self.plot_widget.resize(self.width(), self.height())
    
    def _toggle_auto_range(self, state):
        """
        Toggle auto-range on/off.
        
        Args:
            state (int): Checkbox state
        """
        if not PYQTGRAPH_AVAILABLE or not self.plot_widget: return
        self.config["auto_range"] = (Qt.CheckState(state) == Qt.CheckState.Checked) # So sánh với enum
        self._update_plot() # Cập nhật lại plot để áp dụng
    
    def _on_channel_changed(self, index):
        """
        Handle channel selection change.
        
        Args:
            index (int): Selected index
        """
        # Update the plot immediately
        self._update_plot()


# How to modify functionality:
# 1. Add more plot types: Add methods to switch between line, scatter, bar plots
# 2. Add export functionality: Add methods to export plot as image or data as CSV
# 3. Add more controls: Add sliders for time range, zoom controls, etc.
# 4. Add annotations: Add methods to annotate the plot with markers or text
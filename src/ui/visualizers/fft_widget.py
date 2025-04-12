# File: src/ui/visualizers/fft_widget.py
# Purpose: Widget to display FFT (Fast Fourier Transform) data
# Target Lines: ≤150

"""
Methods to implement:
- __init__(self, parent=None, config=None): Initialize with optional parent and config
- update_data(self, data): Update widget with new data
- set_position(self, position): Set widget position
- set_size(self, size): Set widget size
- _setup_plot(self): Setup the plot area
- _update_plot(self): Update the plot with current data
- _compute_fft(self, data): Compute FFT from time series data
"""

import logging
import numpy as np
from collections import deque
from PyQt6.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QSlider, QCheckBox
from PyQt6.QtCore import Qt, QTimer

try:
    import pyqtgraph as pg
    PYQTGRAPH_AVAILABLE = True
except ImportError:
    PYQTGRAPH_AVAILABLE = False

from src.ui.visualizers.base_widget import BaseWidget


class FFTWidget(BaseWidget):
    """
    Widget to display FFT (Fast Fourier Transform) data.
    
    Computes and visualizes frequency domain representation of time series data.
    """
    
    def __init__(self, parent=None, config=None):
        """
        Initialize the FFT widget.
        
        Args:
            parent (QWidget, optional): Parent widget
            config (dict, optional): Widget configuration
        """
        # Default configuration
        default_config = {
            "title": "FFT Analysis", "max_points": 512, "update_interval": 200,
            "sample_rate": 100, "show_legend": True, "show_grid": True,
            "window_function": "hanning", "channels": ["accel_x", "accel_y", "accel_z"],
            "colors": ["#0F9D58", "#4285F4", "#DB4437"], "max_freq": 50, "log_scale": False,
        }
        if config: default_config.update(config)
        super().__init__(parent, default_config)

        self.data_buffers = {}
        for channel in self.config["channels"]:
            self.data_buffers[channel] = deque(maxlen=self.config["max_points"])
        self.fft_results = {}
        self.frequencies = np.array([])
        self.update_timer = QTimer()
        self.update_timer.setInterval(self.config["update_interval"])
        self.update_timer.timeout.connect(self._update_plot)

        self._setup_plot()

        # --- SỬA ĐỔI: Gọi _setup_controls() ---
        self._setup_controls()
        # --- KẾT THÚC SỬA ĐỔI ---

        self.update_timer.start()
        self.logger.info("FFTWidget initialized")
    
    def _setup_plot(self):
        """
        Setup the FFT plot area with proper axes and grid.
        """
        if not PYQTGRAPH_AVAILABLE:
            self.plot_widget = QLabel("PyQtGraph not available...")
            self.content_layout.addWidget(self.plot_widget)
            return
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground('w')
        self.plot_widget.showGrid(x=True, y=True, alpha=0.3)
        self.plot_widget.setLabel('left', 'Magnitude')
        self.plot_widget.setLabel('bottom', 'Frequency (Hz)')
        self.plot_widget.getAxis('left').setPen(pg.mkPen(color='k', width=1))
        self.plot_widget.getAxis('bottom').setPen(pg.mkPen(color='k', width=1))
        self.plot_widget.setTitle(self.config.get("title", "FFT Analysis")) # Lấy title từ config
        self.plot_widget.setLogMode(y=self.config["log_scale"])
        self.plot_widget.setXRange(0, self.config["max_freq"])
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
            self.channel_selector = None
            self.log_scale_cb = None
            self.window_selector = None
            return # Không tạo control nếu không có đồ thị

        control_panel = QHBoxLayout()
        channel_label = QLabel("Channel:")
        self.channel_selector = QComboBox()
        self.channel_selector.addItem("All")
        for channel in self.config["channels"]:
            self.channel_selector.addItem(channel)
        self.channel_selector.currentIndexChanged.connect(self._on_channel_changed)

        self.log_scale_cb = QCheckBox("Log Scale")
        self.log_scale_cb.setChecked(self.config["log_scale"])
        self.log_scale_cb.stateChanged.connect(self._toggle_log_scale)

        window_label = QLabel("Window:")
        self.window_selector = QComboBox()
        self.window_selector.addItems(["None", "Hanning", "Hamming", "Blackman"])
        window_idx = {"none": 0, "hanning": 1, "hamming": 2, "blackman": 3}.get(self.config.get("window_function", "hanning").lower(), 1)
        self.window_selector.setCurrentIndex(window_idx)
        self.window_selector.currentIndexChanged.connect(self._on_window_changed)

        control_panel.addWidget(channel_label)
        control_panel.addWidget(self.channel_selector)
        control_panel.addStretch(1)
        control_panel.addWidget(window_label)
        control_panel.addWidget(self.window_selector)
        control_panel.addWidget(self.log_scale_cb)

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
        for channel in self.config["channels"]:
            # Chỉ thêm nếu channel có trong dữ liệu và không phải None
            if channel in data and data[channel] is not None:
                try:
                    self.data_buffers[channel].append(float(data[channel]))
                except (ValueError, TypeError):
                     self.logger.debug(f"Non-numeric data for channel {channel} in FFTWidget, skipping.")
            # Không thêm gì nếu channel không có hoặc là None

    
    def _compute_fft(self, data):
        """
        Compute FFT from time series data.
        
        Args:
            data (list): Time series data
            
        Returns:
            tuple: (frequencies, magnitudes)
        """
        if not data or len(data) == 0:
            return np.array([]), np.array([])
        data_array = np.array(data)
        n_points = len(data_array)
        # Cần đủ điểm để tính FFT hiệu quả
        if n_points < 2: return np.array([]), np.array([])

        # Áp dụng window function
        window_func = self.config.get("window_function", "hanning").lower()
        if window_func == "hanning": window = np.hanning(n_points)
        elif window_func == "hamming": window = np.hamming(n_points)
        elif window_func == "blackman": window = np.blackman(n_points)
        else: window = np.ones(n_points) # No window
        data_array = data_array * window

        # Tính FFT
        fft_result = np.fft.rfft(data_array)
        # Tính tần số
        sample_rate = self.config.get("sample_rate", 100)
        frequencies = np.fft.rfftfreq(n_points, 1.0 / sample_rate)
        # Tính độ lớn, chuẩn hóa theo số điểm và window gain (ước lượng)
        # Chuẩn hóa đơn giản bằng N/2 cho tín hiệu thực
        magnitudes = np.abs(fft_result) / (n_points / 2)

        # Apply log scale if needed
        if self.config.get("log_scale", False):
            magnitudes = 20 * np.log10(magnitudes + 1e-9) # dB scale

        # Filter to max frequency
        max_freq = self.config.get("max_freq", sample_rate / 2)
        max_idx = np.searchsorted(frequencies, max_freq, side="right")
        return frequencies[:max_idx], magnitudes[:max_idx]
    
    def _update_plot(self):
        """
        Update the plot with current FFT data.
        """
        # --- SỬA ĐỔI: Thêm kiểm tra channel_selector tồn tại ---
        if not PYQTGRAPH_AVAILABLE or not self.plot_lines or self.channel_selector is None:
            # self.logger.debug("Plot update skipped: PyQtGraph not available or UI not fully set up.")
            return
        # --- KẾT THÚC SỬA ĐỔI ---

        selected = self.channel_selector.currentText()
        plot_updated = False # Kiểm tra xem có gì được vẽ không

        for channel, plot_line in self.plot_lines.items():
             plot_line.setVisible(selected == "All" or selected == channel)
             if plot_line.isVisible():
                 data = list(self.data_buffers[channel])
                 if len(data) == self.config["max_points"]: # Chỉ tính FFT khi buffer đầy? Hoặc đủ lớn?
                      frequencies, magnitudes = self._compute_fft(data)
                      if frequencies.size > 0: # Kiểm tra có kết quả FFT không
                           self.fft_results[channel] = magnitudes
                           self.frequencies = frequencies
                           plot_line.setData(frequencies, magnitudes)
                           plot_updated = True
                      else:
                           plot_line.setData([], []) # Xóa nếu không tính được FFT
                 else:
                      plot_line.setData([], []) # Xóa nếu chưa đủ dữ liệu


        # Cập nhật log scale và X range sau khi vẽ
        if self.plot_widget and hasattr(self.plot_widget, 'setLogMode'):
             self.plot_widget.setLogMode(y=self.config["log_scale"])
             # Tự động điều chỉnh Y range nếu cần, trừ khi log scale đang bật
             if not self.config["log_scale"] and plot_updated:
                  self.plot_widget.enableAutoRange(axis=pg.ViewBox.YAxis, enable=True)
             elif not plot_updated: # Nếu không có gì vẽ, reset Y range
                  self.plot_widget.setYRange(0, 1) # Đặt range mặc định nhỏ

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
    
    def _toggle_log_scale(self, state):
        """
        Toggle log scale on/off.
        
        Args:
            state (int): Checkbox state
        """
        if not self.plot_widget: return
        self.config["log_scale"] = (Qt.CheckState(state) == Qt.CheckState.Checked)
        self._update_plot() # Cập nhật plot để áp dụng scale
    
    def _on_channel_changed(self, index):
        """
        Handle channel selection change.
        
        Args:
            index (int): Selected index
        """
        # Update the plot immediately
        self._update_plot()
    
    def _on_window_changed(self, index):
        """
        Handle window function change.
        
        Args:
            index (int): Selected index
        """
        if not self.window_selector: return
        windows = ["none", "hanning", "hamming", "blackman"]
        self.config["window_function"] = windows[index]
        self._update_plot() # Cập nhật plot để áp dụng window mới

# How to modify functionality:
# 1. Add more FFT options: Add controls for sample rate, FFT size, etc.
# 2. Add peak detection: Add methods to detect and mark frequency peaks
# 3. Add spectrogram view: Add option to switch to spectrogram (2D time-frequency) view
# 4. Add export functionality: Add methods to export FFT data as CSV
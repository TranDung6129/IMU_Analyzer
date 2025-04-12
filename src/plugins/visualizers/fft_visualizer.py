# File: src/plugins/visualizers/fft_visualizer.py
# Purpose: Visualize frequency domain data using FFT
# Target Lines: ≤150

"""
Methods to implement:
- __init__(self, config=None): Initialize with optional configuration
- init(self, config): Initialize or re-initialize with new configuration
- visualize(self, data): Process and prepare FFT data for visualization
- destroy(self): Clean up resources
"""

import logging
import numpy as np
from collections import deque
from src.plugins.visualizers.base_visualizer import BaseVisualizer


class FFTVisualizer(BaseVisualizer):
    """
    Visualizer for frequency domain data using Fast Fourier Transform.
    
    Computes and visualizes the frequency spectrum of sensor data.
    """
    
    def __init__(self, config=None):
        """
        Initialize the FFT visualizer with optional configuration.
        
        Args:
            config (dict, optional): Configuration with the following keys:
                - fields (list): List of fields to compute FFT for (default: ['accel_x', 'accel_y', 'accel_z'])
                - buffer_size (int): Number of samples to use for FFT (default: 256)
                - sample_rate (float): Sample rate in Hz (default: 100.0)
                - freq_range (list): Frequency range to display [min_freq, max_freq] (default: [0, 50])
                - window_type (str): Window function ('hann', 'hamming', 'blackman') (default: 'hann')
                - scale (str): Scale for magnitude ('linear', 'log', 'db') (default: 'linear')
                - colors (dict): Colors for each field's spectrum (default: auto-generated)
        """
        super().__init__(config)
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # --- LOGIC KHỞI TẠO CỤ THỂ ---
        # Gán giá trị mặc định TRƯỚC KHI đọc config
        self.fields = ['accel_x', 'accel_y', 'accel_z']
        self.buffer_size = 256
        self.sample_rate = 100.0
        self.freq_range = [0, 50]
        self.window_type = 'hann'
        self.scale = 'linear'
        self.colors = {}
        self.default_colors = [ # Giữ nguyên default colors
            '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
            '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf'
        ]

        # Data buffers và results (sẽ được khởi tạo trong init/update_config)
        self.data_buffers = {}
        self.fft_results = {}
        self.frequencies = None

        # Gọi init để xử lý config ban đầu và khởi tạo state
        # self.config được lấy từ lớp cha
        self.init(self.config) # Gọi init của chính lớp này

        # Đánh dấu initialized sau khi init thành công
        if not self.error_state:
             self.initialized = True
             self.logger.info("FFTVisualizer initialized successfully.")
        else:
             self.initialized = False
             self.logger.error("FFTVisualizer initialization failed due to configuration errors.")

    def init(self, config):
        """
        Initialize or re-initialize the visualizer with the specified configuration.
        ...
        """
        # Gọi init của lớp cha để cập nhật self.config
        super().init(config)
        # Giờ self.config đã được cập nhật

        effective_config = self.config # Sử dụng config đã cập nhật

        # --- Logic đọc config và cập nhật thuộc tính (như cũ) ---
        original_buffer_size = self.buffer_size # Lưu lại buffer_size cũ

        # Update fields
        if 'fields' in effective_config and isinstance(effective_config['fields'], list):
            self.fields = effective_config['fields']

        # Update buffer size
        if 'buffer_size' in effective_config:
            # ... (logic xử lý buffer_size như cũ) ...
            try:
                buffer_size = int(effective_config['buffer_size'])
                if buffer_size < 16: buffer_size = 16
                # Làm tròn lên lũy thừa của 2
                if not self._is_power_of_two(buffer_size):
                    new_size = 2 ** int(np.ceil(np.log2(buffer_size)))
                    buffer_size = new_size
                self.buffer_size = buffer_size
            except (ValueError, TypeError): self.logger.warning("Invalid buffer_size value, using current value")


        # Update sample rate
        if 'sample_rate' in effective_config:
            # ... (logic xử lý sample_rate như cũ) ...
            try:
                sample_rate = float(effective_config['sample_rate'])
                if sample_rate <= 0: self.logger.warning("sample_rate must be positive, using current value")
                else: self.sample_rate = sample_rate
            except (ValueError, TypeError): self.logger.warning("Invalid sample_rate value, using current value")

        # Update frequency range
        if 'freq_range' in effective_config and isinstance(effective_config['freq_range'], list) and len(effective_config['freq_range']) == 2:
             # ... (logic xử lý freq_range như cũ) ...
            try:
                min_freq, max_freq = float(effective_config['freq_range'][0]), float(effective_config['freq_range'][1])
                nyquist = self.sample_rate / 2
                min_freq = max(0, min_freq)
                max_freq = min(nyquist, max(max_freq, min_freq + 1.0)) # Đảm bảo max > min và <= nyquist
                self.freq_range = [min_freq, max_freq]
            except (ValueError, TypeError): self.logger.warning("Invalid freq_range values, using current value")


        # Update window type
        if 'window_type' in effective_config:
             # ... (logic xử lý window_type như cũ) ...
            window_type = str(effective_config['window_type']).lower()
            if window_type in ['hann', 'hamming', 'blackman']: self.window_type = window_type


        # Update scale
        if 'scale' in effective_config:
             # ... (logic xử lý scale như cũ) ...
            scale = str(effective_config['scale']).lower()
            if scale in ['linear', 'log', 'db']: self.scale = scale


        # Update colors
        if 'colors' in effective_config and isinstance(effective_config['colors'], dict):
            self.colors = effective_config['colors']

        # Khởi tạo lại buffer nếu buffer_size thay đổi hoặc lần đầu
        if self.buffer_size != original_buffer_size or not self.data_buffers:
             self.data_buffers = {} # Reset hoàn toàn

        # Khởi tạo/Cập nhật buffer và màu sắc cho từng field
        for i, field in enumerate(self.fields):
             if field not in self.data_buffers:
                 self.data_buffers[field] = deque([0.0] * self.buffer_size, maxlen=self.buffer_size) # Khởi tạo với 0.0
                 # self.data_buffers[field].extend([0.0] * self.buffer_size) # deque khởi tạo rỗng, dùng extend

             if field not in self.colors:
                 self.colors[field] = self.default_colors[i % len(self.default_colors)]

        # Tính toán lại trục tần số nếu sample_rate hoặc buffer_size thay đổi
        self._compute_frequency_axis()

        # Không đặt self.initialized ở đây, __init__ sẽ làm việc đó
        self.clear_error() # Xóa lỗi nếu cấu hình thành công
        return True
    
    def _is_power_of_two(self, n):
        """Check if a number is a power of two"""
        return n > 0 and (n & (n - 1)) == 0
    
    def _compute_frequency_axis(self):
        """Compute the frequency axis for FFT results"""
        # FFT frequencies
        self.frequencies = np.fft.rfftfreq(self.buffer_size, d=1.0/self.sample_rate)
    
    def _compute_window(self):
        """Compute the window function for FFT"""
        if self.window_type == 'hann':
            return np.hanning(self.buffer_size)
        elif self.window_type == 'hamming':
            return np.hamming(self.buffer_size)
        elif self.window_type == 'blackman':
            return np.blackman(self.buffer_size)
        else:
            return np.hanning(self.buffer_size)
    
    def visualize(self, data):
        """
        Process and prepare FFT data for visualization.
        ...
        """
        # --- SỬA ĐỔI BẮT ĐẦU: Xử lý data đầu vào ---
        # Data có thể là ProcessedData hoặc AnalysisResult (dict)
        original_data_dict = {}
        if isinstance(data, ProcessedData):
             original_data_dict = data.to_dict()
        elif isinstance(data, dict): # Giả sử là dict từ Processor hoặc Analyzer
             original_data_dict = data
        else:
             self.set_error(f"Invalid data type for visualization: {type(data)}")
             return None

        if not self.initialized:
             self.logger.warning("Visualizer not initialized, skipping visualization.")
             return None
        # --- SỬA ĐỔI KẾT THÚC ---

        # Process each field
        processed_any_field = False
        for field in self.fields:
             # --- SỬA ĐỔI BẮT ĐẦU: Lấy giá trị từ dict ---
             if field not in original_data_dict or original_data_dict[field] is None:
                 # self.logger.debug(f"Field '{field}' not found or is None in data for FFT.")
                 continue

             value = original_data_dict[field]
             # --- SỬA ĐỔI KẾT THÚC ---

             try:
                 value_float = float(value)
                 if field not in self.data_buffers: # Khởi tạo nếu chưa có
                     self.data_buffers[field] = deque([0.0] * self.buffer_size, maxlen=self.buffer_size)

                 self.data_buffers[field].append(value_float)
                 self._compute_fft(field)
                 processed_any_field = True

             except (ValueError, TypeError):
                 self.logger.debug(f"Field '{field}' has non-numeric value '{value}'. Cannot compute FFT.")
             except Exception as e:
                 self.logger.error(f"Unexpected error visualizing field {field}: {e}", exc_info=True)


        # Chỉ trả về data nếu có ít nhất một field được xử lý
        if not processed_any_field and not self.fft_results:
             self.logger.debug("No fields processed for FFT in this cycle.")
             return self.data_buffer # Trả về buffer cũ nếu có

        # Prepare visualization data for UI (như cũ)
        # ... (logic tạo viz_data như cũ) ...
        viz_data = {
            'type': 'fft',
            'frequencies': self.frequencies.tolist() if self.frequencies is not None else [],
            'spectra': {},
            'fields': list(self.fft_results.keys()), # Chỉ lấy fields thực sự có kết quả FFT
            'colors': {f: self.colors.get(f) for f in self.fft_results.keys()},
            'freq_range': self.freq_range,
            'scale': self.scale,
            'sample_rate': self.sample_rate
        }

        for field, fft_mag in self.fft_results.items():
             if self.frequencies is not None and len(fft_mag) == len(self.frequencies):
                 mask = (self.frequencies >= self.freq_range[0]) & (self.frequencies <= self.freq_range[1])
                 viz_data['spectra'][field] = {
                     'freq': self.frequencies[mask].tolist(),
                     'magnitude': fft_mag[mask].tolist()
                 }
             else:
                  self.logger.warning(f"Frequency axis or FFT magnitude mismatch for field {field}")


        self.data_buffer = viz_data # Cập nhật buffer
        super().visualize(data) # Tăng visualize_count
        return viz_data
    
    def _compute_fft(self, field):
        """
        Compute FFT for the specified field.
        
        Args:
            field (str): Field to compute FFT for
        """
        if field not in self.data_buffers:
            return
        
        # Get data buffer as numpy array
        data_array = np.array(self.data_buffers[field])
        
        # Apply window function
        window = self._compute_window()
        windowed_data = data_array * window
        
        # Compute FFT
        fft_result = np.abs(np.fft.rfft(windowed_data))
        
        # Scale the result
        if self.scale == 'linear':
            # Normalize by window energy
            fft_result = fft_result / np.sum(window)
        elif self.scale == 'log':
            # Log scale (add small value to avoid log(0))
            fft_result = np.log10(fft_result + 1e-10)
        elif self.scale == 'db':
            # dB scale (add small value to avoid log(0))
            fft_result = 20 * np.log10(fft_result + 1e-10)
        
        # Store result
        self.fft_results[field] = fft_result
    
    def destroy(self):
        """
        Clean up resources used by the visualizer.
        
        Returns:
            bool: True if successful, False otherwise
        """
        # Clear all data buffers
        for field in self.data_buffers:
            self.data_buffers[field].clear()
        
        # Clear FFT results
        self.fft_results = {}
        
        self.initialized = False
        self.clear_error()
        return True
    
    def get_peak_frequencies(self, field=None, num_peaks=3):
        """
        Get the peak frequencies for a specific field or all fields.
        
        Args:
            field (str, optional): Field to get peaks for, or None for all fields
            num_peaks (int): Number of peaks to return (default: 3)
            
        Returns:
            dict: Dictionary of peak frequencies and magnitudes
        """
        peaks = {}
        
        if field:
            # Get peaks for a specific field
            if field in self.fft_results and self.frequencies is not None:
                peaks[field] = self._find_peaks(field, num_peaks)
        else:
            # Get peaks for all fields
            for f in self.fields:
                if f in self.fft_results and self.frequencies is not None:
                    peaks[f] = self._find_peaks(f, num_peaks)
        
        return peaks
    
    def _find_peaks(self, field, num_peaks):
        """Find the strongest frequency peaks for a field"""
        # Get only the frequencies within the specified range
        mask = (self.frequencies >= self.freq_range[0]) & (self.frequencies <= self.freq_range[1])
        freqs = self.frequencies[mask]
        mags = self.fft_results[field][mask]
        
        # Find indices of peaks in descending order of magnitude
        peak_indices = np.argsort(mags)[-num_peaks:][::-1]
        
        # Collect peaks
        peaks = []
        for idx in peak_indices:
            peaks.append({
                'frequency': float(freqs[idx]),
                'magnitude': float(mags[idx])
            })
        
        return peaks


# How to extend and modify:
# 1. Add more FFT options: Modify init() to support different FFT algorithms or parameters
# 2. Add spectral features: Add methods to extract features like spectral centroid, bandwidth, etc.
# 3. Add overlapping windows: Modify to support overlapping FFT windows for smoother visualization
# 4. Add spectrogram visualization: Add support for time-frequency spectrograms
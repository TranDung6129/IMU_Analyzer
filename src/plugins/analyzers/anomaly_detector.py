# File: src/plugins/analyzers/anomaly_detector.py
# Purpose: Detect anomalies in sensor data using statistical methods
# Target Lines: ≤150

"""
Methods to implement:
- __init__(self, config=None): Initialize with optional configuration
- analyze(self, data): Analyze data and detect anomalies
- reset(self): Reset the anomaly detector state
- update_config(self, new_config): Update analyzer configuration
"""

import logging
import numpy as np
from collections import deque
from src.plugins.analyzers.base_analyzer import BaseAnalyzer
from src.data.models import AnalysisResult


class AnomalyDetector(BaseAnalyzer):
    """
    Detects anomalies in sensor data using statistical methods.
    
    Uses a sliding window approach to calculate mean and standard deviation,
    then flags values that exceed a threshold as anomalies.
    """
    
    def __init__(self, config=None):
        """
        Initialize the anomaly detector with optional configuration.
        
        Args:
            config (dict, optional): Configuration with the following keys:
                - threshold (float): Number of standard deviations to consider as anomaly (default: 3.0)
                - window_size (int): Size of sliding window for statistics (default: 100)
                - fields (list): List of fields to monitor for anomalies (default: ['accel_x', 'accel_y', 'accel_z'])
                - min_window_size (int): Minimum window size before detection starts (default: 10)
        """
        super().__init__(config)
        self.logger = logging.getLogger(self.__class__.__name__)
        
        
        # --- LOGIC KHỞI TẠO CỤ THỂ ---
        # Gán giá trị mặc định TRƯỚC KHI đọc config
        self.threshold = 3.0
        self.window_size = 100
        self.min_window_size = 10
        self.fields = ['accel_x', 'accel_y', 'accel_z'] # Default fields

        # Data windows và statistics (sẽ được khởi tạo trong reset/update_config)
        self.data_windows = {}
        self.means = {}
        self.stds = {}

        # Gọi update_config để xử lý config ban đầu và khởi tạo state
        # self.config được lấy từ lớp cha
        self.update_config(self.config) # Gọi update_config của chính lớp này

        # Đánh dấu initialized sau khi update_config thành công
        if not self.error_state:
             self.initialized = True
             self.logger.info("AnomalyDetector initialized successfully.")
        else:
             self.initialized = False
             self.logger.error("AnomalyDetector initialization failed due to configuration errors.")
    
    def update_config(self, new_config):
        """
        Update the anomaly detector configuration.
        
        Args:
            new_config (dict): New configuration dictionary
            
        Returns:
            bool: True if successful, False otherwise
        """
        # Gọi update_config của lớp cha để cập nhật self.config
        super().update_config(new_config)
        effective_config = self.config # Sử dụng config đã cập nhật

        if not isinstance(new_config, dict):
            self.set_error("Configuration must be a dictionary")
            return False
        
        # Update threshold
        if 'threshold' in effective_config:
            try:
                threshold = float(effective_config['threshold'])
                if threshold <= 0: self.logger.warning("Threshold must be positive, using current value")
                else: self.threshold = threshold
            except (ValueError, TypeError): self.logger.warning("Invalid threshold value, using current value")
        
        # Update window size
        if 'window_size' in effective_config:
            try:
                window_size = int(effective_config['window_size'])
                if window_size < 10: self.window_size = 10
                else: self.window_size = window_size
            except (ValueError, TypeError): self.logger.warning("Invalid window size, using current value")
        
        # Update minimum window size
        if 'min_window_size' in effective_config:
            # ... (logic xử lý min_window_size như cũ) ...
            try:
                min_window_size = int(effective_config['min_window_size'])
                if min_window_size < 1: self.min_window_size = 1
                elif min_window_size > self.window_size: self.min_window_size = self.window_size
                else: self.min_window_size = min_window_size
            except (ValueError, TypeError): self.logger.warning("Invalid minimum window size, using current value")

        # Update fields to monitor
        if 'fields' in effective_config and isinstance(effective_config['fields'], list):
            self.fields = effective_config['fields']

        # Reset state (quan trọng: gọi sau khi các tham số đã được cập nhật)
        self.reset()

        # Không đặt self.initialized ở đây, __init__ sẽ làm việc đó
        self.clear_error() # Xóa lỗi nếu cấu hình thành công
        return True
    
    def reset(self):
        """
        Reset the anomaly detector state.
        ...
        """
        # Initialize data windows for each field (sử dụng self.fields đã cập nhật)
        self.data_windows = {field: deque(maxlen=self.window_size) for field in self.fields}
        self.means = {field: 0.0 for field in self.fields}
        self.stds = {field: 0.0 for field in self.fields}
        self.analyze_count = 0 # Reset counter
        self.analyze_errors = 0
        self.logger.debug("Anomaly detector state reset.")
        self.clear_error()
        return True
    
    def analyze(self, data):
        """
        Analyze data to detect anomalies.
        ...
        """
        # --- SỬA ĐỔI BẮT ĐẦU: Xử lý ProcessedData ---
        # Kiểm tra xem data có phải là ProcessedData không
        original_data_dict = {}
        if isinstance(data, ProcessedData):
             original_data_dict = data.to_dict() # Chuyển đổi thành dict nếu cần
        elif isinstance(data, dict):
             original_data_dict = data
        else:
             self.set_error(f"Invalid data type for analysis: {type(data)}")
             return None

        if not self.initialized:
             self.logger.warning("Analyzer not initialized, skipping analysis.")
             # Không raise lỗi, chỉ bỏ qua để pipeline không bị dừng
             return None # Hoặc trả về AnalysisResult rỗng
        # --- SỬA ĐỔI KẾT THÚC ---

        # Create base analysis result
        result = AnalysisResult()
        result.processed_data_id = original_data_dict.get('id', None) # Lấy ID từ dict
        result.sensor_id = original_data_dict.get('sensor_id', None)
        result.timestamp = original_data_dict.get('timestamp', None) # Thêm timestamp

        anomalies = {}
        max_anomaly_score = 0.0

        # Check each field for anomalies
        for field in self.fields:
            # --- SỬA ĐỔI BẮT ĐẦU: Lấy giá trị từ dict ---
            if field not in original_data_dict or original_data_dict[field] is None:
                # self.logger.debug(f"Field '{field}' not found or is None in data, skipping.")
                continue # Bỏ qua nếu field không có hoặc là None

            value = original_data_dict[field]
            # --- SỬA ĐỔI KẾT THÚC ---

            try:
                value_float = float(value)

                # Add value to window (đảm bảo field tồn tại trong data_windows)
                if field not in self.data_windows:
                     self.data_windows[field] = deque(maxlen=self.window_size)
                     self.means[field] = 0.0
                     self.stds[field] = 0.0

                self.data_windows[field].append(value_float)

                # Skip analysis if not enough data
                if len(self.data_windows[field]) < self.min_window_size:
                    continue

                # Calculate statistics
                window_array = np.array(self.data_windows[field])
                current_mean = np.mean(window_array)
                current_std = np.std(window_array)
                self.means[field] = current_mean # Lưu lại mean/std hiện tại
                self.stds[field] = current_std

                if current_std == 0:
                    z_score = 0.0 # Nếu std là 0, z_score là 0
                else:
                    z_score = abs(value_float - current_mean) / current_std

                anomaly_score = min(z_score / self.threshold, 1.0) if self.threshold > 0 else (1.0 if z_score > 0 else 0.0)
                max_anomaly_score = max(max_anomaly_score, anomaly_score)
                is_anomaly = z_score > self.threshold

                anomalies[field] = {
                    'value': value_float, 'mean': current_mean, 'std': current_std,
                    'z_score': z_score, 'anomaly_score': anomaly_score, 'is_anomaly': is_anomaly
                }

            except (ValueError, TypeError) as e:
                self.logger.warning(f"Field '{field}' has non-numeric value '{value}'. Cannot analyze. Error: {e}")
            except Exception as e:
                 self.logger.error(f"Unexpected error analyzing field {field}: {e}", exc_info=True)


        result.anomaly_score = max_anomaly_score
        result.results['threshold'] = self.threshold
        result.results['anomalies'] = anomalies

        # ... (phần còn lại của logic dự đoán và metadata như cũ) ...
        if max_anomaly_score >= 1.0: # Sửa thành >= 1.0 vì score đã chuẩn hóa
            result.prediction = "Significant Anomaly"
            result.confidence = max_anomaly_score
        elif max_anomaly_score > 0.5:
            result.prediction = "Possible Anomaly"
            result.confidence = max_anomaly_score

        result.analysis_metadata = {
            'analyzer_type': 'statistical', 'window_size': self.window_size,
            'fields_analyzed': self.fields, 'threshold': self.threshold
        }


        # Cập nhật số lượt phân tích thành công
        super().analyze(data) # Gọi hàm cha để tăng analyze_count

        return result



# How to extend and modify:
# 1. Add different anomaly detection methods: Modify analyze() to use more advanced methods like IQR or DBSCAN
# 2. Add support for multivariate analysis: Modify to consider correlations between fields
# 3. Add adaptive thresholding: Modify to dynamically adjust threshold based on data characteristics
# 4. Add trend detection: Add methods to detect trends or patterns over time
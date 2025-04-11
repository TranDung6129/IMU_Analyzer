# File: IMUAnalyzer/src/core/config_loader.py
# Mục đích: Tải, hợp nhất và xác thực cấu hình từ các tệp YAML
# Số dòng mục tiêu: ≤200

"""
Các phương thức cần triển khai:
- __init__(self, config_dir): Khởi tạo với thư mục chứa cấu hình
- load(self): Tải và hợp nhất tất cả các tệp cấu hình, trả về dictionary
- _load_file(self, file_path): Tải một tệp YAML
- _merge_configs(self, config1, config2): Hợp nhất hai cấu hình, ưu tiên config2
- _validate(self, config): Xác thực cấu trúc và giá trị của cấu hình
"""

import os
import yaml
import logging


class ConfigLoader:
    """
    Tải và xác thực cấu hình từ nhiều tệp YAML.
    Hỗ trợ hợp nhất cấu hình từ các tệp khác nhau với ưu tiên.
    """
    
    def __init__(self, config_dir):
        """
        Khởi tạo ConfigLoader với thư mục chứa các tệp cấu hình.
        
        Args:
            config_dir (str): Đường dẫn đến thư mục chứa các tệp cấu hình
        """
        self.config_dir = config_dir
        self.logger = logging.getLogger("ConfigLoader")
        
        # Các tệp cấu hình cần tải theo thứ tự (các tệp sau ghi đè các tệp trước)
        self.config_files = [
            "default.yaml",
            "pipelines.yaml",
            "sensors.yaml",
            "dashboard.yaml"
        ]
    
    def load(self):
        """
        Tải tất cả các tệp cấu hình và hợp nhất chúng thành một cấu hình duy nhất.
        
        Returns:
            dict: Dictionary cấu hình đã hợp nhất
        """
        # Tạo các tệp cấu hình mặc định nếu chúng không tồn tại
        self._create_default_configs()
        
        merged_config = {}
        
        for config_file in self.config_files:
            file_path = os.path.join(self.config_dir, config_file)
            if os.path.exists(file_path):
                config = self._load_file(file_path)
                merged_config = self._merge_configs(merged_config, config)
                self.logger.info(f"Đã tải cấu hình từ {file_path}")
            else:
                self.logger.warning(f"Tệp cấu hình không tìm thấy: {file_path}")
        
        # Xác thực cấu hình đã hợp nhất
        self._validate(merged_config)
        
        return merged_config

    
    def _load_file(self, file_path):
        """
        Tải một tệp cấu hình YAML.
        
        Args:
            file_path (str): Đường dẫn đến tệp YAML
            
        Returns:
            dict: Cấu hình từ tệp
            
        Raises:
            Exception: Nếu tệp không thể đọc hoặc phân tích
        """
        try:
            with open(file_path, 'r') as config_file:
                config = yaml.safe_load(config_file)
                return config if config else {}
        except Exception as e:
            self.logger.error(f"Không thể tải tệp cấu hình {file_path}: {str(e)}")
            return {}
    
    def _merge_configs(self, config1, config2):
        """
        Hợp nhất hai dictionary cấu hình, với config2 được ưu tiên.
        
        Args:
            config1 (dict): Cấu hình cơ bản
            config2 (dict): Cấu hình được hợp nhất lên trên cơ bản
            
        Returns:
            dict: Cấu hình đã hợp nhất
        """
        if not config1:
            return config2
        if not config2:
            return config1
            
        merged = config1.copy()
        
        for key, value in config2.items():
            # Nếu cả hai cấu hình đều có key và cả hai giá trị đều là dict, hợp nhất đệ quy
            if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
                merged[key] = self._merge_configs(merged[key], value)
            else:
                # Nếu không, giá trị của config2 ghi đè config1
                merged[key] = value
                
        return merged
    
    def _validate(self, config):
        """
        Xác thực cấu trúc và giá trị của cấu hình.
        
        Args:
            config (dict): Cấu hình cần xác thực
            
        Raises:
            ValueError: Nếu cấu hình không hợp lệ
        """
        # Xác thực các phần bắt buộc
        required_sections = ["logging", "system", "ui", "plugins"]
        for section in required_sections:
            if section not in config:
                self.logger.warning(f"Thiếu phần bắt buộc: {section}")
        
        # #TODO: Thêm xác thực cụ thể hơn cho từng phần cấu hình
        
        # Xác thực phần logging
        if "logging" in config:
            log_config = config["logging"]
            
            # Xác thực mức độ log
            if "level" in log_config:
                valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
                if log_config["level"] not in valid_levels:
                    self.logger.warning(f"Mức độ logging không hợp lệ: {log_config['level']}. Phải là một trong {valid_levels}")
                    log_config["level"] = "INFO"  # Đặt mặc định
        
        # Xác thực phần system
        if "system" in config:
            sys_config = config["system"]
            
            # Xác thực max_pipelines
            if "max_pipelines" in sys_config:
                if not isinstance(sys_config["max_pipelines"], int) or sys_config["max_pipelines"] <= 0:
                    self.logger.warning(f"max_pipelines không hợp lệ: {sys_config['max_pipelines']}. Phải là một số nguyên dương")
                    sys_config["max_pipelines"] = 5  # Đặt mặc định
            
            # Xác thực monitor_interval
            if "monitor_interval" in sys_config:
                if not isinstance(sys_config["monitor_interval"], (int, float)) or sys_config["monitor_interval"] <= 0:
                    self.logger.warning(f"monitor_interval không hợp lệ: {sys_config['monitor_interval']}. Phải là một số dương")
                    sys_config["monitor_interval"] = 1.0  # Đặt mặc định
        
        # Xác thực phần UI
        if "ui" in config:
            ui_config = config["ui"]
            
            # Xác thực refresh_rate
            if "refresh_rate" in ui_config:
                if not isinstance(ui_config["refresh_rate"], int) or ui_config["refresh_rate"] < 1 or ui_config["refresh_rate"] > 60:
                    self.logger.warning(f"refresh_rate không hợp lệ: {ui_config['refresh_rate']}. Phải nằm trong khoảng từ 1 đến 60")
                    ui_config["refresh_rate"] = 30  # Đặt mặc định
        
        # #TODO: Xác thực cấu trúc của pipelines.yaml
        # #TODO: Xác thực cấu trúc của sensors.yaml
        # #TODO: Xác thực cấu trúc của dashboard.yaml
        
        return True
    
    def _create_default_configs(self):
        """
        Tạo các tệp cấu hình mặc định nếu chúng không tồn tại.
        """
        # Đảm bảo thư mục cấu hình tồn tại
        os.makedirs(self.config_dir, exist_ok=True)
        
        # Cấu hình mặc định
        default_configs = {
            "default.yaml": {
                "logging": {"level": "INFO", "format": "[%(asctime)s][%(name)s][%(levelname)s] %(message)s", "file": "logs/imu_analyzer.log"},
                "system": {"max_pipelines": 5, "monitor_interval": 1.0, "thread_timeout": 2.0},
                "data": {"storage_path": "./data", "max_buffer_size": 10000},
                "ui": {"theme": "dark", "default_layout": "default_layout.json", "refresh_rate": 30},
                "plugins": {"auto_reload": True, "plugin_dirs": [
                    "src/io/readers", "src/io/writers", "src/plugins/decoders",
                    "src/plugins/processors", "src/plugins/analyzers", "src/plugins/visualizers", "src/plugins/exporters"
                ]}
            },
            # Các phiên bản tối thiểu của các tệp cấu hình khác sẽ được thêm vào đây
        }
        
        for filename, config in default_configs.items():
            file_path = os.path.join(self.config_dir, filename)
            if not os.path.exists(file_path):
                try:
                    with open(file_path, 'w') as f:
                        yaml.dump(config, f, default_flow_style=False)
                    self.logger.info(f"Đã tạo tệp cấu hình mặc định: {file_path}")
                except Exception as e:
                    self.logger.error(f"Không thể tạo tệp cấu hình mặc định {file_path}: {str(e)}")


# Hướng dẫn chỉnh sửa chức năng:
# 1. Thêm file config mới: Thêm tên file vào danh sách self.config_files trong __init__
# 2. Thêm logic validate: Mở rộng phương thức `_validate()` để kiểm tra cấu trúc và giá trị của các phần config
# 3. Thay đổi cách đọc file: Sửa phương thức `_load_file()` nếu muốn hỗ trợ định dạng khác ngoài YAML
# 4. Thay đổi ưu tiên hợp nhất: Sửa phương thức `_merge_configs()`` để thay đổi cách xử lý xung đột

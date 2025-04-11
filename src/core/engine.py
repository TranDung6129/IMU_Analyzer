# File: IMUAnalyzer/src/core/engine.py
# Mục đích: Bộ máy lõi điều phối toàn bộ hệ thống
# Các dòng mục tiêu: ≤400

"""
Các phương thức cần triển khai:
- __init__(self, config): Khởi tạo với cấu hình đầy đủ
- setup(self): Thiết lập PluginManager, SystemMonitor, SensorRegistry, và tạo các pipeline
- _setup_pipelines(self): Tạo các pipeline từ config["pipelines"]
- _setup_monitor(self): Khởi tạo SystemMonitor với config["system"]["monitor_interval"]
- _setup_sensor_registry(self): Khởi tạo SensorRegistry với config["sensors"]
- run(self): Chạy tất cả các pipeline và SystemMonitor
- stop(self): Dừng tất cả các pipeline và SystemMonitor
"""

import logging
import threading
from PyQt6.QtWidgets import QApplication
from src.core.plugin_manager import PluginManager
from src.system.monitor import SystemMonitor
from src.system.sensor_registry import SensorRegistry
from src.core.pipeline import PipelineExecutor
from src.ui.main_window import MainWindow
from src.ui_adapter.engine_adapter import EngineAdapter
from src.ui_adapter.data_bridge import DataBridge


class Engine:
    """
    Bộ máy lõi điều phối tất cả các thành phần của hệ thống IMU Analyzer.
    Quản lý các pipeline, hệ thống plugin, giám sát, và tích hợp giao diện người dùng.
    """
    
    def __init__(self, config):
        """
        Khởi tạo Engine với cấu hình.
        
        Args:
            config (dict): Từ điển cấu hình đầy đủ
        """
        self.config = config
        self.logger = logging.getLogger("Engine")
        self.pipelines = {}
        self.running = False
        self.plugin_manager = None
        self.system_monitor = None
        self.sensor_registry = None
        self.main_window = None
        self.engine_adapter = None
        self.data_bridge = None
        
        # Thiết lập logging dựa trên cấu hình
        self._setup_logging()
    
    def _setup_logging(self):
        """Cấu hình logging dựa trên cấu hình."""
        log_config = self.config.get("logging", {})
        log_level = getattr(logging, log_config.get("level", "INFO"))
        log_format = log_config.get("format", "[%(asctime)s][%(name)s][%(levelname)s] %(message)s")
        log_file = log_config.get("file", "logs/imu_analyzer.log")
        
        # Tạo formatter
        formatter = logging.Formatter(log_format)
        
        # Cấu hình root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(log_level)
        
        # Xóa các handler hiện có
        root_logger.handlers = []
        
        # Thêm console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
        
        # Thêm file handler nếu được chỉ định
        if log_file:
            import os
            # Đảm bảo thư mục log tồn tại
            os.makedirs(os.path.dirname(log_file), exist_ok=True)
            
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)
    
    def setup(self):
        """
        Thiết lập tất cả các thành phần của hệ thống.
        """
        self.logger.info("Đang thiết lập IMU Analyzer Engine")
        
        # Tạo plugin manager
        plugin_dirs = self.config.get("plugins", {}).get("plugin_dirs", [])
        self.plugin_manager = PluginManager(plugin_dirs)
        self.plugin_manager.discover_plugins()
        
        # Thiết lập sensor registry
        self._setup_sensor_registry()
        
        # Thiết lập system monitor
        self._setup_monitor()
        
        # Thiết lập data bridge để tích hợp giao diện người dùng
        self.data_bridge = DataBridge()
        
        # Thiết lập các thành phần giao diện người dùng nếu chạy ở chế độ GUI
        self._setup_ui()
        
        # Thiết lập engine adapter để kết nối giao diện người dùng và backend
        self.engine_adapter = EngineAdapter()
        self.engine_adapter.set_engine(self)
        
        # Tạo và thiết lập các pipeline
        self._setup_pipelines()
        
        self.logger.info("Hoàn tất thiết lập Engine")
    
    def _setup_sensor_registry(self):
        """
        Khởi tạo sensor registry với cấu hình cảm biến.
        """
        sensors_config = self.config.get("sensors", {})
        self.sensor_registry = SensorRegistry()
        
        # Đăng ký tất cả các cảm biến từ cấu hình
        for sensor in sensors_config.get("sensors", []):
            self.sensor_registry.register_sensor(sensor)
            self.logger.info(f"Đã đăng ký cảm biến: {sensor.get('id', 'unknown')}")
    
    def _setup_monitor(self):
        """
        Khởi tạo system monitor.
        """
        monitor_interval = self.config.get("system", {}).get("monitor_interval", 1.0)
        self.system_monitor = SystemMonitor(interval=monitor_interval)
        self.logger.info(f"Đã khởi tạo system monitor với khoảng thời gian: {monitor_interval}s")
    
    def _setup_ui(self):
        """
        Thiết lập cửa sổ chính và các thành phần giao diện người dùng.
        """
        # Kiểm tra nếu đang trong ngữ cảnh QApplication
        if QApplication.instance():
            self.main_window = MainWindow(self.config)
            # Kết nối data bridge với cửa sổ chính
            self.data_bridge.connect_to_ui(self.main_window)
            self.logger.info("Đã khởi tạo các thành phần giao diện người dùng")
        else:
            self.logger.warning("Không chạy ở chế độ GUI, các thành phần giao diện người dùng sẽ không được khởi tạo")
    
    def _setup_pipelines(self):
        """
        Tạo các pipeline executor dựa trên cấu hình pipeline.
        """
        pipeline_configs = self.config.get("pipelines", [])
        max_pipelines = self.config.get("system", {}).get("max_pipelines", 5)
        
        # Kiểm tra nếu có quá nhiều pipeline
        if len(pipeline_configs) > max_pipelines:
            self.logger.warning(f"Có quá nhiều pipeline được cấu hình: {len(pipeline_configs)}. Tối đa là {max_pipelines}.")
            pipeline_configs = pipeline_configs[:max_pipelines]
        
        # Tạo từng pipeline
        for pipeline_config in pipeline_configs:
            pipeline_id = pipeline_config.get("id")
            
            if not pipeline_id:
                self.logger.error("Cấu hình pipeline thiếu trường 'id' bắt buộc")
                continue
                
            if not pipeline_config.get("enabled", True):
                self.logger.info(f"Pipeline '{pipeline_id}' bị vô hiệu hóa, bỏ qua")
                continue
            
            try:
                pipeline = PipelineExecutor(pipeline_config, self.plugin_manager)
                self.pipelines[pipeline_id] = pipeline
                pipeline.setup()
                
                # Đăng ký pipeline với data bridge để cập nhật giao diện người dùng
                if self.data_bridge:
                    self.data_bridge.register_pipeline(pipeline_id, pipeline)
                
                self.logger.info(f"Pipeline '{pipeline_id}' đã được thiết lập thành công")
            except Exception as e:
                self.logger.error(f"Không thể thiết lập pipeline '{pipeline_id}': {str(e)}")
    
    def run(self):
        """
        Bắt đầu tất cả các thành phần của hệ thống.
        """
        if self.running:
            self.logger.warning("Engine đã chạy")
            return
        
        self.logger.info("Đang khởi động IMU Analyzer Engine")
        self.running = True
        
        # Bắt đầu system monitor
        if self.system_monitor:
            self.system_monitor.start()
        
        # Bắt đầu tất cả các pipeline
        for pipeline_id, pipeline in self.pipelines.items():
            try:
                pipeline.run()
                self.logger.info(f"Đã bắt đầu pipeline: {pipeline_id}")
            except Exception as e:
                self.logger.error(f"Không thể bắt đầu pipeline '{pipeline_id}': {str(e)}")
        
        # Hiển thị cửa sổ chính nếu ở chế độ GUI
        if self.main_window:
            self.main_window.show()
            self.logger.info("Đã hiển thị cửa sổ chính")
    
    def stop(self):
        """
        Dừng tất cả các thành phần của hệ thống.
        """
        if not self.running:
            self.logger.warning("Engine chưa chạy")
            return
        
        self.logger.info("Đang dừng IMU Analyzer Engine")
        self.running = False
        
        # Dừng tất cả các pipeline
        for pipeline_id, pipeline in self.pipelines.items():
            try:
                pipeline.stop()
                self.logger.info(f"Đã dừng pipeline: {pipeline_id}")
            except Exception as e:
                self.logger.error(f"Lỗi khi dừng pipeline '{pipeline_id}': {str(e)}")
        
        # Dừng system monitor
        if self.system_monitor:
            self.system_monitor.stop()
        
        self.logger.info("Engine đã dừng")
    
    def get_pipeline(self, pipeline_id):
        """
        Lấy một pipeline cụ thể theo ID.
        
        Args:
            pipeline_id (str): ID của pipeline cần lấy
            
        Returns:
            PipelineExecutor: Pipeline được yêu cầu, hoặc None nếu không tìm thấy
        """
        return self.pipelines.get(pipeline_id)
    
    def start_pipeline(self, pipeline_id):
        """
        Bắt đầu một pipeline cụ thể theo ID.
        
        Args:
            pipeline_id (str): ID của pipeline cần bắt đầu
            
        Returns:
            bool: True nếu pipeline được bắt đầu, False nếu không
        """
        pipeline = self.get_pipeline(pipeline_id)
        if pipeline:
            try:
                pipeline.run()
                self.logger.info(f"Đã bắt đầu pipeline: {pipeline_id}")
                return True
            except Exception as e:
                self.logger.error(f"Không thể bắt đầu pipeline '{pipeline_id}': {str(e)}")
        else:
            self.logger.error(f"Không tìm thấy pipeline: {pipeline_id}")
        return False
    
    def stop_pipeline(self, pipeline_id):
        """
        Dừng một pipeline cụ thể theo ID.
        
        Args:
            pipeline_id (str): ID của pipeline cần dừng
            
        Returns:
            bool: True nếu pipeline được dừng, False nếu không
        """
        pipeline = self.get_pipeline(pipeline_id)
        if pipeline:
            try:
                pipeline.stop()
                self.logger.info(f"Đã dừng pipeline: {pipeline_id}")
                return True
            except Exception as e:
                self.logger.error(f"Lỗi khi dừng pipeline '{pipeline_id}': {str(e)}")
        else:
            self.logger.error(f"Không tìm thấy pipeline: {pipeline_id}")
        return False
    
# Hướng dẫn chỉnh sửa chức năng
# 1. Thay đổi cách xử lý logging: Sửa phương thức _setup_logging() để thay đổi format hoặc thêm handler khác
# 2. Thêm chế độ non-GUI: Khi muốn chạy chỉ backend, sửa phương thức _setup_ui() và logic trong run()
# 3. Thêm xử lý tín hiệu dừng: Thêm code bắt signal trong run() để gọi stop() khi nhận SIGINT/SIGTERM
# 4. Mở rộng quản lý pipeline: Thêm phương thức mới vào class để thêm/xóa/tạm dừng pipeline trong thời gian chạy

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

import traceback
import sys
import logging
import threading
from typing import TYPE_CHECKING, Any, Dict
from PyQt6.QtWidgets import QApplication
from src.core.plugin_manager import PluginManager
from src.system.monitor import SystemMonitor
from src.system.sensor_registry import SensorRegistry
from src.core.pipeline import PipelineExecutor
from src.ui_adapter.data_bridge import DataBridge
from src.ui.main_window import MainWindow

# Tránh circular import bằng cách lazy import
if TYPE_CHECKING:
    from src.ui_adapter.engine_adapter import EngineAdapter


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
        self.sensor_registry = SensorRegistry()  # Initialize sensor registry
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
        
        # Tạo plugin manager với đường dẫn rõ ràng
        import os
        
        # Đường dẫn tuyệt đối đến thư mục gốc của dự án
        project_root = os.path.abspath(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        # Tạo đường dẫn đến các thư mục plugin
        plugin_dirs = [
            os.path.join(project_root, "io", "readers"),
            os.path.join(project_root, "io", "writers"),
            os.path.join(project_root, "plugins", "decoders"),
            os.path.join(project_root, "plugins", "processors"),
            os.path.join(project_root, "plugins", "analyzers"),
            os.path.join(project_root, "plugins", "visualizers"),
            os.path.join(project_root, "plugins", "exporters"),
            os.path.join(project_root, "plugins", "configurators")
        ]
        
        # In thông tin debug về các đường dẫn
        self.logger.info(f"Project root: {project_root}")
        for p_dir in plugin_dirs:
            if os.path.exists(p_dir):
                self.logger.info(f"Plugin directory exists: {p_dir}")
                # Liệt kê các tệp trong thư mục
                try:
                    files = os.listdir(p_dir)
                    self.logger.info(f"  Files: {files}")
                except Exception as e:
                    self.logger.error(f"  Error listing files: {str(e)}")
            else:
                self.logger.warning(f"Plugin directory does not exist: {p_dir}")
        
        # Khởi tạo plugin manager
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
        # Lazy import để tránh circular import
        from src.ui_adapter.engine_adapter import EngineAdapter
        self.engine_adapter = EngineAdapter()
        self.engine_adapter.set_engine(self)
        
        # Tạo và thiết lập các pipeline
        self._setup_pipelines()
        
        self.logger.info("Hoàn tất thiết lập Engine")
    
    def _setup_sensor_registry(self):
        """
        Khởi tạo sensor registry với cấu hình cảm biến.
        """
        sensors_config = self.config.get("sensors", [])
        # Đăng ký tất cả các cảm biến từ cấu hình
        for sensor in sensors_config:
            if isinstance(sensor, dict):
                self.sensor_registry.register_sensor(sensor)
                self.logger.info(f"Đã đăng ký cảm biến: {sensor.get('id', 'unknown')}")
    
    def _setup_monitor(self):
        """
        Khởi tạo system monitor.
        """
        system_config = self.config.get("system", {})
        monitor_interval = system_config.get("monitor_interval", 1.0)
        enable_logging = system_config.get("monitor_logging", True)
        log_interval = system_config.get("monitor_log_interval", 60.0)
        
        self.system_monitor = SystemMonitor(
            interval=monitor_interval,
            logger=enable_logging,
            log_interval=log_interval
        )
        self.logger.info(f"Đã khởi tạo system monitor với khoảng thời gian: {monitor_interval}s")
    
    def _setup_ui(self):
        """
        Thiết lập cửa sổ chính và các thành phần giao diện người dùng.
        """
        self.logger.debug("Entering _setup_ui...") # Thêm log bắt đầu
        try:
            app = QApplication.instance()
            if not app:
                self.logger.warning("QApplication instance not found during UI setup.")
                # Có thể return hoặc raise lỗi ở đây nếu muốn dừng sớm
                # return

            self.logger.debug("Attempting to create MainWindow...")
            self.main_window = MainWindow(self.config)
            self.logger.debug(f"MainWindow object created: {self.main_window is not None}")

            # Kiểm tra MainWindow đã được tạo chưa trước khi tiếp tục
            if self.main_window:
                self.logger.debug("Setting up dashboard...")
                self.main_window.setup_dashboard()
                self.logger.debug("Dashboard setup called.")

                # Kết nối DataBridge SAU KHI dashboard đã setup
                if self.data_bridge:
                    self.logger.debug("Connecting DataBridge to UI...")
                    self.data_bridge.connect_to_ui(self.main_window)
                    self.logger.debug("DataBridge connected.")
                else:
                    self.logger.warning("DataBridge is None, cannot connect to UI.")

                self.logger.info("UI setup completed successfully in Engine try block.") # Log thành công trong try
            else:
                # Lỗi này không nên xảy ra nếu MainWindow constructor không raise exception
                # Nhưng để chắc chắn
                self.logger.error("MainWindow object is None after creation attempt.")
                # Không cần raise ở đây, khối except bên ngoài sẽ xử lý

        except Exception as e:
            # --- SỬA ĐỔI QUAN TRỌNG ---
            self.logger.error(f"!!! Exception caught during UI setup: {str(e)}")
            # In traceback trực tiếp ra console/stderr
            print("--- TRACEBACK START ---", file=sys.stderr)
            traceback.print_exc()
            print("--- TRACEBACK END ---", file=sys.stderr)
            # Ghi log kèm traceback (vẫn giữ lại phòng trường hợp logger hoạt động)
            self.logger.error(f"Failed to setup UI in Engine (see console for full traceback): {str(e)}\n{traceback.format_exc()}")
            # --- KẾT THÚC SỬA ĐỔI ---
            self.main_window = None # Đặt main_window thành None khi có lỗi

        self.logger.debug("Exiting _setup_ui...") # Thêm log kết thúc

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
            
            # Cấu hình cảm biến nếu có configurator
            if "configurator" in pipeline_config and pipeline_config["configurator"]:
                try:
                    configurator_config = pipeline_config["configurator"]
                    configurator_type = configurator_config.get("type")
                    if configurator_type:
                        configurator = self.plugin_manager.get_or_create_plugin(
                            "configurators", configurator_type, configurator_config.get("config", {})
                        )
                        configurator.configure()
                        self.logger.info(f"Đã cấu hình cảm biến cho pipeline '{pipeline_id}' sử dụng {configurator_type}")
                except Exception as e:
                    self.logger.error(f"Không thể cấu hình cảm biến cho pipeline '{pipeline_id}': {str(e)}")
            
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
    
    def start(self):
        """
        Start the engine and all components.
        """
        try:
            if self.running:
                self.logger.warning("Engine already running.")
                return
            self.logger.info("Starting IMU Analyzer Engine")
            self.running = True

            # Start system monitor
            if self.system_monitor:
                 if hasattr(self.system_monitor, 'start') and callable(self.system_monitor.start):
                      self.system_monitor.start()
                 else:
                      self.logger.warning("SystemMonitor does not have a 'start' method.")


            # Kết nối engine adapter với main window (nếu chưa làm trong set_engine)
            if self.engine_adapter and self.main_window:
                 if hasattr(self.main_window, 'set_engine_adapter') and not self.main_window.engine_adapter:
                      self.main_window.set_engine_adapter(self.engine_adapter)

            # Bắt đầu các pipeline
            for pipeline_id, pipeline in self.pipelines.items():
                 # --- SỬA ĐỔI CÁCH KIỂM TRA ---
                 # if not pipeline.is_running(): # Lỗi ở đây
                 if not pipeline.running: # Sử dụng thuộc tính boolean 'running'
                 # --- KẾT THÚC SỬA ĐỔI ---
                     try:
                         pipeline.run() # Chạy pipeline
                         self.logger.info(f"Pipeline '{pipeline_id}' started.")
                     except Exception as e:
                         self.logger.error(f"Failed to start pipeline '{pipeline_id}': {str(e)}")

            # Việc hiển thị main window nên ở main.py
            # if self.main_window:
            #     self.main_window.show()

            self.logger.info("Engine started successfully")
        except Exception as e:
            self.logger.error(f"Failed to start engine: {str(e)}", exc_info=True)
            # Có thể raise lỗi ở đây để main.py biết engine không khởi động được
            # raise

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

    def configure_sensor(self, sensor_id: str, config: Dict):
        """        
        Cấu hình một cảm biến cụ thể với cấu hình được cung cấp.
        
        Args:
            sensor_id (str): ID của cảm biến cần cấu hình
            config (Dict): Cấu hình cần áp dụng cho cảm biến
        """
        try:
            # Tìm pipeline liên quan đến sensor_id
            pipeline_id = None
            for p_id, pipeline in self.pipelines.items():
                if hasattr(pipeline, 'config') and 'id' in pipeline.config:
                    if pipeline.config['id'] == sensor_id:
                        pipeline_id = p_id
                        break
            
            if not pipeline_id:
                # Không tìm thấy pipeline cụ thể, sử dụng pipeline đầu tiên
                if self.pipelines:
                    pipeline_id = next(iter(self.pipelines))
                    self.logger.info(f"Sử dụng pipeline {pipeline_id} để cấu hình cảm biến {sensor_id}")
                else:
                    self.logger.error(f"Không có pipeline nào để cấu hình cảm biến {sensor_id}")
                    return
            
            # Lấy thông tin configurator từ pipeline config
            pipeline_config = self.config.get("pipelines", [])
            configurator_config = None
            configurator_type = None
            
            for p_config in pipeline_config:
                if p_config.get("id") == pipeline_id and "configurator" in p_config:
                    configurator_config = p_config["configurator"]
                    configurator_type = configurator_config.get("type")
                    break
            
            if not configurator_type:
                self.logger.error(f"Không tìm thấy loại configurator trong pipeline {pipeline_id}")
                return
                
            # Tạo instance của configurator plugin
            try:
                # Sửa: Sử dụng create_plugin_instance thay vì load_plugin
                configurator = self.plugin_manager.create_plugin_instance(
                    "configurators", 
                    configurator_type, 
                    {**configurator_config.get("config", {}), **config}  # Kết hợp cấu hình từ file và từ tham số
                )
                
                # Gọi configure
                configurator.configure()
                
                # Cập nhật trạng thái cảm biến
                if self.sensor_registry:
                    self.sensor_registry.update_status(sensor_id, "configured")
                
                self.logger.info(f"Đã cấu hình thành công cảm biến {sensor_id} sử dụng {configurator_type}")
            except Exception as e:
                self.logger.error(f"Lỗi khi tạo configurator: {str(e)}")
                
        except Exception as e:
            self.logger.error(f"Lỗi khi cấu hình cảm biến {sensor_id}: {str(e)}")
    
    def get_available_devices(self) -> list:
        """
        Get list of available devices (e.g., serial ports, network addresses).
        
        Returns:
            list: List of available device names
        """
        try:
            # Placeholder: Actual device discovery implementation needed
            # For now, return a list of common serial ports
            return ["COM1", "COM2", "COM3", "/dev/ttyUSB0", "/dev/ttyUSB1"]
        except Exception as e:
            self.logger.error(f"Failed to get available devices: {str(e)}")
            return []

    def get_sensor_config(self, device: str) -> dict:
        """
        Get configuration for a specific sensor.
        
        Args:
            device: Device name to get configuration for
            
        Returns:
            dict: Sensor configuration
        """
        try:
            if device and self.sensor_registry:
                sensor = self.sensor_registry.get_sensor(device)
                if sensor:
                    return sensor["config"]
            return {}
        except Exception as e:
            self.logger.error(f"Failed to get sensor config: {str(e)}")
            return {}

    def get_pipeline(self, pipeline_id: str):
        """
        Get a specific pipeline by ID.
        
        Args:
            pipeline_id: ID of the pipeline to get
            
        Returns:
            Pipeline: The pipeline instance, or None if not found
        """
        try:
            if pipeline_id in self.pipelines:
                return self.pipelines[pipeline_id]
            return None
        except Exception as e:
            self.logger.error(f"Failed to get pipeline {pipeline_id}: {str(e)}")
            return None

    def get_visualizers(self):
        """
        Get all active visualizers.
        
        Returns:
            list: List of visualizer instances
        """
        try:
            if self.visualizers:
                return list(self.visualizers.values())
            return []
        except Exception as e:
            self.logger.error(f"Failed to get visualizers: {str(e)}")
            return []

    def get_sensor_registry(self):
        """
        Get the sensor registry.
        
        Returns:
            SensorRegistry: The sensor registry instance
        """
        return self.sensor_registry

    def _setup_sensor_registry(self):
        """
        Initialize and configure the sensor registry.
        """
        try:
            sensors_config = self.config.get("sensors", [])
            # Đăng ký tất cả các cảm biến từ cấu hình
            for sensor in sensors_config:
                if isinstance(sensor, dict):
                    self.sensor_registry.register_sensor(sensor)
            self.logger.info("Sensor registry setup completed")
        except Exception as e:
            self.logger.error(f"Failed to setup sensor registry: {str(e)}")

    def _setup_system_monitor(self):
        """
        Initialize and configure the system monitor.
        """
        try:
            self.system_monitor = SystemMonitor()
            self.system_monitor.start_monitoring()
            self.logger.info("System monitor setup completed")
        except Exception as e:
            self.logger.error(f"Failed to setup system monitor: {str(e)}")

    def _setup_ui(self):
        """
        Initialize and configure the UI components.
        """
        try:
            self.main_window = MainWindow(self.config)
            self.main_window.setup_ui()
            self.logger.info("UI setup completed")
        except Exception as e:
            self.logger.error(f"Failed to setup UI: {str(e)}")
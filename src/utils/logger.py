# File: src/utils/logger.py
# Mục đích: Các hàm tiện ích để cấu hình logging
# Các dòng mục tiêu: ≤150

"""
Các phương thức cần triển khai:
- get_logger(name, level, log_file=None): Cấu hình và trả về một logger
"""

import logging
import os


def get_logger(name, level=logging.INFO, log_file=None):
    """
    Cấu hình và trả về một logger với tên, mức độ và tùy chọn file handler được chỉ định.
    
    Args:
        name (str): Tên của logger
        level (int hoặc str): Mức độ logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file (str, optional): Đường dẫn đến file log
        
    Returns:
        logging.Logger: Logger đã
    """
    # Chuyển đổi mức độ từ chuỗi sang hằng số logging nếu cần
    if isinstance(level, str):
        level = getattr(logging, level.upper(), logging.INFO)
    
    # Tạo logger
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Xóa các handler hiện có nếu có
    if logger.handlers:
        logger.handlers = []
    
    # Tạo console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    
    # Tạo formatter
    formatter = logging.Formatter('[%(asctime)s][%(name)s][%(levelname)s] %(message)s')
    console_handler.setFormatter(formatter)
    
    # Thêm console handler vào logger
    logger.addHandler(console_handler)
    
    # Thêm file handler nếu log_file được chỉ định
    if log_file:
        # Tạo thư mục nếu chưa tồn tại
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
        
        # Tạo file handler
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        
        # Thêm file handler vào logger
        logger.addHandler(file_handler)
    
    return logger


def setup_logger():
    """
    Setup root logger configuration with both console and file handlers.
    
    Returns:
        logging.Logger: Root logger instance
    """
    try:
        # Get root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)
        
        # Create console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter('[%(asctime)s][%(name)s][%(levelname)s] %(message)s')
        console_handler.setFormatter(console_formatter)
        
        # Add console handler to root logger
        root_logger.addHandler(console_handler)
        
        # Create file handler
        log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, "imu_analyzer.log")
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter('[%(asctime)s][%(name)s][%(levelname)s] %(message)s')
        file_handler.setFormatter(file_formatter)
        
        # Add file handler to root logger
        root_logger.addHandler(file_handler)
        
        # Set up module-specific loggers
        module_loggers = [
            "src.core.engine",
            "src.core.config_loader",
            "src.ui.main_window",
            "src.ui_adapter.engine_adapter",
            "src.system.monitor",
            "src.system.sensor_registry"
        ]
        
        for module in module_loggers:
            logger = logging.getLogger(module)
            logger.setLevel(logging.DEBUG)
            
        return root_logger
    except Exception as e:
        print(f"Failed to setup logger: {str(e)}")
        raise

# Ví dụ sử dụng:
# logger = get_logger("ModuleName", "INFO", "logs/module.log")
# logger.info("Đây là một thông báo info")
# logger.error("Đây là một thông báo lỗi")

# Cách mở rộng và chỉnh sửa:
# 1. Tùy chỉnh định dạng log: Sửa mẫu formatter trong get_logger()
# 2. Thêm xoay vòng log: Triển khai RotatingFileHandler thay vì FileHandler
# 3. Thêm mức độ log: Tạo các hàm tiện ích cho các mức độ log cụ thể
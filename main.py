# File: IMUAnalyzer/main.py
# Mục đích: Điểm khởi đầu của ứng dụng IMU Analyzer
# Số dòng mục tiêu: ≤50

"""
Các phương thức cần triển khai:
- main(): Điểm khởi đầu tải cấu hình, thiết lập Engine, và chạy ứng dụng
"""

import sys
from src.core.engine import Engine
from src.core.config_loader import ConfigLoader
from PyQt6.QtWidgets import QApplication


def main():
    """
    Điểm khởi đầu của ứng dụng, khởi tạo và chạy IMU Analyzer.
    Tải cấu hình, thiết lập engine và khởi chạy ứng dụng.
    
    Trả về:
        int: Mã thoát của ứng dụng
    """
    # Tạo một instance của QApplication
    app = QApplication(sys.argv)
    
    # Tải cấu hình
    config_loader = ConfigLoader("config")
    config = config_loader.load()
    
    # Thiết lập và chạy engine
    engine = Engine(config)
    engine.setup()
    
    # Bắt đầu engine và vào vòng lặp sự kiện của Qt
    engine.run()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())


# Cách chỉnh sửa chức năng:
# 1. Thay đổi đường dẫn thư mục config: Sửa tham số trong ConfigLoader thành đường dẫn mới.
# 2. Thêm theme hoặc style cho ứng dụng: Thêm code `app = QApplication(sys.argv)` để thiết lập theme (ví dụ: app.setStyle("Fusion"))
# 3. Thêm xử lý dòng lệnh: Thêm `argparse` để xử lý tham số dòng lệnh trước khi khởi tạo Engine.
# 4. Thay đổi flow khởi động: Có thể tách riêng việc khởi tạo UI và Engine để hiện splash screen hoặc logo.

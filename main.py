"""
IMU Analyzer main entry point
"""

import sys
import argparse
import logging
import traceback
from pathlib import Path
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import QTimer
from src.core.engine import Engine
from src.core.config_loader import ConfigLoader
from src.utils.logger import setup_logger


def parse_arguments():
    """
    Parse command line arguments
    
    Returns:
        argparse.Namespace: Parsed arguments
    """
    parser = argparse.ArgumentParser(description="IMU Analyzer Application")
    parser.add_argument(
        '-c', '--config',
        type=str,
        default="config",
        help='Path to configuration directory'
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug mode'
    )
    parser.add_argument(
        '--version',
        action='version',
        version='IMU Analyzer 1.0.0'
    )
    return parser.parse_args()


def show_error_message(parent, message):
    """
    Show error message dialog
    
    Args:
        parent: Parent widget
        message: Error message
    """
    QMessageBox.critical(parent, "Error", message)



def main():
    """
    Main entry point of the IMU Analyzer application
    """
    app = QApplication(sys.argv)
    engine = None # Khởi tạo engine là None
    main_window = None # Khởi tạo main_window là None

    try:
        args = parse_arguments()
        root_logger = setup_logger()
        if args.debug:
            root_logger.setLevel(logging.DEBUG)
            root_logger.info("Debug mode enabled")

        app.setStyle('Fusion')

        config_loader = ConfigLoader(args.config)
        config = config_loader.load() # Có thể raise lỗi ở đây

        engine = Engine(config)
        engine.setup() # Có thể raise lỗi ở đây

        # Lấy main_window từ engine SAU KHI setup
        main_window = engine.main_window
        if not main_window:
             # Nếu setup UI thất bại trong engine, main_window sẽ là None
             raise RuntimeError("UI setup failed in Engine.")

        # --- SỬA ĐỔI BẮT ĐẦU ---
        # Bắt đầu engine TRƯỚC KHI hiển thị cửa sổ
        engine.start() # Có thể raise lỗi ở đây

        # Hiển thị cửa sổ SAU KHI engine đã start
        main_window.show()
        logging.info("Main window displayed.")
        # --- SỬA ĐỔI KẾT THÚC ---

        # Start Qt event loop
        exit_code = app.exec()
        logging.info(f"Application finished with exit code: {exit_code}")
        return exit_code

    except Exception as e:
        logging.error(f"Fatal error during application startup: {str(e)}", exc_info=True)
        # Hiển thị lỗi nếu có thể
        if 'app' in locals():
            # Tạo một cửa sổ tạm để hiển thị lỗi nếu main_window chưa tạo xong
            temp_parent = main_window if main_window else None
            show_error_message(temp_parent, f"Application failed to start:\n{str(e)}\n\nSee logs for details.")
        return 1
    finally:
        # Đảm bảo engine được dừng nếu nó đã được tạo
        if engine and engine.running:
             logging.info("Stopping engine due to exit or error...")
             engine.stop()

if __name__ == "__main__":
    sys.exit(main())
# File: src/ui/main_window.py
# Purpose: Main window of the application with all UI components
# Target Lines: ≤400

"""
Methods to implement:
- __init__(self, config): Initialize with configuration
- _setup_ui(self): Setup UI components
- start_engine(self): Start the engine
- stop_engine(self): Stop the engine
- setup_dashboard(self): Setup dashboard area
- update_dashboard(self, data): Update dashboard with data
- update_monitor(self, stats): Update system monitor
"""

import logging
import os
import sys
import traceback
from PyQt6.QtWidgets import (
    QMainWindow, QTabWidget, QWidget, QVBoxLayout,
    QHBoxLayout, QSplitter, QStatusBar, QLabel,
    QPushButton, QMessageBox, QDialog, QListWidget,
    QListWidgetItem, QDialogButtonBox
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QIcon, QAction

# Import dashboard components
from src.ui.dashboard.dashboard_manager import DashboardManager
from src.ui.dashboard.widget_manager import WidgetManager
# Thêm import cho các panel để kiểm tra lỗi import tiềm ẩn
from src.ui.panels.config_panel import ConfigPanel
from src.ui.panels.connection_panel import ConnectionPanel
from src.ui.panels.sensor_panel import SensorPanel
from src.ui.panels.plugin_panel import PluginPanel
from src.ui.panels.monitor_panel import MonitorPanel

class MainWindow(QMainWindow):
    """
    Main window of the application.
    
    Contains all UI components including:
    - Menu bar
    - Tool bar
    - Left panel (config, connection, sensor, plugin panels)
    - Dashboard area
    - System monitor
    - Status bar
    """
    
    def __init__(self, config):
        """
        Initialize the main window with configuration.
        ...
        """
        super().__init__()
        self.logger = logging.getLogger("MainWindow")
        self.logger.debug("Initializing MainWindow...") # Log bắt đầu init

        self.config = config
        self.dashboard_manager = None
        self.widget_manager = None
        self.dashboard_widgets = {}
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update_ui)
        self.engine_adapter = None # Khởi tạo là None

        # --- THÊM TRY-EXCEPT BAO QUANH _setup_ui ---
        try:
            self._setup_ui()
            self.logger.info("Main window UI setup completed successfully in __init__.")
        except Exception as e:
            self.logger.error(f"!!! Exception during MainWindow._setup_ui: {str(e)}")
            print("--- TRACEBACK IN MainWindow.__init__ ---", file=sys.stderr)
            traceback.print_exc()
            print("--- TRACEBACK END ---", file=sys.stderr)
            self.logger.error(f"MainWindow UI setup failed: {str(e)}\n{traceback.format_exc()}")
            # Có thể raise lỗi ở đây để Engine biết init thất bại hoàn toàn
            raise # Re-raise lỗi để Engine bắt được

        self.logger.info("MainWindow initialized.")

    
    def _setup_ui(self):
        """
        Setup UI components.
        """
        self.logger.debug("Starting _setup_ui...")
        # Set window properties
        self.setWindowTitle("IMU Analyzer")
        self.resize(1000, 600)
        self.logger.debug("Window properties set.")

        # Setup central widget and layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(5, 5, 5, 5)
        self.logger.debug("Central widget and main layout setup.")

        # Create main splitter
        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.main_layout.addWidget(self.main_splitter)
        self.logger.debug("Main splitter created.")

        # Setup left panel
        self.logger.debug("Setting up left panel...")
        self._setup_left_panel()
        self.logger.debug("Left panel setup finished.")

        # Setup dashboard area
        self.logger.debug("Setting up dashboard area...")
        self._setup_dashboard_area()
        self.logger.debug("Dashboard area setup finished.")

        # Setup menu bar
        self.logger.debug("Setting up menu bar...")
        self._setup_menu_bar()
        self.logger.debug("Menu bar setup finished.")

        # Setup tool bar
        self.logger.debug("Setting up tool bar...")
        self._setup_tool_bar()
        self.logger.debug("Tool bar setup finished.")

        # Setup status bar
        self.logger.debug("Setting up status bar...")
        self._setup_status_bar()
        self.logger.debug("Status bar setup finished.")

        # Set splitter sizes
        self.main_splitter.setSizes([250, 750])
        self.logger.debug("Splitter sizes set.")

        # Set theme
        ui_config = self.config.get("ui", {})
        theme = ui_config.get("theme", "dark")
        self._apply_theme(theme)
        self.logger.debug(f"Theme '{theme}' applied.")

        # Start UI update timer
        update_interval = ui_config.get("refresh_rate", 30)
        # Đảm bảo update_interval > 0
        if update_interval <= 0:
            update_interval = 1 # Tránh chia cho 0
            self.logger.warning("Invalid refresh_rate, using 1 FPS.")
        self.update_timer.start(1000 // update_interval)
        self.logger.debug(f"UI update timer started with interval {1000 // update_interval} ms.")
        self.logger.debug("_setup_ui finished.")
    
    def _setup_left_panel(self):
        """
        Setup left panel with tabs for configuration, connection, and sensors.
        """
        self.logger.debug("Starting _setup_left_panel...")
        self.left_panel = QWidget()
        self.left_panel.setMaximumWidth(400)
        self.left_panel.setMinimumWidth(200)
        left_layout = QVBoxLayout(self.left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        self.left_tabs = QTabWidget()
        left_layout.addWidget(self.left_tabs)

        self.logger.debug("Creating ConfigPanel...")
        self.config_panel = ConfigPanel() # Có thể lỗi ở đây
        self.left_tabs.addTab(self.config_panel, "Config")
        self.logger.debug("ConfigPanel added.")

        self.logger.debug("Creating ConnectionPanel...")
        self.connection_panel = ConnectionPanel() # Có thể lỗi ở đây
        self.left_tabs.addTab(self.connection_panel, "Connection")
        self.logger.debug("ConnectionPanel added.")

        self.logger.debug("Creating SensorPanel...")
        self.sensor_panel = SensorPanel() # Có thể lỗi ở đây
        self.left_tabs.addTab(self.sensor_panel, "Sensors")
        self.logger.debug("SensorPanel added.")

        self.logger.debug("Creating PluginPanel...")
        self.plugin_panel = PluginPanel() # Có thể lỗi ở đây
        self.left_tabs.addTab(self.plugin_panel, "Plugins")
        self.logger.debug("PluginPanel added.")

        self.logger.debug("Creating MonitorPanel...")
        self.monitor_panel = MonitorPanel() # Có thể lỗi ở đây
        self.left_tabs.addTab(self.monitor_panel, "Monitor")
        self.logger.debug("MonitorPanel added.")

        self.main_splitter.addWidget(self.left_panel)
        self.logger.debug("_setup_left_panel finished.")

    def _setup_dashboard_area(self):
        """
        Setup dashboard area.
        """
        self.logger.debug("Starting _setup_dashboard_area...")
        self.dashboard_area = QWidget()
        self.dashboard_layout = QVBoxLayout(self.dashboard_area)
        self.dashboard_layout.setContentsMargins(0, 0, 0, 0)
        self.dashboard_content = QWidget() # Container cho dashboard manager
        self.dashboard_layout.addWidget(self.dashboard_content)
        self.dashboard_content_layout = QVBoxLayout(self.dashboard_content) # Layout cho container
        self.dashboard_content_layout.setContentsMargins(0, 0, 0, 0)

        self.main_splitter.addWidget(self.dashboard_area)
        self.logger.debug("_setup_dashboard_area finished. DashboardManager will be created in setup_dashboard().")
    
    def _setup_menu_bar(self):
        """
        Setup menu bar with proper actions and visibility.
        """
        # Ensure menu is visible
        self.menuBar().setNativeMenuBar(False)
        
        # File menu
        file_menu = self.menuBar().addMenu("&File")
        
        # Add Load Config action
        load_config_action = QAction("&Load Configuration", self)
        load_config_action.setShortcut("Ctrl+L")
        file_menu.addAction(load_config_action)
        
        # Add Save Config action
        save_config_action = QAction("&Save Configuration", self)
        save_config_action.setShortcut("Ctrl+S")
        file_menu.addAction(save_config_action)
        
        file_menu.addSeparator()
        
        # Exit action
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # View menu
        view_menu = self.menuBar().addMenu("&View")
        
        # Add theme options
        theme_menu = view_menu.addMenu("&Theme")
        
        dark_theme_action = QAction("&Dark", self)
        dark_theme_action.triggered.connect(lambda: self._apply_theme("dark"))
        theme_menu.addAction(dark_theme_action)
        
        light_theme_action = QAction("&Light", self)
        light_theme_action.triggered.connect(lambda: self._apply_theme("light"))
        theme_menu.addAction(light_theme_action)
        
        # Add refresh action
        refresh_action = QAction("&Refresh", self)
        refresh_action.setShortcut("F5")
        refresh_action.triggered.connect(self.update_ui)
        view_menu.addAction(refresh_action)
    
    def _setup_tool_bar(self):
        """
        Setup tool bar.
        """
        # Main toolbar
        main_toolbar = self.addToolBar("Main")
        main_toolbar.setMovable(False)
        
        # Start action
        start_action = QAction("Start All", self)
        start_action.triggered.connect(self.start_engine)
        main_toolbar.addAction(start_action)
        
        # Stop action
        stop_action = QAction("Stop All", self)
        stop_action.triggered.connect(self.stop_engine)
        main_toolbar.addAction(stop_action)
        
        main_toolbar.addSeparator()
        
        # Export actions
        export_csv_action = QAction("Export CSV", self)
        export_csv_action.triggered.connect(self.export_csv)
        main_toolbar.addAction(export_csv_action)
        
        export_json_action = QAction("Export JSON", self)
        export_json_action.triggered.connect(self.export_json)
        main_toolbar.addAction(export_json_action)
    
    def _setup_status_bar(self):
        """
        Setup status bar.
        """
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Status label
        self.status_label = QLabel("Status: Ready")
        self.status_bar.addWidget(self.status_label, 1)
        
        # Pipeline throughput label
        self.throughput_label = QLabel("Pipeline throughput: 0 Hz")
        self.status_bar.addWidget(self.throughput_label)
        
        # CPU usage label
        self.cpu_label = QLabel("CPU: 0%")
        self.status_bar.addWidget(self.cpu_label)
        
        # Memory usage label
        self.memory_label = QLabel("Memory: 0 MB")
        self.status_bar.addWidget(self.memory_label)
    
    def _apply_theme(self, theme):
        """
        Apply the specified theme to the UI.
        
        Args:
            theme (str): Theme name ('dark' or 'light')
        """
        # Basic theming
        if theme == 'dark':
            self.setStyleSheet("""
                QMainWindow { background-color: #333; color: #EEE; }
                QWidget { background-color: #333; color: #EEE; }
                QPushButton { background-color: #555; color: #EEE; border: 1px solid #777; padding: 5px; border-radius: 3px; }
                QPushButton:hover { background-color: #666; }
                QTabWidget::pane { border: 1px solid #777; }
                QTabBar::tab { background-color: #444; color: #EEE; padding: 5px 10px; }
                QTabBar::tab:selected { background-color: #555; }
            """)
        else:  # light theme is default
            self.setStyleSheet("")  # Use system default
    
    def set_engine_adapter(self, engine_adapter):
        """
        Set the engine adapter for interacting with the backend.
        
        Args:
            engine_adapter: Engine adapter instance
        """
        self.engine_adapter = engine_adapter
        self.logger.info("Engine adapter set in main window")
    
    def update_ui(self):
        """
        Update UI components periodically.
        
        This method is called by the update timer.
        """
        # If engine adapter is available, fetch system stats
        if self.engine_adapter:
            try:
                # Check if engine has system monitor and get stats
                engine = self.engine_adapter.engine
                if engine and hasattr(engine, 'system_monitor'):
                    system_stats = engine.system_monitor.get_system_stats()
                    if system_stats:
                        self.update_monitor(system_stats)
            except Exception as e:
                self.logger.debug(f"Error updating system stats: {str(e)}")
    
    def start_engine(self):
        """
        Start the engine.
        
        This method is called when the Start All button is clicked.
        """
        if self.engine_adapter:
            try:
                # Start all pipelines
                for pipeline_id in self.engine_adapter.engine.pipelines.keys():
                    self.engine_adapter.start_pipeline(pipeline_id)
                self.status_label.setText("Status: Running")
                self.logger.info("Engine started")
            except Exception as e:
                self.logger.error(f"Error starting engine: {str(e)}")
                self.status_label.setText("Status: Start failed")
                QMessageBox.critical(self, "Error", f"Failed to start engine: {str(e)}")
        else:
            self.logger.warning("No engine adapter available")
            self.status_label.setText("Status: No engine")
    
    def stop_engine(self):
        """
        Stop the engine.
        
        This method is called when the Stop All button is clicked.
        """
        if self.engine_adapter:
            try:
                # Stop all pipelines
                for pipeline_id in self.engine_adapter.engine.pipelines.keys():
                    self.engine_adapter.stop_pipeline(pipeline_id)
                self.status_label.setText("Status: Stopped")
                self.logger.info("Engine stopped")
            except Exception as e:
                self.logger.error(f"Error stopping engine: {str(e)}")
                self.status_label.setText("Status: Stop failed")
                QMessageBox.critical(self, "Error", f"Failed to stop engine: {str(e)}")
        else:
            self.logger.warning("No engine adapter available")
            self.status_label.setText("Status: No engine")
    
    def setup_dashboard(self):
        """
        Setup dashboard with widgets from configuration.
        """
        self.logger.debug("Starting setup_dashboard...")
        try:
            # Clear existing layout if any
            # ... (logic xóa dashboard_manager cũ) ...
            if self.dashboard_manager:
                self.logger.debug("Removing existing dashboard manager.")
                # Lấy widget cha của dashboard_manager (là self.dashboard_content)
                container_widget = self.dashboard_manager.parentWidget()
                if container_widget:
                     container_widget.layout().removeWidget(self.dashboard_manager)
                self.dashboard_manager.deleteLater()
                self.dashboard_manager = None
            if self.widget_manager:
                self.widget_manager = None

            self.logger.debug("Creating DashboardManager...")
            # Tạo DashboardManager
            self.dashboard_manager = DashboardManager(parent=self.dashboard_content) # Đặt parent
            self.dashboard_content_layout.addWidget(self.dashboard_manager)
            self.logger.debug("DashboardManager added to layout.")

            self.logger.debug("Creating WidgetManager...")
            # Tạo WidgetManager, truyền DashboardManager vào
            self.widget_manager = WidgetManager(self.dashboard_manager)
            self.logger.debug("WidgetManager created.")

            # --- SỬA ĐỔI: Truyền WidgetManager vào DashboardManager ---
            # Sau khi cả hai được tạo, thiết lập liên kết
            if hasattr(self.dashboard_manager, 'set_widget_manager'):
                self.dashboard_manager.set_widget_manager(self.widget_manager)
            else:
                 # Nếu không có setter, có thể gán trực tiếp (không khuyến khích)
                 # self.dashboard_manager.widget_manager = self.widget_manager
                 self.logger.warning("DashboardManager does not have set_widget_manager method.")
            # --- KẾT THÚC SỬA ĐỔI ---


            default_layout_path = "config/dashboard.yaml"
            self.logger.debug(f"Checking for layout file: {default_layout_path}")
            # Truyền WidgetManager vào load_layout
            if not self.dashboard_manager.load_layout(default_layout_path, self.widget_manager):
                self.logger.warning(f"Layout file not found or failed to load: {default_layout_path}. Adding default widgets.")
                # Chỉ thêm widget mặc định nếu load thất bại VÀ file không tồn tại
                if not os.path.exists(default_layout_path) and self.widget_manager:
                     # WidgetManager.add_widget bây giờ đã đúng
                     self.widget_manager.add_widget("TimeSeriesWidget", {"title": "Acceleration"})
                     self.widget_manager.add_widget("FFTWidget", {"title": "FFT Analysis"})
                     self.logger.debug("Default widgets added.")
                     if self.status_label: self.status_label.setText("Status: Default widgets added")
                elif self.status_label:
                      self.status_label.setText("Status: Layout load failed")


            self.logger.info("Dashboard setup completed.")

        except Exception as e:
            # ... (xử lý lỗi như cũ) ...
            self.logger.error(f"!!! Exception during setup_dashboard: {str(e)}")
            print("--- TRACEBACK IN setup_dashboard ---", file=sys.stderr)
            traceback.print_exc()
            print("--- TRACEBACK END ---", file=sys.stderr)
            self.logger.error(f"Dashboard setup failed: {str(e)}\n{traceback.format_exc()}")
            if self.status_label: self.status_label.setText("Status: Dashboard setup failed!")
            QMessageBox.critical(self, "Dashboard Error", f"Failed to setup dashboard: {str(e)}")
    
    def update_dashboard(self, data):
        """
        Update dashboard with data.
        """
        # Thêm kiểm tra widget_manager
        if self.widget_manager:
            try:
                # Log data nhận được (có thể rất nhiều log)
                # self.logger.debug(f"Updating dashboard with data keys: {list(data.keys())}")
                # Cập nhật từng pipeline
                for pipeline_id, pipeline_data in data.items():
                     # Tìm dữ liệu phù hợp để cập nhật widget (visualized > analyzed > processed)
                     update_payload = None
                     if pipeline_data.get("visualized") is not None:
                          update_payload = pipeline_data["visualized"]
                     elif pipeline_data.get("analyzed") is not None:
                          update_payload = pipeline_data["analyzed"]
                     elif pipeline_data.get("processed") is not None:
                          update_payload = pipeline_data["processed"]

                     if update_payload:
                          # Giả định widget_manager có phương thức để cập nhật theo pipeline_id
                          # Hoặc cần tìm widget_id tương ứng với pipeline_id
                          # Ví dụ đơn giản: Cập nhật tất cả widget với cùng data (không đúng)
                          # self.widget_manager.update_all_widgets(update_payload)
                          # Cần cơ chế mapping pipeline_id -> widget_id hoặc widget type
                          # Tạm thời log để xem data
                          # self.logger.debug(f"Data for pipeline {pipeline_id}: {update_payload}")
                          pass # Logic cập nhật widget cụ thể cần xem xét lại

            except Exception as e:
                self.logger.error(f"Error updating dashboard: {str(e)}", exc_info=True) # Thêm exc_info
        # else:
        #     self.logger.warning("WidgetManager not available for dashboard update.")
    
    def update_monitor(self, stats):
        """
        Update system monitor with stats.
        
        Args:
            stats (dict): System statistics
        """
        if stats:
            # Update CPU usage
            cpu_usage = stats.get("cpu_usage", 0)
            self.cpu_label.setText(f"CPU: {cpu_usage:.0f}%")
            
            # Update memory usage
            memory_usage = stats.get("process_memory_formatted", "0 MB")
            self.memory_label.setText(f"Memory: {memory_usage}")
            
            # Update pipeline throughput
            throughput = stats.get("pipeline_throughput", 0)
            self.throughput_label.setText(f"Pipeline throughput: {throughput:.0f} Hz")
    
    def save_dashboard_layout(self):
        """
        Save the current dashboard layout.
        
        This method is called when the Save Layout button is clicked.
        """
        if self.dashboard_manager:
            try:
                # Save to default location
                layout_path = "config/dashboard_layout.json"
                if self.dashboard_manager.save_layout(layout_path):
                    self.status_label.setText("Status: Layout saved")
                    self.logger.info(f"Dashboard layout saved to {layout_path}")
                    QMessageBox.information(self, "Success", f"Layout saved to {layout_path}")
                else:
                    self.status_label.setText("Status: Layout save failed")
                    self.logger.warning("Failed to save dashboard layout")
            except Exception as e:
                self.logger.error(f"Error saving dashboard layout: {str(e)}")
                self.status_label.setText("Status: Layout save failed")
                QMessageBox.critical(self, "Error", f"Failed to save layout: {str(e)}")
        else:
            self.logger.warning("No dashboard manager available")
            self.status_label.setText("Status: No dashboard manager")
    
    def load_dashboard_layout(self):
        """
        Load a saved dashboard layout.
        
        This method is called when the Load Layout button is clicked.
        """
        if self.dashboard_manager:
            try:
                # Load from default location
                layout_path = "config/dashboard_layout.json"
                if os.path.exists(layout_path):
                    if self.dashboard_manager.load_layout(layout_path):
                        self.status_label.setText("Status: Layout loaded")
                        self.logger.info(f"Dashboard layout loaded from {layout_path}")
                    else:
                        self.status_label.setText("Status: Layout load failed")
                        self.logger.warning(f"Failed to load dashboard layout from {layout_path}")
                else:
                    self.status_label.setText("Status: Layout file not found")
                    self.logger.warning(f"Layout file not found: {layout_path}")
                    QMessageBox.warning(self, "Warning", f"Layout file not found: {layout_path}")
            except Exception as e:
                self.logger.error(f"Error loading dashboard layout: {str(e)}")
                self.status_label.setText("Status: Layout load failed")
                QMessageBox.critical(self, "Error", f"Failed to load layout: {str(e)}")
        else:
            self.logger.warning("No dashboard manager available")
            self.status_label.setText("Status: No dashboard manager")
    
    def add_dashboard_widget(self):
        """
        Add a new widget to the dashboard.
        
        This method is called when the + Widget button is clicked.
        """
        if self.widget_manager:
            try:
                # Open widget selection dialog
                widget_type = self._show_widget_selection_dialog()
                if widget_type:
                    widget_id = self.widget_manager.add_widget(widget_type)
                    if widget_id is not None:
                        self.status_label.setText(f"Status: {widget_type} widget added")
                        self.logger.info(f"Added {widget_type} widget to dashboard")
                    else:
                        self.status_label.setText("Status: Widget add failed")
                        self.logger.warning(f"Failed to add {widget_type} widget")
            except Exception as e:
                self.logger.error(f"Error adding dashboard widget: {str(e)}")
                self.status_label.setText("Status: Widget add failed")
                QMessageBox.critical(self, "Error", f"Failed to add widget: {str(e)}")
        else:
            self.logger.warning("No widget manager available")
            self.status_label.setText("Status: No widget manager")
    
    def _show_widget_selection_dialog(self):
        """
        Show dialog for selecting widget type.
        
        Returns:
            str: Selected widget type or None if canceled
        """
        dialog = QDialog(self)
        dialog.setWindowTitle("Select Widget Type")
        dialog.setMinimumWidth(300)
        
        layout = QVBoxLayout(dialog)
        
        # Widget list
        widget_list = QListWidget()
        widget_types = [
            "TimeSeriesWidget", 
            "FFTWidget", 
            "Orientation3DWidget",
            "MetricWidget",
            "StatusWidget"
        ]
        
        for widget_type in widget_types:
            item = QListWidgetItem(widget_type)
            widget_list.addItem(item)
        
        layout.addWidget(widget_list)
        
        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)
        
        # Show dialog
        if dialog.exec() == QDialog.DialogCode.Accepted:
            selected_items = widget_list.selectedItems()
            if selected_items:
                return selected_items[0].text()
        
        return None
    
    def export_csv(self):
        """
        Export data to CSV.
        
        This method is called when the Export CSV button is clicked.
        """
        if self.engine_adapter:
            try:
                # Default export path
                export_path = "exports/data.csv"
                
                # Make sure directory exists
                os.makedirs(os.path.dirname(export_path), exist_ok=True)
                
                # Call engine adapter to export
                if hasattr(self.engine_adapter, 'export_data'):
                    if self.engine_adapter.export_data("csv", export_path):
                        self.status_label.setText(f"Status: Exported to {export_path}")
                        self.logger.info(f"Data exported to CSV: {export_path}")
                        QMessageBox.information(self, "Export Complete", f"Data exported to {export_path}")
                    else:
                        self.status_label.setText("Status: Export failed")
                        self.logger.warning("Failed to export data to CSV")
                else:
                    self.status_label.setText("Status: CSV export not implemented")
                    self.logger.warning("CSV export not implemented in engine adapter")
            except Exception as e:
                self.logger.error(f"Error exporting to CSV: {str(e)}")
                self.status_label.setText("Status: Export failed")
                QMessageBox.critical(self, "Error", f"Failed to export to CSV: {str(e)}")
        else:
            self.logger.warning("No engine adapter available")
            self.status_label.setText("Status: No engine")
    
    def export_json(self):
        """
        Export data to JSON.
        
        This method is called when the Export JSON button is clicked.
        """
        if self.engine_adapter:
            try:
                # Default export path
                export_path = "exports/data.json"
                
                # Make sure directory exists
                os.makedirs(os.path.dirname(export_path), exist_ok=True)
                
                # Call engine adapter to export
                if hasattr(self.engine_adapter, 'export_data'):
                    if self.engine_adapter.export_data("json", export_path):
                        self.status_label.setText(f"Status: Exported to {export_path}")
                        self.logger.info(f"Data exported to JSON: {export_path}")
                        QMessageBox.information(self, "Export Complete", f"Data exported to {export_path}")
                    else:
                        self.status_label.setText("Status: Export failed")
                        self.logger.warning("Failed to export data to JSON")
                else:
                    self.status_label.setText("Status: JSON export not implemented")
                    self.logger.warning("JSON export not implemented in engine adapter")
            except Exception as e:
                self.logger.error(f"Error exporting to JSON: {str(e)}")
                self.status_label.setText("Status: Export failed")
                QMessageBox.critical(self, "Error", f"Failed to export to JSON: {str(e)}")
        else:
            self.logger.warning("No engine adapter available")
            self.status_label.setText("Status: No engine")
    
    def show_about_dialog(self):
        """
        Show about dialog.
        
        This method is called when the About action is triggered.
        """
        QMessageBox.about(
            self,
            "About IMU Analyzer",
            "IMU Analyzer v1.0\n\n"
            "A system to process, configure, and visualize IMU sensor data."
        )
    
    def closeEvent(self, event):
        """
        Handle close event.
        
        Args:
            event: Close event
        """
        # Stop update timer
        self.update_timer.stop()
        
        # Stop engine
        self.stop_engine()
        
        # Accept close event
        event.accept()
        
        self.logger.info("Main window closed")
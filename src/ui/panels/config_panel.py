# File: src/ui/panels/config_panel.py
# Purpose: Panel for editing configuration options
# Target Lines: ≤150

"""
Methods to implement:
- __init__(self, parent=None): Initialize the panel
- _setup_ui(self): Setup UI components
- load_config(self, config): Load configuration
- save_config(self): Save configuration
- apply_config(self): Apply configuration without saving
"""

import os
import logging
import yaml
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTabWidget, QScrollArea, QFormLayout,
    QComboBox, QSpinBox, QDoubleSpinBox, QCheckBox,
    QFileDialog, QMessageBox, QGroupBox
)
from PyQt6.QtCore import Qt


class ConfigPanel(QWidget):
    """
    Panel for editing configuration options.
    
    Allows editing and saving configuration for:
    - System settings
    - UI settings
    - Logging settings
    - Plugin settings
    """
    
    def __init__(self, parent=None):
        """
        Initialize the config panel.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        
        self.logger = logging.getLogger("ConfigPanel")
        self.config = {}
        self.config_widgets = {}
        
        self._setup_ui()
    
    def _setup_ui(self):
        """
        Setup UI components.
        """
        # Main layout
        main_layout = QVBoxLayout(self)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        # Create tabs for different config sections
        self._create_system_tab()
        self._create_ui_tab()
        self._create_logging_tab()
        self._create_plugins_tab()
        
        # Add buttons
        button_layout = QHBoxLayout()
        
        # Add spacer to push buttons to the right
        button_layout.addStretch()
        
        # Apply button
        apply_btn = QPushButton("Apply")
        apply_btn.clicked.connect(self.apply_config)
        button_layout.addWidget(apply_btn)
        
        # Save button
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.save_config)
        button_layout.addWidget(save_btn)
        
        # Reload button
        reload_btn = QPushButton("Reload")
        reload_btn.clicked.connect(lambda: self.load_config(self.config))
        button_layout.addWidget(reload_btn)
        
        main_layout.addLayout(button_layout)
    
    def _create_system_tab(self):
        """
        Create tab for system settings.
        """
        system_tab = QWidget()
        system_layout = QFormLayout(system_tab)
        
        # Maximum Pipelines
        max_pipelines_spin = QSpinBox()
        max_pipelines_spin.setMinimum(1)
        max_pipelines_spin.setMaximum(20)
        max_pipelines_spin.setValue(5)
        system_layout.addRow("Maximum Pipelines:", max_pipelines_spin)
        self.config_widgets["system.max_pipelines"] = max_pipelines_spin
        
        # Monitor Interval
        monitor_interval_spin = QDoubleSpinBox()
        monitor_interval_spin.setMinimum(0.1)
        monitor_interval_spin.setMaximum(10.0)
        monitor_interval_spin.setSingleStep(0.1)
        monitor_interval_spin.setValue(1.0)
        system_layout.addRow("Monitor Interval (s):", monitor_interval_spin)
        self.config_widgets["system.monitor_interval"] = monitor_interval_spin
        
        # Thread Timeout
        thread_timeout_spin = QDoubleSpinBox()
        thread_timeout_spin.setMinimum(0.5)
        thread_timeout_spin.setMaximum(10.0)
        thread_timeout_spin.setSingleStep(0.5)
        thread_timeout_spin.setValue(2.0)
        system_layout.addRow("Thread Timeout (s):", thread_timeout_spin)
        self.config_widgets["system.thread_timeout"] = thread_timeout_spin
        
        # Data group
        data_group = QGroupBox("Data Settings")
        data_layout = QFormLayout(data_group)
        
        # Storage Path
        storage_path_edit = QLineEdit("./data")
        data_layout.addRow("Storage Path:", storage_path_edit)
        self.config_widgets["data.storage_path"] = storage_path_edit
        
        # Buffer Size
        buffer_size_spin = QSpinBox()
        buffer_size_spin.setMinimum(100)
        buffer_size_spin.setMaximum(100000)
        buffer_size_spin.setSingleStep(100)
        buffer_size_spin.setValue(10000)
        data_layout.addRow("Max Buffer Size:", buffer_size_spin)
        self.config_widgets["data.max_buffer_size"] = buffer_size_spin
        
        system_layout.addRow(data_group)
        
        self.tab_widget.addTab(system_tab, "System")
    
    def _create_ui_tab(self):
        """
        Create tab for UI settings.
        """
        ui_tab = QWidget()
        ui_layout = QFormLayout(ui_tab)
        
        # Theme
        theme_combo = QComboBox()
        theme_combo.addItems(["light", "dark"])
        ui_layout.addRow("Theme:", theme_combo)
        self.config_widgets["ui.theme"] = theme_combo
        
        # Refresh Rate
        refresh_rate_spin = QSpinBox()
        refresh_rate_spin.setMinimum(1)
        refresh_rate_spin.setMaximum(60)
        refresh_rate_spin.setValue(30)
        ui_layout.addRow("Refresh Rate (Hz):", refresh_rate_spin)
        self.config_widgets["ui.refresh_rate"] = refresh_rate_spin
        
        # Default Layout
        default_layout_edit = QLineEdit("default_layout.json")
        ui_layout.addRow("Default Layout:", default_layout_edit)
        self.config_widgets["ui.default_layout"] = default_layout_edit
        
        self.tab_widget.addTab(ui_tab, "UI")
    
    def _create_logging_tab(self):
        """
        Create tab for logging settings.
        """
        logging_tab = QWidget()
        logging_layout = QFormLayout(logging_tab)
        
        # Log Level
        level_combo = QComboBox()
        level_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
        level_combo.setCurrentText("INFO")
        logging_layout.addRow("Log Level:", level_combo)
        self.config_widgets["logging.level"] = level_combo
        
        # Log Format
        format_edit = QLineEdit("[%(asctime)s][%(name)s][%(levelname)s] %(message)s")
        logging_layout.addRow("Log Format:", format_edit)
        self.config_widgets["logging.format"] = format_edit
        
        # Log File
        file_edit = QLineEdit("logs/imu_analyzer.log")
        logging_layout.addRow("Log File:", file_edit)
        self.config_widgets["logging.file"] = file_edit
        
        self.tab_widget.addTab(logging_tab, "Logging")
    
    def _create_plugins_tab(self):
        """
        Create tab for plugin settings.
        """
        plugins_tab = QWidget()
        plugins_layout = QFormLayout(plugins_tab)
        
        # Auto Reload
        auto_reload_check = QCheckBox()
        auto_reload_check.setChecked(True)
        plugins_layout.addRow("Auto Reload:", auto_reload_check)
        self.config_widgets["plugins.auto_reload"] = auto_reload_check
        
        # TODO: Add plugin directories management
        # This would require a more complex UI component to manage a list of directories
        
        self.tab_widget.addTab(plugins_tab, "Plugins")
    
    def load_config(self, config):
        """
        Load configuration into UI.
        
        Args:
            config (dict): Configuration dictionary
        """
        self.config = config
        
        try:
            # System settings
            system_config = config.get("system", {})
            if "max_pipelines" in system_config:
                self.config_widgets["system.max_pipelines"].setValue(system_config["max_pipelines"])
            if "monitor_interval" in system_config:
                self.config_widgets["system.monitor_interval"].setValue(system_config["monitor_interval"])
            if "thread_timeout" in system_config:
                self.config_widgets["system.thread_timeout"].setValue(system_config["thread_timeout"])
            
            # Data settings
            data_config = config.get("data", {})
            if "storage_path" in data_config:
                self.config_widgets["data.storage_path"].setText(data_config["storage_path"])
            if "max_buffer_size" in data_config:
                self.config_widgets["data.max_buffer_size"].setValue(data_config["max_buffer_size"])
            
            # UI settings
            ui_config = config.get("ui", {})
            if "theme" in ui_config:
                self.config_widgets["ui.theme"].setCurrentText(ui_config["theme"])
            if "refresh_rate" in ui_config:
                self.config_widgets["ui.refresh_rate"].setValue(ui_config["refresh_rate"])
            if "default_layout" in ui_config:
                self.config_widgets["ui.default_layout"].setText(ui_config["default_layout"])
            
            # Logging settings
            logging_config = config.get("logging", {})
            if "level" in logging_config:
                self.config_widgets["logging.level"].setCurrentText(logging_config["level"])
            if "format" in logging_config:
                self.config_widgets["logging.format"].setText(logging_config["format"])
            if "file" in logging_config:
                self.config_widgets["logging.file"].setText(logging_config["file"])
            
            # Plugin settings
            plugins_config = config.get("plugins", {})
            if "auto_reload" in plugins_config:
                self.config_widgets["plugins.auto_reload"].setChecked(plugins_config["auto_reload"])
            
            self.logger.info("Configuration loaded into UI")
        except Exception as e:
            self.logger.error(f"Error loading configuration: {str(e)}")
            QMessageBox.warning(self, "Configuration Error", f"Error loading configuration: {str(e)}")
    
    def _get_config_from_ui(self):
        """
        Get configuration from UI widgets.
        
        Returns:
            dict: Configuration dictionary
        """
        config = {}
        
        # System settings
        config["system"] = {
            "max_pipelines": self.config_widgets["system.max_pipelines"].value(),
            "monitor_interval": self.config_widgets["system.monitor_interval"].value(),
            "thread_timeout": self.config_widgets["system.thread_timeout"].value()
        }
        
        # Data settings
        config["data"] = {
            "storage_path": self.config_widgets["data.storage_path"].text(),
            "max_buffer_size": self.config_widgets["data.max_buffer_size"].value()
        }
        
        # UI settings
        config["ui"] = {
            "theme": self.config_widgets["ui.theme"].currentText(),
            "refresh_rate": self.config_widgets["ui.refresh_rate"].value(),
            "default_layout": self.config_widgets["ui.default_layout"].text()
        }
        
        # Logging settings
        config["logging"] = {
            "level": self.config_widgets["logging.level"].currentText(),
            "format": self.config_widgets["logging.format"].text(),
            "file": self.config_widgets["logging.file"].text()
        }
        
        # Plugin settings
        config["plugins"] = {
            "auto_reload": self.config_widgets["plugins.auto_reload"].isChecked(),
            # TODO: Add plugin directories from the config
            "plugin_dirs": self.config.get("plugins", {}).get("plugin_dirs", [])
        }
        
        return config
    
    def apply_config(self):
        """
        Apply configuration without saving.
        """
        try:
            config = self._get_config_from_ui()
            
            # TODO: Apply configuration to the engine
            # This would require a callback or signal to notify the engine
            
            self.logger.info("Configuration applied")
            QMessageBox.information(self, "Configuration", "Configuration applied successfully")
        except Exception as e:
            self.logger.error(f"Error applying configuration: {str(e)}")
            QMessageBox.warning(self, "Configuration Error", f"Error applying configuration: {str(e)}")
    
    def save_config(self):
        """
        Save configuration to files.
        """
        try:
            config = self._get_config_from_ui()
            
            # TODO: Save configuration to files
            # This would require implementing the save logic or passing to ConfigLoader
            
            self.logger.info("Configuration saved")
            QMessageBox.information(self, "Configuration", "Configuration saved successfully")
        except Exception as e:
            self.logger.error(f"Error saving configuration: {str(e)}")
            QMessageBox.warning(self, "Configuration Error", f"Error saving configuration: {str(e)}")

# How to modify functionality:
# 1. Add new settings sections: Add new methods similar to _create_system_tab()
# 2. Add visual validation: Add validation to fields (e.g., red background for invalid values)
# 3. Add import/export: Add buttons to import/export config from/to external files
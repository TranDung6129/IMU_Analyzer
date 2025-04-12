# File: src/ui/panels/plugin_panel.py
# Purpose: UI panel for managing plugins
# Target Lines: ≤150

"""
Methods to implement:
- _setup_ui(): Set up the UI components
- load_plugins(): Load and display available plugins
- enable_plugin(): Enable a plugin
- disable_plugin(): Disable a plugin
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QPushButton, QComboBox, QListWidget, QListWidgetItem,
                            QTabWidget, QGroupBox, QCheckBox, QScrollArea)
from PyQt6.QtCore import Qt, pyqtSignal

class PluginPanel(QWidget):
    """
    Panel for managing plugins in the IMU Analyzer.
    
    Allows users to view, enable, and disable plugins of different types.
    """
    
    # Signals
    plugin_enabled = pyqtSignal(str, str)  # (plugin_type, plugin_name)
    plugin_disabled = pyqtSignal(str, str)  # (plugin_type, plugin_name)
    
    def __init__(self, parent=None):
        """
        Initialize the plugin panel.
        
        Args:
            parent (QWidget, optional): Parent widget
        """
        super().__init__(parent)
        self.plugin_manager = None
        self.enabled_plugins = {}  # {plugin_type: [plugin_name1, plugin_name2, ...]}
        
        # Store plugin widgets for easy access
        self.plugin_widgets = {}  # {plugin_type: {plugin_name: QCheckBox}}
        
        self._setup_ui()
    
    def set_plugin_manager(self, plugin_manager):
        """
        Set the plugin manager for this panel.
        
        Args:
            plugin_manager: PluginManager instance
        """
        self.plugin_manager = plugin_manager
        # Load plugins when plugin manager is set
        self.load_plugins()
    
    def _setup_ui(self):
        """
        Set up the UI components of the plugin panel.
        """
        # Main layout
        main_layout = QVBoxLayout(self)
        
        # Header
        header_label = QLabel("Plugin Management")
        header_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        main_layout.addWidget(header_label)
        
        # Tab widget for different plugin types
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        # Create tabs for each plugin type
        plugin_types = [
            "readers", "writers", "decoders", "processors", 
            "analyzers", "visualizers", "exporters", "configurators"
        ]
        
        for plugin_type in plugin_types:
            # Create a scroll area for each tab
            scroll_area = QScrollArea()
            scroll_area.setWidgetResizable(True)
            
            # Create a widget to hold the content
            tab_content = QWidget()
            scroll_area.setWidget(tab_content)
            
            # Add layout to the content widget
            tab_layout = QVBoxLayout(tab_content)
            
            # Group box for available plugins
            plugins_group = QGroupBox(f"Available {plugin_type.capitalize()}")
            plugins_layout = QVBoxLayout(plugins_group)
            self.plugin_widgets[plugin_type] = {}
            
            # Placeholder text when no plugins are available
            placeholder = QLabel(f"No {plugin_type} plugins available")
            placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
            placeholder.setStyleSheet("color: gray; font-style: italic;")
            plugins_layout.addWidget(placeholder)
            
            # Add group box to tab layout
            tab_layout.addWidget(plugins_group)
            
            # Add refresh button
            refresh_btn = QPushButton("Refresh Plugins")
            refresh_btn.clicked.connect(self.load_plugins)
            tab_layout.addWidget(refresh_btn)
            
            # Add stretch to push content to the top
            tab_layout.addStretch()
            
            # Add tab to tab widget
            self.tab_widget.addTab(scroll_area, plugin_type.capitalize())
        
        # Add reload button
        reload_button = QPushButton("Reload All Plugins")
        reload_button.clicked.connect(self.reload_all_plugins)
        main_layout.addWidget(reload_button)
    
    def load_plugins(self):
        """
        Load and display available plugins from the plugin manager.
        """
        if not self.plugin_manager:
            return
            
        # Get all available plugins
        all_plugins = self.plugin_manager.get_available_plugins()
        
        # Update UI for each plugin type
        for plugin_type, plugins in all_plugins.items():
            # Skip if this plugin type is not in the UI
            if plugin_type not in self.plugin_widgets:
                continue
                
            # Get the group box for this plugin type
            tab_index = self.tab_widget.findText(plugin_type.capitalize())
            if tab_index == -1:
                continue
                
            scroll_area = self.tab_widget.widget(tab_index)
            content_widget = scroll_area.widget()
            group_box = None
            
            # Find the group box
            for i in range(content_widget.layout().count()):
                item = content_widget.layout().itemAt(i)
                if item and item.widget() and isinstance(item.widget(), QGroupBox):
                    group_box = item.widget()
                    break
                    
            if not group_box:
                continue
                
            # Clear existing widgets in group box
            while group_box.layout().count():
                item = group_box.layout().takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
            
            # Add plugin checkboxes
            if plugins:
                for plugin_name in sorted(plugins):
                    checkbox = QCheckBox(plugin_name)
                    checkbox.setChecked(plugin_name in self.enabled_plugins.get(plugin_type, []))
                    checkbox.stateChanged.connect(
                        lambda state, t=plugin_type, n=plugin_name: self._on_plugin_state_changed(t, n, state)
                    )
                    group_box.layout().addWidget(checkbox)
                    self.plugin_widgets[plugin_type][plugin_name] = checkbox
            else:
                # No plugins available
                placeholder = QLabel(f"No {plugin_type} plugins available")
                placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
                placeholder.setStyleSheet("color: gray; font-style: italic;")
                group_box.layout().addWidget(placeholder)
    
    def _on_plugin_state_changed(self, plugin_type, plugin_name, state):
        """
        Handle when a plugin checkbox is checked or unchecked.
        
        Args:
            plugin_type (str): Type of the plugin
            plugin_name (str): Name of the plugin
            state (int): Qt.Checked or Qt.Unchecked
        """
        if state == Qt.CheckState.Checked.value:
            self.enable_plugin(plugin_type, plugin_name)
        else:
            self.disable_plugin(plugin_type, plugin_name)
    
    def enable_plugin(self, plugin_type, plugin_name):
        """
        Enable a plugin.
        
        Args:
            plugin_type (str): Type of the plugin
            plugin_name (str): Name of the plugin
        """
        if plugin_type not in self.enabled_plugins:
            self.enabled_plugins[plugin_type] = []
            
        if plugin_name not in self.enabled_plugins[plugin_type]:
            self.enabled_plugins[plugin_type].append(plugin_name)
            self.plugin_enabled.emit(plugin_type, plugin_name)
    
    def disable_plugin(self, plugin_type, plugin_name):
        """
        Disable a plugin.
        
        Args:
            plugin_type (str): Type of the plugin
            plugin_name (str): Name of the plugin
        """
        if plugin_type in self.enabled_plugins and plugin_name in self.enabled_plugins[plugin_type]:
            self.enabled_plugins[plugin_type].remove(plugin_name)
            self.plugin_disabled.emit(plugin_type, plugin_name)
    
    def reload_all_plugins(self):
        """
        Reload all plugins.
        """
        if self.plugin_manager:
            self.plugin_manager.discover_plugins()
            self.load_plugins()
    
    def get_enabled_plugins(self):
        """
        Get the currently enabled plugins.
        
        Returns:
            dict: Dictionary of enabled plugins by type
        """
        return self.enabled_plugins.copy()

# How to modify functionality:
# 1. Add plugin details: Extend _setup_ui() to show more details about each plugin
# 2. Add plugin settings: Add UI for plugin-specific settings
# 3. Change plugin organization: Modify the tab structure in _setup_ui()
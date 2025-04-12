# File: src/ui/visualizers/base_widget.py
# Purpose: Abstract base class for all dashboard widgets
# Target Lines: ≤150

"""
Methods to implement in derived classes:
- __init__(self, parent=None, config=None): Initialize with optional parent and config
- update_data(self, data): Update widget with new data
- set_position(self, position): Set widget position
- set_size(self, size): Set widget size
- get_config(self): Get widget configuration
"""

from PyQt6.QtWidgets import QFrame, QVBoxLayout, QLabel, QPushButton, QMenu
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QPoint
import logging
from abc import ABC, abstractmethod


class BaseWidget(QFrame):
    """
    Abstract base class for all dashboard widgets.
    
    Provides common functionality and interface for dashboard widgets.
    """
    
    # Signals
    data_updated = pyqtSignal(dict)  # Emitted when widget data is updated
    config_changed = pyqtSignal(dict)  # Emitted when widget configuration changes
    widget_closed = pyqtSignal()  # Emitted when widget is closed
    
    def __init__(self, parent=None, config=None):
        """
        Initialize the base widget.
        ...
        """
        super().__init__(parent)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.config = config or {}
        self._setup_ui()
        self.data_buffer = {}
        self.is_maximized = False
        self.setMinimumSize(200, 150)

        # Set frame style
        self.setFrameShape(QFrame.Shape.StyledPanel) # Shape này OK

        # --- SỬA ĐỔI: Sử dụng đúng enum Shadow ---
        # self.setFrameShadow(QFrame.Shape.Raised) # Dòng này sai
        self.setFrameShadow(QFrame.Shadow.Raised) # Sửa thành Shadow.Raised
        # --- KẾT THÚC SỬA ĐỔI ---

        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.logger.debug("BaseWidget initialized")
    
    def _setup_ui(self):
        """
        Setup the UI components.
        """
        # Main layout
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(4, 4, 4, 4)
        self.layout.setSpacing(4)
        
        # Widget title area
        self.title_layout = self._create_title_area()
        
        # Content area
        self.content_widget = QFrame()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        
        # Add to main layout
        self.layout.addLayout(self.title_layout)
        self.layout.addWidget(self.content_widget, 1)  # Content area gets all extra space
    
    def _create_title_area(self):
        """
        Create the title area with controls.
        
        Returns:
            QLayout: The title area layout
        """
        # Horizontal layout for title area
        title_layout = QVBoxLayout()
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(2)
        
        # Create title label
        self.title_label = QLabel(self.config.get("title", self.__class__.__name__))
        self.title_label.setStyleSheet("font-weight: bold;")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Add to layout
        title_layout.addWidget(self.title_label)
        
        return title_layout
    
    def _toggle_maximize(self):
        """
        Toggle between normal and maximized state.
        """
        # To be implemented in concrete widgets if needed
        pass
    
    def _show_config_dialog(self):
        """
        Show configuration dialog for this widget.
        """
        # To be implemented in concrete widgets if needed
        pass
    
    def _close_widget(self):
        """
        Handle close button click.
        """
        self.widget_closed.emit()
    
    @abstractmethod
    def update_data(self, data):
        """
        Update the widget with new data.
        
        Args:
            data (dict): New data for the widget
        """
        self.data_buffer = data
        self.data_updated.emit(data)
    
    @abstractmethod
    def set_position(self, position):
        """
        Set the widget position in the grid.
        
        Args:
            position (tuple): Grid position as (row, column)
        """
        self.config['position'] = position
        self.config_changed.emit(self.config)
    
    @abstractmethod
    def set_size(self, size):
        """
        Set the widget size in the grid.
        
        Args:
            size (tuple): Grid size as (row_span, column_span)
        """
        self.config['size'] = size
        self.config_changed.emit(self.config)
    
    def get_config(self):
        """
        Get the widget configuration.
        
        Returns:
            dict: Widget configuration
        """
        return self.config
    
    def set_config(self, config):
        """
        Set the widget configuration.
        
        Args:
            config (dict): New configuration
        """
        self.config.update(config)
        
        # Update title if provided
        if "title" in config:
            self.title_label.setText(config["title"])
        
        self.config_changed.emit(self.config)
    
    def export_data(self):
        """
        Export widget data.
        
        Returns:
            dict: Widget data for export
        """
        return {
            'type': self.__class__.__name__,
            'config': self.config,
            'data': self.data_buffer
        }
    
    def poll_data(self):
        """
        Poll for new data (to be called periodically).
        
        Default implementation does nothing.
        Override in subclasses that need to poll data.
        """
        pass
    
    def resizeEvent(self, event):
        """Handle resize events."""
        super().resizeEvent(event)
        
        # Update config if needed
        if self.config.get('pixel_size') != (event.size().width(), event.size().height()):
            self.config['pixel_size'] = (event.size().width(), event.size().height())
    
    def moveEvent(self, event):
        """Handle move events."""
        super().moveEvent(event)
        
        # Update config if needed
        if self.config.get('pixel_position') != (event.pos().x(), event.pos().y()):
            self.config['pixel_position'] = (event.pos().x(), event.pos().y())
    
    def contextMenuEvent(self, event):
        """Handle context menu events."""
        menu = QMenu(self)
        
        # Add common actions
        maximize_action = menu.addAction("Maximize/Restore")
        menu.addSeparator()
        config_action = menu.addAction("Configure...")
        menu.addSeparator()
        close_action = menu.addAction("Close")
        
        # Show menu and handle action
        action = menu.exec(event.globalPos())
        
        if action == maximize_action:
            self._toggle_maximize()
        elif action == config_action:
            self._show_config_dialog()
        elif action == close_action:
            self._close_widget()


# How to modify functionality:
# 1. Add data source selection: Add methods to select and configure data sources
# 2. Add more widget controls: Add methods for widget-specific controls
# 3. Add state persistence: Add methods to save and restore widget state
# 4. Add theming: Add methods to change widget appearance
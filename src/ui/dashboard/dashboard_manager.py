# src/ui/dashboard/dashboard_manager.py
import os
import json
import logging
from typing import Dict, Any, List, Optional, Tuple, Callable
from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot, QSize, QPoint

logger = logging.getLogger(__name__)

class DashboardManager(QObject):
    """
    Manages dashboard layouts and configurations.
    
    Responsibilities:
    - Maintain widget registry (track active widgets)
    - Manage widget placement and layout
    - Load/save dashboard configurations
    - Coordinate interactions between widgets
    """
    
    # Signals
    layout_loaded = pyqtSignal(dict)  # Emitted when a layout is loaded
    layout_saved = pyqtSignal(str)    # Emitted when a layout is saved
    widget_added = pyqtSignal(str, object)  # Emitted when a widget is added (id, widget)
    widget_removed = pyqtSignal(str)  # Emitted when a widget is removed (id)
    widget_moved = pyqtSignal(str, QPoint)  # Emitted when a widget is moved (id, position)
    widget_resized = pyqtSignal(str, QSize)  # Emitted when a widget is resized (id, size)
    
    def __init__(self, dashboard_panel=None, parent=None):
        """
        Initialize the dashboard manager.
        
        Args:
            dashboard_panel: Panel containing the dashboard widgets
            parent: Parent Qt object
        """
        super().__init__(parent)
        
        self.dashboard_panel = dashboard_panel
        self.widgets = {}  # {widget_id: widget_object}
        self.widget_configs = {}  # {widget_id: widget_config}
        self.widget_factories = {}  # {widget_type: factory_function}
        
        # Default widget settings
        self.default_widget_size = QSize(400, 300)
        self.default_spacing = 10
        
        logger.info("DashboardManager initialized")
    
    def register_widget_factory(self, widget_type: str, factory: Callable):
        """
        Register a factory function to create widgets of a specific type.
        
        Args:
            widget_type: Type identifier for the widget
            factory: Function that creates widgets of this type
        """
        self.widget_factories[widget_type] = factory
        logger.info(f"Registered widget factory for '{widget_type}'")
    
    def create_widget(self, widget_type: str, widget_id: Optional[str] = None, config: Optional[Dict[str, Any]] = None) -> Tuple[str, Any]:
        """
        Create a widget using the registered factory function.
        
        Args:
            widget_type: Type of widget to create
            widget_id: Optional ID for the widget (generated if None)
            config: Configuration for the widget
            
        Returns:
            Tuple of (widget_id, widget)
            
        Raises:
            ValueError: If the widget type is not registered
        """
        if widget_type not in self.widget_factories:
            raise ValueError(f"No factory registered for widget type '{widget_type}'")
        
        # Generate widget ID if not provided
        if widget_id is None:
            base_id = f"{widget_type}_{len(self.widgets) + 1}"
            widget_id = base_id
            # Ensure unique ID
            counter = 1
            while widget_id in self.widgets:
                counter += 1
                widget_id = f"{base_id}_{counter}"
        
        # Use empty config if none provided
        config = config or {}
        
        # Create widget
        widget = self.widget_factories[widget_type](widget_id, config)
        
        # Store configuration
        self.widget_configs[widget_id] = config
        
        return widget_id, widget
    
    def add_widget(self, widget_type: str, position: Optional[QPoint] = None, size: Optional[QSize] = None, 
                  widget_id: Optional[str] = None, config: Optional[Dict[str, Any]] = None) -> str:
        """
        Add a widget to the dashboard.
        
        Args:
            widget_type: Type of widget to add
            position: Position for the widget (optional)
            size: Size for the widget (optional)
            widget_id: ID for the widget (optional)
            config: Configuration for the widget (optional)
            
        Returns:
            Widget ID
            
        Raises:
            ValueError: If the widget type is not registered
        """
        # Create widget
        widget_id, widget = self.create_widget(widget_type, widget_id, config)
        
        # Use default size if not provided
        if size is None:
            size = self.default_widget_size
        
        # Use next available position if not provided
        if position is None:
            position = self._get_next_position()
        
        # Add to dashboard
        if self.dashboard_panel:
            self.dashboard_panel.add_widget(widget, position, size, widget_id)
        
        # Register widget
        self.widgets[widget_id] = widget
        
        # Emit signal
        self.widget_added.emit(widget_id, widget)
        
        logger.info(f"Added {widget_type} widget with ID '{widget_id}'")
        return widget_id
    
    def remove_widget(self, widget_id: str):
        """
        Remove a widget from the dashboard.
        
        Args:
            widget_id: ID of the widget to remove
        """
        if widget_id not in self.widgets:
            logger.warning(f"Widget '{widget_id}' not found, cannot remove")
            return
        
        # Remove from dashboard
        if self.dashboard_panel:
            self.dashboard_panel.remove_widget(widget_id)
        
        # Clean up
        widget = self.widgets.pop(widget_id)
        self.widget_configs.pop(widget_id, None)
        
        # Emit signal
        self.widget_removed.emit(widget_id)
        
        logger.info(f"Removed widget '{widget_id}'")
    
    def clear_dashboard(self):
        """Remove all widgets from the dashboard."""
        # Copy IDs to avoid modifying dict during iteration
        widget_ids = list(self.widgets.keys())
        
        for widget_id in widget_ids:
            self.remove_widget(widget_id)
        
        logger.info("Cleared all widgets from dashboard")
    
    def get_widget(self, widget_id: str) -> Optional[Any]:
        """
        Get a widget by ID.
        
        Args:
            widget_id: ID of the widget to get
            
        Returns:
            Widget object or None if not found
        """
        return self.widgets.get(widget_id)
    
    def get_widget_config(self, widget_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a widget's configuration.
        
        Args:
            widget_id: ID of the widget
            
        Returns:
            Widget configuration or None if not found
        """
        return self.widget_configs.get(widget_id)
    
    def update_widget_config(self, widget_id: str, config: Dict[str, Any]):
        """
        Update a widget's configuration.
        
        Args:
            widget_id: ID of the widget
            config: New configuration (merged with existing)
        """
        if widget_id not in self.widget_configs:
            logger.warning(f"Widget '{widget_id}' not found, cannot update config")
            return
        
        # Update config
        self.widget_configs[widget_id].update(config)
        
        # Get widget
        widget = self.widgets.get(widget_id)
        if widget and hasattr(widget, 'update_config'):
            # Apply config to widget if it supports it
            widget.update_config(self.widget_configs[widget_id])
    
    def move_widget(self, widget_id: str, position: QPoint):
        """
        Move a widget to a new position.
        
        Args:
            widget_id: ID of the widget to move
            position: New position
        """
        if widget_id not in self.widgets:
            logger.warning(f"Widget '{widget_id}' not found, cannot move")
            return
        
        # Move widget if dashboard panel supports it
        if self.dashboard_panel and hasattr(self.dashboard_panel, 'move_widget'):
            self.dashboard_panel.move_widget(widget_id, position)
        
        # Emit signal
        self.widget_moved.emit(widget_id, position)
    
    def resize_widget(self, widget_id: str, size: QSize):
        """
        Resize a widget.
        
        Args:
            widget_id: ID of the widget to resize
            size: New size
        """
        if widget_id not in self.widgets:
            logger.warning(f"Widget '{widget_id}' not found, cannot resize")
            return
        
        # Resize widget if dashboard panel supports it
        if self.dashboard_panel and hasattr(self.dashboard_panel, 'resize_widget'):
            self.dashboard_panel.resize_widget(widget_id, size)
        
        # Emit signal
        self.widget_resized.emit(widget_id, size)
    
    def save_layout(self, file_path: str) -> bool:
        """
        Save the current dashboard layout to a file.
        
        Args:
            file_path: Path to save the layout to
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Collect layout information
            layout = {
                "widgets": [],
                "version": "1.0"
            }
            
            # Get layout from dashboard panel if available
            if self.dashboard_panel and hasattr(self.dashboard_panel, 'get_layout_state'):
                layout["panel_state"] = self.dashboard_panel.get_layout_state()
            
            # Add widget information
            for widget_id, widget in self.widgets.items():
                widget_info = {
                    "id": widget_id,
                    "type": widget.__class__.__name__,
                    "config": self.widget_configs.get(widget_id, {})
                }
                
                # Add position and size if available
                if self.dashboard_panel and hasattr(self.dashboard_panel, 'get_widget_geometry'):
                    geometry = self.dashboard_panel.get_widget_geometry(widget_id)
                    if geometry:
                        position, size = geometry
                        widget_info["position"] = {"x": position.x(), "y": position.y()}
                        widget_info["size"] = {"width": size.width(), "height": size.height()}
                
                layout["widgets"].append(widget_info)
            
            # Save to file
            with open(file_path, 'w') as f:
                json.dump(layout, f, indent=2)
            
            # Emit signal
            self.layout_saved.emit(file_path)
            
            logger.info(f"Saved dashboard layout to {file_path}")
            return True
        
        except Exception as e:
            logger.error(f"Error saving layout to {file_path}: {e}")
            return False
    
    def load_layout(self, file_path: str) -> bool:
        """
        Load a dashboard layout from a file.
        
        Args:
            file_path: Path to the layout file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Load layout file
            with open(file_path, 'r') as f:
                layout = json.load(f)
            
            # Clear current dashboard
            self.clear_dashboard()
            
            # Restore dashboard panel state if available
            if "panel_state" in layout and self.dashboard_panel and hasattr(self.dashboard_panel, 'restore_layout_state'):
                self.dashboard_panel.restore_layout_state(layout["panel_state"])
            
            # Add widgets
            for widget_info in layout.get("widgets", []):
                widget_id = widget_info.get("id")
                widget_type = widget_info.get("type")
                config = widget_info.get("config", {})
                
                # Extract position and size if available
                position = None
                size = None
                
                if "position" in widget_info:
                    pos_data = widget_info["position"]
                    position = QPoint(pos_data.get("x", 0), pos_data.get("y", 0))
                
                if "size" in widget_info:
                    size_data = widget_info["size"]
                    size = QSize(size_data.get("width", 400), size_data.get("height", 300))
                
                # Create widget
                try:
                    self.add_widget(widget_type, position, size, widget_id, config)
                except ValueError as e:
                    logger.warning(f"Error creating widget {widget_id}: {e}")
            
            # Emit signal
            self.layout_loaded.emit(layout)
            
            logger.info(f"Loaded dashboard layout from {file_path}")
            return True
        
        except Exception as e:
            logger.error(f"Error loading layout from {file_path}: {e}")
            return False
    
    def _get_next_position(self) -> QPoint:
        """
        Get the next available position for a new widget.
        
        This is a simple implementation that places widgets in a grid.
        
        Returns:
            Next available position
        """
        # Default starting position
        x, y = 10, 10
        
        # If dashboard panel provides positioning, use it
        if self.dashboard_panel and hasattr(self.dashboard_panel, 'get_next_position'):
            return self.dashboard_panel.get_next_position()
        
        # Simple grid layout
        columns = 2
        width = self.default_widget_size.width() + self.default_spacing
        height = self.default_widget_size.height() + self.default_spacing
        
        # Calculate position based on widget count
        count = len(self.widgets)
        row = count // columns
        col = count % columns
        
        x = col * width + self.default_spacing
        y = row * height + self.default_spacing
        
        return QPoint(x, y)
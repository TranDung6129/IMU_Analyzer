# File: src/ui/dashboard/widget_manager.py
# Purpose: Manage widgets on the dashboard
# Target Lines: ≤200

"""
Methods to implement:
- __init__(self, dashboard_manager): Initialize with dashboard manager
- add_widget(self, widget_type, config=None): Add a widget by type and config
- update_widget(self, widget_id, data): Update a widget with new data
- resize_widget(self, widget_id, size): Resize a widget
- remove_widget(self, widget_id): Remove a widget
"""

import logging
from PyQt6.QtWidgets import QWidget, QFrame, QVBoxLayout, QLabel, QMessageBox, QMenu
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from src.ui.visualizers.time_series_widget import TimeSeriesWidget
from src.ui.visualizers.fft_widget import FFTWidget
from src.ui.visualizers.orientation3d_widget import Orientation3DWidget

class WidgetManager:
    """
    Manages widgets on the dashboard.
    Handles widget creation, updates, resizing, and removal.
    """
    
    def __init__(self, dashboard_manager):
        """
        Initialize the widget manager.

        Args:
            dashboard_manager (DashboardManager): The manager for the dashboard layout.
        """
        self.logger = logging.getLogger("WidgetManager")
        self.dashboard_manager = dashboard_manager
        self.widgets = {}  # Stores widget_id -> widget_instance mapping

        # --- SỬA ĐỔI: Map tên widget với lớp của nó ---
        self.widget_classes = {
            "TimeSeriesWidget": TimeSeriesWidget,
            "FFTWidget": FFTWidget,
            "Orientation3DWidget": Orientation3DWidget,
            # "MetricWidget": MetricWidget,
            # "StatusWidget": StatusWidget,
        }
        self.logger.debug(f"WidgetManager initialized with known types: {list(self.widget_classes.keys())}")

    
    def add_widget(self, widget_type, config=None, position=None, size=None):
        """
        Add a widget of a specific type to the dashboard.

        Args:
            widget_type (str): The class name of the widget to add.
            config (dict, optional): Configuration for the widget. Defaults to None.
            position (tuple, optional): (row, col). Defaults to None (auto-position).
            size (tuple, optional): (row_span, col_span). Defaults to None (e.g., 1x1).

        Returns:
            int or None: The ID of the added widget, or None if creation failed.
        """
        self.logger.info(f"Attempting to add widget of type: {widget_type}")
        if widget_type not in self.widget_classes:
            self.logger.error(f"Unknown widget type requested: {widget_type}")
            QMessageBox.warning(self.dashboard_manager, "Error", f"Unknown widget type: {widget_type}")
            return None

        try:
            # Lấy lớp widget từ dictionary
            WidgetClass = self.widget_classes[widget_type]

            # Tạo instance của widget
            # Giả sử constructor của widget chấp nhận config (hoặc không)
            self.logger.debug(f"Creating instance of {widget_type} with config: {config}")
            # --- SỬA ĐỔI: Khởi tạo widget bằng lớp đã import ---
            # Cần đảm bảo các lớp Widget thực tế có constructor phù hợp
            widget_instance = WidgetClass(config=config if config else {}) # Truyền config vào
            self.logger.debug(f"Widget instance created: {widget_instance}")

            if not isinstance(widget_instance, QWidget):
                 self.logger.error(f"{widget_type} did not create a valid QWidget instance.")
                 return None

            # Thêm widget vào DashboardManager (nó sẽ xử lý layout)
            widget_id = self.dashboard_manager.add_widget(widget_instance, position, size)
            self.logger.debug(f"Widget added to DashboardManager with ID: {widget_id}")

            # Lưu trữ tham chiếu đến widget bằng ID
            self.widgets[widget_id] = widget_instance

            # Thiết lập menu ngữ cảnh (nếu cần)
            # self._setup_widget_context_menu(widget_instance, widget_id)

            self.logger.info(f"Successfully added widget '{widget_type}' with ID {widget_id}")
            return widget_id

        except Exception as e:
            self.logger.error(f"Failed to create or add widget '{widget_type}': {e}", exc_info=True)
            QMessageBox.critical(self.dashboard_manager, "Widget Error", f"Failed to add widget '{widget_type}':\n{e}")
            return None
    
    def update_widget(self, widget_id, data):
        """
        Update a specific widget with new data.

        Args:
            widget_id (int): The ID of the widget to update.
            data: The data payload for the widget.
        """
        if widget_id not in self.widgets:
            # self.logger.warning(f"Widget ID {widget_id} not found for update.")
            return

        widget = self.widgets[widget_id]
        if hasattr(widget, 'update_data') and callable(widget.update_data):
            try:
                widget.update_data(data)
            except Exception as e:
                self.logger.error(f"Error updating widget {widget_id} ({widget.__class__.__name__}): {e}", exc_info=True)
        # else:
        #     self.logger.debug(f"Widget {widget_id} ({widget.__class__.__name__}) has no update_data method.")
    
    def resize_widget(self, widget_id, size):
        """
        Resize a widget.
        
        Args:
            widget_id (int): Widget ID
            size (tuple): New size as (row_span, column_span)
            
        Returns:
            bool: True if successful, False otherwise
        """
        if widget_id not in self.widgets:
            self.logger.warning(f"Cannot resize non-existent widget: {widget_id}")
            return False
        
        try:
            widget = self.widgets[widget_id]
            
            # Find widget info in dashboard manager
            for wid, widget_info in self.dashboard_manager.widgets.items():
                if wid == widget_id:
                    # Get current position and widget
                    position = widget_info['position']
                    old_size = widget_info['size']
                    
                    # Validate size limits
                    row_span, col_span = size
                    max_rows = self.dashboard_manager.grid_rows if hasattr(self.dashboard_manager, 'grid_rows') else 4
                    max_cols = self.dashboard_manager.grid_cols if hasattr(self.dashboard_manager, 'grid_cols') else 3
                    
                    # Ensure widget stays within grid bounds
                    row, col = position
                    if (row + row_span > max_rows) or (col + col_span > max_cols):
                        # If widget would exceed grid bounds, adjust size
                        row_span = min(row_span, max_rows - row)
                        col_span = min(col_span, max_cols - col)
                        self.logger.warning(f"Adjusted widget size to fit grid: ({row_span}, {col_span})")
                    
                    # Remove widget from grid
                    self.dashboard_manager.dashboard_layout.removeWidget(widget)
                    
                    # Update size info
                    widget_info['size'] = (row_span, col_span)
                    
                    # Re-add widget with new size
                    self.dashboard_manager.dashboard_layout.addWidget(
                        widget, row, col, row_span, col_span
                    )
                    
                    # Apply visual resize effect
                    self._apply_resize_effect(widget)
                    
                    self.logger.info(f"Resized widget {widget_id} from {old_size} to {size}")
                    self.dashboard_manager.layout_changed.emit()
                    return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error resizing widget {widget_id}: {str(e)}")
            return False
            
    def _apply_resize_effect(self, widget):
        """
        Apply a visual effect when resizing a widget.
        
        Args:
            widget (QWidget): Widget to resize
        """
        # Save original style
        original_style = widget.styleSheet()
        
        # Apply highlight style to indicate resize
        highlight_style = original_style + "; border: 2px solid #4285F4;"
        widget.setStyleSheet(highlight_style)
        
        # Create timer to revert style after a delay
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(300, lambda: widget.setStyleSheet(original_style))
        
    def enable_resize_handles(self, widget_id):
        """
        Enable resize handles for a widget.
        
        Args:
            widget_id (int): Widget ID
            
        Returns:
            bool: True if successful, False otherwise
        """
        if widget_id not in self.widgets:
            self.logger.warning(f"Cannot add resize handles to non-existent widget: {widget_id}")
            return False
            
        try:
            widget = self.widgets[widget_id]
            
            # Create resize handles if needed
            if not hasattr(widget, 'resize_handles'):
                self._create_resize_handles(widget, widget_id)
                
            # Show resize handles
            for handle in widget.resize_handles:
                handle.show()
                
            return True
            
        except Exception as e:
            self.logger.error(f"Error enabling resize handles for widget {widget_id}: {str(e)}")
            return False
            
    def _create_resize_handles(self, widget, widget_id):
        """
        Create resize handles for a widget.
        
        Args:
            widget (QWidget): Widget to add resize handles to
            widget_id (int): Widget ID
        """
        from PyQt6.QtWidgets import QFrame
        from PyQt6.QtCore import Qt, QSize
        
        # Create handles
        widget.resize_handles = []
        
        # Handle size
        handle_size = 10
        
        # Handle positions (corners)
        positions = [
            ('nw', 0, 0),                          # North-west
            ('ne', widget.width() - handle_size, 0),  # North-east
            ('sw', 0, widget.height() - handle_size),  # South-west
            ('se', widget.width() - handle_size, widget.height() - handle_size)   # South-east
        ]
        
        for corner, x, y in positions:
            # Create handle
            handle = QFrame(widget)
            handle.setObjectName(f"resize_handle_{corner}")
            handle.setGeometry(x, y, handle_size, handle_size)
            handle.setFrameShape(QFrame.Shape.Box)
            handle.setStyleSheet("background-color: #4285F4; border: 1px solid white;")
            handle.setCursor(self._get_corner_cursor(corner))
            handle.setMouseTracking(True)
            
            # Store corner type in handle
            handle.corner = corner
            
            # Install event filter
            handle.installEventFilter(self)
            
            # Add to list
            widget.resize_handles.append(handle)
            
        # Add resize state to widget
        widget.is_resizing = False
        widget.resize_start_pos = None
        widget.resize_start_size = None
        widget.resize_corner = None
        
    def _get_corner_cursor(self, corner):
        """
        Get cursor shape for a corner resize handle.
        
        Args:
            corner (str): Corner type ('nw', 'ne', 'sw', 'se')
            
        Returns:
            Qt.CursorShape: Cursor shape
        """
        from PyQt6.QtCore import Qt
        
        if corner == 'nw':
            return Qt.CursorShape.SizeFDiagCursor
        elif corner == 'ne':
            return Qt.CursorShape.SizeBDiagCursor
        elif corner == 'sw':
            return Qt.CursorShape.SizeBDiagCursor
        elif corner == 'se':
            return Qt.CursorShape.SizeFDiagCursor
        else:
            return Qt.CursorShape.SizeAllCursor
    
    def remove_widget(self, widget_id):
        """
        Remove a widget from the dashboard.

        Args:
            widget_id (int): The ID of the widget to remove.
        """
        if widget_id not in self.widgets:
            self.logger.warning(f"Widget ID {widget_id} not found for removal.")
            return

        try:
            # Yêu cầu DashboardManager xóa widget khỏi layout và bộ nhớ của nó
            success = self.dashboard_manager.remove_widget(widget_id) # Giả sử DM có phương thức này

            if success:
                # Xóa khỏi bộ nhớ của WidgetManager
                del self.widgets[widget_id]
                self.logger.info(f"Removed widget {widget_id}.")
            else:
                 self.logger.error(f"DashboardManager failed to remove widget {widget_id}.")

        except Exception as e:
            self.logger.error(f"Error removing widget {widget_id}: {e}", exc_info=True)
    
    def eventFilter(self, obj, event):
        """
        Filter events for widgets.
        
        Args:
            obj: Object that received the event
            event: Event
            
        Returns:
            bool: True if event was handled, False otherwise
        """
        from PyQt6.QtCore import Qt, QEvent
        
        # Check if this is a resize handle event
        if hasattr(obj, 'corner') and obj.corner in ['nw', 'ne', 'sw', 'se']:
            # Find parent widget and its ID
            parent_widget = obj.parent()
            widget_id = None
            
            for wid, widget in self.widgets.items():
                if widget == parent_widget:
                    widget_id = wid
                    break
                    
            if widget_id is None:
                return False
                
            # Handle mouse press on resize handle
            if event.type() == QEvent.Type.MouseButtonPress and event.button() == Qt.MouseButton.LeftButton:
                parent_widget.is_resizing = True
                parent_widget.resize_start_pos = event.globalPosition().toPoint()
                parent_widget.resize_start_size = parent_widget.size()
                parent_widget.resize_corner = obj.corner
                return True
                
            # Handle mouse release after resize
            elif event.type() == QEvent.Type.MouseButtonRelease and event.button() == Qt.MouseButton.LeftButton and parent_widget.is_resizing:
                parent_widget.is_resizing = False
                
                # Find widget info in dashboard
                for wid, widget_info in self.dashboard_manager.widgets.items():
                    if wid == widget_id:
                        # Calculate new grid size based on pixels
                        width = parent_widget.width()
                        height = parent_widget.height()
                        
                        grid_width = self.dashboard_manager.grid_cell_width
                        grid_height = self.dashboard_manager.grid_cell_height
                        
                        # Calculate new size in grid cells (rounded to nearest)
                        col_span = max(1, round(width / grid_width))
                        row_span = max(1, round(height / grid_height))
                        
                        # Update size
                        self.resize_widget(widget_id, (row_span, col_span))
                        break
                
                return True
                
            # Handle mouse move during resize
            elif event.type() == QEvent.Type.MouseMove and parent_widget.is_resizing:
                # Calculate resize delta
                delta = event.globalPosition().toPoint() - parent_widget.resize_start_pos
                
                # Get original size
                original_width = parent_widget.resize_start_size.width()
                original_height = parent_widget.resize_start_size.height()
                
                # Apply resize based on corner
                if parent_widget.resize_corner == 'se':
                    # Bottom-right: resize width and height
                    new_width = max(100, original_width + delta.x())
                    new_height = max(100, original_height + delta.y())
                    parent_widget.resize(new_width, new_height)
                    
                elif parent_widget.resize_corner == 'sw':
                    # Bottom-left: resize width (inverse) and height
                    new_width = max(100, original_width - delta.x())
                    new_height = max(100, original_height + delta.y())
                    parent_widget.resize(new_width, new_height)
                    parent_widget.move(parent_widget.x() + (original_width - new_width), parent_widget.y())
                    
                elif parent_widget.resize_corner == 'ne':
                    # Top-right: resize width and height (inverse)
                    new_width = max(100, original_width + delta.x())
                    new_height = max(100, original_height - delta.y())
                    parent_widget.resize(new_width, new_height)
                    parent_widget.move(parent_widget.x(), parent_widget.y() + (original_height - new_height))
                    
                elif parent_widget.resize_corner == 'nw':
                    # Top-left: resize width (inverse) and height (inverse)
                    new_width = max(100, original_width - delta.x())
                    new_height = max(100, original_height - delta.y())
                    parent_widget.resize(new_width, new_height)
                    parent_widget.move(
                        parent_widget.x() + (original_width - new_width),
                        parent_widget.y() + (original_height - new_height)
                    )
                
                # Update handle positions
                self._update_resize_handle_positions(parent_widget)
                
                return True
                
        return False
        
    def _update_resize_handle_positions(self, widget):
        """
        Update positions of resize handles after widget resize.
        
        Args:
            widget (QWidget): Widget whose handles to update
        """
        if not hasattr(widget, 'resize_handles'):
            return
            
        # Handle size
        handle_size = 10
        
        # Update handle positions
        for handle in widget.resize_handles:
            if handle.corner == 'nw':
                handle.move(0, 0)
            elif handle.corner == 'ne':
                handle.move(widget.width() - handle_size, 0)
            elif handle.corner == 'sw':
                handle.move(0, widget.height() - handle_size)
            elif handle.corner == 'se':
                handle.move(widget.width() - handle_size, widget.height() - handle_size)
    
    def _setup_widget_context_menu(self, widget, widget_id):
        """
        Setup context menu for a widget.
        
        Args:
            widget (QWidget): Widget to setup
            widget_id (int): Widget ID
        """
        widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        widget.customContextMenuRequested.connect(
            lambda pos: self._show_widget_context_menu(pos, widget_id)
        )
        
        # Add resize handles
        self.enable_resize_handles(widget_id)
    
    def _show_widget_context_menu(self, pos, widget_id):
        """
        Show context menu for a widget.
        
        Args:
            pos (QPoint): Position where to show menu
            widget_id (int): Widget ID
        """
        menu = QMenu()
        
        # Add actions
        resize_action = menu.addAction("Resize")
        remove_action = menu.addAction("Remove")
        
        # Add size submenu
        size_menu = menu.addMenu("Set Size")
        size_1x1_action = size_menu.addAction("1x1")
        size_1x2_action = size_menu.addAction("1x2")
        size_2x1_action = size_menu.addAction("2x1")
        size_2x2_action = size_menu.addAction("2x2")
        
        # Show menu and handle action
        action = menu.exec(self.widgets[widget_id].mapToGlobal(pos))
        
        if action == resize_action:
            # For demo, just toggle between 1x1 and 2x2
            # In a real app, this would open a resize dialog
            for wid, widget_info in self.dashboard_manager.widgets.items():
                if wid == widget_id:
                    current_size = widget_info['size']
                    if current_size == (1, 1):
                        self.resize_widget(widget_id, (2, 2))
                    else:
                        self.resize_widget(widget_id, (1, 1))
                    break
        
        elif action == remove_action:
            self.remove_widget(widget_id)
            
        elif action == size_1x1_action:
            self.resize_widget(widget_id, (1, 1))
        elif action == size_1x2_action:
            self.resize_widget(widget_id, (1, 2))
        elif action == size_2x1_action:
            self.resize_widget(widget_id, (2, 1))
        elif action == size_2x2_action:
            self.resize_widget(widget_id, (2, 2))
    
    def _update_all_widgets(self):
        """
        Update all widgets with latest data.
        Called periodically by update_timer.
        """
        # This would typically fetch real-time data and update widgets
        # For demo, we'll update just widgets that support polling
        for widget_id, widget in self.widgets.items():
            if hasattr(widget, 'poll_data') and callable(widget.poll_data):
                try:
                    widget.poll_data()
                except Exception as e:
                    self.logger.debug(f"Error polling widget {widget_id}: {str(e)}")

    def get_widget(self, widget_id):
        """ Get a widget instance by its ID. """
        return self.widgets.get(widget_id)
    
    def create_widget_instance(self, widget_type, config=None):
        """ Creates an instance of the specified widget type. """
        self.logger.debug(f"Request to create widget instance: {widget_type}")
        if widget_type not in self.widget_classes:
            self.logger.error(f"Unknown widget type requested for instance creation: {widget_type}")
            return None
        try:
            WidgetClass = self.widget_classes[widget_type]
            # Truyền config vào constructor của widget
            instance = WidgetClass(config=config if config else {})
            if not isinstance(instance, QWidget):
                self.logger.error(f"{widget_type} class did not return a QWidget instance.")
                return None
            self.logger.debug(f"Successfully created instance of {widget_type}")
            return instance
        except Exception as e:
            self.logger.error(f"Failed to create instance of widget '{widget_type}': {e}", exc_info=True)
            return None

# How to modify functionality:
# 1. Add real widget classes: Replace _create_placeholder with real widget implementations
# 2. Add save/load support: Add methods to serialize and deserialize widget state
# 3. Add auto-refresh config: Add methods to configure update frequency
# 4. Add widget templates: Add method to create widgets from predefined templates
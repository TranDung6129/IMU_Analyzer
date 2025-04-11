# src/ui/dashboard/grid_dashboard_panel.py
import logging
from typing import Dict, Any, List, Optional, Tuple
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, 
                             QFrame, QSizePolicy, QScrollArea, QMenu)
from PyQt6.QtCore import Qt, pyqtSignal, pyqtSlot, QSize, QPoint, QRect
from PyQt6.QtGui import QMouseEvent, QContextMenuEvent

from .draggable_widget import DraggableWidget

logger = logging.getLogger(__name__)

class GridDashboardPanel(QScrollArea):
    """
    A scrollable grid-based dashboard panel for visualizer widgets.
    
    Provides a grid layout for arranging visualizer widgets, with support for:
    - Adding/removing widgets
    - Dragging and dropping widgets
    - Resizing widgets
    - Saving/loading layout state
    """
    
    # Signals
    widget_added = pyqtSignal(str, object)  # (widget_id, widget)
    widget_removed = pyqtSignal(str)  # (widget_id)
    widget_selected = pyqtSignal(str)  # (widget_id)
    
    def __init__(self, parent=None):
        """
        Initialize the grid dashboard panel.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        
        # Setup scrollable area
        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # Create grid container widget
        self.container = QWidget()
        self.setWidget(self.container)
        
        # Setup grid layout
        self.grid_layout = QGridLayout(self.container)
        self.grid_layout.setContentsMargins(10, 10, 10, 10)
        self.grid_layout.setSpacing(10)
        
        # Dictionary of widgets
        self.widgets = {}  # {widget_id: DraggableWidget}
        
        # Currently selected widget
        self.selected_widget_id = None
        
        # Grid state tracking
        self.grid_positions = {}  # {(row, col): widget_id}
        self.widget_positions = {}  # {widget_id: (row, col, row_span, col_span)}
        self.max_row = 0
        self.max_col = 3  # Default to 3 columns
        
        logger.info("GridDashboardPanel initialized")
    
    def add_widget(self, widget: QWidget, position: Optional[QPoint] = None, 
                  size: Optional[QSize] = None, widget_id: Optional[str] = None) -> str:
        """
        Add a widget to the dashboard grid.
        
        Args:
            widget: Widget to add
            position: Position (if None, uses next available cell)
            size: Size (if None, uses default)
            widget_id: Widget ID (if None, generates one)
            
        Returns:
            Widget ID
        """
        # Generate widget ID if not provided
        if widget_id is None:
            base_id = f"widget_{len(self.widgets) + 1}"
            widget_id = base_id
            # Ensure unique ID
            counter = 1
            while widget_id in self.widgets:
                counter += 1
                widget_id = f"{base_id}_{counter}"
        
        # Create draggable container for the widget
        title = getattr(widget, 'title', widget.__class__.__name__)
        container = DraggableWidget(widget, title, widget_id)
        
        # Connect signals
        container.close_requested.connect(lambda wid=widget_id: self.remove_widget(wid))
        container.selected.connect(lambda wid=widget_id: self._on_widget_selected(wid))
        from functools import partial
        container.move_requested.connect(partial(self._on_widget_move_requested, widget_id))
        
        # Set size if provided
        if size is not None:
            container.setMinimumSize(size)
            container.resize(size)
        
        # Place widget in grid
        row, col = self._get_position(position)
        self._place_widget_at(container, widget_id, row, col)
        
        # Store widget
        self.widgets[widget_id] = container
        
        # Emit signal
        self.widget_added.emit(widget_id, widget)
        
        logger.info(f"Added widget '{widget_id}' at grid position ({row}, {col})")
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
        
        # Get widget and its position
        container = self.widgets[widget_id]
        position = self.widget_positions.get(widget_id)
        
        # Remove from grid
        if position:
            row, col, row_span, col_span = position
            for r in range(row, row + row_span):
                for c in range(col, col + col_span):
                    self.grid_positions.pop((r, c), None)
        
        # Remove from layout
        self.grid_layout.removeWidget(container)
        container.close()  # This should handle deletion
        
        # Clean up tracking
        self.widgets.pop(widget_id)
        self.widget_positions.pop(widget_id, None)
        
        # Clear selection if this was the selected widget
        if self.selected_widget_id == widget_id:
            self.selected_widget_id = None
        
        # Emit signal
        self.widget_removed.emit(widget_id)
        
        logger.info(f"Removed widget '{widget_id}'")
    
    def clear_all(self):
        """Remove all widgets from the dashboard."""
        # Copy IDs to avoid modifying dict during iteration
        widget_ids = list(self.widgets.keys())
        
        for widget_id in widget_ids:
            self.remove_widget(widget_id)
        
        # Reset tracking
        self.grid_positions = {}
        self.widget_positions = {}
        self.max_row = 0
        self.selected_widget_id = None
        
        logger.info("Cleared all widgets from dashboard")
    
    def get_widget(self, widget_id: str) -> Optional[QWidget]:
        """
        Get the content widget by ID.
        
        Args:
            widget_id: ID of the widget to get
            
        Returns:
            Content widget or None if not found
        """
        container = self.widgets.get(widget_id)
        if container:
            return container.content_widget
        return None
    
    def get_container(self, widget_id: str) -> Optional[DraggableWidget]:
        """
        Get the draggable container widget by ID.
        
        Args:
            widget_id: ID of the widget to get
            
        Returns:
            Container widget or None if not found
        """
        return self.widgets.get(widget_id)
    
    def move_widget(self, widget_id: str, position: QPoint):
        """
        Move a widget to a new position.
        
        Args:
            widget_id: ID of the widget to move
            position: New position in screen coordinates
        """
        if widget_id not in self.widgets:
            logger.warning(f"Widget '{widget_id}' not found, cannot move")
            return
        
        # Convert screen position to grid position
        row, col = self._screen_to_grid_position(position)
        
        # Get widget
        container = self.widgets[widget_id]
        
        # Get current position
        current_position = self.widget_positions.get(widget_id)
        if current_position:
            current_row, current_col, row_span, col_span = current_position
            
            # Skip if position hasn't changed
            if current_row == row and current_col == col:
                return
            
            # Remove from current position
            for r in range(current_row, current_row + row_span):
                for c in range(current_col, current_col + col_span):
                    self.grid_positions.pop((r, c), None)
        
        # Place at new position
        self._place_widget_at(container, widget_id, row, col)
        
        logger.info(f"Moved widget '{widget_id}' to grid position ({row}, {col})")
    
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
        
        # Get widget
        container = self.widgets[widget_id]
        
        # Resize widget
        container.setMinimumSize(size)
        container.resize(size)
        
        logger.info(f"Resized widget '{widget_id}' to {size.width()}x{size.height()}")
    
    def get_next_position(self) -> QPoint:
        """
        Get the next available grid position.
        
        Returns:
            Next available position in screen coordinates
        """
        # Find next available cell
        row, col = self._find_next_available_cell()
        
        # Convert to screen coordinates
        cell_rect = self.grid_layout.cellRect(row, col)
        position = QPoint(cell_rect.x(), cell_rect.y())
        
        # Add container's position
        container_pos = self.container.pos()
        position += container_pos
        
        return position
    
    def get_widget_geometry(self, widget_id: str) -> Optional[Tuple[QPoint, QSize]]:
        """
        Get a widget's geometry.
        
        Args:
            widget_id: ID of the widget
            
        Returns:
            Tuple of (position, size) or None if not found
        """
        container = self.widgets.get(widget_id)
        if not container:
            return None
        
        position = container.pos()
        size = container.size()
        
        return position, size
    
    def get_selected_widget_id(self) -> Optional[str]:
        """
        Get the ID of the currently selected widget.
        
        Returns:
            Selected widget ID or None if none selected
        """
        return self.selected_widget_id
    
    def get_layout_state(self) -> Dict[str, Any]:
        """
        Get the current layout state.
        
        Returns:
            Dictionary representing the current layout state
        """
        state = {
            "widgets": {},
            "max_row": self.max_row,
            "max_col": self.max_col
        }
        
        for widget_id, position in self.widget_positions.items():
            row, col, row_span, col_span = position
            container = self.widgets.get(widget_id)
            size = container.size() if container else QSize(300, 200)
            
            state["widgets"][widget_id] = {
                "position": {
                    "row": row,
                    "col": col,
                    "row_span": row_span,
                    "col_span": col_span
                },
                "size": {
                    "width": size.width(),
                    "height": size.height()
                }
            }
        
        return state
    
    def restore_layout_state(self, state: Dict[str, Any]) -> bool:
        """
        Restore the layout state.
        
        Args:
            state: Layout state dictionary
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Extract layout information
            self.max_row = state.get("max_row", self.max_row)
            self.max_col = state.get("max_col", self.max_col)
            
            # Process widgets
            widget_states = state.get("widgets", {})
            for widget_id, widget_state in widget_states.items():
                # Skip if widget doesn't exist
                if widget_id not in self.widgets:
                    continue
                
                # Get widget
                container = self.widgets[widget_id]
                
                # Extract position and size
                position = widget_state.get("position", {})
                size_data = widget_state.get("size", {})
                
                row = position.get("row", 0)
                col = position.get("col", 0)
                row_span = position.get("row_span", 1)
                col_span = position.get("col_span", 1)
                
                width = size_data.get("width", 300)
                height = size_data.get("height", 200)
                
                # Apply position and size
                self._place_widget_at(container, widget_id, row, col, row_span, col_span)
                container.resize(width, height)
            
            logger.info("Restored layout state")
            return True
            
        except Exception as e:
            logger.error(f"Error restoring layout state: {e}")
            return False
    
    def _get_position(self, position: Optional[QPoint]) -> Tuple[int, int]:
        """
        Convert screen position to grid position.
        
        Args:
            position: Position in screen coordinates or None
            
        Returns:
            Grid position as (row, col)
        """
        if position is not None:
            return self._screen_to_grid_position(position)
        else:
            return self._find_next_available_cell()
    
    def _screen_to_grid_position(self, position: QPoint) -> Tuple[int, int]:
        """
        Convert screen position to grid position.
        
        Args:
            position: Position in screen coordinates
            
        Returns:
            Grid position as (row, col)
        """
        # Adjust for container position
        relative_pos = position - self.container.pos()
        
        # Find cell containing the position
        for row in range(self.grid_layout.rowCount()):
            for col in range(self.grid_layout.columnCount()):
                cell_rect = self.grid_layout.cellRect(row, col)
                if cell_rect.contains(relative_pos):
                    return row, col
        
        # If not found, use next available cell
        return self._find_next_available_cell()
    
    def _find_next_available_cell(self) -> Tuple[int, int]:
        """
        Find the next available grid cell.
        
        Returns:
            Grid position as (row, col)
        """
        # Scan grid for available cell
        for row in range(self.max_row + 2):  # +2 to allow growth
            for col in range(self.max_col):
                if (row, col) not in self.grid_positions:
                    return row, col
        
        # If no cell found, add to a new row
        return self.max_row + 1, 0
    
    def _place_widget_at(self, container: DraggableWidget, widget_id: str, 
                         row: int, col: int, row_span: int = 1, col_span: int = 1):
        """
        Place a widget at the specified grid position.
        
        Args:
            container: Widget container
            widget_id: Widget ID
            row: Grid row
            col: Grid column
            row_span: Number of rows to span
            col_span: Number of columns to span
        """
        # Check if cells are available
        for r in range(row, row + row_span):
            for c in range(col, col + col_span):
                if (r, c) in self.grid_positions and self.grid_positions[(r, c)] != widget_id:
                    # Cell is occupied by another widget, adjust position
                    row, col = self._find_next_available_cell()
                    return self._place_widget_at(container, widget_id, row, col, row_span, col_span)
        
        # Place widget in grid
        self.grid_layout.addWidget(container, row, col, row_span, col_span)
        
        # Update tracking
        for r in range(row, row + row_span):
            for c in range(col, col + col_span):
                self.grid_positions[(r, c)] = widget_id
        
        self.widget_positions[widget_id] = (row, col, row_span, col_span)
        
        # Update max_row
        self.max_row = max(self.max_row, row + row_span - 1)
    
    @pyqtSlot(str)
    def _on_widget_selected(self, widget_id: str):
        """
        Handle widget selection.
        
        Args:
            widget_id: ID of the selected widget
        """
        # Deselect previous widget
        if self.selected_widget_id and self.selected_widget_id != widget_id:
            if self.selected_widget_id in self.widgets:
                self.widgets[self.selected_widget_id].set_selected(False)
        
        # Update selection
        self.selected_widget_id = widget_id
        
        # Emit signal
        self.widget_selected.emit(widget_id)
    
    @pyqtSlot(str, QPoint)
    def _on_widget_move_requested(self, widget_id: str, position: QPoint):
        """
        Handle widget move request.
        
        Args:
            widget_id: ID of the widget to move
            position: New position in screen coordinates
        """
        self.move_widget(widget_id, position)
    
    def contextMenuEvent(self, event: QContextMenuEvent):
        """
        Handle context menu event.
        
        Args:
            event: Context menu event
        """
        # Create context menu
        menu = QMenu(self)
        
        # Add actions
        clear_action = menu.addAction("Clear All Widgets")
        clear_action.triggered.connect(self.clear_all)
        
        # If a widget is selected, add widget-specific actions
        if self.selected_widget_id:
            menu.addSeparator()
            remove_action = menu.addAction(f"Remove Widget '{self.selected_widget_id}'")
            remove_action.triggered.connect(lambda: self.remove_widget(self.selected_widget_id))
        
        # Show menu
        menu.exec(event.globalPos())
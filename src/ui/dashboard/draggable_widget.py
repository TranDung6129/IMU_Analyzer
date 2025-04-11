# src/ui/dashboard/draggable_widget.py
import logging
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                            QLabel, QFrame, QSizePolicy, QMenu)
from PyQt6.QtCore import Qt, pyqtSignal, pyqtSlot, QSize, QPoint, QEvent, QObject
from PyQt6.QtGui import QMouseEvent, QContextMenuEvent, QColor, QPalette

logger = logging.getLogger(__name__)

class DraggableWidget(QFrame):
    """
    A draggable container for dashboard widgets.
    
    Features:
    - Custom title bar with close button
    - Dragging support
    - Selection highlighting
    - Context menu
    """
    
    # Signals
    close_requested = pyqtSignal(str)  # (widget_id)
    selected = pyqtSignal(str)  # (widget_id)
    move_requested = pyqtSignal(str, QPoint)  # (widget_id, position)
    resize_requested = pyqtSignal(str, QSize)  # (widget_id, size)
    
    def __init__(self, content_widget: QWidget, title: str = "Widget", widget_id: str = None, parent: QWidget = None):
        """
        Initialize the draggable widget.
        
        Args:
            content_widget: Widget to contain
            title: Title to display in the title bar
            widget_id: Unique identifier for the widget
            parent: Parent widget
        """
        super().__init__(parent)
        
        # Store widget ID and content
        self.widget_id = widget_id
        self.content_widget = content_widget
        self.title_text = title
        
        # Dragging state
        self.dragging = False
        self.drag_start_position = QPoint()
        
        # Selection state
        self.is_selected = False
        
        # Setup UI
        self._setup_ui()
        
        # Install event filter on title bar for dragging
        self.title_bar.installEventFilter(self)
        
        logger.debug(f"DraggableWidget '{widget_id}' initialized")
    
    def _setup_ui(self):
        """Set up the widget UI."""
        # Setup frame
        self.setFrameShape(QFrame.Shape.Panel)
        self.setFrameShadow(QFrame.Shadow.Raised)
        self.setLineWidth(1)
        
        # Main layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(1, 1, 1, 1)
        self.main_layout.setSpacing(0)
        
        # Create title bar
        self.title_bar = self._create_title_bar()
        self.main_layout.addWidget(self.title_bar)
        
        # Add content widget
        self.main_layout.addWidget(self.content_widget)
        
        # Set size policy
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        # Apply styling
        self._update_styling()
    
    def _create_title_bar(self) -> QWidget:
        """
        Create the title bar widget.
        
        Returns:
            Title bar widget
        """
        # Title bar container
        title_bar = QWidget()
        title_bar.setObjectName("titleBar")
        title_bar.setMinimumHeight(24)
        title_bar.setMaximumHeight(24)
        
        # Title bar layout
        layout = QHBoxLayout(title_bar)
        layout.setContentsMargins(5, 0, 5, 0)
        layout.setSpacing(4)
        
        # Title label
        self.title_label = QLabel(self.title_text)
        self.title_label.setObjectName("titleLabel")
        layout.addWidget(self.title_label)
        
        # Add stretch to push buttons to the right
        layout.addStretch(1)
        
        # Close button
        self.close_btn = QPushButton("×")
        self.close_btn.setObjectName("closeButton")
        self.close_btn.setFixedSize(16, 16)
        self.close_btn.clicked.connect(self._on_close_clicked)
        layout.addWidget(self.close_btn)
        
        return title_bar
    
    def _update_styling(self):
        """Update widget styling based on selection state."""
        if self.is_selected:
            # Selected style
            self.setStyleSheet("""
                DraggableWidget {
                    border: 1px solid #3498db;
                }
                #titleBar {
                    background-color: #3498db;
                    color: white;
                }
                #titleLabel {
                    color: white;
                    font-weight: bold;
                }
                #closeButton {
                    background-color: #e74c3c;
                    color: white;
                    border: none;
                    border-radius: 8px;
                }
                #closeButton:hover {
                    background-color: #c0392b;
                }
            """)
        else:
            # Normal style
            self.setStyleSheet("""
                DraggableWidget {
                    border: 1px solid #bdc3c7;
                }
                #titleBar {
                    background-color: #ecf0f1;
                }
                #titleLabel {
                    color: #2c3e50;
                }
                #closeButton {
                    background-color: #e74c3c;
                    color: white;
                    border: none;
                    border-radius: 8px;
                }
                #closeButton:hover {
                    background-color: #c0392b;
                }
            """)
    
    def set_selected(self, selected: bool):
        """
        Set the selection state of the widget.
        
        Args:
            selected: Whether the widget is selected
        """
        if self.is_selected != selected:
            self.is_selected = selected
            self._update_styling()
    
    def mousePressEvent(self, event: QMouseEvent):
        """
        Handle mouse press event.
        
        Args:
            event: Mouse press event
        """
        # Select widget on click
        if event.button() == Qt.MouseButton.LeftButton:
            self.set_selected(True)
            self.selected.emit(self.widget_id)
        
        super().mousePressEvent(event)
    
    def contextMenuEvent(self, event: QContextMenuEvent):
        """
        Handle context menu event.
        
        Args:
            event: Context menu event
        """
        # Create context menu
        menu = QMenu(self)
        
        # Add actions
        close_action = menu.addAction("Close")
        close_action.triggered.connect(self._on_close_clicked)
        
        # Add any custom actions here
        
        # Show menu
        menu.exec(event.globalPos())
    
    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        """
        Filter events for child widgets.
        
        Used to implement dragging from the title bar.
        
        Args:
            obj: Object that received the event
            event: Event
            
        Returns:
            True if the event was handled, False otherwise
        """
        # Handle dragging from title bar
        if obj == self.title_bar:
            if event.type() == QEvent.Type.MouseButtonPress:
                mouse_event = QMouseEvent(event)
                if mouse_event.button() == Qt.MouseButton.LeftButton:
                    self.dragging = True
                    self.drag_start_position = mouse_event.position().toPoint()
                    return True
                
            elif event.type() == QEvent.Type.MouseMove:
                if self.dragging:
                    mouse_event = QMouseEvent(event)
                    delta = mouse_event.position().toPoint() - self.drag_start_position
                    
                    # Calculate new position in parent coordinates
                    global_pos = self.mapToGlobal(delta)
                    new_pos = self.parent().mapFromGlobal(global_pos)
                    
                    # Emit move request
                    self.move_requested.emit(self.widget_id, new_pos)
                    return True
                
            elif event.type() == QEvent.Type.MouseButtonRelease:
                if self.dragging:
                    self.dragging = False
                    return True
        
        # Pass event to parent class
        return super().eventFilter(obj, event)
    
    def _on_close_clicked(self):
        """Handle close button click."""
        self.close_requested.emit(self.widget_id)
    
    def sizeHint(self) -> QSize:
        """
        Get the suggested size for the widget.
        
        Returns:
            Suggested size
        """
        return QSize(300, 200)
# src/ui/dashboard/dashboard_control_panel.py
import os
import logging
from typing import Dict, Any, List, Optional, Callable
from PyQt6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QPushButton, 
                            QLabel, QComboBox, QFileDialog, QMessageBox, 
                            QGroupBox, QGridLayout, QToolButton, QSizePolicy)
from PyQt6.QtCore import Qt, pyqtSignal, pyqtSlot, QSize
from PyQt6.QtGui import QIcon

from src.ui.dashboard.grid_dashboard_panel import GridDashboardPanel
from src.ui.dashboard.dashboard_manager import DashboardManager

logger = logging.getLogger(__name__)

class DashboardControlPanel(QWidget):
    """
    Control panel for the dashboard UI.
    
    Provides controls for:
    - Adding/removing widgets
    - Selecting widget types
    - Saving/loading layouts
    - Configuring dashboard settings
    """
    
    # Signals
    widget_added = pyqtSignal(str, str)  # (widget_type, widget_id)
    layout_saved = pyqtSignal(str)  # (file_path)
    layout_loaded = pyqtSignal(str)  # (file_path)
    
    def __init__(self, dashboard_panel: GridDashboardPanel, dashboard_manager: Optional[DashboardManager] = None, parent: Optional[QWidget] = None):
        """
        Initialize the dashboard control panel.
        
        Args:
            dashboard_panel: The dashboard panel to control
            dashboard_manager: The dashboard manager (created if None)
            parent: Parent widget
        """
        super().__init__(parent)
        
        # Store references
        self.dashboard_panel = dashboard_panel
        self.dashboard_manager = dashboard_manager or DashboardManager(dashboard_panel)
        
        # Widget factories
        self.widget_factories = {}  # {widget_type: factory_function}
        
        # Setup UI
        self._setup_ui()
        
        # Connect signals
        self._connect_signals()
        
        logger.info("DashboardControlPanel initialized")
    
    def _setup_ui(self):
        """Set up the UI components."""
        # Main layout
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(10)
        
        # ===== Left side: Widget actions =====
        widget_group = QGroupBox("Add Widgets")
        widget_layout = QVBoxLayout(widget_group)
        
        # Widget type combobox
        self.widget_type_combo = QComboBox()
        self.widget_type_combo.addItem("Select Widget Type")
        widget_layout.addWidget(self.widget_type_combo)
        
        # Add widget button
        self.add_widget_btn = QPushButton("Add Widget")
        self.add_widget_btn.setEnabled(False)
        widget_layout.addWidget(self.add_widget_btn)
        
        # Remove widget button
        self.remove_widget_btn = QPushButton("Remove Selected Widget")
        self.remove_widget_btn.setEnabled(False)
        widget_layout.addWidget(self.remove_widget_btn)
        
        # Add widget group to main layout
        main_layout.addWidget(widget_group)
        
        # ===== Middle: Layout actions =====
        layout_group = QGroupBox("Layout")
        layout_layout = QVBoxLayout(layout_group)
        
        # Save layout button
        self.save_layout_btn = QPushButton("Save Layout")
        layout_layout.addWidget(self.save_layout_btn)
        
        # Load layout button
        self.load_layout_btn = QPushButton("Load Layout")
        layout_layout.addWidget(self.load_layout_btn)
        
        # Clear dashboard button
        self.clear_dashboard_btn = QPushButton("Clear Dashboard")
        layout_layout.addWidget(self.clear_dashboard_btn)
        
        # Add layout group to main layout
        main_layout.addWidget(layout_group)
        
        # ===== Right side: Quick Add buttons =====
        quick_add_group = QGroupBox("Quick Add")
        quick_add_layout = QGridLayout(quick_add_group)
        
        # This will be populated as widget factories are registered
        self.quick_add_buttons = {}
        
        # Placeholder
        quick_add_layout.addWidget(QLabel("Register widget factories to see quick add buttons"), 0, 0)
        
        # Add quick add group to main layout
        main_layout.addWidget(quick_add_group)
        
        # Add stretch to push groups to the left
        main_layout.addStretch(1)
    
    def _connect_signals(self):
        """Connect signals to slots."""
        # Widget actions
        self.widget_type_combo.currentIndexChanged.connect(self._on_widget_type_selected)
        self.add_widget_btn.clicked.connect(self._on_add_widget_clicked)
        self.remove_widget_btn.clicked.connect(self._on_remove_widget_clicked)
        
        # Layout actions
        self.save_layout_btn.clicked.connect(self._on_save_layout_clicked)
        self.load_layout_btn.clicked.connect(self._on_load_layout_clicked)
        self.clear_dashboard_btn.clicked.connect(self._on_clear_dashboard_clicked)
        
        # Dashboard panel signals
        self.dashboard_panel.widget_selected.connect(self._on_widget_selected)
        self.dashboard_panel.widget_removed.connect(self._on_widget_removed)
    
    def register_widget_factory(self, widget_type: str, factory: Callable, icon_path: Optional[str] = None, tooltip: Optional[str] = None):
        """
        Register a widget factory function.
        
        Args:
            widget_type: Type identifier for the widget
            factory: Function that creates widgets of this type
            icon_path: Path to icon for quick add button (optional)
            tooltip: Tooltip for quick add button (optional)
        """
        # Register with dashboard manager
        self.dashboard_manager.register_widget_factory(widget_type, factory)
        
        # Store locally
        self.widget_factories[widget_type] = factory
        
        # Add to combobox
        self.widget_type_combo.addItem(widget_type)
        
        # Create quick add button
        quick_add_group = self.findChild(QGroupBox, "Quick Add")
        if quick_add_group:
            quick_add_layout = quick_add_group.layout()
            
            # Remove placeholder if this is the first factory
            if len(self.widget_factories) == 1:
                for i in reversed(range(quick_add_layout.count())):
                    item = quick_add_layout.itemAt(i)
                    if item and item.widget():
                        item.widget().deleteLater()
            
            # Create button
            button = QToolButton()
            button.setText(widget_type)
            button.setToolTip(tooltip or f"Add {widget_type}")
            button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
            button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
            button.setMinimumSize(70, 70)
            
            # Add icon if provided
            if icon_path and os.path.exists(icon_path):
                button.setIcon(QIcon(icon_path))
                button.setIconSize(QSize(32, 32))
            
            # Connect signal
            button.clicked.connect(lambda checked, wt=widget_type: self._on_quick_add_clicked(wt))
            
            # Add to layout
            row = (len(self.widget_factories) - 1) // 3
            col = (len(self.widget_factories) - 1) % 3
            quick_add_layout.addWidget(button, row, col)
            
            # Store reference
            self.quick_add_buttons[widget_type] = button
        
        logger.info(f"Registered widget factory for '{widget_type}'")
    
    @pyqtSlot(int)
    def _on_widget_type_selected(self, index: int):
        """
        Handle widget type selection.
        
        Args:
            index: Selected index in the combobox
        """
        # Enable add button if a real type is selected (not the placeholder)
        self.add_widget_btn.setEnabled(index > 0)
    
    @pyqtSlot()
    def _on_add_widget_clicked(self):
        """Handle add widget button click."""
        # Get selected widget type
        index = self.widget_type_combo.currentIndex()
        if index <= 0:
            return
        
        widget_type = self.widget_type_combo.currentText()
        
        # Add widget
        try:
            widget_id = self.dashboard_manager.add_widget(widget_type)
            
            # Emit signal
            self.widget_added.emit(widget_type, widget_id)
            
            logger.info(f"Added {widget_type} widget with ID '{widget_id}'")
            
        except Exception as e:
            logger.error(f"Error adding widget: {e}")
            QMessageBox.critical(self, "Error", f"Could not add widget: {e}")
    
    @pyqtSlot()
    def _on_remove_widget_clicked(self):
        """Handle remove widget button click."""
        # Get selected widget
        widget_id = self.dashboard_panel.get_selected_widget_id()
        if not widget_id:
            QMessageBox.information(self, "No Selection", "Please select a widget to remove.")
            return
        
        # Confirm removal
        reply = QMessageBox.question(
            self, 
            "Confirm Removal", 
            f"Remove widget '{widget_id}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Remove widget
            self.dashboard_manager.remove_widget(widget_id)
            
            # Disable remove button
            self.remove_widget_btn.setEnabled(False)
    
    @pyqtSlot(str)
    def _on_widget_selected(self, widget_id: str):
        """
        Handle widget selection.
        
        Args:
            widget_id: ID of the selected widget
        """
        # Enable remove button
        self.remove_widget_btn.setEnabled(True)
    
    @pyqtSlot(str)
    def _on_widget_removed(self, widget_id: str):
        """
        Handle widget removal.
        
        Args:
            widget_id: ID of the removed widget
        """
        # Disable remove button if no selection
        if not self.dashboard_panel.get_selected_widget_id():
            self.remove_widget_btn.setEnabled(False)
    
    @pyqtSlot()
    def _on_save_layout_clicked(self):
        """Handle save layout button click."""
        # Get save path
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Dashboard Layout",
            "",
            "Layout Files (*.json)"
        )
        
        if not file_path:
            return
        
        # Add .json extension if missing
        if not file_path.lower().endswith(".json"):
            file_path += ".json"
        
        # Save layout
        if self.dashboard_manager.save_layout(file_path):
            # Emit signal
            self.layout_saved.emit(file_path)
            
            # Show success message
            QMessageBox.information(self, "Success", f"Layout saved to {file_path}")
        else:
            # Show error message
            QMessageBox.critical(self, "Error", f"Could not save layout to {file_path}")
    
    @pyqtSlot()
    def _on_load_layout_clicked(self):
        """Handle load layout button click."""
        # Get file path
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Load Dashboard Layout",
            "",
            "Layout Files (*.json)"
        )
        
        if not file_path or not os.path.exists(file_path):
            return
        
        # Confirm if dashboard is not empty
        if self.dashboard_panel.widgets:
            reply = QMessageBox.question(
                self, 
                "Confirm Load", 
                "Loading a layout will clear the current dashboard. Continue?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply != QMessageBox.StandardButton.Yes:
                return
        
        # Load layout
        if self.dashboard_manager.load_layout(file_path):
            # Emit signal
            self.layout_loaded.emit(file_path)
            
            # Show success message
            QMessageBox.information(self, "Success", f"Layout loaded from {file_path}")
        else:
            # Show error message
            QMessageBox.critical(self, "Error", f"Could not load layout from {file_path}")
    
    @pyqtSlot()
    def _on_clear_dashboard_clicked(self):
        """Handle clear dashboard button click."""
        # Confirm clear
        if not self.dashboard_panel.widgets:
            QMessageBox.information(self, "Empty Dashboard", "Dashboard is already empty.")
            return
        
        reply = QMessageBox.question(
            self, 
            "Confirm Clear", 
            "Clear all widgets from the dashboard?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Clear dashboard
            self.dashboard_manager.clear_dashboard()
            
            # Disable remove button
            self.remove_widget_btn.setEnabled(False)
    
    @pyqtSlot(str)
    def _on_quick_add_clicked(self, widget_type: str):
        """
        Handle quick add button click.
        
        Args:
            widget_type: Type of widget to add
        """
        # Add widget
        try:
            widget_id = self.dashboard_manager.add_widget(widget_type)
            
            # Emit signal
            self.widget_added.emit(widget_type, widget_id)
            
            logger.info(f"Quick-added {widget_type} widget with ID '{widget_id}'")
            
        except Exception as e:
            logger.error(f"Error adding widget: {e}")
            QMessageBox.critical(self, "Error", f"Could not add widget: {e}")
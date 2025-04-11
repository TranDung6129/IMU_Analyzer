# src/ui/main_dashboard_app.py
import os
import sys
import logging
import argparse
from typing import Dict, Any, List, Optional
from PyQt6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QWidget, 
                            QDockWidget, QStatusBar, QMenuBar, QMenu, QToolBar, QLabel)
from PyQt6.QtCore import Qt, pyqtSlot, QSettings
from PyQt6.QtGui import QAction, QIcon, QKeySequence, QActionGroup

# Import dashboard components
from src.ui.dashboard.grid_dashboard_panel import GridDashboardPanel
from src.ui.dashboard.dashboard_manager import DashboardManager
from src.ui.dashboard.dashboard_control_panel import DashboardControlPanel

# Import visualizers used in the dashboard
from src.plugins.visualizers.time_series_visualizer import TimeSeriesVisualizer
from src.plugins.visualizers.fft_visualizer import FFTVisualizer

# Import UI utilities
from src.ui.utils.themes import apply_theme, get_theme_names, get_current_theme

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

class MainDashboardWindow(QMainWindow):
    """
    Main window for the IMU Analyzer dashboard UI.
    
    Features:
    - Customizable dashboard with various visualizer widgets
    - Dockable control panels
    - Menu and toolbar actions
    - Theme selection
    - Layout saving/loading
    """
    
    def __init__(self):
        """Initialize the main window."""
        super().__init__()
        
        # Setup window properties
        self.setWindowTitle("IMU Analyzer Dashboard")
        self.setMinimumSize(1024, 768)
        
        # Create central widget with dashboard
        self.setup_central_widget()
        
        # Create dockable panels
        self.setup_dock_widgets()
        
        # Create menu bar
        self.setup_menu()
        
        # Create toolbar
        self.setup_toolbar()
        
        # Create status bar
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("Ready")
        
        # Register widget factories
        self.register_widget_factories()
        
        # Load settings
        self.load_settings()
        
        logger.info("Main dashboard window initialized")
    
    def setup_central_widget(self):
        """Set up the central widget with dashboard panel."""
        # Create central container
        central_widget = QWidget()
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Create dashboard panel
        self.dashboard_panel = GridDashboardPanel()
        layout.addWidget(self.dashboard_panel)
        
        # Create dashboard manager
        self.dashboard_manager = DashboardManager(self.dashboard_panel)
        
        # Create control panel
        self.control_panel = DashboardControlPanel(self.dashboard_panel, self.dashboard_manager)
        layout.addWidget(self.control_panel)
        
        # Set central widget
        self.setCentralWidget(central_widget)
        
        # Connect signals
        self.dashboard_panel.widget_selected.connect(self.on_widget_selected)
        self.control_panel.widget_added.connect(self.on_widget_added)
        self.control_panel.layout_saved.connect(self.on_layout_saved)
        self.control_panel.layout_loaded.connect(self.on_layout_loaded)
    
    def setup_dock_widgets(self):
        """Set up dockable widgets."""
        # Configuration dock - placeholder for future use
        self.config_dock = QDockWidget("Configuration", self)
        self.config_dock.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea | 
                                          Qt.DockWidgetArea.RightDockWidgetArea)
        
        # Create a placeholder widget for now
        config_widget = QWidget()
        self.config_dock.setWidget(config_widget)
        
        # Add to main window
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.config_dock)
        
        # Hide by default - will be used in future
        self.config_dock.hide()
    
    def setup_menu(self):
        """Set up the menu bar."""
        # Create menu bar
        menu_bar = self.menuBar()
        
        # File menu
        file_menu = menu_bar.addMenu("&File")
        
        # Save layout action
        save_layout_action = QAction("&Save Layout...", self)
        save_layout_action.setShortcut(QKeySequence.StandardKey.Save)
        save_layout_action.triggered.connect(self.on_save_layout)
        file_menu.addAction(save_layout_action)
        
        # Load layout action
        load_layout_action = QAction("&Load Layout...", self)
        load_layout_action.setShortcut(QKeySequence.StandardKey.Open)
        load_layout_action.triggered.connect(self.on_load_layout)
        file_menu.addAction(load_layout_action)
        
        file_menu.addSeparator()
        
        # Exit action
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut(QKeySequence.StandardKey.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # View menu
        view_menu = menu_bar.addMenu("&View")
        
        # Add dock widget toggles
        view_menu.addAction(self.config_dock.toggleViewAction())
        
        view_menu.addSeparator()
        
        # Themes submenu
        themes_menu = view_menu.addMenu("Themes")
        
        # Add theme actions
        theme_names = get_theme_names()
        theme_group = QActionGroup(self)
        theme_group.setExclusive(True)
        
        for theme_name in theme_names:
            theme_action = QAction(theme_name, self)
            theme_action.setCheckable(True)
            if theme_name == get_current_theme():
                theme_action.setChecked(True)
            theme_action.triggered.connect(lambda checked, tn=theme_name: self.on_theme_selected(tn))
            themes_menu.addAction(theme_action)
            theme_group.addAction(theme_action)
        
        # Help menu
        help_menu = menu_bar.addMenu("&Help")
        
        # About action
        about_action = QAction("&About", self)
        about_action.triggered.connect(self.on_about)
        help_menu.addAction(about_action)
    
    def setup_toolbar(self):
        """Set up the toolbar."""
        # Create toolbar
        toolbar = QToolBar("Main Toolbar", self)
        self.addToolBar(toolbar)
        
        # Add actions
        # Save layout action
        save_layout_action = QAction("Save Layout", self)
        save_layout_action.triggered.connect(self.on_save_layout)
        toolbar.addAction(save_layout_action)
        
        # Load layout action
        load_layout_action = QAction("Load Layout", self)
        load_layout_action.triggered.connect(self.on_load_layout)
        toolbar.addAction(load_layout_action)
        
        # Add separator
        toolbar.addSeparator()
        
        # Clear dashboard action
        clear_action = QAction("Clear Dashboard", self)
        clear_action.triggered.connect(self.on_clear_dashboard)
        toolbar.addAction(clear_action)
    
    def register_widget_factories(self):
        """Register factories for different widget types."""
        # Register time series visualizer
        self.control_panel.register_widget_factory(
            "TimeSeriesVisualizer",
            self.create_time_series_visualizer,
            tooltip="Add Time Series Plot"
        )
        
        # Register FFT visualizer
        self.control_panel.register_widget_factory( 
            "FFTVisualizer",
            self.create_fft_visualizer,
            tooltip="Add FFT Plot"
        )
    
    def create_time_series_visualizer(self, widget_id: str, config: Optional[Dict[str, Any]] = None) -> QWidget:
        """
        Factory function to create a time series visualizer widget.
        
        Args:
            widget_id: ID for the widget
            config: Configuration for the widget
            
        Returns:
            Time series visualizer widget
        """
        # Use default config if not provided
        config = config or {
            'channels': ['x', 'y', 'z'],
            'window_size': 100,
            'update_interval': 0.5,
            'ascii_plot': False,
            'gui_mode': True
        }
        
        # Create visualizer
        visualizer = TimeSeriesVisualizer(config)
        visualizer.setup()
        
        # Create Qt container for the visualizer
        container = QWidget()
        layout = QVBoxLayout(container)
        
        # If matplotlib is available, use matplotlib figure
        if hasattr(visualizer, 'canvas'):
            layout.addWidget(visualizer.canvas)
        else:
            # Otherwise create a placeholder
            label = QLabel("Time Series Plot")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(label)
        
        # Store visualizer reference
        container.visualizer = visualizer
        
        return container
    
    def create_fft_visualizer(self, widget_id: str, config: Optional[Dict[str, Any]] = None) -> QWidget:
        """
        Factory function to create an FFT visualizer widget.
        
        Args:
            widget_id: ID for the widget
            config: Configuration for the widget
            
        Returns:
            FFT visualizer widget
        """
        # Use default config if not provided
        config = config or {
            'channels': ['x', 'y', 'z'],
            'window_size': 100,
            'update_interval': 0.5,
            'frequency_range': [0.1, 50],
            'log_scale': True,
            'gui_mode': True
        }
        
        # Create visualizer
        visualizer = FFTVisualizer(config)
        visualizer.setup()
        
        # Create Qt container for the visualizer
        container = QWidget()
        layout = QVBoxLayout(container)
        
        # If matplotlib is available, use matplotlib figure
        if hasattr(visualizer, 'canvas'):
            layout.addWidget(visualizer.canvas)
        else:
            # Otherwise create a placeholder
            label = QLabel("FFT Plot")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(label)
        
        # Store visualizer reference
        container.visualizer = visualizer
        
        return container
    
    def load_settings(self):
        """Load application settings."""
        settings = QSettings("IMUAnalyzer", "Dashboard")
        
        # Load window geometry
        geometry = settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)
        
        # Load window state
        state = settings.value("windowState")
        if state:
            self.restoreState(state)
        
        # Load theme
        theme = settings.value("theme")
        if theme:
            apply_theme(theme)
    
    def save_settings(self):
        """Save application settings."""
        settings = QSettings("IMUAnalyzer", "Dashboard")
        
        # Save window geometry
        settings.setValue("geometry", self.saveGeometry())
        
        # Save window state
        settings.setValue("windowState", self.saveState())
        
        # Save theme
        settings.setValue("theme", get_current_theme())
    
    def closeEvent(self, event):
        """Handle window close event."""
        # Save settings
        self.save_settings()
        
        # Accept the close event
        event.accept()
    
    @pyqtSlot(str)
    def on_widget_selected(self, widget_id: str):
        """
        Handle widget selection.
        
        Args:
            widget_id: ID of the selected widget
        """
        self.statusBar.showMessage(f"Selected widget: {widget_id}")
    
    @pyqtSlot(str, str)
    def on_widget_added(self, widget_type: str, widget_id: str):
        """
        Handle widget addition.
        
        Args:
            widget_type: Type of the added widget
            widget_id: ID of the added widget
        """
        self.statusBar.showMessage(f"Added {widget_type} widget: {widget_id}")
    
    @pyqtSlot(str)
    def on_layout_saved(self, file_path: str):
        """
        Handle layout save.
        
        Args:
            file_path: Path where the layout was saved
        """
        self.statusBar.showMessage(f"Layout saved to: {file_path}")
    
    @pyqtSlot(str)
    def on_layout_loaded(self, file_path: str):
        """
        Handle layout load.
        
        Args:
            file_path: Path from where the layout was loaded
        """
        self.statusBar.showMessage(f"Layout loaded from: {file_path}")
    
    @pyqtSlot()
    def on_save_layout(self):
        """Handle save layout action."""
        # Call the control panel's save layout function
        self.control_panel._on_save_layout_clicked()
    
    @pyqtSlot()
    def on_load_layout(self):
        """Handle load layout action."""
        # Call the control panel's load layout function
        self.control_panel._on_load_layout_clicked()
    
    @pyqtSlot()
    def on_clear_dashboard(self):
        """Handle clear dashboard action."""
        # Call the control panel's clear dashboard function
        self.control_panel._on_clear_dashboard_clicked()
    
    @pyqtSlot(str)
    def on_theme_selected(self, theme_name: str):
        """
        Handle theme selection.
        
        Args:
            theme_name: Name of the selected theme
        """
        # Apply the theme
        apply_theme(theme_name)
        
        # Update status
        self.statusBar.showMessage(f"Theme changed to: {theme_name}")
    
    @pyqtSlot()
    def on_about(self):
        """Handle about action."""
        from PyQt6.QtWidgets import QMessageBox
        
        QMessageBox.about(
            self,
            "About IMU Analyzer Dashboard",
            """
            <h1>IMU Analyzer Dashboard</h1>
            <p>A customizable dashboard for visualizing IMU sensor data.</p>
            <p>Version: 0.1.0</p>
            <p>Built with PyQt6</p>
            """
        )

def main():
    """Main entry point for the dashboard application."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="IMU Analyzer Dashboard")
    parser.add_argument("--theme", help="UI theme to use", default="Light")
    args = parser.parse_args()
    
    # Create application
    app = QApplication(sys.argv)
    app.setApplicationName("IMU Analyzer Dashboard")
    app.setOrganizationName("IMUAnalyzer")
    
    # Apply initial theme
    apply_theme(args.theme)
    
    # Create and show main window
    main_window = MainDashboardWindow()
    main_window.show()
    
    # Run application
    return app.exec()

if __name__ == "__main__":
    sys.exit(main())
# src/ui/dashboard/__init__.py
"""
Dashboard UI components for IMU Analyzer.

This package contains components for creating and managing
a customizable dashboard UI for visualizing sensor data.
"""

from .dashboard_manager import DashboardManager
from .grid_dashboard_panel import GridDashboardPanel
from .draggable_widget import DraggableWidget

# Exports
__all__ = ['DashboardManager', 'GridDashboardPanel', 'DraggableWidget']
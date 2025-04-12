# File: tests/test_dashboard.py
# Purpose: Unit tests for the Dashboard classes
# Target Lines: ≤150

import unittest
import sys
import os
import tempfile
import json
from unittest.mock import MagicMock, patch

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock PyQt6 modules for test environment
sys.modules['PyQt6'] = MagicMock()
sys.modules['PyQt6.QtWidgets'] = MagicMock()
sys.modules['PyQt6.QtCore'] = MagicMock()
sys.modules['PyQt6.QtGui'] = MagicMock()

# Import after mocking
from src.ui.dashboard.dashboard_manager import DashboardManager
from src.ui.dashboard.widget_manager import WidgetManager
from src.ui.dashboard.layout_config import LayoutConfig


class TestDashboardManager(unittest.TestCase):
    """Tests for the DashboardManager class"""

    def setUp(self):
        """Set up test fixtures"""
        self.parent_widget = MagicMock()
        self.dashboard_manager = DashboardManager(self.parent_widget)
        self.dashboard_manager.widget_manager = MagicMock()
        self.dashboard_manager.layout_config = MagicMock()
        self.test_layout = {
            "widgets": [
                {"id": "widget1", "type": "time_series", "position": {"x": 10, "y": 10},
                 "size": {"width": 300, "height": 200}, "config": {"title": "Test Widget 1"}},
                {"id": "widget2", "type": "fft", "position": {"x": 320, "y": 10},
                 "size": {"width": 300, "height": 200}, "config": {"title": "Test Widget 2"}}
            ]
        }

    def test_save_load(self):
        """Test save and load methods"""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as temp_file:
            temp_file_path = temp_file.name
        try:
            self.dashboard_manager.layout_config.save(self.test_layout, temp_file_path)
            self.assertTrue(os.path.exists(temp_file_path))
            with open(temp_file_path, "r") as f:
                self.assertEqual(json.load(f), self.test_layout)
            loaded_layout = self.dashboard_manager.layout_config.load(temp_file_path)
            self.assertEqual(loaded_layout, self.test_layout)
        finally:
            os.unlink(temp_file_path)

    def test_load_nonexistent_file(self):
        """Test loading a nonexistent file"""
        loaded_layout = self.dashboard_manager.layout_config.load("nonexistent_file.json")
        self.assertEqual(loaded_layout, {"widgets": []})

    def test_load_invalid_json(self):
        """Test loading an invalid JSON file"""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as temp_file:
            temp_file.write(b"invalid json")
            temp_file_path = temp_file.name
        try:
            loaded_layout = self.dashboard_manager.layout_config.load(temp_file_path)
            self.assertEqual(loaded_layout, {"widgets": []})
        finally:
            os.unlink(temp_file_path)

    def test_add_widget(self):
        """Test add_widget method"""
        widget_mock = MagicMock()
        self.dashboard_manager.widget_manager.add_widget.return_value = widget_mock
        result = self.dashboard_manager.add_widget(
            "test_widget", "time_series", {"title": "Test Widget"},
            {"x": 10, "y": 10}, {"width": 300, "height": 200}
        )
        self.assertEqual(result, widget_mock)
        self.dashboard_manager.widget_manager.add_widget.assert_called_once_with(
            "test_widget", "time_series", {"title": "Test Widget"},
            {"x": 10, "y": 10}, {"width": 300, "height": 200}
        )

    def test_enable_drag_and_drop(self):
        """Test enable_drag_and_drop method"""
        self.dashboard_manager.enable_drag_and_drop()
        self.dashboard_manager.widget_manager.enable_drag_and_drop.assert_called_once()

    def test_save_layout(self):
        """Test save_layout method"""
        self.dashboard_manager.widget_manager.get_layout.return_value = self.test_layout
        self.dashboard_manager.save_layout("test_layout.json")
        self.dashboard_manager.layout_config.save.assert_called_once_with(
            self.test_layout, "test_layout.json"
        )

    def test_load_layout(self):
        """Test load_layout method"""
        self.dashboard_manager.layout_config.load.return_value = self.test_layout
        self.dashboard_manager.load_layout("test_layout.json")
        self.dashboard_manager.layout_config.load.assert_called_once_with("test_layout.json")
        self.assertEqual(self.dashboard_manager.widget_manager.add_widget.call_count, 2)

    def test_init_from_config(self):
        """Test _init_from_config method"""
        self.dashboard_manager._init_from_config(self.test_layout)
        self.assertEqual(self.dashboard_manager.widget_manager.add_widget.call_count, 2)
        self.dashboard_manager.widget_manager.add_widget.assert_any_call(
            "widget1", "time_series", {"title": "Test Widget 1"},
            {"x": 10, "y": 10}, {"width": 300, "height": 200}
        )
        self.dashboard_manager.widget_manager.add_widget.assert_any_call(
            "widget2", "fft", {"title": "Test Widget 2"},
            {"x": 320, "y": 10}, {"width": 300, "height": 200}
        )


class TestWidgetManager(unittest.TestCase):
    """Tests for the WidgetManager class"""

    def setUp(self):
        """Set up test fixtures"""
        self.parent_widget = MagicMock()
        self.widget_manager = WidgetManager(self.parent_widget)
        self.widget_manager.widget_classes = {
            "time_series": MagicMock(),
            "fft": MagicMock(),
            "orientation3d": MagicMock()
        }

    def test_add_widget(self):
        """Test add_widget method"""
        widget_mock = MagicMock()
        self.widget_manager.widget_classes["time_series"].return_value = widget_mock
        result = self.widget_manager.add_widget(
            "test_widget", "time_series", {"title": "Test Widget"},
            {"x": 10, "y": 10}, {"width": 300, "height": 200}
        )
        self.assertEqual(result, widget_mock)
        self.assertIn("test_widget", self.widget_manager.widgets)
        self.widget_manager.widget_classes["time_series"].assert_called_once_with(
            self.parent_widget, {"title": "Test Widget"}
        )
        widget_mock.set_position.assert_called_once_with({"x": 10, "y": 10})
        widget_mock.set_size.assert_called_once_with({"width": 300, "height": 200})

    def test_update_widget(self):
        """Test update_widget method"""
        widget_mock = MagicMock()
        self.widget_manager.widgets["test_widget"] = widget_mock
        self.widget_manager.update_widget("test_widget", {"value": 42})
        widget_mock.update_data.assert_called_once_with({"value": 42})

    def test_resize_widget(self):
        """Test resize_widget method"""
        widget_mock = MagicMock()
        self.widget_manager.widgets["test_widget"] = widget_mock
        self.widget_manager.resize_widget("test_widget", {"width": 400, "height": 300})
        widget_mock.set_size.assert_called_once_with({"width": 400, "height": 300})

    def test_remove_widget(self):
        """Test remove_widget method"""
        widget_mock = MagicMock()
        self.widget_manager.widgets["test_widget"] = widget_mock
        self.widget_manager.remove_widget("test_widget")
        self.assertNotIn("test_widget", self.widget_manager.widgets)
        widget_mock.deleteLater.assert_called_once()

    def test_get_layout(self):
        """Test get_layout method"""
        widget1 = MagicMock()
        widget1.get_position.return_value = {"x": 10, "y": 10}
        widget1.get_size.return_value = {"width": 300, "height": 200}
        widget1.get_config.return_value = {"title": "Test Widget 1"}
        widget2 = MagicMock()
        widget2.get_position.return_value = {"x": 320, "y": 10}
        widget2.get_size.return_value = {"width": 300, "height": 200}
        widget2.get_config.return_value = {"title": "Test Widget 2"}
        self.widget_manager.widgets = {"widget1": widget1, "widget2": widget2}
        layout = self.widget_manager.get_layout()
        self.assertIn("widgets", layout)
        self.assertEqual(len(layout["widgets"]), 2)
        self.assertEqual(layout["widgets"][0]["position"], {"x": 10, "y": 10})
        self.assertEqual(layout["widgets"][1]["position"], {"x": 320, "y": 10})


class TestLayoutConfig(unittest.TestCase):
    """Tests for the LayoutConfig class"""

    def setUp(self):
        """Set up test fixtures"""
        self.layout_config = LayoutConfig()
        self.test_layout = {
            "widgets": [
                {"id": "widget1", "type": "time_series", "position": {"x": 10, "y": 10},
                 "size": {"width": 300, "height": 200}, "config": {"title": "Test Widget 1"}},
                {"id": "widget2", "type": "fft", "position": {"x": 320, "y": 10},
                 "size": {"width": 300, "height": 200}, "config": {"title": "Test Widget 2"}}
            ]
        }

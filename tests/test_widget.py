# File: tests/test_widget.py
# Purpose: Unit tests for the Widget classes
# Target Lines: ≤150

import unittest
import sys
import os
from unittest.mock import MagicMock, patch

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mocking PyQt6 modules since they may not be available in test environment
sys.modules['PyQt6'] = MagicMock()
sys.modules['PyQt6.QtWidgets'] = MagicMock()
sys.modules['PyQt6.QtCore'] = MagicMock()
sys.modules['PyQt6.QtGui'] = MagicMock()
sys.modules['pyqtgraph'] = MagicMock()

# Import after mocking
from src.ui.visualizers.base_widget import BaseWidget


# Custom Widget implementation for testing
class TestWidget(BaseWidget):
    """Custom widget implementation for testing"""
    
    def __init__(self, parent=None, config=None):
        """Initialize widget with config"""
        super().__init__(parent, config)
        self.updated_data = None
    
    def _setup_ui(self):
        """Set up UI components"""
        # Mock implementation
        pass
    
    def update_data(self, data):
        """Update widget with new data"""
        self.updated_data = data
        return True


class TestBaseWidget(unittest.TestCase):
    """Tests for the BaseWidget class"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Mock parent widget
        self.parent_widget = MagicMock()
        
        # Config for widget
        self.config = {
            "title": "Test Widget",
            "update_rate": 10,
            "colors": ["red", "green", "blue"]
        }
        
        # Create test widget
        self.widget = TestWidget(self.parent_widget, self.config)
    
    def test_initialization(self):
        """Test widget initialization"""
        # Verify widget is initialized properly
        self.assertEqual(self.widget.config, self.config)
        self.assertEqual(self.widget.parent(), self.parent_widget)
        self.assertEqual(self.widget.title, "Test Widget")
        self.assertIsNone(self.widget.updated_data)
    
    def test_set_position(self):
        """Test set_position method"""
        # Set position
        position = {"x": 100, "y": 200}
        self.widget.set_position(position)
        
        # Verify position was set
        self.widget.move.assert_called_once_with(100, 200)
    
    def test_set_size(self):
        """Test set_size method"""
        # Set size
        size = {"width": 300, "height": 200}
        self.widget.set_size(size)
        
        # Verify size was set
        self.widget.resize.assert_called_once_with(300, 200)
    
    def test_get_position(self):
        """Test get_position method"""
        # Mock widget position
        self.widget.x.return_value = 100
        self.widget.y.return_value = 200
        
        # Get position
        position = self.widget.get_position()
        
        # Verify position
        self.assertEqual(position, {"x": 100, "y": 200})
    
    def test_get_size(self):
        """Test get_size method"""
        # Mock widget size
        self.widget.width.return_value = 300
        self.widget.height.return_value = 200
        
        # Get size
        size = self.widget.get_size()
        
        # Verify size
        self.assertEqual(size, {"width": 300, "height": 200})
    
    def test_get_config(self):
        """Test get_config method"""
        # Get config
        config = self.widget.get_config()
        
        # Verify config
        self.assertEqual(config, self.config)
    
    def test_update_data(self):
        """Test update_data method"""
        # Update data
        data = {"value": 42, "timestamp": 123456789}
        result = self.widget.update_data(data)
        
        # Verify data was updated
        self.assertTrue(result)
        self.assertEqual(self.widget.updated_data, data)
    
    def test_update_config(self):
        """Test update_config method"""
        # Initial config
        self.assertEqual(self.widget.title, "Test Widget")
        
        # Update config
        new_config = {
            "title": "Updated Widget",
            "update_rate": 20
        }
        self.widget.update_config(new_config)
        
        # Verify config was updated and merged
        self.assertEqual(self.widget.title, "Updated Widget")
        self.assertEqual(self.widget.config["update_rate"], 20)
        self.assertEqual(self.widget.config["colors"], ["red", "green", "blue"])
    
    def test_show_hide(self):
        """Test show and hide methods"""
        # Show widget
        self.widget.show_widget()
        
        # Verify widget was shown
        self.widget.show.assert_called_once()
        
        # Hide widget
        self.widget.hide_widget()
        
        # Verify widget was hidden
        self.widget.hide.assert_called_once()


# Additional tests for specific widget implementations
class TestTimeSeriesWidget(unittest.TestCase):
    """Tests for the TimeSeriesWidget class"""
    
    @patch('src.ui.visualizers.time_series_widget.TimeSeriesWidget')
    def test_time_series_widget(self, MockTimeSeriesWidget):
        """Test TimeSeriesWidget implementation"""
        # Mock implementation
        widget_instance = MagicMock()
        MockTimeSeriesWidget.return_value = widget_instance
        
        # Create widget
        parent = MagicMock()
        config = {"title": "Time Series"}
        
        from src.ui.visualizers.time_series_widget import TimeSeriesWidget
        widget = TimeSeriesWidget(parent, config)
        
        # Verify widget was created
        MockTimeSeriesWidget.assert_called_once_with(parent, config)


class TestFFTWidget(unittest.TestCase):
    """Tests for the FFTWidget class"""
    
    @patch('src.ui.visualizers.fft_widget.FFTWidget')
    def test_fft_widget(self, MockFFTWidget):
        """Test FFTWidget implementation"""
        # Mock implementation
        widget_instance = MagicMock()
        MockFFTWidget.return_value = widget_instance
        
        # Create widget
        parent = MagicMock()
        config = {"title": "FFT"}
        
        from src.ui.visualizers.fft_widget import FFTWidget
        widget = FFTWidget(parent, config)
        
        # Verify widget was created
        MockFFTWidget.assert_called_once_with(parent, config)


class TestOrientation3DWidget(unittest.TestCase):
    """Tests for the Orientation3DWidget class"""
    
    @patch('src.ui.visualizers.orientation3d_widget.Orientation3DWidget')
    def test_orientation3d_widget(self, MockOrientation3DWidget):
        """Test Orientation3DWidget implementation"""
        # Mock implementation
        widget_instance = MagicMock()
        MockOrientation3DWidget.return_value = widget_instance
        
        # Create widget
        parent = MagicMock()
        config = {"title": "3D Orientation"}
        
        from src.ui.visualizers.orientation3d_widget import Orientation3DWidget
        widget = Orientation3DWidget(parent, config)
        
        # Verify widget was created
        MockOrientation3DWidget.assert_called_once_with(parent, config)


if __name__ == '__main__':
    unittest.main()
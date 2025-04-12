# File: tests/test_plugin_manager.py
# Purpose: Unit tests for the PluginManager class
# Target Lines: ≤150

import unittest
import sys
import os
import tempfile
import shutil
from unittest.mock import patch, MagicMock

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.plugin_manager import PluginManager


class TestPluginManager(unittest.TestCase):
    """Tests for the PluginManager class"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create temporary directory for test plugins
        self.test_dir = tempfile.mkdtemp()
        
        # Create readers directory
        self.readers_dir = os.path.join(self.test_dir, "readers")
        os.makedirs(self.readers_dir, exist_ok=True)
        
        # Create processors directory
        self.processors_dir = os.path.join(self.test_dir, "processors")
        os.makedirs(self.processors_dir, exist_ok=True)
        
        # Create test plugin files
        self.reader_plugin_content = """
from src.io.readers.base_reader import BaseReader

class TestReader(BaseReader):
    def __init__(self, config):
        super().__init__(config)
    
    def open(self):
        return True
    
    def read(self):
        return {"test": "data"}
    
    def close(self):
        return True
"""
        
        self.processor_plugin_content = """
from src.plugins.processors.base_processor import BaseProcessor

class TestProcessor(BaseProcessor):
    def __init__(self, config=None):
        super().__init__(config)
    
    def init(self, config):
        self.initialized = True
        return True
    
    def process(self, data):
        return {"processed": data}
    
    def destroy(self):
        return True
"""
        
        # Write test plugin files
        with open(os.path.join(self.readers_dir, "test_reader.py"), "w") as f:
            f.write(self.reader_plugin_content)
        
        with open(os.path.join(self.processors_dir, "test_processor.py"), "w") as f:
            f.write(self.processor_plugin_content)
        
        # Create plugin manager with test directories
        self.plugin_manager = PluginManager([self.readers_dir, self.processors_dir])
    
    def tearDown(self):
        """Tear down test fixtures"""
        # Remove temporary directory
        shutil.rmtree(self.test_dir)
    
    def test_discover_plugins(self):
        """Test plugin discovery"""
        # Discover plugins
        self.plugin_manager.discover_plugins()
        
        # Verify readers plugin was discovered
        self.assertIn("test_reader", self.plugin_manager.plugins["readers"])
        self.assertEqual(
            self.plugin_manager.plugins["readers"]["test_reader"]["file_path"],
            os.path.join(self.readers_dir, "test_reader.py")
        )
        
        # Verify processors plugin was discovered
        self.assertIn("test_processor", self.plugin_manager.plugins["processors"])
        self.assertEqual(
            self.plugin_manager.plugins["processors"]["test_processor"]["file_path"],
            os.path.join(self.processors_dir, "test_processor.py")
        )
    
    @patch('importlib.util.spec_from_file_location')
    def test_load_plugin(self, mock_spec_from_file_location):
        """Test plugin loading"""
        # Setup mock module
        mock_module = MagicMock()
        mock_spec = MagicMock()
        mock_spec_from_file_location.return_value = mock_spec
        mock_spec.loader.exec_module = MagicMock()
        
        # Create a fake TestReader class in the mock module
        class TestReader:
            pass
        
        # Setup mock module to return TestReader
        mock_module.__name__ = "readers.test_reader"
        mock_module.TestReader = TestReader
        mock_spec.loader.exec_module.side_effect = lambda m: setattr(m, "TestReader", TestReader)
        
        # Simulate discovery
        self.plugin_manager.plugins["readers"]["test_reader"] = {
            "file_path": os.path.join(self.readers_dir, "test_reader.py"),
            "module": None,
            "class": None
        }
        
        # Mock _find_plugin_class to return TestReader class
        self.plugin_manager._find_plugin_class = MagicMock(return_value=TestReader)
        
        # Load plugin
        plugin_info = self.plugin_manager.load_plugin("readers", "test_reader")
        
        # Verify plugin was loaded
        self.assertIsNotNone(plugin_info["module"])
        self.assertEqual(plugin_info["class"], TestReader)
    
    def test_create_plugin_instance(self):
        """Test plugin instance creation"""
        # Setup a mock plugin class
        mock_class = MagicMock()
        mock_instance = MagicMock()
        mock_class.return_value = mock_instance
        
        # Setup plugin_info with mock class
        plugin_info = {
            "module": MagicMock(),
            "class": mock_class
        }
        
        # Mock load_plugin to return plugin_info
        self.plugin_manager.load_plugin = MagicMock(return_value=plugin_info)
        
        # Create plugin instance
        config = {"test": "config"}
        instance = self.plugin_manager.create_plugin_instance("readers", "test_reader", config)
        
        # Verify instance creation
        self.assertEqual(instance, mock_instance)
        mock_class.assert_called_once_with(config)
    
    def test_get_available_plugins(self):
        """Test getting available plugins"""
        # Simulate discovery
        self.plugin_manager.plugins["readers"]["test_reader"] = {
            "file_path": os.path.join(self.readers_dir, "test_reader.py"),
            "module": None,
            "class": None
        }
        self.plugin_manager.plugins["processors"]["test_processor"] = {
            "file_path": os.path.join(self.processors_dir, "test_processor.py"),
            "module": None,
            "class": None
        }
        
        # Get all available plugins
        all_plugins = self.plugin_manager.get_available_plugins()
        
        # Verify all plugins are returned
        self.assertIn("readers", all_plugins)
        self.assertIn("processors", all_plugins)
        self.assertIn("test_reader", all_plugins["readers"])
        self.assertIn("test_processor", all_plugins["processors"])
        
        # Get readers plugins only
        readers_plugins = self.plugin_manager.get_available_plugins("readers")
        
        # Verify only readers plugins are returned
        self.assertEqual(readers_plugins, ["test_reader"])
    
    def test_find_plugin_class(self):
        """Test finding plugin class in module"""
        # Create a module with a plugin class
        class BaseClass:
            pass
        
        class PluginClass(BaseClass):
            pass
        
        module = type('module', (), {
            "__name__": "test_module",
            "PluginClass": PluginClass,
            "SomeOtherClass": type('SomeOtherClass', (), {})
        })
        
        # Find the plugin class
        plugin_class = self.plugin_manager._find_plugin_class(module, "BaseClass")
        
        # Verify the correct class was found
        self.assertEqual(plugin_class, PluginClass)
    
    def test_get_plugin_type(self):
        """Test getting plugin type from directory name"""
        # Test valid plugin types
        for plugin_type in ["readers", "writers", "decoders", "processors", 
                          "analyzers", "visualizers", "exporters"]:
            self.assertEqual(self.plugin_manager._get_plugin_type(plugin_type), plugin_type)
        
        # Test invalid plugin type
        self.assertIsNone(self.plugin_manager._get_plugin_type("invalid_type"))


if __name__ == '__main__':
    unittest.main()
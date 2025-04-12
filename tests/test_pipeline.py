# File: tests/test_pipeline.py
# Purpose: Unit tests for the Pipeline class
# Target Lines: ≤150

import unittest
import sys
import os
import time
from unittest.mock import MagicMock, patch

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.pipeline import PipelineExecutor
from src.io.readers.base_reader import BaseReader
from src.io.writers.base_writer import BaseWriter
from src.plugins.decoders.base_decoder import BaseDecoder
from src.plugins.processors.base_processor import BaseProcessor
from src.plugins.analyzers.base_analyzer import BaseAnalyzer
from src.plugins.visualizers.base_visualizer import BaseVisualizer


class MockPluginManager:
    """Mock PluginManager for testing"""
    
    def __init__(self):
        self.plugins = {}
    
    def create_plugin_instance(self, plugin_type, plugin_name, config=None):
        """Mock plugin creation"""
        if plugin_type == "readers":
            mock = MagicMock(spec=BaseReader)
            mock.open.return_value = True
            mock.read.return_value = {"test": "data"}
            mock.close.return_value = True
            return mock
        elif plugin_type == "writers":
            mock = MagicMock(spec=BaseWriter)
            mock.open.return_value = True
            mock.write.return_value = 10
            mock.close.return_value = True
            return mock
        elif plugin_type == "decoders":
            mock = MagicMock(spec=BaseDecoder)
            mock.init.return_value = True
            mock.decode.return_value = {"decoded": "data"}
            mock.destroy.return_value = True
            return mock
        elif plugin_type == "processors":
            mock = MagicMock(spec=BaseProcessor)
            mock.init.return_value = True
            mock.process.return_value = {"processed": "data"}
            mock.destroy.return_value = True
            return mock
        elif plugin_type == "analyzers":
            mock = MagicMock(spec=BaseAnalyzer)
            mock.reset.return_value = True
            mock.analyze.return_value = {"analyzed": "data"}
            mock.update_config.return_value = True
            return mock
        elif plugin_type == "visualizers":
            mock = MagicMock(spec=BaseVisualizer)
            mock.init.return_value = True
            mock.visualize.return_value = {"visualization": "object"}
            mock.destroy.return_value = True
            return mock
        else:
            return MagicMock()


class TestPipeline(unittest.TestCase):
    """Tests for the PipelineExecutor class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.plugin_manager = MockPluginManager()
        self.config = {
            "id": "test_pipeline",
            "reader": {
                "type": "MockReader",
                "config": {"source": "test"}
            },
            "writer": {
                "type": "MockWriter",
                "config": {"destination": "test"}
            },
            "decoder": {
                "type": "MockDecoder",
                "config": {}
            },
            "processor": {
                "type": "MockProcessor",
                "config": {}
            },
            "analyzer": {
                "type": "MockAnalyzer",
                "config": {}
            },
            "visualizer": {
                "type": "MockVisualizer",
                "config": {}
            }
        }
        self.pipeline = PipelineExecutor(self.config, self.plugin_manager)
    
    def test_setup(self):
        """Test pipeline setup"""
        # Setup should initialize all components
        result = self.pipeline.setup()
        self.assertTrue(result)
        self.assertIsNotNone(self.pipeline.reader)
        self.assertIsNotNone(self.pipeline.writer)
        self.assertIsNotNone(self.pipeline.decoder)
        self.assertIsNotNone(self.pipeline.processor)
        self.assertIsNotNone(self.pipeline.analyzer)
        self.assertIsNotNone(self.pipeline.visualizer)
    
    def test_run_stop(self):
        """Test pipeline run and stop"""
        # Setup the pipeline
        self.pipeline.setup()
        
        # Run the pipeline
        result = self.pipeline.run()
        self.assertTrue(result)
        self.assertTrue(self.pipeline.running)
        
        # Give the threads some time to start
        time.sleep(0.1)
        
        # Check that threads are running
        for thread in self.pipeline.threads.values():
            self.assertTrue(thread.is_alive())
        
        # Stop the pipeline
        result = self.pipeline.stop()
        self.assertTrue(result)
        self.assertFalse(self.pipeline.running)
        
        # Give the threads some time to stop
        time.sleep(0.1)
        
        # Check that threads are stopped
        for thread in self.pipeline.threads.values():
            self.assertFalse(thread.is_alive())
    
    def test_get_metrics(self):
        """Test getting pipeline metrics"""
        # Setup and run pipeline
        self.pipeline.setup()
        self.pipeline.run()
        
        # Give the pipeline some time to generate metrics
        time.sleep(0.1)
        
        # Get metrics
        metrics = self.pipeline.get_metrics()
        
        # Verify metrics structure
        self.assertIn("read_count", metrics)
        self.assertIn("decode_count", metrics)
        self.assertIn("process_count", metrics)
        self.assertIn("analyze_count", metrics)
        self.assertIn("visualize_count", metrics)
        self.assertIn("write_count", metrics)
        self.assertIn("start_time", metrics)
        self.assertIn("throughput", metrics)
        
        # Stop the pipeline
        self.pipeline.stop()
    
    def test_get_status(self):
        """Test getting pipeline status"""
        # Setup and run pipeline
        self.pipeline.setup()
        self.pipeline.run()
        time.sleep(0.1)
        
        # Get status
        status = self.pipeline.get_status()
        
        # Verify status structure
        self.assertIn("id", status)
        self.assertIn("running", status)
        self.assertIn("metrics", status)
        self.assertIn("components", status)
        self.assertIn("queues", status)
        self.assertIn("threads", status)
        
        # Verify component status
        components = status["components"]
        self.assertIn("reader", components)
        self.assertIn("writer", components)
        self.assertIn("decoder", components)
        self.assertIn("processor", components)
        self.assertIn("analyzer", components)
        self.assertIn("visualizer", components)
        
        # Stop the pipeline
        self.pipeline.stop()
    
    def test_partial_pipeline(self):
        """Test pipeline with only some components"""
        # Create a config with only reader and writer
        config = {
            "id": "partial_pipeline",
            "reader": {
                "type": "MockReader",
                "config": {"source": "test"}
            },
            "writer": {
                "type": "MockWriter",
                "config": {"destination": "test"}
            }
        }
        pipeline = PipelineExecutor(config, self.plugin_manager)
        
        # Setup should complete without errors
        result = pipeline.setup()
        self.assertTrue(result)
        self.assertIsNotNone(pipeline.reader)
        self.assertIsNotNone(pipeline.writer)
        self.assertIsNone(pipeline.decoder)
        self.assertIsNone(pipeline.processor)
        self.assertIsNone(pipeline.analyzer)
        self.assertIsNone(pipeline.visualizer)
        
        # Run should complete without errors
        result = pipeline.run()
        self.assertTrue(result)
        time.sleep(0.1)
        
        # Stop should complete without errors
        result = pipeline.stop()
        self.assertTrue(result)


if __name__ == '__main__':
    unittest.main()
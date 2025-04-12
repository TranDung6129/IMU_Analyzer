# File: tests/test_sensor_sync.py
# Purpose: Unit tests for sensor synchronization
# Target Lines: ≤150

import unittest
import sys
import os
import time
import threading
from unittest.mock import MagicMock, patch
from queue import Queue

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.pipeline import PipelineExecutor
from src.system.sensor_registry import SensorRegistry


class TestSensorSync(unittest.TestCase):
    """Tests for sensor synchronization"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create sensor registry
        self.sensor_registry = SensorRegistry()
        
        # Create mock plugin manager
        self.plugin_manager = MagicMock()
        
        # Setup reader mock
        self.reader_mock = MagicMock()
        self.reader_mock.open.return_value = True
        self.reader_mock.read.return_value = {"timestamp": time.time(), "data": "test"}
        self.reader_mock.close.return_value = True
        
        # Setup writer mock
        self.writer_mock = MagicMock()
        self.writer_mock.open.return_value = True
        self.writer_mock.write.return_value = 10
        self.writer_mock.close.return_value = True
        
        # Setup decoder mock
        self.decoder_mock = MagicMock()
        self.decoder_mock.init.return_value = True
        self.decoder_mock.decode.return_value = {"decoded": "data", "timestamp": time.time()}
        self.decoder_mock.destroy.return_value = True
        
        # Setup plugin manager to return mocks
        self.plugin_manager.create_plugin_instance.side_effect = lambda plugin_type, plugin_name, config=None: {
            "readers": self.reader_mock,
            "writers": self.writer_mock,
            "decoders": self.decoder_mock
        }.get(plugin_type)
        
        # Create pipeline config
        self.pipeline_config = {
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
            }
        }
        
        # Create pipelines
        self.pipeline1 = PipelineExecutor(self.pipeline_config, self.plugin_manager)
        self.pipeline1.setup()
        
        self.pipeline_config2 = self.pipeline_config.copy()
        self.pipeline_config2["id"] = "test_pipeline2"
        self.pipeline2 = PipelineExecutor(self.pipeline_config2, self.plugin_manager)
        self.pipeline2.setup()
        
        # Register sensors in registry
        self.sensor_registry.register_sensor({
            "id": "sensor1",
            "type": "IMU",
            "pipeline": "test_pipeline"
        })
        
        self.sensor_registry.register_sensor({
            "id": "sensor2",
            "type": "IMU",
            "pipeline": "test_pipeline2"
        })
        
        # Create shared queue for test data collection
        self.test_queue = Queue()
        
        # Data collection function for patching
        def collect_data(self, data):
            self.test_queue.put((self.id, data))
            return 10
        
        # Patch writer.write to collect data
        self.original_write = self.writer_mock.write
        self.writer_mock.write = collect_data
    
    def tearDown(self):
        """Tear down test fixtures"""
        # Restore original write method
        self.writer_mock.write = self.original_write
        
        # Stop pipelines if running
        if self.pipeline1.running:
            self.pipeline1.stop()
        if self.pipeline2.running:
            self.pipeline2.stop()
    
    def test_concurrent_pipelines(self):
        """Test running multiple pipelines concurrently"""
        # Start pipelines
        self.pipeline1.run()
        self.pipeline2.run()
        
        # Wait for threads to start
        time.sleep(0.1)
        
        # Verify both pipelines are running
        self.assertTrue(self.pipeline1.running)
        self.assertTrue(self.pipeline2.running)
        
        # Verify readers were opened
        self.reader_mock.open.assert_called()
        
        # Wait for some data to be processed
        time.sleep(0.5)
        
        # Stop pipelines
        self.pipeline1.stop()
        self.pipeline2.stop()
        
        # Verify both pipelines are stopped
        self.assertFalse(self.pipeline1.running)
        self.assertFalse(self.pipeline2.running)
        
        # Check data was processed correctly
        self.assertFalse(self.test_queue.empty())
    
    def test_pipeline_synchronization(self):
        """Test synchronization between pipelines"""
        # Set up test reader to produce sequential timestamps
        timestamp = time.time()
        timestamps = []
        
        def sequential_read():
            nonlocal timestamp
            timestamp += 0.01
            data = {"timestamp": timestamp, "data": "test"}
            timestamps.append(timestamp)
            return data
        
        self.reader_mock.read = sequential_read
        
        # Start pipelines
        self.pipeline1.run()
        self.pipeline2.run()
        
        # Wait for some data to be processed
        time.sleep(0.5)
        
        # Stop pipelines
        self.pipeline1.stop()
        self.pipeline2.stop()
        
        # Collect data from test queue
        data_points = []
        while not self.test_queue.empty():
            data_points.append(self.test_queue.get())
        
        # Verify we have data from both pipelines
        pipeline1_data = [d for d in data_points if d[0] == "test_pipeline"]
        pipeline2_data = [d for d in data_points if d[0] == "test_pipeline2"]
        
        self.assertTrue(len(pipeline1_data) > 0)
        self.assertTrue(len(pipeline2_data) > 0)
    
    def test_sensor_registry_status(self):
        """Test sensor registry status updates"""
        # Start pipelines
        self.pipeline1.run()
        self.pipeline2.run()
        
        # Update status in registry
        self.sensor_registry.update_status("sensor1", "connected", {
            "pipeline": "test_pipeline",
            "throughput": 100
        })
        
        self.sensor_registry.update_status("sensor2", "connected", {
            "pipeline": "test_pipeline2",
            "throughput": 150
        })
        
        # Get sensor status
        status1 = self.sensor_registry.get_sensor_status("sensor1")
        status2 = self.sensor_registry.get_sensor_status("sensor2")
        
        # Verify status
        self.assertEqual(status1["status"], "connected")
        self.assertEqual(status1["details"]["throughput"], 100)
        self.assertEqual(status2["status"], "connected")
        self.assertEqual(status2["details"]["throughput"], 150)
        
        # Verify all sensors
        all_sensors = self.sensor_registry.get_all_sensors()
        self.assertEqual(len(all_sensors), 2)
        self.assertIn("sensor1", all_sensors)
        self.assertIn("sensor2", all_sensors)
        
        # Stop pipelines
        self.pipeline1.stop()
        self.pipeline2.stop()
        
        # Update status to disconnected
        self.sensor_registry.update_status("sensor1", "disconnected", {})
        
        # Verify status update
        status1 = self.sensor_registry.get_sensor_status("sensor1")
        self.assertEqual(status1["status"], "disconnected")


if __name__ == '__main__':
    unittest.main()
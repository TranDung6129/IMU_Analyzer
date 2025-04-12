# File: tests/test_configurator.py
# Purpose: Unit tests for the SensorConfigurator classes
# Target Lines: ≤150

import unittest
import sys
import os
from unittest.mock import MagicMock, patch

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.plugins.configurators.base_configurator import BaseConfigurator
from src.plugins.configurators.witmotion_configurator import WitMotionConfigurator


# Simple configurator implementation for testing
class SimpleConfigurator(BaseConfigurator):
    """Simple configurator for testing"""
    
    def __init__(self, config):
        super().__init__(config)
        self.configure_called = False
        self.reset_called = False
    
    def configure(self):
        """Configure the sensor"""
        self.configure_called = True
        self.is_configured = True
        return True
    
    def reset(self):
        """Reset the sensor"""
        self.reset_called = True
        self.is_configured = False
        return True


class TestBaseConfigurator(unittest.TestCase):
    """Tests for the BaseConfigurator class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.config = {
            "param1": "value1",
            "param2": "value2"
        }
        self.configurator = SimpleConfigurator(self.config)
    
    def test_initialization(self):
        """Test configurator initialization"""
        # Verify configurator is initialized properly
        self.assertEqual(self.configurator.config, self.config)
        self.assertFalse(self.configurator.is_configured)
        self.assertFalse(self.configurator.error_state)
        self.assertIsNone(self.configurator.error_message)
    
    def test_configure(self):
        """Test configure method"""
        # Configure sensor
        result = self.configurator.configure()
        
        # Verify configuration was successful
        self.assertTrue(result)
        self.assertTrue(self.configurator.configure_called)
        self.assertTrue(self.configurator.is_configured)
    
    def test_reset(self):
        """Test reset method"""
        # Configure sensor first
        self.configurator.configure()
        
        # Reset sensor
        result = self.configurator.reset()
        
        # Verify reset was successful
        self.assertTrue(result)
        self.assertTrue(self.configurator.reset_called)
        self.assertFalse(self.configurator.is_configured)
    
    def test_error_handling(self):
        """Test error handling in configurator"""
        # Set error
        self.configurator.set_error("Test error")
        
        # Verify error state
        self.assertTrue(self.configurator.error_state)
        self.assertEqual(self.configurator.error_message, "Test error")
        
        # Clear error
        self.configurator.clear_error()
        
        # Verify error cleared
        self.assertFalse(self.configurator.error_state)
        self.assertIsNone(self.configurator.error_message)
    
    def test_get_status(self):
        """Test get_status method"""
        # Configure sensor
        self.configurator.configure()
        
        # Set error
        self.configurator.set_error("Test error")
        
        # Get status
        status = self.configurator.get_status()
        
        # Verify status structure
        self.assertIn("is_configured", status)
        self.assertIn("error_state", status)
        self.assertIn("error_message", status)
        
        # Verify status values
        self.assertTrue(status["is_configured"])
        self.assertTrue(status["error_state"])
        self.assertEqual(status["error_message"], "Test error")


class TestWitMotionConfigurator(unittest.TestCase):
    """Tests for the WitMotionConfigurator class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.config = {
            "port": "COM3",
            "baudrate": 9600,
            "timeout": 1.0,
            "init_sequence": [
                "FF AA 69",
                "FF AA 02 01"
            ]
        }
        # Use patch to mock serial.Serial
        self.serial_patcher = patch('serial.Serial')
        self.mock_serial = self.serial_patcher.start()
        
        # Create mock serial instance
        self.mock_serial_instance = MagicMock()
        self.mock_serial.return_value = self.mock_serial_instance
        
        # Set is_open property of mock serial instance
        type(self.mock_serial_instance).is_open = MagicMock(return_value=True)
        
        self.configurator = WitMotionConfigurator(self.config)
    
    def tearDown(self):
        """Tear down test fixtures"""
        self.serial_patcher.stop()
    
    def test_initialization(self):
        """Test configurator initialization"""
        # Verify configurator is initialized properly
        self.assertEqual(self.configurator.config, self.config)
        self.assertEqual(self.configurator.port, "COM3")
        self.assertEqual(self.configurator.baudrate, 9600)
        self.assertEqual(self.configurator.timeout, 1.0)
        self.assertEqual(self.configurator.init_sequence, ["FF AA 69", "FF AA 02 01"])
        self.assertFalse(self.configurator.is_configured)
    
    def test_configure(self):
        """Test configure method"""
        # Configure sensor
        result = self.configurator.configure()
        
        # Verify configuration was successful
        self.assertTrue(result)
        self.assertTrue(self.configurator.is_configured)
        
        # Verify Serial was created with correct parameters
        self.mock_serial.assert_called_once_with(
            port="COM3",
            baudrate=9600,
            timeout=1.0
        )
        
        # Verify commands were sent
        self.assertEqual(self.mock_serial_instance.write.call_count, 2)
        
        # Verify specific commands were sent
        expected_calls = [
            ((bytes.fromhex("FF AA 69"),),),
            ((bytes.fromhex("FF AA 02 01"),),)
        ]
        actual_calls = self.mock_serial_instance.write.call_args_list
        for expected, actual in zip(expected_calls, actual_calls):
            self.assertEqual(expected, actual)
    
    def test_reset(self):
        """Test reset method"""
        # Reset sensor
        result = self.configurator.reset()
        
        # Verify reset was successful
        self.assertTrue(result)
        self.assertFalse(self.configurator.is_configured)
        
        # Verify Serial was created with correct parameters
        self.mock_serial.assert_called_once_with(
            port="COM3",
            baudrate=9600,
            timeout=1.0
        )
        
        # Verify reset command was sent
        self.mock_serial_instance.write.assert_called_once_with(b'\xFF\xAA\x00')
    
    def test_parse_init_sequence(self):
        """Test _parse_init_sequence method"""
        # Parse hex string
        result = self.configurator._parse_init_sequence("FF AA 69")
        
        # Verify result
        self.assertEqual(result, b'\xFF\xAA\x69')
        
        # Parse hex string without spaces
        result = self.configurator._parse_init_sequence("FFAA69")
        
        # Verify result
        self.assertEqual(result, b'\xFF\xAA\x69')
    
    def test_send_command(self):
        """Test _send_command method"""
        # Set up mock serial instance
        self.mock_serial_instance.is_open = True
        self.mock_serial_instance.write.return_value = 3
        
        # Send command
        command = b'\xFF\xAA\x69'
        result = self.configurator._send_command(command)
        
        # Verify command was sent successfully
        self.assertTrue(result)
        self.mock_serial_instance.write.assert_called_once_with(command)
        
        # Test error handling
        self.mock_serial_instance.write.side_effect = Exception("Test error")
        result = self.configurator._send_command(command)
        
        # Verify error was handled
        self.assertFalse(result)
        self.assertTrue(self.configurator.error_state)
        self.assertIn("Test error", self.configurator.error_message)


if __name__ == '__main__':
    unittest.main()
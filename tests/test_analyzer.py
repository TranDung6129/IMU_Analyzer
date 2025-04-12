# File: tests/test_analyzer.py
# Purpose: Unit tests for the Analyzer classes
# Target Lines: ≤150

import unittest
import sys
import os
import time
from unittest.mock import MagicMock, patch

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.plugins.analyzers.base_analyzer import BaseAnalyzer


# Simple analyzer implementation for testing
class SimpleAnalyzer(BaseAnalyzer):
    """Simple analyzer for testing"""
    
    def __init__(self, config=None):
        super().__init__(config)
        self.analysis_count = 0
    
    def analyze(self, data):
        """Analyze data"""
        super().analyze(data)
        self.analysis_count += 1
        return {
            "original": data,
            "analysis_result": "analyzed",
            "analysis_count": self.analysis_count
        }
    
    def reset(self):
        """Reset analyzer state"""
        self.analysis_count = 0
        return True
    
    def update_config(self, new_config):
        """Update analyzer configuration"""
        super().update_config(new_config)
        if "threshold" in new_config:
            self.threshold = new_config["threshold"]
        return True


class TestAnalyzer(unittest.TestCase):
    """Tests for the BaseAnalyzer class and implementations"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.config = {
            "threshold": 0.5,
            "window_size": 10
        }
        self.analyzer = SimpleAnalyzer(self.config)
    
    def test_initialization(self):
        """Test analyzer initialization"""
        # Verify analyzer is initialized properly
        self.assertTrue(self.analyzer.initialized)
        self.assertEqual(self.analyzer.config, self.config)
        self.assertEqual(self.analyzer.analyze_count, 0)
        self.assertEqual(self.analyzer.analyze_errors, 0)
        self.assertFalse(self.analyzer.error_state)
        self.assertIsNone(self.analyzer.error_message)
    
    def test_analyze(self):
        """Test analyze method"""
        # Prepare test data
        test_data = {
            "timestamp": time.time(),
            "values": [1, 2, 3, 4, 5]
        }
        
        # Analyze data
        result = self.analyzer.analyze(test_data)
        
        # Verify results
        self.assertEqual(result["original"], test_data)
        self.assertEqual(result["analysis_result"], "analyzed")
        self.assertEqual(result["analysis_count"], 1)
        
        # Verify counters are updated
        self.assertEqual(self.analyzer.analyze_count, 1)
        self.assertEqual(self.analyzer.analysis_count, 1)
    
    def test_error_handling(self):
        """Test error handling in analyzer"""
        # Create an analyzer with a buggy analyze method
        class BuggyAnalyzer(BaseAnalyzer):
            def analyze(self, data):
                super().analyze(data)
                raise ValueError("Test error")
            
            def reset(self):
                return True
            
            def update_config(self, new_config):
                super().update_config(new_config)
                return True
        
        buggy_analyzer = BuggyAnalyzer()
        
        # Try to analyze data
        with self.assertRaises(ValueError):
            buggy_analyzer.analyze({"test": "data"})
        
        # Set error manually
        buggy_analyzer.set_error("Manual error")
        
        # Verify error state
        self.assertTrue(buggy_analyzer.error_state)
        self.assertEqual(buggy_analyzer.error_message, "Manual error")
        self.assertEqual(buggy_analyzer.analyze_errors, 1)
        
        # Clear error
        buggy_analyzer.clear_error()
        
        # Verify error cleared
        self.assertFalse(buggy_analyzer.error_state)
        self.assertIsNone(buggy_analyzer.error_message)
    
    def test_reset(self):
        """Test reset method"""
        # Analyze some data first
        for i in range(5):
            self.analyzer.analyze({"index": i})
        
        # Verify counters are updated
        self.assertEqual(self.analyzer.analyze_count, 5)
        self.assertEqual(self.analyzer.analysis_count, 5)
        
        # Reset analyzer
        result = self.analyzer.reset()
        
        # Verify reset was successful
        self.assertTrue(result)
        self.assertEqual(self.analyzer.analysis_count, 0)
        
        # BaseAnalyzer counters are not reset
        self.assertEqual(self.analyzer.analyze_count, 5)
    
    def test_update_config(self):
        """Test update_config method"""
        # Verify initial config
        self.assertEqual(self.analyzer.config["threshold"], 0.5)
        
        # Update config
        new_config = {"threshold": 0.8, "new_param": "value"}
        result = self.analyzer.update_config(new_config)
        
        # Verify update was successful
        self.assertTrue(result)
        self.assertEqual(self.analyzer.config["threshold"], 0.8)
        self.assertEqual(self.analyzer.config["new_param"], "value")
        self.assertEqual(self.analyzer.threshold, 0.8)
    
    def test_get_status(self):
        """Test get_status method"""
        # Analyze some data first
        for i in range(3):
            self.analyzer.analyze({"index": i})
        
        # Set error
        self.analyzer.set_error("Test error")
        
        # Get status
        status = self.analyzer.get_status()
        
        # Verify status structure
        self.assertIn("initialized", status)
        self.assertIn("error_state", status)
        self.assertIn("error_message", status)
        self.assertIn("analyze_count", status)
        self.assertIn("analyze_errors", status)
        
        # Verify status values
        self.assertTrue(status["initialized"])
        self.assertTrue(status["error_state"])
        self.assertEqual(status["error_message"], "Test error")
        self.assertEqual(status["analyze_count"], 3)
        self.assertEqual(status["analyze_errors"], 1)


if __name__ == '__main__':
    unittest.main()
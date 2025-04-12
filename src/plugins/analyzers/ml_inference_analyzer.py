# File: src/plugins/analyzers/ml_inference_analyzer.py
# Purpose: Run machine learning inference on sensor data
# Target Lines: ≤150

"""
Methods to implement:
- __init__(self, config=None): Initialize with optional configuration
- analyze(self, data): Analyze data using the ML model
- reset(self): Reset the analyzer state
- update_config(self, new_config): Update analyzer configuration
- _load_model(self, model_path): Load ML model from file
"""

import logging
import numpy as np
import pickle
import os
from collections import deque
from src.plugins.analyzers.base_analyzer import BaseAnalyzer
from src.data.models import AnalysisResult


class MLInferenceAnalyzer(BaseAnalyzer):
    """
    Performs machine learning inference on sensor data.
    
    Supports loading pre-trained models from pickle files and running inference
    on sensor data. Can handle both classification and regression models.
    """
    
    def __init__(self, config=None):
        """
        Initialize the ML inference analyzer with optional configuration.
        
        Args:
            config (dict, optional): Configuration with the following keys:
                - model_path (str): Path to the ML model file (pickle format)
                - input_fields (list): List of fields to use as model input
                - batch_size (int): Number of samples to process at once (default: 1)
                - mode (str): "classification" or "regression" (default: "classification")
                - output_labels (list): List of class labels for classification (optional)
                - threshold (float): Confidence threshold for classification (default: 0.5)
        """
        super().__init__(config)
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Model and inference settings
        self.model = None
        self.model_path = None
        self.input_fields = []
        self.batch_size = 1
        self.mode = "classification"
        self.output_labels = []
        self.threshold = 0.5
        
        # Data buffer for batch processing
        self.data_buffer = deque(maxlen=100)
        
        # Update with provided configuration
        if config:
            self.update_config(config)
    
    def update_config(self, new_config):
        """
        Update the analyzer configuration.
        
        Args:
            new_config (dict): New configuration dictionary
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not isinstance(new_config, dict):
            self.set_error("Configuration must be a dictionary")
            return False
        
        # Check if model path changed and needs reloading
        model_changed = False
        if 'model_path' in new_config and new_config['model_path'] != self.model_path:
            self.model_path = new_config['model_path']
            model_changed = True
        
        # Update input fields
        if 'input_fields' in new_config and isinstance(new_config['input_fields'], list):
            self.input_fields = new_config['input_fields']
        elif not self.input_fields:
            # Default input fields if not provided
            self.input_fields = ['accel_x', 'accel_y', 'accel_z', 'gyro_x', 'gyro_y', 'gyro_z']
        
        # Update batch size
        if 'batch_size' in new_config:
            try:
                batch_size = int(new_config['batch_size'])
                if batch_size < 1:
                    self.logger.warning("Batch size must be at least 1, using 1")
                    self.batch_size = 1
                else:
                    self.batch_size = batch_size
            except (ValueError, TypeError):
                self.logger.warning("Invalid batch size, using default")
        
        # Update mode
        if 'mode' in new_config:
            mode = new_config['mode'].lower()
            if mode in ["classification", "regression"]:
                self.mode = mode
            else:
                self.logger.warning(f"Invalid mode: {mode}, using 'classification'")
                self.mode = "classification"
        
        # Update output labels
        if 'output_labels' in new_config and isinstance(new_config['output_labels'], list):
            self.output_labels = new_config['output_labels']
        
        # Update threshold
        if 'threshold' in new_config:
            try:
                threshold = float(new_config['threshold'])
                if threshold < 0 or threshold > 1:
                    self.logger.warning("Threshold must be between 0 and 1, using default")
                else:
                    self.threshold = threshold
            except (ValueError, TypeError):
                self.logger.warning("Invalid threshold, using default")
        
        # Load model if path is provided and changed
        if self.model_path and model_changed:
            try:
                self._load_model(self.model_path)
            except Exception as e:
                self.set_error(f"Failed to load model: {str(e)}")
                return False
        
        self.initialized = True
        self.clear_error()
        return True
    
    def _load_model(self, model_path):
        """
        Load the ML model from a file.
        
        Args:
            model_path (str): Path to the model file
            
        Raises:
            FileNotFoundError: If the model file doesn't exist
            Exception: If there's an error loading the model
        """
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model file not found: {model_path}")
        
        try:
            with open(model_path, 'rb') as f:
                self.model = pickle.load(f)
            self.logger.info(f"Loaded model from {model_path}")
        except Exception as e:
            self.logger.error(f"Error loading model: {str(e)}")
            raise
    
    def reset(self):
        """
        Reset the analyzer state.
        
        Returns:
            bool: True if successful, False otherwise
        """
        # Clear data buffer
        self.data_buffer.clear()
        
        self.clear_error()
        return True
    
    def analyze(self, data):
        """
        Analyze data using the ML model.
        
        Args:
            data (dict): Processed data with fields to analyze
            
        Returns:
            AnalysisResult: Analysis result with prediction information
            
        Raises:
            ValueError: If the data doesn't contain the required fields
            RuntimeError: If the model is not loaded
        """
        if not self.initialized:
            raise RuntimeError("Analyzer not initialized")
        
        if self.model is None:
            raise RuntimeError("Model not loaded")
        
        if not isinstance(data, dict):
            self.set_error("Data must be a dictionary")
            return None
        
        # Create base analysis result
        result = AnalysisResult()
        result.processed_data_id = data.get('id', '')
        result.sensor_id = data.get('sensor_id', '')
        
        # Add data to buffer
        self.data_buffer.append(data)
        
        # Skip if we don't have enough data for a batch
        if len(self.data_buffer) < self.batch_size:
            # Update counters but don't return real analysis yet
            super().analyze(data)
            
            # Return partial result indicating waiting for batch
            result.results['status'] = 'waiting_for_batch'
            result.results['batch_progress'] = f"{len(self.data_buffer)}/{self.batch_size}"
            return result
        
        try:
            # Extract features from the most recent batch
            batch_data = list(self.data_buffer)[-self.batch_size:]
            features = self._extract_features(batch_data)
            
            # Run inference
            if self.mode == "classification":
                prediction_result = self._run_classification(features)
            else:  # regression
                prediction_result = self._run_regression(features)
            
            # Update result with prediction
            result.prediction = prediction_result.get('prediction', '')
            result.confidence = prediction_result.get('confidence', 0.0)
            result.results = prediction_result
            
        except Exception as e:
            self.set_error(f"Error during inference: {str(e)}")
            # Return partial result with error
            result.results['error'] = str(e)
        
        # Add metadata about the analysis
        result.analysis_metadata = {
            'analyzer_type': 'ml_inference',
            'model_path': self.model_path,
            'mode': self.mode,
            'batch_size': self.batch_size,
            'input_fields': self.input_fields
        }
        
        # Update counters
        super().analyze(data)
        
        return result
    
    def _extract_features(self, batch_data):
        """
        Extract features from the batch data.
        
        Args:
            batch_data (list): List of data dictionaries
            
        Returns:
            numpy.ndarray: Features array
        """
        # Create feature matrix
        features = []
        
        for data_point in batch_data:
            # Extract features for this data point
            point_features = []
            for field in self.input_fields:
                if field in data_point:
                    try:
                        point_features.append(float(data_point[field]))
                    except (ValueError, TypeError):
                        # Use 0 for missing or invalid values
                        point_features.append(0.0)
                else:
                    # Use 0 for missing fields
                    point_features.append(0.0)
            
            features.append(point_features)
        
        return np.array(features)
    
    def _run_classification(self, features):
        """
        Run classification on the features.
        
        Args:
            features (numpy.ndarray): Features array
            
        Returns:
            dict: Classification results
        """
        try:
            # Get raw prediction probabilities
            if hasattr(self.model, 'predict_proba'):
                proba = self.model.predict_proba(features)
                # Get the highest probability class
                max_proba_idx = np.argmax(proba[-1])
                confidence = proba[-1][max_proba_idx]
                
                # Get class labels
                if hasattr(self.model, 'classes_'):
                    classes = self.model.classes_
                    prediction = str(classes[max_proba_idx])
                elif self.output_labels and max_proba_idx < len(self.output_labels):
                    prediction = self.output_labels[max_proba_idx]
                else:
                    prediction = str(max_proba_idx)
                
                return {
                    'prediction': prediction,
                    'confidence': float(confidence),
                    'probabilities': {str(i): float(p) for i, p in enumerate(proba[-1])},
                    'above_threshold': confidence >= self.threshold
                }
            else:
                # For models without probability support
                prediction = self.model.predict(features)[-1]
                
                # Convert to string for consistent output
                prediction = str(prediction)
                
                return {
                    'prediction': prediction,
                    'confidence': 1.0,  # No confidence available
                    'above_threshold': True
                }
        except Exception as e:
            self.logger.error(f"Classification error: {str(e)}")
            raise
    
    def _run_regression(self, features):
        """
        Run regression on the features.
        
        Args:
            features (numpy.ndarray): Features array
            
        Returns:
            dict: Regression results
        """
        try:
            # Get prediction
            prediction = float(self.model.predict(features)[-1])
            
            return {
                'prediction': str(prediction),
                'value': prediction,
                'confidence': 1.0  # No confidence for regression
            }
        except Exception as e:
            self.logger.error(f"Regression error: {str(e)}")
            raise


# How to extend and modify:
# 1. Add support for different model types: Modify _load_model() to support TensorFlow, PyTorch, etc.
# 2. Add feature preprocessing: Modify _extract_features() to normalize or scale features
# 3. Add ensemble methods: Modify analyze() to combine predictions from multiple models
# 4. Add model performance metrics: Track inference accuracy and performance over time
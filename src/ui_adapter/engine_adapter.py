# File: src/ui_adapter/engine_adapter.py
# Purpose: Adapter between UI and Engine to control pipelines
# Target Lines: ≤200

"""
Methods to implement:
- __init__(self): Initialize the adapter
- set_engine(self, engine): Set the engine instance
- start_pipeline(self, pipeline_id): Start a specific pipeline
- stop_pipeline(self, pipeline_id): Stop a specific pipeline
- get_pipeline_status(self, pipeline_id): Get status of a specific pipeline
- get_all_pipeline_status(self): Get status of all pipelines
- send_configuration(self, sensor_id, config): Send configuration to a sensor
"""

import logging


class EngineAdapter:
    """
    Adapter between UI and Engine to control pipelines.
    
    Provides methods for UI to control the engine without direct dependency.
    """
    
    def __init__(self):
        """
        Initialize the adapter.
        """
        self.engine = None
        self.logger = logging.getLogger("EngineAdapter")
    
    def set_engine(self, engine):
        """
        Đặt engine và thiết lập các kết nối cần thiết.
        
        Args:
            engine: Phiên bản của Engine
        """
        self.engine = engine
        
        # Nếu có main_window, thiết lập dashboard
        if hasattr(engine, 'main_window') and engine.main_window:
            engine.main_window.set_engine_adapter(self)
            engine.main_window.setup_dashboard()
        
        self.logger.info("Engine set in adapter")
    
    def start_pipeline(self, pipeline_id):
        """
        Start a specific pipeline.
        
        Args:
            pipeline_id (str): ID of the pipeline to start
            
        Returns:
            bool: True if started successfully, False otherwise
        """
        if not self.engine:
            self.logger.error("Engine not set in adapter")
            return False
            
        try:
            return self.engine.start_pipeline(pipeline_id)
        except Exception as e:
            self.logger.error(f"Error starting pipeline {pipeline_id}: {str(e)}")
            return False
    
    def stop_pipeline(self, pipeline_id):
        """
        Stop a specific pipeline.
        
        Args:
            pipeline_id (str): ID of the pipeline to stop
            
        Returns:
            bool: True if stopped successfully, False otherwise
        """
        if not self.engine:
            self.logger.error("Engine not set in adapter")
            return False
            
        try:
            return self.engine.stop_pipeline(pipeline_id)
        except Exception as e:
            self.logger.error(f"Error stopping pipeline {pipeline_id}: {str(e)}")
            return False
    
    def get_pipeline_status(self, pipeline_id):
        """
        Get status of a specific pipeline.
        
        Args:
            pipeline_id (str): ID of the pipeline
            
        Returns:
            dict: Status information or None if not found
        """
        if not self.engine:
            self.logger.error("Engine not set in adapter")
            return None
            
        try:
            pipeline = self.engine.get_pipeline(pipeline_id)
            if pipeline:
                return pipeline.get_status()
            else:
                self.logger.warning(f"Pipeline {pipeline_id} not found")
                return None
        except Exception as e:
            self.logger.error(f"Error getting pipeline status for {pipeline_id}: {str(e)}")
            return None
    
    def get_all_pipeline_status(self):
        """
        Get status of all pipelines.
        
        Returns:
            dict: Dictionary of pipeline IDs and their status
        """
        if not self.engine:
            self.logger.error("Engine not set in adapter")
            return {}
            
        try:
            result = {}
            for pipeline_id, pipeline in self.engine.pipelines.items():
                result[pipeline_id] = pipeline.get_status()
            return result
        except Exception as e:
            self.logger.error(f"Error getting all pipeline status: {str(e)}")
            return {}
    
    def send_configuration(self, sensor_id, config):
        """
        Send configuration to a sensor.
        
        Args:
            sensor_id (str): ID of the sensor/pipeline
            config (dict): Configuration to send
            
        Returns:
            bool: True if configuration sent successfully, False otherwise
            
        Raises:
            ValueError: If configuration is invalid
            RuntimeError: If engine not set or pipeline not found
        """
        if not self.engine:
            self.logger.error("Engine not set in adapter")
            raise RuntimeError("Engine not set in adapter")
        
        # Validate configuration
        if not self._validate_config(config):
            error_msg = f"Invalid configuration format for sensor {sensor_id}"
            self.logger.error(error_msg)
            raise ValueError(error_msg)
        
        try:
            # Find the pipeline for this sensor
            pipeline = self.engine.get_pipeline(sensor_id)
            if not pipeline:
                error_msg = f"Pipeline not found for sensor {sensor_id}"
                self.logger.error(error_msg)
                raise RuntimeError(error_msg)
            
            # Check if engine has configure_sensor method
            if hasattr(self.engine, 'configure_sensor'):
                result = self.engine.configure_sensor(sensor_id, config)
                self.logger.info(f"Configuration sent to sensor {sensor_id} via engine")
                return result
                
            # Check if pipeline has a configurator
            pipeline_status = pipeline.get_status()
            if (hasattr(pipeline, 'configurator') and pipeline.configurator is not None):
                result = pipeline.configurator.configure(config)
                self.logger.info(f"Configuration sent to sensor {sensor_id} via pipeline configurator")
                return result
            else:
                error_msg = f"No configurator available for sensor {sensor_id}"
                self.logger.error(error_msg)
                raise RuntimeError(error_msg)
                
        except Exception as e:
            self.logger.error(f"Error sending configuration to sensor {sensor_id}: {str(e)}")
            raise RuntimeError(f"Failed to send configuration: {str(e)}")
    
    def _validate_config(self, config):
        """
        Validate configuration structure.
        
        Args:
            config (dict): Configuration to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        # Must be a dictionary
        if not isinstance(config, dict):
            return False
        
        # Check for init_sequence if present
        if 'init_sequence' in config:
            init_sequence = config['init_sequence']
            # Must be a list
            if not isinstance(init_sequence, list):
                return False
            
            # Each element must be a string
            for cmd in init_sequence:
                if not isinstance(cmd, str):
                    return False
        
        return True


# How to modify functionality:
# 1. Add more engine control methods: Add methods similar to start_pipeline() and stop_pipeline()
# 2. Add monitoring capabilities: Add methods to retrieve engine performance metrics
# 3. Add configuration methods: Add methods to modify engine or pipeline configuration
# 4. Extend _validate_config: Add validation for more complex configuration structures
# 5. Add bulk configuration: Add method to configure multiple sensors at once
# 6. Add configuration profiles: Add methods to save and load configuration profiles
# File: src/system/sensor_registry.py
# Purpose: Registry for sensors and pipeline status
# Target Lines: ≤200

"""
Methods to implement:
- __init__(self): Initialize the registry
- register_sensor(self, sensor_config): Register a sensor with configuration
- deregister_sensor(self, sensor_id): Deregister a sensor
- get_sensor_config(self, sensor_id): Get configuration of a sensor
- get_all_sensors(self): Get all registered sensors
- update_sensor_status(self, sensor_id, status): Update the status of a sensor
- get_sensor_status(self, sensor_id): Get the status of a sensor
- update_pipeline_status(self, pipeline_id, status): Update the status of a pipeline
- get_pipeline_status(self, pipeline_id): Get the status of a pipeline
"""

import logging
import threading
import copy
import time


class SensorRegistry:
    """
    Registry for sensors and pipeline status.
    
    Maintains a registry of all sensors in the system,
    their configurations, and current status.
    Also tracks pipeline status for each sensor.
    """
    
    def __init__(self):
        """
        Initialize the sensor registry.
        """
        self.logger = logging.getLogger("SensorRegistry")
        
        # Dictionary of sensors by ID
        self.sensors = {}
        
        # Dictionary of sensor status by ID
        self.sensor_status = {}
        
        # Dictionary of pipeline status by ID
        self.pipeline_status = {}
        
        # Lock for thread safety
        self.lock = threading.RLock()
    
    def register_sensor(self, sensor_config):
        """
        Register a sensor with configuration.
        
        Args:
            sensor_config (dict): Sensor configuration
                Must contain 'id' key.
                
        Returns:
            bool: True if registered successfully, False otherwise
        """
        if not sensor_config or "id" not in sensor_config:
            self.logger.error("Invalid sensor configuration: missing 'id'")
            return False
            
        sensor_id = sensor_config["id"]
        
        with self.lock:
            # Check if sensor already exists
            if sensor_id in self.sensors:
                self.logger.warning(f"Sensor {sensor_id} already registered, updating configuration")
            
            # Store sensor configuration
            self.sensors[sensor_id] = copy.deepcopy(sensor_config)
            
            # Initialize status if not exists
            if sensor_id not in self.sensor_status:
                self.sensor_status[sensor_id] = {
                    "state": "registered",
                    "connected": False,
                    "last_update": time.time(),
                    "error": None
                }
        
        self.logger.info(f"Sensor {sensor_id} registered")
        return True
    
    def deregister_sensor(self, sensor_id):
        """
        Deregister a sensor.
        
        Args:
            sensor_id (str): ID of the sensor to deregister
            
        Returns:
            bool: True if deregistered successfully, False otherwise
        """
        with self.lock:
            if sensor_id not in self.sensors:
                self.logger.warning(f"Sensor {sensor_id} not found in registry")
                return False
                
            # Remove sensor
            self.sensors.pop(sensor_id)
            
            # Remove status
            if sensor_id in self.sensor_status:
                self.sensor_status.pop(sensor_id)
            
            # Remove associated pipeline status
            for pipeline_id in list(self.pipeline_status.keys()):
                if pipeline_id.startswith(f"{sensor_id}_"):
                    self.pipeline_status.pop(pipeline_id)
        
        self.logger.info(f"Sensor {sensor_id} deregistered")
        return True
    
    def get_sensor_config(self, sensor_id):
        """
        Get configuration of a sensor.
        
        Args:
            sensor_id (str): ID of the sensor
            
        Returns:
            dict: Sensor configuration or None if not found
        """
        with self.lock:
            if sensor_id not in self.sensors:
                return None
                
            return copy.deepcopy(self.sensors[sensor_id])
    
    def get_all_sensors(self):
        """
        Get all registered sensors.
        
        Returns:
            dict: Dictionary of sensor configurations by ID
        """
        with self.lock:
            return copy.deepcopy(self.sensors)
    
    def update_sensor_status(self, sensor_id, status):
        """
        Update the status of a sensor.
        
        Args:
            sensor_id (str): ID of the sensor
            status (dict): Status information
                May contain 'state', 'connected', 'error', etc.
                
        Returns:
            bool: True if updated successfully, False otherwise
        """
        with self.lock:
            if sensor_id not in self.sensors:
                self.logger.warning(f"Sensor {sensor_id} not found in registry")
                return False
                
            # Create status entry if not exists
            if sensor_id not in self.sensor_status:
                self.sensor_status[sensor_id] = {
                    "state": "unknown",
                    "connected": False,
                    "last_update": time.time(),
                    "error": None
                }
            
            # Update status
            current_status = self.sensor_status[sensor_id]
            
            for key, value in status.items():
                current_status[key] = value
                
            # Update timestamp
            current_status["last_update"] = time.time()
        
        return True
    
    def get_sensor_status(self, sensor_id):
        """
        Get the status of a sensor.
        
        Args:
            sensor_id (str): ID of the sensor
            
        Returns:
            dict: Sensor status or None if not found
        """
        with self.lock:
            if sensor_id not in self.sensor_status:
                return None
                
            return copy.deepcopy(self.sensor_status[sensor_id])
    
    def update_pipeline_status(self, pipeline_id, status):
        """
        Update the status of a pipeline.
        
        Args:
            pipeline_id (str): ID of the pipeline
            status (dict): Status information
                
        Returns:
            bool: True if updated successfully, False otherwise
        """
        with self.lock:
            # Store pipeline status
            if pipeline_id in self.pipeline_status:
                current_status = self.pipeline_status[pipeline_id]
                
                # Update existing status
                for key, value in status.items():
                    current_status[key] = value
                    
                # Update timestamp
                current_status["last_update"] = time.time()
            else:
                # Create new status entry
                status["last_update"] = time.time()
                self.pipeline_status[pipeline_id] = status
            
            # Extract sensor ID from pipeline ID if possible
            # Assuming pipeline IDs are in format "{sensor_id}_{pipeline_type}"
            parts = pipeline_id.split("_", 1)
            if len(parts) > 1:
                sensor_id = parts[0]
                
                # Update sensor status if sensor exists
                if sensor_id in self.sensors:
                    self.update_sensor_status(sensor_id, {
                        "pipeline_status": {pipeline_id: status.get("state", "unknown")}
                    })
        
        return True
    
    def get_pipeline_status(self, pipeline_id):
        """
        Get the status of a pipeline.
        
        Args:
            pipeline_id (str): ID of the pipeline
            
        Returns:
            dict: Pipeline status or None if not found
        """
        with self.lock:
            if pipeline_id not in self.pipeline_status:
                return None
                
            return copy.deepcopy(self.pipeline_status[pipeline_id])
    
    def get_all_pipeline_status(self):
        """
        Get status of all pipelines.
        
        Returns:
            dict: Dictionary of pipeline status by ID
        """
        with self.lock:
            return copy.deepcopy(self.pipeline_status)
    
    def get_sensors_with_status(self):
        """
        Get all sensors with their status.
        
        Returns:
            dict: Dictionary of sensors with status
        """
        result = {}
        
        with self.lock:
            for sensor_id, config in self.sensors.items():
                result[sensor_id] = {
                    "config": copy.deepcopy(config),
                    "status": copy.deepcopy(self.sensor_status.get(sensor_id, {}))
                }
                
                # Add pipeline status for this sensor
                pipeline_status = {}
                for pipeline_id, status in self.pipeline_status.items():
                    if pipeline_id.startswith(f"{sensor_id}_"):
                        pipeline_status[pipeline_id] = copy.deepcopy(status)
                        
                result[sensor_id]["pipelines"] = pipeline_status
        
        return result

# How to modify functionality:
# 1. Add sensor grouping: Add methods to group sensors by type or location
# 2. Add validation: Add validation for sensor configuration
# 3. Add status history: Store history of status changes for analysis
# 4. Add sensor discovery: Add methods to discover sensors automatically
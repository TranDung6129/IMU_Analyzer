# File: src/ui_adapter/data_bridge.py
# Purpose: Bridge for data flow between backend and UI
# Target Lines: ≤200

"""
Methods to implement:
- __init__(self): Initialize the data bridge
- connect_to_ui(self, ui): Connect to main UI
- register_pipeline(self, pipeline_id, pipeline): Register a pipeline for monitoring
- deregister_pipeline(self, pipeline_id): Deregister a pipeline
- process_data(self, pipeline_id, data_type, data): Process data from pipeline to UI
- update_ui(self): Update UI with latest data
"""

import logging
import threading
import time


class DataBridge:
    """
    Bridge for data flow between backend and UI.
    
    Handles data flow from pipelines to UI components,
    and provides methods for UI to query latest data.
    """
    
    def __init__(self):
        """
        Initialize the data bridge.
        """
        self.logger = logging.getLogger("DataBridge")
        self.ui = None
        self.pipelines = {}
        self.visualizers = {}
        self.latest_data = {}
        self.data_lock = threading.RLock()
        self.update_thread = None
        self.stop_event = threading.Event()
        self.update_interval = 0.1  # seconds
    
    def connect_to_ui(self, ui):
        """
        Connect to main UI.
        
        Args:
            ui: Main UI instance
        """
        self.ui = ui
        self.logger.info("Connected to UI")
        
        # Start update thread
        self.stop_event.clear()
        self.update_thread = threading.Thread(target=self._update_loop, daemon=True)
        self.update_thread.start()
        self.logger.debug("Started UI update thread")
    
    def disconnect_from_ui(self):
        """
        Disconnect from UI and stop update thread.
        """
        if self.update_thread and self.update_thread.is_alive():
            self.stop_event.set()
            self.update_thread.join(timeout=1.0)
            self.logger.debug("Stopped UI update thread")
        
        self.ui = None
        self.logger.info("Disconnected from UI")
    
    def register_pipeline(self, pipeline_id, pipeline):
        """
        Register a pipeline for monitoring.
        
        Args:
            pipeline_id (str): ID of the pipeline
            pipeline: Pipeline instance
        """
        self.pipelines[pipeline_id] = pipeline
        
        # Create entry for this pipeline in latest_data
        with self.data_lock:
            self.latest_data[pipeline_id] = {
                "processed": None,
                "analyzed": None,
                "visualized": None,
                "status": None
            }
            
        self.logger.info(f"Registered pipeline: {pipeline_id}")
    
    def deregister_pipeline(self, pipeline_id):
        """
        Deregister a pipeline.
        
        Args:
            pipeline_id (str): ID of the pipeline to deregister
        """
        if pipeline_id in self.pipelines:
            del self.pipelines[pipeline_id]
            
            # Remove data for this pipeline
            with self.data_lock:
                if pipeline_id in self.latest_data:
                    del self.latest_data[pipeline_id]
                    
            self.logger.info(f"Deregistered pipeline: {pipeline_id}")
    
    def register_visualizer(self, pipeline_id, visualizer_id, visualizer):
        """
        Register a visualizer for a pipeline.
        
        Args:
            pipeline_id (str): ID of the pipeline
            visualizer_id (str): ID of the visualizer
            visualizer: Visualizer widget instance
        """
        if pipeline_id not in self.visualizers:
            self.visualizers[pipeline_id] = {}
            
        self.visualizers[pipeline_id][visualizer_id] = visualizer
        self.logger.debug(f"Registered visualizer {visualizer_id} for pipeline {pipeline_id}")
    
    def deregister_visualizer(self, pipeline_id, visualizer_id):
        """
        Deregister a visualizer.
        
        Args:
            pipeline_id (str): ID of the pipeline
            visualizer_id (str): ID of the visualizer to deregister
        """
        if pipeline_id in self.visualizers and visualizer_id in self.visualizers[pipeline_id]:
            del self.visualizers[pipeline_id][visualizer_id]
            self.logger.debug(f"Deregistered visualizer {visualizer_id} for pipeline {pipeline_id}")
    
    def process_data(self, pipeline_id, data_type, data):
        """
        Process data from pipeline to UI.
        
        Args:
            pipeline_id (str): ID of the pipeline
            data_type (str): Type of data (processed, analyzed, visualized)
            data: Data to process
        """
        if pipeline_id not in self.latest_data:
            self.logger.warning(f"No data entry for pipeline {pipeline_id}")
            return
            
        with self.data_lock:
            self.latest_data[pipeline_id][data_type] = data
    
    def update_pipeline_status(self, pipeline_id, status):
        """
        Update pipeline status.
        
        Args:
            pipeline_id (str): ID of the pipeline
            status (dict): Status information
        """
        if pipeline_id not in self.latest_data:
            self.logger.warning(f"No data entry for pipeline {pipeline_id}")
            return
            
        with self.data_lock:
            self.latest_data[pipeline_id]["status"] = status
    
    def _update_loop(self):
        """
        Update UI in a loop.
        
        This method runs in a separate thread and periodically
        updates the UI with the latest data.
        """
        while not self.stop_event.is_set():
            try:
                if self.ui:
                    self.update_ui()
            except Exception as e:
                self.logger.error(f"Error in update loop: {str(e)}")
                
            # Sleep for a short interval
            time.sleep(self.update_interval)
    
    def update_ui(self):
        """
        Update UI with latest data.
        
        This method is called periodically by the update thread.
        """
        if not self.ui:
            return
            
        try:
            # Make a copy of the latest data to avoid holding the lock
            with self.data_lock:
                data_copy = {k: v.copy() for k, v in self.latest_data.items()}
                
            # Update UI components
            # Note: Actual implementation depends on UI structure
            if hasattr(self.ui, "update_dashboard"):
                self.ui.update_dashboard(data_copy)
                
            # Update visualizers
            for pipeline_id, visualizers in self.visualizers.items():
                if pipeline_id in data_copy:
                    pipeline_data = data_copy[pipeline_id]
                    for visualizer_id, visualizer in visualizers.items():
                        if hasattr(visualizer, "update_data"):
                            # Determine the data type to use (processed, analyzed, or visualized)
                            data = None
                            for data_type in ["visualized", "analyzed", "processed"]:
                                if pipeline_data[data_type] is not None:
                                    data = pipeline_data[data_type]
                                    break
                                    
                            if data is not None:
                                visualizer.update_data(data)
        except Exception as e:
            self.logger.error(f"Error updating UI: {str(e)}")

# How to modify functionality:
# 1. Add data filtering: Add methods to filter or transform data before sending to UI
# 2. Add data caching: Modify to store historical data for trends or replay
# 3. Add more UI update methods: Add methods for different UI components
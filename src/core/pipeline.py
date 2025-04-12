# File: src/core/pipeline.py
# Purpose: Manage data processing pipeline for each sensor
# Target Lines: ≤400

"""
Methods to implement:
- __init__(self, config, plugin_manager): Initialize pipeline with config and plugin manager
- setup(self): Initialize components (reader, decoder, processor, analyzer, visualizer, writer)
- run(self): Run pipeline on separate threads
- _read_loop(self), _decode_loop(self), _process_loop(self), _analyze_loop(self), _visualize_loop(self), _write_loop(self): Processing loops for each step
- stop(self): Stop pipeline
"""

import threading
import queue
import logging
import time
from datetime import datetime


class PipelineExecutor:
    """
    Executes a data processing pipeline for a sensor.
    
    The pipeline consists of these stages:
    1. Reading raw data
    2. Decoding raw data into structured format
    3. Processing data (filtering, etc.)
    4. Analyzing data (anomaly detection, etc.)
    5. Visualizing data
    6. Writing data to storage
    
    Each stage runs in its own thread and communicates via queues.
    """
    
    def __init__(self, config, plugin_manager):
        """
        Initialize the pipeline with configuration.
        
        Args:
            config (dict): Pipeline configuration
            plugin_manager: Plugin manager instance for creating plugins
        """
        self.config = config
        self.plugin_manager = plugin_manager
        self.id = config.get("id", "unknown")
        self.logger = logging.getLogger(f"Pipeline-{self.id}")
        
        # Initialize components
        self.reader = None
        self.decoder = None
        self.processor = None
        self.analyzer = None
        self.visualizer = None
        self.writer = None
        self.exporter = None
        
        # Initialize queues for inter-thread communication
        self.read_queue = queue.Queue(maxsize=100)  # Raw data from reader
        self.decode_queue = queue.Queue(maxsize=100)  # Decoded data
        self.process_queue = queue.Queue(maxsize=100)  # Processed data
        self.analyze_queue = queue.Queue(maxsize=100)  # Analyzed data
        self.visualize_queue = queue.Queue(maxsize=100)  # Data for visualization
        self.write_queue = queue.Queue(maxsize=100)  # Data for writing
        
        # Thread management
        self.threads = {}
        self.stop_event = threading.Event()
        self.running = False
        
        # Performance metrics
        self.metrics = {
            "read_count": 0,
            "decode_count": 0,
            "process_count": 0,
            "analyze_count": 0,
            "visualize_count": 0,
            "write_count": 0,
            "start_time": None,
            "throughput": 0.0
        }
    
    def setup(self):
        """
        Initialize all components of the pipeline.
        
        Returns:
            bool: True if setup was successful, False otherwise
        """
        self.logger.info(f"Setting up pipeline: {self.id}")
        
        try:
            # Setup Reader
            if "reader" in self.config and self.config["reader"]:
                reader_config = self.config["reader"]
                reader_type = reader_config.get("type")
                if reader_type:
                    self.reader = self.plugin_manager.create_plugin_instance(
                        "readers", reader_type, reader_config.get("config", {})
                    )
                    self.logger.info(f"Created reader: {reader_type}")
            
            # Setup Writer
            if "writer" in self.config and self.config["writer"]:
                writer_config = self.config["writer"]
                writer_type = writer_config.get("type")
                if writer_type:
                    self.writer = self.plugin_manager.create_plugin_instance(
                        "writers", writer_type, writer_config.get("config", {})
                    )
                    self.logger.info(f"Created writer: {writer_type}")
            
            # Setup Decoder
            if "decoder" in self.config and self.config["decoder"]:
                decoder_config = self.config["decoder"]
                decoder_type = decoder_config.get("type")
                if decoder_type:
                    self.decoder = self.plugin_manager.create_plugin_instance(
                        "decoders", decoder_type, decoder_config.get("config", {})
                    )
                    self.logger.info(f"Created decoder: {decoder_type}")
            
            # Setup Processor
            if "processor" in self.config and self.config["processor"]:
                processor_config = self.config["processor"]
                processor_type = processor_config.get("type")
                if processor_type:
                    self.processor = self.plugin_manager.create_plugin_instance(
                        "processors", processor_type, processor_config.get("config", {})
                    )
                    self.logger.info(f"Created processor: {processor_type}")
            
            # Setup Analyzer
            if "analyzer" in self.config and self.config["analyzer"]:
                analyzer_config = self.config["analyzer"]
                analyzer_type = analyzer_config.get("type")
                if analyzer_type:
                    self.analyzer = self.plugin_manager.create_plugin_instance(
                        "analyzers", analyzer_type, analyzer_config.get("config", {})
                    )
                    self.logger.info(f"Created analyzer: {analyzer_type}")
            
            # Setup Visualizer
            if "visualizer" in self.config and self.config["visualizer"]:
                visualizer_config = self.config["visualizer"]
                visualizer_type = visualizer_config.get("type")
                if visualizer_type:
                    self.visualizer = self.plugin_manager.create_plugin_instance(
                        "visualizers", visualizer_type, visualizer_config.get("config", {})
                    )
                    self.logger.info(f"Created visualizer: {visualizer_type}")
            
            # Setup Exporter
            if "exporter" in self.config and self.config["exporter"]:
                exporter_config = self.config["exporter"]
                exporter_type = exporter_config.get("type")
                if exporter_type:
                    self.exporter = self.plugin_manager.create_plugin_instance(
                        "exporters", exporter_type, exporter_config.get("config", {})
                    )
                    self.logger.info(f"Created exporter: {exporter_type}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error setting up pipeline: {str(e)}")
            return False
    
    def run(self):
        """
        Run the pipeline on separate threads.
        
        Returns:
            bool: True if started successfully, False otherwise
        """
        if self.running:
            self.logger.warning(f"Pipeline {self.id} is already running")
            return False
        
        self.logger.info(f"Starting pipeline: {self.id}")
        
        try:
            # Reset stop event
            self.stop_event.clear()
            
            # Open reader and writer
            if self.reader:
                self.reader.open()
            if self.writer:
                self.writer.open()
            
            # Start threads
            self.threads = {}
            
            if self.reader:
                self.threads["reader"] = threading.Thread(
                    target=self._read_loop,
                    name=f"Pipeline-{self.id}-Reader"
                )
                self.threads["reader"].daemon = True
                self.threads["reader"].start()
            
            if self.decoder:
                self.threads["decoder"] = threading.Thread(
                    target=self._decode_loop,
                    name=f"Pipeline-{self.id}-Decoder"
                )
                self.threads["decoder"].daemon = True
                self.threads["decoder"].start()
            
            if self.processor:
                self.threads["processor"] = threading.Thread(
                    target=self._process_loop,
                    name=f"Pipeline-{self.id}-Processor"
                )
                self.threads["processor"].daemon = True
                self.threads["processor"].start()
            
            if self.analyzer:
                self.threads["analyzer"] = threading.Thread(
                    target=self._analyze_loop,
                    name=f"Pipeline-{self.id}-Analyzer"
                )
                self.threads["analyzer"].daemon = True
                self.threads["analyzer"].start()
            
            if self.visualizer:
                self.threads["visualizer"] = threading.Thread(
                    target=self._visualize_loop,
                    name=f"Pipeline-{self.id}-Visualizer"
                )
                self.threads["visualizer"].daemon = True
                self.threads["visualizer"].start()
            
            if self.writer:
                self.threads["writer"] = threading.Thread(
                    target=self._write_loop,
                    name=f"Pipeline-{self.id}-Writer"
                )
                self.threads["writer"].daemon = True
                self.threads["writer"].start()
            
            # Update state
            self.running = True
            self.metrics["start_time"] = time.time()
            
            self.logger.info(f"Pipeline {self.id} started successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error starting pipeline: {str(e)}")
            self.stop()
            return False
    
    def stop(self):
        """
        Stop the pipeline and clean up resources.
        
        Returns:
            bool: True if stopped successfully, False otherwise
        """
        if not self.running:
            self.logger.warning(f"Pipeline {self.id} is not running")
            return False
        
        self.logger.info(f"Stopping pipeline: {self.id}")
        
        try:
            # Signal threads to stop
            self.stop_event.set()
            
            # Wait for threads to finish
            for thread_name, thread in self.threads.items():
                thread_timeout = 2.0  # seconds
                thread.join(thread_timeout)
                if thread.is_alive():
                    self.logger.warning(f"Thread {thread_name} did not finish within {thread_timeout} seconds")
            
            # Close reader and writer
            if self.reader:
                self.reader.close()
            if self.writer:
                self.writer.close()
            
            # Cleanup components
            if self.decoder:
                self.decoder.destroy()
            if self.processor:
                self.processor.destroy()
            if self.visualizer:
                self.visualizer.destroy()
            if self.exporter:
                self.exporter.destroy()
            
            # Update state
            self.running = False
            
            self.logger.info(f"Pipeline {self.id} stopped successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error stopping pipeline: {str(e)}")
            self.running = False
            return False
    
    def _read_loop(self):
        """
        Thread function for reading data from the sensor.
        
        Reads data from the reader and puts it in the read queue.
        """
        self.logger.info(f"Reader thread started for pipeline: {self.id}")
        
        while not self.stop_event.is_set():
            try:
                # Read data from reader
                data = self.reader.read()
                
                if data:
                    # Add timestamp if not present
                    if isinstance(data, dict) and "timestamp" not in data:
                        data["timestamp"] = datetime.now().isoformat()
                    
                    # Put data in queue
                    self.read_queue.put(data, block=True, timeout=1.0)
                    self.metrics["read_count"] += 1
                
                # Small sleep to prevent CPU hogging
                time.sleep(0.001)
                
            except queue.Full:
                self.logger.warning("Read queue full, discarding data")
            except Exception as e:
                self.logger.error(f"Error in reader thread: {str(e)}")
                # Allow some recovery time
                time.sleep(0.1)
        
        self.logger.info(f"Reader thread stopped for pipeline: {self.id}")
    
    def _decode_loop(self):
        """
        Thread function for decoding raw data.
        
        Gets raw data from the read queue, decodes it,
        and puts it in the decode queue.
        """
        self.logger.info(f"Decoder thread started for pipeline: {self.id}")
        
        while not self.stop_event.is_set():
            try:
                # Get data from the queue
                data = self.read_queue.get(block=True, timeout=1.0)
                
                # Decode data
                decoded_data = self.decoder.decode(data)
                
                if decoded_data:
                    # Put decoded data in the next queue
                    self.decode_queue.put(decoded_data, block=True, timeout=1.0)
                    self.metrics["decode_count"] += 1
                
                # Mark task as done
                self.read_queue.task_done()
                
            except queue.Empty:
                # No data available, just continue
                pass
            except queue.Full:
                self.logger.warning("Decode queue full, discarding data")
            except Exception as e:
                self.logger.error(f"Error in decoder thread: {str(e)}")
                # Allow some recovery time
                time.sleep(0.1)
        
        self.logger.info(f"Decoder thread stopped for pipeline: {self.id}")
    
    def _process_loop(self):
        """
        Thread function for processing decoded data.
        
        Gets decoded data from the decode queue, processes it,
        and puts it in the process queue.
        """
        self.logger.info(f"Processor thread started for pipeline: {self.id}")
        
        while not self.stop_event.is_set():
            try:
                # Get data from the queue
                data = self.decode_queue.get(block=True, timeout=1.0)
                
                # Process data
                processed_data = self.processor.process(data)
                
                if processed_data:
                    # Send data to both analyze and visualize queues
                    self.process_queue.put(processed_data, block=True, timeout=1.0)
                    self.metrics["process_count"] += 1
                
                # Mark task as done
                self.decode_queue.task_done()
                
            except queue.Empty:
                # No data available, just continue
                pass
            except queue.Full:
                self.logger.warning("Process queue full, discarding data")
            except Exception as e:
                self.logger.error(f"Error in processor thread: {str(e)}")
                # Allow some recovery time
                time.sleep(0.1)
        
        self.logger.info(f"Processor thread stopped for pipeline: {self.id}")
    
    def _analyze_loop(self):
        """
        Thread function for analyzing processed data.
        
        Gets processed data from the process queue, analyzes it,
        and puts it in the analyze queue.
        """
        if not self.analyzer:
            return
            
        self.logger.info(f"Analyzer thread started for pipeline: {self.id}")
        
        while not self.stop_event.is_set():
            try:
                # Get data from the queue
                data = self.process_queue.get(block=True, timeout=1.0)
                
                # Analyze data
                analysis_result = self.analyzer.analyze(data)
                
                if analysis_result:
                    # Put analysis result in the next queue
                    self.analyze_queue.put(analysis_result, block=True, timeout=1.0)
                    self.metrics["analyze_count"] += 1
                
                # Mark task as done
                self.process_queue.task_done()
                
            except queue.Empty:
                # No data available, just continue
                pass
            except queue.Full:
                self.logger.warning("Analyze queue full, discarding data")
            except Exception as e:
                self.logger.error(f"Error in analyzer thread: {str(e)}")
                # Allow some recovery time
                time.sleep(0.1)
        
        self.logger.info(f"Analyzer thread stopped for pipeline: {self.id}")
    
    def _visualize_loop(self):
        """
        Thread function for visualizing data.
        
        Gets processed or analyzed data and sends it to the visualizer.
        """
        if not self.visualizer:
            return
            
        self.logger.info(f"Visualizer thread started for pipeline: {self.id}")
        
        while not self.stop_event.is_set():
            try:
                # Get data from the appropriate queue
                if not self.analyze_queue.empty() and self.analyzer:
                    # If we have analyzed data, use that
                    data = self.analyze_queue.get(block=True, timeout=1.0)
                    using_analyze_queue = True
                elif not self.process_queue.empty():
                    # Otherwise use processed data
                    data = self.process_queue.get(block=True, timeout=1.0)
                    using_analyze_queue = False
                else:
                    # No data available, wait a bit
                    time.sleep(0.01)
                    continue
                
                # Send data to visualizer
                self.visualizer.visualize(data)
                self.metrics["visualize_count"] += 1
                
                # Send data to write queue if not already sent
                self.write_queue.put(data, block=True, timeout=1.0)
                
                # Mark task as done in the appropriate queue
                if using_analyze_queue:
                    self.analyze_queue.task_done()
                else:
                    self.process_queue.task_done()
                
            except queue.Empty:
                # No data available, just continue
                pass
            except queue.Full:
                self.logger.warning("Write queue full, discarding data")
            except Exception as e:
                self.logger.error(f"Error in visualizer thread: {str(e)}")
                # Allow some recovery time
                time.sleep(0.1)
        
        self.logger.info(f"Visualizer thread stopped for pipeline: {self.id}")
    
    def _write_loop(self):
        """
        Thread function for writing data.
        
        Gets data from the write queue and sends it to the writer.
        """
        if not self.writer:
            return
            
        self.logger.info(f"Writer thread started for pipeline: {self.id}")
        
        while not self.stop_event.is_set():
            try:
                # Get data from the queue
                data = self.write_queue.get(block=True, timeout=1.0)
                
                # Write data
                self.writer.write(data)
                self.metrics["write_count"] += 1
                
                # Mark task as done
                self.write_queue.task_done()
                
                # Calculate throughput
                if self.metrics["start_time"]:
                    elapsed_time = time.time() - self.metrics["start_time"]
                    if elapsed_time > 0:
                        self.metrics["throughput"] = self.metrics["write_count"] / elapsed_time
                
            except queue.Empty:
                # No data available, just continue
                pass
            except Exception as e:
                self.logger.error(f"Error in writer thread: {str(e)}")
                # Allow some recovery time
                time.sleep(0.1)
        
        self.logger.info(f"Writer thread stopped for pipeline: {self.id}")
    
    def get_metrics(self):
        """
        Get the current metrics for the pipeline.
        
        Returns:
            dict: Dictionary of metrics
        """
        return self.metrics.copy()
    
    def get_status(self):
        """
        Get the current status of the pipeline.
        
        Returns:
            dict: Status information
        """
        component_statuses = {}
        
        # Get status of each component
        if self.reader:
            component_statuses["reader"] = self.reader.get_status()
        if self.writer:
            component_statuses["writer"] = self.writer.get_status()
        if self.decoder:
            component_statuses["decoder"] = self.decoder.get_status()
        if self.processor:
            component_statuses["processor"] = self.processor.get_status()
        if self.analyzer:
            component_statuses["analyzer"] = self.analyzer.get_status()
        if self.visualizer:
            component_statuses["visualizer"] = self.visualizer.get_status()
        if self.exporter:
            component_statuses["exporter"] = self.exporter.get_status()
        
        # Calculate queue sizes
        queue_sizes = {
            "read_queue": self.read_queue.qsize(),
            "decode_queue": self.decode_queue.qsize(),
            "process_queue": self.process_queue.qsize(),
            "analyze_queue": self.analyze_queue.qsize(),
            "visualize_queue": self.visualize_queue.qsize(),
            "write_queue": self.write_queue.qsize()
        }
        
        # Combine all status information
        status = {
            "id": self.id,
            "running": self.running,
            "metrics": self.get_metrics(),
            "components": component_statuses,
            "queues": queue_sizes,
            "threads": {name: thread.is_alive() for name, thread in self.threads.items()}
        }
        
        return status


# How to modify functionality:
# 1. Add new processing stage: Add new queue, thread and loop method similar to existing ones
# 2. Change data flow: Modify the queue connections in the loop methods
# 3. Add thread timeout: Change thread.join(thread_timeout) parameter in stop() method
# 4. Add pause functionality: Add a pause_event similar to stop_event and check it in loops
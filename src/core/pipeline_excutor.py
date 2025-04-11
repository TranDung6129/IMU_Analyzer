# src/core/pipeline_executor.py
import threading
import time
import logging
from queue import Queue, Empty
from typing import List, Dict, Any, Optional, Generator

from src.io.readers.base_reader import IDataReader
from src.plugins.decoders.base_decoder import IDecoder
from src.plugins.processors.base_processor import IProcessor
from src.plugins.analyzers.base_analyzer import IAnalyzer
from src.plugins.visualizers.base_visualizer import IVisualizer
from src.data.models import SensorData

logger = logging.getLogger(__name__)

class PipelineExecutor:
    """
    Executes a data processing pipeline.
    
    Coordinates the flow of data between pipeline components:
    Reader -> Decoder -> Processors -> [Analyzers] -> Visualizers
    
    Supports both single-threaded and multi-threaded execution.
    """
    
    def __init__(
        self,
        name: str,
        reader: IDataReader,
        decoder: IDecoder,
        processors: Optional[List[IProcessor]] = None,
        analyzers: Optional[List[IAnalyzer]] = None,  # Added analyzers
        visualizers: Optional[List[IVisualizer]] = None,
        use_threading: bool = True,
        queue_size: int = 100,
        processing_interval: float = 0.01
    ):
        """
        Initialize the pipeline executor.
        
        Args:
            name: Name of the pipeline
            reader: Data reader component
            decoder: Data decoder component
            processors: List of processor components (optional)
            analyzers: List of analyzer components (optional)
            visualizers: List of visualizer components (optional)
            use_threading: Whether to use multi-threaded execution (default: True)
            queue_size: Size of the queues between components (default: 100)
            processing_interval: Time interval between processing cycles in seconds (default: 0.01)
        """
        self.name = name
        self.reader = reader
        self.decoder = decoder
        self.processors = processors or []
        self.analyzers = analyzers or []  # Initialize analyzers
        self.visualizers = visualizers or []
        self.use_threading = use_threading
        self.queue_size = queue_size
        self.processing_interval = processing_interval
        
        # Pipeline state
        self.running = False
        self.paused = False
        
        # Queues for inter-component communication
        self.raw_data_queue = Queue(maxsize=queue_size)
        self.decoded_data_queue = Queue(maxsize=queue_size)
        self.processed_data_queues = [Queue(maxsize=queue_size) for _ in range(len(self.processors) + 1)]
        self.analyzer_queue = Queue(maxsize=queue_size)  # Queue for analyzer input
        self.analyzer_result_queue = Queue(maxsize=queue_size)  # Queue for analyzer results
        
        # Threads
        self.reader_thread = None
        self.decoder_thread = None
        self.processor_threads = []
        self.analyzer_threads = []  # Threads for analyzers
        self.visualization_threads = []
        
        logger.info(f"Pipeline '{name}' initialized with: "
                  f"reader={reader.__class__.__name__}, "
                  f"decoder={decoder.__class__.__name__}, "
                  f"{len(self.processors)} processors, "
                  f"{len(self.analyzers)} analyzers, "  # Log analyzers
                  f"{len(self.visualizers)} visualizers")
    
    def setup(self):
        """Set up pipeline components before execution."""
        logger.info(f"Setting up pipeline '{self.name}'")
        
        # Set up visualizers first (they might need to create UI elements)
        for visualizer in self.visualizers:
            if hasattr(visualizer, 'setup'):
                visualizer.setup()
        
        # Set up analyzers
        for analyzer in self.analyzers:
            if hasattr(analyzer, 'setup'):
                analyzer.setup()
        
        # Set up processors
        for processor in self.processors:
            if hasattr(processor, 'setup'):
                processor.setup()
    
    def teardown(self):
        """Clean up pipeline components after execution."""
        logger.info(f"Tearing down pipeline '{self.name}'")
        
        # Close reader
        if hasattr(self.reader, 'close'):
            try:
                self.reader.close()
            except Exception as e:
                logger.error(f"Error closing reader: {e}")
        
        # Tear down processors
        for processor in self.processors:
            if hasattr(processor, 'teardown'):
                try:
                    processor.teardown()
                except Exception as e:
                    logger.error(f"Error in processor teardown: {e}")
        
        # Tear down analyzers
        for analyzer in self.analyzers:
            if hasattr(analyzer, 'teardown'):
                try:
                    analyzer.teardown()
                except Exception as e:
                    logger.error(f"Error in analyzer teardown: {e}")
        
        # Tear down visualizers
        for visualizer in self.visualizers:
            if hasattr(visualizer, 'teardown'):
                try:
                    visualizer.teardown()
                except Exception as e:
                    logger.error(f"Error in visualizer teardown: {e}")
    
    def start(self):
        """
        Start the pipeline execution.
        
        In threaded mode, starts separate threads for each component.
        In single-threaded mode, runs the pipeline in the current thread.
        """
        if self.running:
            logger.warning(f"Pipeline '{self.name}' is already running")
            return
        
        try:
            # Set pipeline state
            self.running = True
            self.paused = False
            
            # Initialize components
            self.setup()
            
            if self.use_threading:
                logger.info(f"Starting pipeline '{self.name}' in threaded mode")
                self._start_threaded()
            else:
                logger.info(f"Starting pipeline '{self.name}' in single-threaded mode")
                self._run_single_threaded()
        except Exception as e:
            self.running = False
            logger.error(f"Error starting pipeline '{self.name}': {e}")
            self.teardown()
            raise
    
    def stop(self):
        """
        Stop the pipeline execution.
        
        Signals all threads to stop and waits for them to finish.
        """
        if not self.running:
            return
        
        logger.info(f"Stopping pipeline '{self.name}'")
        self.running = False
        
        if self.use_threading:
            # Wait for threads to finish
            threads = ([self.reader_thread, self.decoder_thread] + 
                      self.processor_threads + 
                      self.analyzer_threads +  # Added analyzer threads
                      self.visualization_threads)
            
            for thread in threads:
                if thread and thread.is_alive():
                    thread.join(timeout=2.0)
            
            logger.info(f"All threads in pipeline '{self.name}' have terminated")
        
        # Clean up
        self.teardown()
    
    def pause(self):
        """Pause the pipeline execution."""
        if self.running and not self.paused:
            logger.info(f"Pausing pipeline '{self.name}'")
            self.paused = True
    
    def resume(self):
        """Resume the pipeline execution."""
        if self.running and self.paused:
            logger.info(f"Resuming pipeline '{self.name}'")
            self.paused = False
    
    def _start_threaded(self):
        """Start pipeline execution in threaded mode."""
        # Start reader thread
        self.reader_thread = threading.Thread(
            target=self._reader_task,
            name=f"{self.name}-Reader"
        )
        self.reader_thread.daemon = True
        self.reader_thread.start()
        
        # Start decoder thread
        self.decoder_thread = threading.Thread(
            target=self._decoder_task,
            name=f"{self.name}-Decoder"
        )
        self.decoder_thread.daemon = True
        self.decoder_thread.start()
        
        # Start processor threads
        self.processor_threads = []
        for i, processor in enumerate(self.processors):
            thread = threading.Thread(
                target=self._processor_task,
                args=(i, processor),
                name=f"{self.name}-Processor-{i}"
            )
            thread.daemon = True
            thread.start()
            self.processor_threads.append(thread)
        
        # Start analyzer threads
        self.analyzer_threads = []
        for i, analyzer in enumerate(self.analyzers):
            thread = threading.Thread(
                target=self._analyzer_task,
                args=(analyzer,),
                name=f"{self.name}-Analyzer-{i}"
            )
            thread.daemon = True
            thread.start()
            self.analyzer_threads.append(thread)
        
        # Start result processor thread for analyzer results
        if self.analyzers:
            result_thread = threading.Thread(
                target=self._analyzer_result_task,
                name=f"{self.name}-AnalyzerResults"
            )
            result_thread.daemon = True
            result_thread.start()
            self.analyzer_threads.append(result_thread)
        
        # Start visualizer threads
        self.visualization_threads = []
        for i, visualizer in enumerate(self.visualizers):
            thread = threading.Thread(
                target=self._visualizer_task,
                args=(visualizer,),
                name=f"{self.name}-Visualizer-{i}"
            )
            thread.daemon = True
            thread.start()
            self.visualization_threads.append(thread)
    
    def _run_single_threaded(self):
        """Run the pipeline in single-threaded mode."""
        try:
            # Open the reader
            if hasattr(self.reader, 'open'):
                self.reader.open()
            
            # Process data until stopped or reader is exhausted
            for raw_data in self.reader.read():
                if not self.running:
                    break
                
                if self.paused:
                    time.sleep(self.processing_interval)
                    continue
                
                # Decode raw data
                for sensor_data in self.decoder.decode(raw_data):
                    if not sensor_data:
                        continue
                    
                    # Process data through each processor
                    data_items = [sensor_data]
                    
                    for processor in self.processors:
                        next_items = []
                        for data_item in data_items:
                            for result in processor.process(data_item):
                                if result:
                                    next_items.append(result)
                        data_items = next_items
                    
                    # Process data through analyzers
                    analyzer_results = []
                    for data_item in data_items:
                        for analyzer in self.analyzers:
                            for result in analyzer.analyze(data_item):
                                if result:
                                    analyzer_results.append(result)
                    
                    # Visualize processed data and analyzer results
                    all_results = data_items + analyzer_results
                    for result in all_results:
                        for visualizer in self.visualizers:
                            visualizer.visualize(result)
        finally:
            self.running = False
            self.teardown()
    
    def _reader_task(self):
        """Reader thread task: read data and put it in the raw data queue."""
        try:
            # Open the reader
            if hasattr(self.reader, 'open'):
                self.reader.open()
            
            # Read data until stopped or reader is exhausted
            for raw_data in self.reader.read():
                if not self.running:
                    break
                
                if self.paused:
                    time.sleep(self.processing_interval)
                    continue
                
                # Put data in queue (with timeout to check running status)
                self.raw_data_queue.put(raw_data, timeout=1.0)
            
            logger.info(f"Reader for pipeline '{self.name}' has finished")
        except Exception as e:
            logger.error(f"Error in reader thread: {e}")
        finally:
            # Signal end of data by putting None in the queue
            if self.running:
                try:
                    self.raw_data_queue.put(None, timeout=1.0)
                except:
                    pass
    
    def _decoder_task(self):
        """Decoder thread task: decode raw data and put it in the decoded data queue."""
        try:
            while self.running:
                try:
                    # Get data from queue (with timeout to check running status)
                    raw_data = self.raw_data_queue.get(timeout=1.0)
                    
                    # Exit if None (end of data)
                    if raw_data is None:
                        break
                    
                    # Skip if paused
                    if self.paused:
                        self.raw_data_queue.task_done()
                        time.sleep(self.processing_interval)
                        continue
                    
                    # Decode raw data
                    for sensor_data in self.decoder.decode(raw_data):
                        if sensor_data:
                            # Put in first processor queue or directly to visualizer queue
                            queue_index = 0
                            self.processed_data_queues[queue_index].put(sensor_data, timeout=1.0)
                    
                    # Mark task as done
                    self.raw_data_queue.task_done()
                    
                except Empty:
                    # Timeout, just continue
                    continue
                except Exception as e:
                    logger.error(f"Error in decoder thread: {e}")
            
            logger.info(f"Decoder for pipeline '{self.name}' has finished")
        except Exception as e:
            logger.error(f"Error in decoder thread: {e}")
        finally:
            # Signal end of data
            if self.running:
                try:
                    for queue in self.processed_data_queues:
                        queue.put(None, timeout=1.0)
                except:
                    pass
    
    def _processor_task(self, index: int, processor: IProcessor):
        """
        Processor thread task: process data and put results in the next queue.
        
        Args:
            index: Index of the processor
            processor: Processor component
        """
        input_queue = self.processed_data_queues[index]
        output_queue = self.processed_data_queues[index + 1]
        
        try:
            while self.running:
                try:
                    # Get data from queue (with timeout to check running status)
                    data = input_queue.get(timeout=1.0)
                    
                    # Exit if None (end of data)
                    if data is None:
                        break
                    
                    # Skip if paused
                    if self.paused:
                        input_queue.task_done()
                        time.sleep(self.processing_interval)
                        continue
                    
                    # Process data
                    for result in processor.process(data):
                        if result:
                            output_queue.put(result, timeout=1.0)
                            
                            # Also feed to analyzer if this is the last processor
                            if index == len(self.processors) - 1 and self.analyzers:
                                self.analyzer_queue.put(result, timeout=1.0)
                    
                    # Mark task as done
                    input_queue.task_done()
                    
                except Empty:
                    # Timeout, just continue
                    continue
                except Exception as e:
                    logger.error(f"Error in processor thread {index}: {e}")
            
            logger.info(f"Processor {index} for pipeline '{self.name}' has finished")
        except Exception as e:
            logger.error(f"Error in processor thread {index}: {e}")
        finally:
            # Signal end of data
            if self.running:
                try:
                    output_queue.put(None, timeout=1.0)
                    
                    # If this is the last processor, signal end to analyzers too
                    if index == len(self.processors) - 1 and self.analyzers:
                        self.analyzer_queue.put(None, timeout=1.0)
                except:
                    pass
    
    def _analyzer_task(self, analyzer: IAnalyzer):
        """
        Analyzer thread task: analyze processed data and put results in the result queue.
        
        Args:
            analyzer: Analyzer component
        """
        try:
            while self.running:
                try:
                    # Get data from queue (with timeout to check running status)
                    data = self.analyzer_queue.get(timeout=1.0)
                    
                    # Exit if None (end of data)
                    if data is None:
                        break
                    
                    # Skip if paused
                    if self.paused:
                        self.analyzer_queue.task_done()
                        time.sleep(self.processing_interval)
                        continue
                    
                    # Analyze data
                    for result in analyzer.analyze(data):
                        if result:
                            self.analyzer_result_queue.put(result, timeout=1.0)
                    
                    # Mark task as done
                    self.analyzer_queue.task_done()
                    
                except Empty:
                    # Timeout, just continue
                    continue
                except Exception as e:
                    logger.error(f"Error in analyzer thread: {e}")
            
            logger.info(f"Analyzer {analyzer.__class__.__name__} for pipeline '{self.name}' has finished")
        except Exception as e:
            logger.error(f"Error in analyzer thread: {e}")
        finally:
            # Signal end of data
            if self.running:
                try:
                    self.analyzer_result_queue.put(None, timeout=1.0)
                except:
                    pass
    
    def _analyzer_result_task(self):
        """Process analyzer results and forward them to visualizers."""
        try:
            end_signals = 0
            expected_signals = len(self.analyzers)
            
            while self.running and end_signals < expected_signals:
                try:
                    # Get result from queue (with timeout to check running status)
                    result = self.analyzer_result_queue.get(timeout=1.0)
                    
                    # Check for end signal
                    if result is None:
                        end_signals += 1
                        self.analyzer_result_queue.task_done()
                        continue
                    
                    # Skip if paused
                    if self.paused:
                        self.analyzer_result_queue.task_done()
                        time.sleep(self.processing_interval)
                        continue
                    
                    # Forward to visualizers by putting in the final processed data queue
                    self.processed_data_queues[-1].put(result, timeout=1.0)
                    
                    # Mark task as done
                    self.analyzer_result_queue.task_done()
                    
                except Empty:
                    # Timeout, just continue
                    continue
                except Exception as e:
                    logger.error(f"Error in analyzer result thread: {e}")
            
            logger.info(f"Analyzer result processor for pipeline '{self.name}' has finished")
        except Exception as e:
            logger.error(f"Error in analyzer result thread: {e}")
        finally:
            # No need to signal end here, as each analyzer already signals end
            pass
    
    def _visualizer_task(self, visualizer: IVisualizer):
        """
        Visualizer thread task: visualize processed data.
        
        Args:
            visualizer: Visualizer component
        """
        # Use the output of the last processor
        input_queue = self.processed_data_queues[-1]
        
        try:
            while self.running:
                try:
                    # Get data from queue (with timeout to check running status)
                    data = input_queue.get(timeout=1.0)
                    
                    # Exit if None (end of data)
                    if data is None:
                        break
                    
                    # Skip if paused
                    if self.paused:
                        input_queue.task_done()
                        time.sleep(self.processing_interval)
                        continue
                    
                    # Visualize data
                    visualizer.visualize(data)
                    
                    # Mark task as done
                    input_queue.task_done()
                    
                except Empty:
                    # Timeout, just continue
                    continue
                except Exception as e:
                    logger.error(f"Error in visualizer thread: {e}")
            
            logger.info(f"Visualizer for pipeline '{self.name}' has finished")
        except Exception as e:
            logger.error(f"Error in visualizer thread: {e}")
    
    def is_running(self) -> bool:
        """Check if the pipeline is currently running."""
        return self.running
    
    def is_paused(self) -> bool:
        """Check if the pipeline is currently paused."""
        return self.paused
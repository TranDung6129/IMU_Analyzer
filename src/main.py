# src/main.py
import os
import time
import logging
import argparse
import signal
import sys
from typing import Dict, Any, List, Optional

from src.core.config_loader import ConfigLoader, ConfigError
from src.core.plugin_manager import PluginManager, PluginLoadError
from src.core.pipeline_executor import PipelineExecutor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Global variables for cleanup handling
running_pipelines = []

def signal_handler(sig, frame):
    """Handle signal for graceful shutdown."""
    logger.info("Interrupt received, stopping pipelines...")
    for pipeline in running_pipelines:
        try:
            pipeline.stop()
        except:
            pass
    sys.exit(0)

def create_sample_csv():
    """Create a sample CSV file for demonstration."""
    import random
    
    # Create data directory if it doesn't exist
    os.makedirs('data_samples', exist_ok=True)
    
    # Create a sample CSV file
    with open('data_samples/sample.csv', 'w') as f:
        # Write header
        f.write('timestamp,x,y,z\n')
        
        # Write data
        start_time = time.time()
        for i in range(100):
            timestamp = start_time + i * 0.01
            x = random.uniform(-1.0, 1.0)
            y = random.uniform(-1.0, 1.0)
            z = random.uniform(-1.0, 1.0)
            f.write(f'{timestamp:.6f},{x:.6f},{y:.6f},{z:.6f}\n')
    
    logger.info("Created sample CSV file at data_samples/sample.csv")

def create_pipeline(config: Dict[str, Any], plugin_manager: PluginManager) -> PipelineExecutor:
    """
    Create a pipeline from a configuration dictionary.
    
    Args:
        config: Configuration dictionary
        plugin_manager: Plugin manager to load plugins
        
    Returns:
        Configured pipeline
    """
    # Extract pipeline configuration
    pipeline_config = config.get('pipeline', {})
    pipeline_name = pipeline_config.get('name', 'Default Pipeline')
    use_threading = pipeline_config.get('use_threading', True)
    
    logger.info(f"Creating pipeline '{pipeline_name}'")
    
    try:
        # Create reader
        reader_config = pipeline_config.get('reader', {})
        reader_type = reader_config.get('type')
        reader_params = reader_config.get('config', {})
        
        reader = plugin_manager.create_plugin('reader', reader_type, reader_params)
        
        # Create decoder
        decoder_config = pipeline_config.get('decoder', {})
        decoder_type = decoder_config.get('type')
        decoder_params = decoder_config.get('config', {})
        
        decoder = plugin_manager.create_plugin('decoder', decoder_type, decoder_params)
        
        # Create processors
        processors = []
        for proc_config in pipeline_config.get('processors', []):
            proc_type = proc_config.get('type')
            proc_params = proc_config.get('config', {})
            
            processor = plugin_manager.create_plugin('processor', proc_type, proc_params)
            processors.append(processor)
        
        # Create visualizers
        visualizers = []
        for vis_config in pipeline_config.get('visualizers', []):
            vis_type = vis_config.get('type')
            vis_params = vis_config.get('config', {})
            
            visualizer = plugin_manager.create_plugin('visualizer', vis_type, vis_params)
            visualizers.append(visualizer)
        
        # Create pipeline
        pipeline = PipelineExecutor(
            name=pipeline_name,
            reader=reader,
            decoder=decoder,
            processors=processors,
            visualizers=visualizers,
            use_threading=use_threading
        )
        
        logger.info(f"Pipeline '{pipeline_name}' created successfully")
        return pipeline
        
    except PluginLoadError as e:
        logger.error(f"Error loading plugin: {e}")
        raise
    except Exception as e:
        logger.error(f"Error creating pipeline: {e}")
        raise

def list_available_plugins(plugin_manager: PluginManager):
    """
    List all available plugins.
    
    Args:
        plugin_manager: Plugin manager instance
    """
    print("\nAvailable Plugins:")
    print("-----------------")
    
    for plugin_type in ['reader', 'decoder', 'processor', 'visualizer']:
        try:
            plugins = plugin_manager.get_available_plugins(plugin_type)
            print(f"* {plugin_type.capitalize()} plugins ({len(plugins)}):")
            for plugin in plugins:
                print(f"  - {plugin}")
        except Exception as e:
            print(f"  Error retrieving {plugin_type} plugins: {e}")
    
    print("")

def run_pipeline(pipeline: PipelineExecutor, runtime: Optional[float] = None):
    """
    Run a pipeline.
    
    Args:
        pipeline: Pipeline to run
        runtime: Maximum runtime in seconds (None for unlimited)
    """
    # Add to global list for signal handling
    running_pipelines.append(pipeline)
    
    try:
        # Start the pipeline
        logger.info(f"Starting pipeline '{pipeline.name}'")
        pipeline.start()
        
        # Run until completion or timeout
        start_time = time.time()
        while pipeline.is_running():
            time.sleep(0.1)
            
            # Check for timeout
            if runtime is not None and time.time() - start_time >= runtime:
                logger.info(f"Maximum runtime of {runtime}s reached, stopping pipeline")
                pipeline.stop()
                break
    
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received, stopping pipeline")
        pipeline.stop()
    except Exception as e:
        logger.error(f"Error running pipeline: {e}")
        pipeline.stop()
    finally:
        # Remove from global list
        if pipeline in running_pipelines:
            running_pipelines.remove(pipeline)
        
        # Ensure pipeline is stopped
        if pipeline.is_running():
            pipeline.stop()

def main():
    """Main entry point."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='IMU Analyzer')
    parser.add_argument('--config', help='Path to pipeline configuration file')
    parser.add_argument('--runtime', type=float, help='Maximum runtime in seconds')
    parser.add_argument('--create-sample', action='store_true', help='Create a sample CSV file')
    parser.add_argument('--list-plugins', action='store_true', help='List available plugins')
    args = parser.parse_args()
    
    # Register signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    
    # Create plugin manager
    plugin_manager = PluginManager()
    
    # List available plugins if requested
    if args.list_plugins:
        list_available_plugins(plugin_manager)
        return
    
    # Create sample CSV if requested
    if args.create_sample:
        create_sample_csv()
    
    # Create config loader
    config_loader = ConfigLoader()
    
    # Load or create configuration
    config = None
    if args.config:
        try:
            config = config_loader.load(args.config)
        except ConfigError as e:
            logger.error(f"Error loading configuration: {e}")
            return
    else:
        # Use default configuration
        config = config_loader.create_default_config()
        
        # If we created a sample file and no config was provided, update the default config
        if args.create_sample:
            config['pipeline']['reader']['config']['file_path'] = 'data_samples/sample.csv'
    
    try:
        # Create pipeline
        pipeline = create_pipeline(config, plugin_manager)
        
        # Run pipeline
        run_pipeline(pipeline, args.runtime)
    except Exception as e:
        logger.error(f"Error: {e}")

if __name__ == '__main__':
    main()
# src/core/config_loader.py
import os
import yaml
import json
import logging
import jsonschema
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

class ConfigError(Exception):
    """Exception raised when there's an error with the configuration."""
    pass

class ConfigLoader:
    """
    Loads and validates configuration files for the IMU Analyzer.
    
    Supports YAML and JSON formats with validation against a schema.
    """
    
    # Default pipeline schema
    DEFAULT_SCHEMA = {
        "type": "object",
        "required": ["pipeline"],
        "properties": {
            "pipeline": {
                "type": "object",
                "required": ["name", "reader", "decoder"],
                "properties": {
                    "name": {"type": "string"},
                    "use_threading": {"type": "boolean"},
                    "reader": {
                        "type": "object",
                        "required": ["type", "config"],
                        "properties": {
                            "type": {"type": "string"},
                            "config": {"type": "object"}
                        }
                    },
                    "decoder": {
                        "type": "object",
                        "required": ["type", "config"],
                        "properties": {
                            "type": {"type": "string"},
                            "config": {"type": "object"}
                        }
                    },
                    "processors": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "required": ["type", "config"],
                            "properties": {
                                "type": {"type": "string"},
                                "config": {"type": "object"}
                            }
                        }
                    },
                    "analyzers": {  # Added analyzers section
                        "type": "array",
                        "items": {
                            "type": "object",
                            "required": ["type", "config"],
                            "properties": {
                                "type": {"type": "string"},
                                "config": {"type": "object"}
                            }
                        }
                    },
                    "visualizers": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "required": ["type", "config"],
                            "properties": {
                                "type": {"type": "string"},
                                "config": {"type": "object"}
                            }
                        }
                    }
                }
            }
        }
    }
    
    def __init__(self, schema: Optional[Dict[str, Any]] = None):
        """
        Initialize the config loader.
        
        Args:
            schema: Optional custom schema for validation
                   If None, uses the default schema
        """
        self.schema = schema or self.DEFAULT_SCHEMA
        
    def load(self, config_path: str) -> Dict[str, Any]:
        """
        Load and validate a configuration file.
        
        Args:
            config_path: Path to the configuration file (YAML or JSON)
            
        Returns:
            Validated configuration dictionary
            
        Raises:
            ConfigError: If the configuration cannot be loaded or is invalid
        """
        logger.info(f"Loading configuration from {config_path}")
        
        try:
            # Check if the file exists
            if not os.path.exists(config_path):
                raise ConfigError(f"Configuration file not found: {config_path}")
            
            # Determine file type from extension
            _, ext = os.path.splitext(config_path)
            
            # Load YAML file
            if ext.lower() in ('.yaml', '.yml'):
                with open(config_path, 'r') as f:
                    config = yaml.safe_load(f)
            
            # Load JSON file
            elif ext.lower() == '.json':
                with open(config_path, 'r') as f:
                    config = json.load(f)
            
            # Unsupported format
            else:
                raise ConfigError(f"Unsupported configuration format: {ext}")
            
            # Validate the configuration
            self.validate(config)
            
            logger.info(f"Successfully loaded and validated configuration from {config_path}")
            return config
            
        except yaml.YAMLError as e:
            raise ConfigError(f"YAML parsing error: {e}")
        except json.JSONDecodeError as e:
            raise ConfigError(f"JSON parsing error: {e}")
        except Exception as e:
            if isinstance(e, ConfigError):
                raise
            raise ConfigError(f"Error loading configuration: {e}")
    
    def validate(self, config: Dict[str, Any]) -> None:
        """
        Validate a configuration against the schema.
        
        Args:
            config: Configuration dictionary to validate
            
        Raises:
            ConfigError: If the configuration is invalid
        """
        try:
            # Validate against schema
            jsonschema.validate(instance=config, schema=self.schema)
            
            # Perform additional validation
            self._validate_pipeline_components(config)
            
        except jsonschema.exceptions.ValidationError as e:
            raise ConfigError(f"Configuration validation error: {e.message}")
    
    def _validate_pipeline_components(self, config: Dict[str, Any]) -> None:
        """
        Perform additional validation on pipeline components.
        
        Args:
            config: Configuration dictionary to validate
            
        Raises:
            ConfigError: If a component is invalid
        """
        # Extract pipeline configuration
        pipeline = config.get('pipeline', {})
        
        # Check reader configuration
        reader = pipeline.get('reader', {})
        reader_type = reader.get('type')
        reader_config = reader.get('config', {})
        
        if not reader_type:
            raise ConfigError("Reader type is required")
        
        # Check decoder configuration
        decoder = pipeline.get('decoder', {})
        decoder_type = decoder.get('type')
        decoder_config = decoder.get('config', {})
        
        if not decoder_type:
            raise ConfigError("Decoder type is required")
        
        # Check processor configurations
        processors = pipeline.get('processors', [])
        for i, processor in enumerate(processors):
            processor_type = processor.get('type')
            processor_config = processor.get('config', {})
            
            if not processor_type:
                raise ConfigError(f"Processor {i} type is required")
        
        # Check analyzer configurations
        analyzers = pipeline.get('analyzers', [])
        for i, analyzer in enumerate(analyzers):
            analyzer_type = analyzer.get('type')
            analyzer_config = analyzer.get('config', {})
            
            if not analyzer_type:
                raise ConfigError(f"Analyzer {i} type is required")
        
        # Check visualizer configurations
        visualizers = pipeline.get('visualizers', [])
        for i, visualizer in enumerate(visualizers):
            visualizer_type = visualizer.get('type')
            visualizer_config = visualizer.get('config', {})
            
            if not visualizer_type:
                raise ConfigError(f"Visualizer {i} type is required")
    
    def save(self, config: Dict[str, Any], config_path: str) -> None:
        """
        Save a configuration to a file.
        
        Args:
            config: Configuration dictionary to save
            config_path: Path to save the configuration to
            
        Raises:
            ConfigError: If the configuration cannot be saved
        """
        logger.info(f"Saving configuration to {config_path}")
        
        try:
            # Validate the configuration before saving
            self.validate(config)
            
            # Determine file type from extension
            _, ext = os.path.splitext(config_path)
            
            # Save as YAML
            if ext.lower() in ('.yaml', '.yml'):
                with open(config_path, 'w') as f:
                    yaml.dump(config, f, default_flow_style=False, sort_keys=False)
            
            # Save as JSON
            elif ext.lower() == '.json':
                with open(config_path, 'w') as f:
                    json.dump(config, f, indent=2)
            
            # Default to YAML if extension is not recognized
            else:
                config_path += '.yaml'
                with open(config_path, 'w') as f:
                    yaml.dump(config, f, default_flow_style=False, sort_keys=False)
            
            logger.info(f"Successfully saved configuration to {config_path}")
            
        except Exception as e:
            if isinstance(e, ConfigError):
                raise
            raise ConfigError(f"Error saving configuration: {e}")
    
    def create_default_config(self) -> Dict[str, Any]:
        """
        Create a default configuration.
        
        Returns:
            Default configuration dictionary
        """
        default_config = {
            "pipeline": {
                "name": "Default Pipeline",
                "use_threading": True,
                "reader": {
                    "type": "FileReader",
                    "config": {
                        "file_path": "data_samples/sample.csv",
                        "simulate_realtime": True,
                        "simulation_speed": 1.0
                    }
                },
                "decoder": {
                    "type": "CSVDecoder",
                    "config": {
                        "sensor_id": "csv_sensor",
                        "data_type": "csv",
                        "timestamp_column": "timestamp",
                        "numeric_columns": ["x", "y", "z"]
                    }
                },
                "processors": [
                    {
                        "type": "SimpleProcessor",
                        "config": {
                            "log_level": "INFO",
                            "pass_through": True
                        }
                    }
                ],
                "analyzers": [  # Added analyzers section
                    {
                        "type": "SimpleAnalyzer",
                        "config": {
                            "channels": ["x", "y", "z"],
                            "window_size": 50,
                            "trigger_interval": 1.0
                        }
                    }
                ],
                "visualizers": [
                    {
                        "type": "TimeSeriesVisualizer",
                        "config": {
                            "channels": ["x", "y", "z"],
                            "window_size": 100,
                            "update_interval": 0.5,
                            "ascii_plot": True
                        }
                    }
                ]
            }
        }
        
        return default_config
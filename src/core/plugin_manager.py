# src/core/plugin_manager.py
import os
import sys
import importlib
import inspect
import logging
from typing import Dict, Any, List, Type, Optional, Set

# Import interfaces
from src.io.readers.base_reader import IDataReader
from src.plugins.decoders.base_decoder import IDecoder
from src.plugins.processors.base_processor import IProcessor
from src.plugins.visualizers.base_visualizer import IVisualizer
from src.plugins.analyzers.base_analyzer import IAnalyzer

logger = logging.getLogger(__name__)

class PluginLoadError(Exception):
    """Exception raised when a plugin cannot be loaded."""
    pass

class PluginManager:
    """
    Manages the discovery, loading, and instantiation of plugins.
    
    Responsibilities:
    - Discover plugins from specified directories
    - Validate plugins against their expected interfaces
    - Load plugin classes by name and type
    - Instantiate plugins with configuration
    - Maintain a registry of available plugins
    """
    
    # Interface mapping: plugin_type -> interface_class
    INTERFACES = {
        'reader': IDataReader,
        'decoder': IDecoder,
        'processor': IProcessor,
        'visualizer': IVisualizer,
        'analyzer': IAnalyzer   # Added analyzer interface
    }
    
    # Default plugin directories
    DEFAULT_PLUGIN_DIRS = {
        'reader': ['src.io.readers'],
        'decoder': ['src.plugins.decoders'],
        'processor': ['src.plugins.processors'],
        'visualizer': ['src.plugins.visualizers'],
        'analyzer': ['src.plugins.analyzers']   # Added analyzer directory
    }
    
    def __init__(self, plugin_dirs: Optional[Dict[str, List[str]]] = None, auto_discover: bool = True):
        """
        Initialize the plugin manager.
        
        Args:
            plugin_dirs: Dictionary mapping plugin types to lists of module paths
                        Where to look for plugins, e.g., {'reader': ['src.io.readers', 'custom.readers']}
                        If None, uses default directories
            auto_discover: Whether to automatically discover plugins at initialization
        """
        # Use provided directories or defaults
        self.plugin_dirs = plugin_dirs or self.DEFAULT_PLUGIN_DIRS
        
        # Plugin registry: {plugin_type: {plugin_name: plugin_class}}
        self.plugins: Dict[str, Dict[str, Type]] = {
            plugin_type: {} for plugin_type in self.INTERFACES
        }
        
        # Track loaded modules to avoid reloading
        self.loaded_modules: Set[str] = set()
        
        # Auto-discover plugins if requested
        if auto_discover:
            self.discover_plugins()
            logger.info(f"Auto-discovered plugins: {self.get_plugin_counts()}")
    
    def discover_plugins(self) -> None:
        """
        Discover and register all available plugins from the specified directories.
        """
        for plugin_type, interface in self.INTERFACES.items():
            # Skip if this plugin type has no directories
            if plugin_type not in self.plugin_dirs:
                continue
            
            logger.info(f"Discovering {plugin_type} plugins...")
            
            for module_path in self.plugin_dirs[plugin_type]:
                try:
                    self._scan_module(module_path, plugin_type, interface)
                except Exception as e:
                    logger.warning(f"Error scanning module {module_path} for {plugin_type} plugins: {e}")
        
        # Log discovery results
        self._log_discovery_results()
    
    def _scan_module(self, module_path: str, plugin_type: str, interface: Type) -> None:
        """
        Scan a module for plugins of the specified type.
        
        Args:
            module_path: Dotted path to the module to scan
            plugin_type: Type of plugin to look for
            interface: Interface class that plugins should implement
        """
        try:
            # Import the module
            module = importlib.import_module(module_path)
            self.loaded_modules.add(module_path)
            
            # If this is a package, scan its contents
            if hasattr(module, '__path__'):
                package_path = module.__path__
                package_name = module.__name__
                
                # Find all Python files in the package
                for _, submodule_name, is_pkg in pkgutil_iter_modules(package_path, f"{package_name}."):
                    if not is_pkg and submodule_name not in self.loaded_modules:
                        try:
                            # Import the submodule
                            submodule = importlib.import_module(submodule_name)
                            self.loaded_modules.add(submodule_name)
                            
                            # Scan the submodule for plugins
                            self._scan_classes(submodule, plugin_type, interface)
                        except Exception as e:
                            logger.warning(f"Error importing submodule {submodule_name}: {e}")
            
            # Scan this module for plugins
            self._scan_classes(module, plugin_type, interface)
            
        except ImportError as e:
            logger.warning(f"Error importing module {module_path}: {e}")
    
    def _scan_classes(self, module, plugin_type: str, interface: Type) -> None:
        """
        Scan a module for classes that implement the specified interface.
        
        Args:
            module: Module to scan
            plugin_type: Type of plugin to register
            interface: Interface class that plugins should implement
        """
        for name, obj in inspect.getmembers(module, inspect.isclass):
            # Skip if it's the interface itself, an abstract class, or a private class
            if (obj is interface or 
                name.startswith('_') or 
                name in ('ABC', 'abstractmethod') or
                obj.__module__ != module.__name__):  # Only consider classes defined in this module
                continue
            
            # Check if this class implements the interface
            if issubclass(obj, interface):
                # Register the plugin
                self.plugins[plugin_type][name] = obj
                logger.info(f"Discovered {plugin_type} plugin: {name} in {module.__name__}")
    
    def _log_discovery_results(self) -> None:
        """Log the results of plugin discovery."""
        for plugin_type, plugins in self.plugins.items():
            logger.info(f"Discovered {len(plugins)} {plugin_type} plugins: {', '.join(plugins.keys())}")
    
    def get_plugin_class(self, plugin_type: str, plugin_name: str) -> Type:
        """
        Get a plugin class by type and name.
        
        Args:
            plugin_type: Type of plugin ('reader', 'decoder', 'processor', 'visualizer', 'analyzer')
            plugin_name: Name of the plugin class
            
        Returns:
            Plugin class
            
        Raises:
            PluginLoadError: If the plugin cannot be found or loaded
        """
        # Check if the plugin type is valid
        if plugin_type not in self.INTERFACES:
            raise PluginLoadError(f"Invalid plugin type: {plugin_type}")
        
        # Try to find the plugin in the registry
        if plugin_name in self.plugins[plugin_type]:
            return self.plugins[plugin_type][plugin_name]
        
        # Try to find the plugin by direct import
        try:
            # Build potential module paths
            if plugin_type in self.plugin_dirs:
                for module_path in self.plugin_dirs[plugin_type]:
                    # Try to import the module
                    potential_module_path = f"{module_path}.{plugin_name.lower()}"
                    try:
                        module = importlib.import_module(potential_module_path)
                        
                        # Look for the plugin class in the module
                        if hasattr(module, plugin_name):
                            plugin_class = getattr(module, plugin_name)
                            interface = self.INTERFACES[plugin_type]
                            
                            # Check if it's a valid plugin
                            if inspect.isclass(plugin_class) and issubclass(plugin_class, interface):
                                # Register the plugin
                                self.plugins[plugin_type][plugin_name] = plugin_class
                                logger.info(f"Loaded {plugin_type} plugin: {plugin_name} from {potential_module_path}")
                                return plugin_class
                    except ImportError:
                        continue
        except Exception as e:
            logger.error(f"Error loading plugin {plugin_type}.{plugin_name}: {e}")
        
        # Plugin not found
        raise PluginLoadError(f"Plugin not found: {plugin_type}.{plugin_name}")
    
    def create_plugin(self, plugin_type: str, plugin_name: str, config: Dict[str, Any]) -> Any:
        """
        Create an instance of a plugin with the specified configuration.
        
        Args:
            plugin_type: Type of plugin ('reader', 'decoder', 'processor', 'visualizer', 'analyzer')
            plugin_name: Name of the plugin class
            config: Configuration dictionary for the plugin
            
        Returns:
            Plugin instance
            
        Raises:
            PluginLoadError: If the plugin cannot be instantiated
        """
        try:
            # Get the plugin class
            plugin_class = self.get_plugin_class(plugin_type, plugin_name)
            
            # Instantiate the plugin with the provided configuration
            plugin_instance = plugin_class(config)
            
            # Run setup if available
            if hasattr(plugin_instance, 'setup') and callable(plugin_instance.setup):
                plugin_instance.setup()
            
            return plugin_instance
        except Exception as e:
            raise PluginLoadError(f"Failed to create plugin {plugin_type}.{plugin_name}: {e}")
    
    def get_available_plugins(self, plugin_type: str) -> List[str]:
        """
        Get a list of all available plugins of the specified type.
        
        Args:
            plugin_type: Type of plugin ('reader', 'decoder', 'processor', 'visualizer', 'analyzer')
            
        Returns:
            List of plugin names
            
        Raises:
            PluginLoadError: If the plugin type is invalid
        """
        if plugin_type not in self.INTERFACES:
            raise PluginLoadError(f"Invalid plugin type: {plugin_type}")
        
        return list(self.plugins[plugin_type].keys())
    
    def get_plugin_counts(self) -> Dict[str, int]:
        """
        Get the number of discovered plugins for each type.
        
        Returns:
            Dictionary mapping plugin types to counts
        """
        return {plugin_type: len(plugins) for plugin_type, plugins in self.plugins.items()}
    
    def add_plugin_directory(self, plugin_type: str, directory: str) -> None:
        """
        Add a directory to scan for plugins of the specified type.
        
        Args:
            plugin_type: Type of plugin ('reader', 'decoder', 'processor', 'visualizer', 'analyzer')
            directory: Dotted module path to scan for plugins
            
        Raises:
            PluginLoadError: If the plugin type is invalid
        """
        if plugin_type not in self.INTERFACES:
            raise PluginLoadError(f"Invalid plugin type: {plugin_type}")
        
        # Add the directory if it's not already in the list
        if directory not in self.plugin_dirs.get(plugin_type, []):
            if plugin_type not in self.plugin_dirs:
                self.plugin_dirs[plugin_type] = []
            
            self.plugin_dirs[plugin_type].append(directory)
            
            # Scan the new directory
            try:
                self._scan_module(directory, plugin_type, self.INTERFACES[plugin_type])
                logger.info(f"Added plugin directory {directory} for {plugin_type} plugins")
            except Exception as e:
                logger.warning(f"Error scanning directory {directory} for {plugin_type} plugins: {e}")

# Helper function for package scanning (simplified pkgutil.iter_modules)
def pkgutil_iter_modules(paths, prefix=''):
    """
    Yield module info for all modules in the given paths.
    
    Args:
        paths: List of paths to scan
        prefix: Prefix to add to module names
        
    Yields:
        Tuples of (module_finder, name, ispkg)
    """
    for path in paths:
        # Convert to absolute path if it's not a string
        if not isinstance(path, str):
            path = str(path)
        
        # Get the base path
        if os.path.isdir(path):
            # Scan the directory for modules
            for entry in os.listdir(path):
                entry_path = os.path.join(path, entry)
                
                # Skip hidden files and directories
                if entry.startswith('.'):
                    continue
                
                # Check if it's a Python module or package
                if os.path.isfile(entry_path) and entry.endswith('.py') and entry != '__init__.py':
                    # It's a module
                    module_name = entry[:-3]  # Remove .py extension
                    yield None, f"{prefix}{module_name}", False
                    
                elif os.path.isdir(entry_path) and os.path.exists(os.path.join(entry_path, '__init__.py')):
                    # It's a package
                    package_name = entry
                    yield None, f"{prefix}{package_name}", True
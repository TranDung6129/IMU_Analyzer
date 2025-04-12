# File: src/core/plugin_manager.py
import os
import sys
import importlib.util
import inspect
import logging

class PluginManager:
    """
    Manages the discovery, loading and instantiation of plugins.
    """
    
    def __init__(self, plugin_dirs):
        """
        Initialize the Plugin Manager with directories to search for plugins.
        
        Args:
            plugin_dirs (list): List of directory paths containing plugins
        """
        self.plugin_dirs = plugin_dirs
        self.logger = logging.getLogger("PluginManager")
        
        # Dictionary to store discovered plugins by type and name
        self.plugins = {
            "readers": {},
            "writers": {},
            "decoders": {},
            "processors": {},
            "analyzers": {},
            "visualizers": {},
            "exporters": {},
            "configurators": {}
        }
        
        # Plugin base classes for validation
        self.base_classes = {
            "readers": "BaseReader",
            "writers": "BaseWriter",
            "decoders": "BaseDecoder",
            "processors": "BaseProcessor",
            "analyzers": "BaseAnalyzer",
            "visualizers": "BaseVisualizer",
            "exporters": "BaseExporter",
            "configurators": "BaseConfigurator"
        }
        
        # Đảm bảo rằng thư mục gốc của dự án trong PYTHONPATH
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if project_root not in sys.path:
            sys.path.insert(0, project_root)
            self.logger.info(f"Added project root to PYTHONPATH: {project_root}")
    
    def discover_plugins(self):
        """
        Scan plugin directories and discover available plugins.
        """
        self.logger.info("Discovering plugins...")
        self.logger.info(f"Plugin directories: {self.plugin_dirs}")
        
        for plugin_dir in self.plugin_dirs:
            # Kiểm tra thư mục có tồn tại không
            if not os.path.exists(plugin_dir):
                self.logger.warning(f"Plugin directory does not exist: {plugin_dir}")
                continue
            
            try:
                # Liệt kê tất cả các file trong thư mục
                self.logger.info(f"Scanning directory: {plugin_dir}")
                
                # Xác định loại plugin từ tên thư mục
                plugin_type = None
                for known_type in self.plugins.keys():
                    if known_type in plugin_dir.lower():
                        plugin_type = known_type
                        break
                        
                if not plugin_type:
                    self.logger.warning(f"Could not determine plugin type from directory: {plugin_dir}")
                    continue
                    
                self.logger.info(f"Directory {plugin_dir} identified as {plugin_type} plugin type")
                    
                # Quét tất cả các file Python trong thư mục
                for file_name in os.listdir(plugin_dir):
                    if file_name.endswith('.py') and not file_name.startswith('__'):
                        plugin_path = os.path.join(plugin_dir, file_name)
                        self.logger.info(f"Found plugin file: {plugin_path}")
                        
                        # Thử tải module để tìm lớp plugin
                        try:
                            # Tạo tên module
                            module_name = f"{plugin_type}.{file_name[:-3]}"
                            
                            # Tải module
                            spec = importlib.util.spec_from_file_location(module_name, plugin_path)
                            module = importlib.util.module_from_spec(spec)
                            spec.loader.exec_module(module)
                            
                            # Tìm các lớp plugin trong module
                            base_class_name = self.base_classes.get(plugin_type)
                            found_plugins = self._find_plugin_classes(module, base_class_name)
                            
                            for plugin_class_name, plugin_class in found_plugins:
                                self.plugins[plugin_type][plugin_class_name] = {
                                    'file_path': plugin_path,
                                    'module': module,
                                    'class': plugin_class
                                }
                                self.logger.info(f"Discovered {plugin_type} plugin: {plugin_class_name}")
                                
                        except Exception as e:
                            self.logger.error(f"Error loading plugin from {plugin_path}: {str(e)}")
                            
            except Exception as e:
                self.logger.error(f"Error scanning directory {plugin_dir}: {str(e)}")
        
        # Log summary of discovered plugins
        for plugin_type, plugins in self.plugins.items():
            self.logger.info(f"Discovered {len(plugins)} {plugin_type} plugins")
        
        # Log chi tiết tất cả plugin đã phát hiện
        self.logger.info("Discovered plugins:")
        for plugin_type, plugins in self.plugins.items():
            if plugins:
                self.logger.info(f"  {plugin_type}:")
                for plugin_name in plugins:
                    self.logger.info(f"    - {plugin_name}")
    
    def _find_plugin_classes(self, module, base_class_name):
        """
        Find classes in the module that derive from the specified base class.
        
        Args:
            module: Module to search in
            base_class_name: Name of the base class
            
        Returns:
            list: List of (class_name, class) tuples
        """
        result = []
        
        # Tìm tất cả các lớp trong module
        for item_name, item in inspect.getmembers(module, inspect.isclass):
            # Bỏ qua các lớp không được định nghĩa trong module này
            if item.__module__ != module.__name__:
                continue
                
            # Bỏ qua các lớp base
            if item_name.startswith('Base'):
                continue
                
            # Kiểm tra có phải là lớp con của base class không
            is_derived = False
            for base_class in item.__mro__[1:]:  # Bỏ qua lớp hiện tại
                if base_class.__name__ == base_class_name:
                    is_derived = True
                    break
                    
            if is_derived:
                result.append((item_name, item))
                
        return result
        
    def load_plugin(self, plugin_type, plugin_name):
        """
        Load a plugin module by type and name.
        
        Args:
            plugin_type (str): Type of plugin (readers, writers, etc.)
            plugin_name (str): Name of the plugin to load
            
        Returns:
            dict: Plugin info including module and class, or None if not found
        """
        # Check if plugin type is valid
        if plugin_type not in self.plugins:
            raise ValueError(f"Invalid plugin type: {plugin_type}")
        
        # Check if plugin exists
        if plugin_name not in self.plugins[plugin_type]:
            # Thử tìm plugin không phân biệt hoa thường
            for name in self.plugins[plugin_type]:
                if name.lower() == plugin_name.lower():
                    self.logger.info(f"Using plugin {name} instead of {plugin_name} (case insensitive match)")
                    return self.plugins[plugin_type][name]
                    
            raise ValueError(f"Plugin {plugin_name} not found in {plugin_type}")
        
        # Return plugin info
        return self.plugins[plugin_type][plugin_name]
    
    def create_plugin_instance(self, plugin_type, plugin_name, config=None):
        """
        Create an instance of a plugin with the provided configuration.
        
        Args:
            plugin_type (str): Type of plugin (readers, writers, etc.)
            plugin_name (str): Name of the plugin to instantiate
            config (dict, optional): Configuration for the plugin
            
        Returns:
            object: Instance of the plugin
        """
        # Tìm cách khác nếu không tìm thấy plugin theo tên chính xác
        if plugin_type in self.plugins and plugin_name not in self.plugins[plugin_type]:
            # Tìm không phân biệt hoa thường
            for name in self.plugins[plugin_type]:
                if name.lower() == plugin_name.lower():
                    plugin_name = name
                    self.logger.info(f"Using plugin {name} instead of {plugin_name} (case insensitive match)")
                    break
            
            # Nếu vẫn không tìm thấy, thử tạo trực tiếp
            if plugin_name not in self.plugins[plugin_type]:
                return self._create_plugin_directly(plugin_type, plugin_name, config)
        
        # Load plugin info
        try:
            plugin_info = self.load_plugin(plugin_type, plugin_name)
        except ValueError as e:
            self.logger.warning(f"Plugin not found: {str(e)}")
            return self._create_plugin_directly(plugin_type, plugin_name, config)
        
        # Create instance
        try:
            plugin_class = plugin_info['class']
            if config is None:
                instance = plugin_class()
            else:
                instance = plugin_class(config)
                
            self.logger.info(f"Created instance of {plugin_type} plugin: {plugin_name}")
            return instance
            
        except Exception as e:
            self.logger.error(f"Failed to instantiate plugin {plugin_name}: {str(e)}")
            raise RuntimeError(f"Error instantiating plugin {plugin_name}: {str(e)}")
    
    def _create_plugin_directly(self, plugin_type, plugin_name, config=None):
        """
        Try to create plugin instance directly by finding file and dynamically loading.
        
        Args:
            plugin_type (str): Type of plugin (readers, writers, etc.)
            plugin_name (str): Name of the plugin to instantiate
            config (dict, optional): Configuration for the plugin
            
        Returns:
            object: Instance of the plugin
        """
        self.logger.info(f"Attempting to create {plugin_name} of type {plugin_type} directly")
        
        # Khởi tạo tên file từ tên plugin
        snake_case_name = ''.join(['_' + c.lower() if c.isupper() else c for c in plugin_name]).lower().lstrip('_')
        
        for plugin_dir in self.plugin_dirs:
            # Kiểm tra nếu thư mục phù hợp với loại plugin
            if plugin_type.lower() in plugin_dir.lower():
                # Thử các khả năng tên file khác nhau
                file_variants = [
                    f"{snake_case_name}.py",
                    f"{plugin_name.lower()}.py",
                    f"{plugin_name}.py"
                ]
                
                for file_name in file_variants:
                    file_path = os.path.join(plugin_dir, file_name)
                    if os.path.exists(file_path):
                        self.logger.info(f"Found plugin file: {file_path}")
                        
                        try:
                            # Tạo tên module
                            module_name = f"{plugin_type}.{file_name[:-3]}"
                            
                            # Tải module
                            spec = importlib.util.spec_from_file_location(module_name, file_path)
                            module = importlib.util.module_from_spec(spec)
                            spec.loader.exec_module(module)
                            
                            # Tìm lớp plugin
                            for item_name, item in inspect.getmembers(module, inspect.isclass):
                                # Kiểm tra tên lớp
                                if item_name == plugin_name or item_name.lower() == plugin_name.lower():
                                    # Tạo instance
                                    if config is None:
                                        instance = item()
                                    else:
                                        instance = item(config)
                                        
                                    # Thêm vào danh sách plugins
                                    self.plugins[plugin_type][item_name] = {
                                        'file_path': file_path,
                                        'module': module,
                                        'class': item
                                    }
                                    
                                    self.logger.info(f"Created instance of {plugin_type} plugin: {item_name}")
                                    return instance
                            
                            # Không tìm thấy lớp với tên chính xác, thử lớp đầu tiên phù hợp
                            base_class_name = self.base_classes.get(plugin_type)
                            plugin_classes = self._find_plugin_classes(module, base_class_name)
                            
                            if plugin_classes:
                                item_name, item = plugin_classes[0]
                                self.logger.info(f"Using {item_name} class for {plugin_name}")
                                
                                # Tạo instance
                                if config is None:
                                    instance = item()
                                else:
                                    instance = item(config)
                                    
                                # Thêm vào danh sách plugins
                                self.plugins[plugin_type][item_name] = {
                                    'file_path': file_path,
                                    'module': module,
                                    'class': item
                                }
                                
                                self.logger.info(f"Created instance of {plugin_type} plugin: {item_name}")
                                return instance
                                
                        except Exception as e:
                            self.logger.error(f"Error creating plugin from {file_path}: {str(e)}")
        
        # Không tìm thấy plugin, tạo mock nếu cần thiết
        return self._create_mock_plugin(plugin_type, plugin_name, config)
    
    def _create_mock_plugin(self, plugin_type, plugin_name, config=None):
        """
        Create a mock plugin as a fallback.
        
        Args:
            plugin_type (str): Type of plugin
            plugin_name (str): Name of the plugin
            config (dict, optional): Configuration
            
        Returns:
            object: A mock plugin instance
        """
        self.logger.warning(f"Creating MOCK plugin for {plugin_name} of type {plugin_type}")
        
        # Các plugin cơ bản
        if plugin_type == "readers":
            class MockReader:
                def __init__(self, config=None):
                    self.config = config or {}
                    self.logger = logging.getLogger(f"Mock{plugin_name}")
                    self.logger.warning(f"Using mock {plugin_name} - functionality limited")
                    
                def open(self):
                    self.logger.warning("Mock reader - open() called")
                    return True
                    
                def read(self):
                    self.logger.warning("Mock reader - read() called")
                    # Return mock data
                    return {"mock": "data", "timestamp": 0}
                    
                def close(self):
                    self.logger.warning("Mock reader - close() called")
                    return True
                    
            return MockReader(config)
            
        elif plugin_type == "writers":
            class MockWriter:
                def __init__(self, config=None):
                    self.config = config or {}
                    self.logger = logging.getLogger(f"Mock{plugin_name}")
                    self.logger.warning(f"Using mock {plugin_name} - functionality limited")
                    
                def open(self):
                    self.logger.warning("Mock writer - open() called")
                    return True
                    
                def write(self, data):
                    self.logger.warning(f"Mock writer - write() called with: {data}")
                    return True
                    
                def close(self):
                    self.logger.warning("Mock writer - close() called")
                    return True
                    
            return MockWriter(config)
            
        elif plugin_type == "configurators":
            class MockConfigurator:
                def __init__(self, config=None):
                    self.config = config or {}
                    self.logger = logging.getLogger(f"Mock{plugin_name}")
                    self.logger.warning(f"Using mock {plugin_name} - functionality limited")
                    
                def configure(self):
                    self.logger.warning(f"Mock configurator - configure() called with: {self.config}")
                    return True
                    
            return MockConfigurator(config)
            
        elif plugin_type == "decoders":
            class MockDecoder:
                def __init__(self, config=None):
                    self.config = config or {}
                    self.logger = logging.getLogger(f"Mock{plugin_name}")
                    self.logger.warning(f"Using mock {plugin_name} - functionality limited")
                    
                def decode(self, data):
                    self.logger.warning(f"Mock decoder - decode() called with: {data}")
                    return {"mock": "decoded_data"}
                    
            return MockDecoder(config)
            
        # Không hỗ trợ các loại plugin khác
        raise RuntimeError(f"Cannot create mock for unknown plugin type: {plugin_type}")
    
    def get_available_plugins(self, plugin_type=None):
        """
        Get a list of available plugins.
        
        Args:
            plugin_type (str, optional): Type of plugins to list
            
        Returns:
            dict or list: Available plugins
        """
        if plugin_type:
            if plugin_type not in self.plugins:
                return []
            return list(self.plugins[plugin_type].keys())
        else:
            result = {}
            for type_name, plugins in self.plugins.items():
                result[type_name] = list(plugins.keys())
            return result
        
    def get_or_create_plugin(self, plugin_type, plugin_name, config=None):
        """
        Get an existing plugin or create a new instance if not found.
        
        Args:
            plugin_type (str): Type of plugin
            plugin_name (str): Name of the plugin
            config (dict, optional): Configuration for the plugin
        
        Returns:
            object: Plugin instance
        """
        try:
            # Thử tìm plugin đã tồn tại
            try:
                return self.create_plugin_instance(plugin_type, plugin_name, config)
            except Exception:
                # Nếu không tìm thấy, tạo mock plugin
                return self._create_mock_plugin(plugin_type, plugin_name, config)
        except Exception as e:
            self.logger.error(f"Error in get_or_create_plugin for {plugin_type}/{plugin_name}: {str(e)}")
            return None
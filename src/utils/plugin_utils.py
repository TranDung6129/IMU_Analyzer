# File: src/utils/plugin_utils.py
# Purpose: Plugin validation and management utilities
# Target Lines: ≤150

"""
Methods to implement:
- validate_plugin(plugin): Check if a plugin meets requirements
"""

import inspect
import logging


def validate_plugin(plugin, base_class=None, required_methods=None):
    """
    Validate if a plugin meets the requirements.
    
    Args:
        plugin (object): Plugin instance or class to validate
        base_class (class, optional): Base class that plugin should inherit from
        required_methods (list, optional): List of method names that plugin must implement
        
    Returns:
        tuple: (is_valid, error_messages)
            - is_valid (bool): True if plugin is valid
            - error_messages (list): List of validation error messages
    """
    errors = []
    
    # Get the class (if plugin is an instance, get its class)
    plugin_class = plugin if inspect.isclass(plugin) else plugin.__class__
    
    # Check base class
    if base_class and not issubclass(plugin_class, base_class):
        errors.append(f"Plugin {plugin_class.__name__} does not inherit from {base_class.__name__}")
    
    # Check required methods
    if required_methods:
        for method_name in required_methods:
            if not hasattr(plugin, method_name) or not callable(getattr(plugin, method_name)):
                errors.append(f"Plugin {plugin_class.__name__} missing required method: {method_name}")
    
    is_valid = len(errors) == 0
    return is_valid, errors


# Additional utility functions (not implemented yet, just signatures)

# TODO: Implement plugin discovery function
# def discover_plugins(directory, base_class):
#     pass

# TODO: Implement plugin loading function
# def load_plugin(plugin_path, plugin_name):
#     pass

# TODO: Implement plugin version check
# def check_plugin_version(plugin, min_version):
#     pass

# How to extend and modify:
# 1. Add version checking: Add functionality to check plugin version compatibility
# 2. Add signature validation: Check method signatures match expected signatures
# 3. Add plugin dependencies: Add functionality to manage plugin dependencies
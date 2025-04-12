# File: src/utils/config_utils.py
# Purpose: Configuration handling utilities
# Target Lines: ≤150

"""
Methods to implement:
- merge_configs(default_config, override_config): Merge configuration dictionaries
"""

import logging


def merge_configs(default_config, override_config):
    """
    Recursively merge two configuration dictionaries.
    Values in override_config take precedence over values in default_config.
    
    Args:
        default_config (dict): Base configuration
        override_config (dict): Configuration to override with
        
    Returns:
        dict: Merged configuration
    """
    if not isinstance(default_config, dict) or not isinstance(override_config, dict):
        return override_config
    
    merged = default_config.copy()
    
    for key, value in override_config.items():
        if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
            # Recursively merge nested dictionaries
            merged[key] = merge_configs(merged[key], value)
        else:
            # Override or add new value
            merged[key] = value
    
    return merged


# Additional utility functions (not implemented yet, just signatures)

# TODO: Implement config validation function
# def validate_config(config, schema):
#     pass

# TODO: Implement config from environment variables
# def config_from_env(prefix="IMU_"):
#     pass

# TODO: Implement config defaults application
# def apply_defaults(config, defaults):
#     pass

# How to extend and modify:
# 1. Add config validation: Add schema-based validation
# 2. Add environment variables: Create function to load config from environment variables
# 3. Add config file watching: Add functionality to reload on config file changes
# File: src/utils/file_utils.py
# Purpose: File operations utilities
# Target Lines: ≤150

"""
Methods to implement:
- read_file(file_path): Read content from a file
- write_file(file_path, content): Write content to a file
"""

import os
import json
import yaml
import logging


def read_file(file_path, encoding="utf-8"):
    """
    Read content from a file.
    
    Args:
        file_path (str): Path to the file
        encoding (str): File encoding, default is utf-8
        
    Returns:
        str: File content
        
    Raises:
        FileNotFoundError: If file does not exist
        IOError: If file cannot be read
    """
    try:
        with open(file_path, 'r', encoding=encoding) as file:
            return file.read()
    except FileNotFoundError:
        logging.error(f"File not found: {file_path}")
        raise
    except IOError as e:
        logging.error(f"Error reading file {file_path}: {str(e)}")
        raise


def write_file(file_path, content, encoding="utf-8", create_dirs=True):
    """
    Write content to a file.
    
    Args:
        file_path (str): Path to the file
        content (str): Content to write
        encoding (str): File encoding, default is utf-8
        create_dirs (bool): Whether to create parent directories if they don't exist
        
    Returns:
        bool: True if successful
        
    Raises:
        IOError: If file cannot be written
    """
    try:
        if create_dirs:
            directory = os.path.dirname(file_path)
            if directory and not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)
                
        with open(file_path, 'w', encoding=encoding) as file:
            file.write(content)
        return True
    except IOError as e:
        logging.error(f"Error writing to file {file_path}: {str(e)}")
        raise


# Additional utility functions (not implemented yet, just signatures)

# TODO: Implement YAML read/write functions
# def read_yaml(file_path):
#     pass

# TODO: Implement JSON read/write functions
# def read_json(file_path):
#     pass

# TODO: Implement file existence check with logging
# def check_file_exists(file_path, raise_error=False):
#     pass

# How to extend and modify:
# 1. Add binary file handling: Add read_binary_file and write_binary_file functions
# 2. Add file backup: Create a function to backup files before modifying
# 3. Add file watching: Implement a file watcher for config changes
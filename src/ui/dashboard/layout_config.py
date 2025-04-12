# File: src/ui/dashboard/layout_config.py
# Purpose: Save and load dashboard layout configurations
# Target Lines: ≤150

"""
Methods to implement:
- __init__(self, config_dir='config'): Initialize with configuration directory
- save(self, layout_data, name='default'): Save layout data to a file
- load(self, name='default'): Load layout data from a file
"""

import os
import json
import logging
import time
from datetime import datetime


class LayoutConfig:
    """
    Handles saving and loading dashboard layout configurations.
    Supports multiple layouts with versioning.
    """
    
    def __init__(self, config_dir='config'):
        """
        Initialize the layout configuration manager.
        
        Args:
            config_dir (str, optional): Directory for layout files
        """
        self.config_dir = config_dir
        self.layout_dir = os.path.join(config_dir, 'layouts')
        self.logger = logging.getLogger("LayoutConfig")
        
        # Ensure directories exist
        self._ensure_directories()
        
        # Track loaded layout
        self.current_layout = None
        self.current_layout_name = None
        
        self.logger.info("LayoutConfig initialized with directory: %s", self.layout_dir)
    
    def _ensure_directories(self):
        """Ensure that the necessary directories exist."""
        try:
            os.makedirs(self.layout_dir, exist_ok=True)
            self.logger.debug("Ensured layout directory exists: %s", self.layout_dir)
        except Exception as e:
            self.logger.error("Failed to create layout directory: %s", str(e))
    
    def save(self, layout_data, name='default'):
        """
        Save layout data to a file.
        
        Args:
            layout_data (dict): Layout data to save
            name (str, optional): Layout name
            
        Returns:
            str: Path to saved file, or None if failed
        """
        try:
            # Generate filename with timestamp for versioning
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{name}_{timestamp}.json"
            filepath = os.path.join(self.layout_dir, filename)
            
            # Enhance layout data with metadata
            enhanced_data = {
                'metadata': {
                    'name': name,
                    'timestamp': timestamp,
                    'created': datetime.now().isoformat(),
                    'version': '1.0'
                },
                'layout': layout_data
            }
            
            # Write to file
            with open(filepath, 'w') as f:
                json.dump(enhanced_data, f, indent=2)
            
            # Create/update symlink to latest version
            latest_link = os.path.join(self.layout_dir, f"{name}_latest.json")
            
            # On Windows, symlinks may not be available, so we'll create a copy
            try:
                if os.path.exists(latest_link):
                    os.remove(latest_link)
                
                # Try to create symlink first (Unix)
                try:
                    os.symlink(filepath, latest_link)
                except (OSError, AttributeError):
                    # If symlink fails (Windows), create a copy
                    with open(latest_link, 'w') as f:
                        json.dump(enhanced_data, f, indent=2)
            except Exception as e:
                self.logger.warning("Failed to create latest symlink: %s", str(e))
            
            self.logger.info("Saved layout '%s' to %s", name, filepath)
            self.current_layout = enhanced_data
            self.current_layout_name = name
            
            return filepath
        except Exception as e:
            self.logger.error("Failed to save layout '%s': %s", name, str(e))
            return None
    
    def load(self, name='default'):
        """
        Load layout data from a file.
        
        Args:
            name (str, optional): Layout name
            
        Returns:
            dict: Layout data, or None if failed
        """
        try:
            # Try to load the latest version first
            latest_link = os.path.join(self.layout_dir, f"{name}_latest.json")
            
            if os.path.exists(latest_link):
                with open(latest_link, 'r') as f:
                    data = json.load(f)
                
                self.logger.info("Loaded latest layout '%s' from %s", name, latest_link)
                self.current_layout = data
                self.current_layout_name = name
                
                return data.get('layout', {})
            
            # If latest doesn't exist, find most recent version
            files = [f for f in os.listdir(self.layout_dir) 
                    if f.startswith(f"{name}_") and f.endswith('.json') and not f.endswith('_latest.json')]
            
            if not files:
                self.logger.warning("No layout files found for name '%s'", name)
                return None
            
            # Sort by timestamp (part of filename)
            files.sort(reverse=True)
            latest_file = os.path.join(self.layout_dir, files[0])
            
            with open(latest_file, 'r') as f:
                data = json.load(f)
            
            self.logger.info("Loaded layout '%s' from %s", name, latest_file)
            self.current_layout = data
            self.current_layout_name = name
            
            return data.get('layout', {})
            
        except Exception as e:
            self.logger.error("Failed to load layout '%s': %s", name, str(e))
            return None
    
    def list_layouts(self):
        """
        List available layout names.
        
        Returns:
            list: List of available layout names
        """
        try:
            # Find all unique layout names
            layouts = set()
            
            for filename in os.listdir(self.layout_dir):
                if filename.endswith('.json'):
                    # Extract name from filename (before the first underscore)
                    parts = filename.split('_', 1)
                    if len(parts) > 0:
                        layouts.add(parts[0])
            
            return list(layouts)
        except Exception as e:
            self.logger.error("Failed to list layouts: %s", str(e))
            return []
    
    def delete_layout(self, name):
        """
        Delete all versions of a layout.
        
        Args:
            name (str): Layout name
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            deleted = 0
            
            for filename in os.listdir(self.layout_dir):
                if filename.startswith(f"{name}_") and filename.endswith('.json'):
                    filepath = os.path.join(self.layout_dir, filename)
                    os.remove(filepath)
                    deleted += 1
            
            if deleted > 0:
                self.logger.info("Deleted %d files for layout '%s'", deleted, name)
                return True
            else:
                self.logger.warning("No files found for layout '%s'", name)
                return False
        except Exception as e:
            self.logger.error("Failed to delete layout '%s': %s", name, str(e))
            return False


# How to modify functionality:
# 1. Add export/import: Add methods to export/import layouts to/from external files
# 2. Add template support: Add methods to create layouts from templates
# 3. Add backup/restore: Add methods to backup all layouts and restore from backup
# 4. Add layout merge: Add methods to merge multiple layouts
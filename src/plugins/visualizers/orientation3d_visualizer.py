# File: src/plugins/visualizers/orientation3d_visualizer.py
# Purpose: Visualize 3D orientation of IMU sensors
# Target Lines: ≤150

"""
Methods to implement:
- __init__(self, config=None): Initialize with optional configuration
- init(self, config): Initialize or re-initialize with new configuration
- visualize(self, data): Process and prepare 3D orientation data for visualization
- destroy(self): Clean up resources
"""

import logging
import numpy as np
from src.plugins.visualizers.base_visualizer import BaseVisualizer


class Orientation3DVisualizer(BaseVisualizer):
    """
    Visualizer for 3D orientation of IMU sensors.
    
    Prepares data for 3D visualization of sensor orientation using
    roll, pitch, and yaw angles.
    """
    
    def __init__(self, config=None):
        """
        Initialize the 3D orientation visualizer with optional configuration.
        
        Args:
            config (dict, optional): Configuration with the following keys:
                - model_type (str): 3D model to display ('cube', 'aircraft', 'arrow') (default: 'cube')
                - use_quaternion (bool): Use quaternions instead of Euler angles (default: False)
                - auto_rotate (bool): Auto-rotate the model for better visualization (default: False)
                - show_axes (bool): Show coordinate axes (default: True)
                - show_trails (bool): Show motion trails (default: False)
                - trail_length (int): Number of points in motion trail (default: 50)
                - model_color (str): Color of the 3D model (default: '#1f77b4')
                - background_color (str): Background color (default: '#f8f9fa')
        """
        super().__init__(config)
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Initialize with default settings
        self.model_type = 'cube'
        self.use_quaternion = False
        self.auto_rotate = False
        self.show_axes = True
        self.show_trails = False
        self.trail_length = 50
        self.model_color = '#1f77b4'
        self.background_color = '#f8f9fa'
        
        # Current orientation state
        self.roll = 0.0
        self.pitch = 0.0
        self.yaw = 0.0
        self.quaternion = [1.0, 0.0, 0.0, 0.0]  # w, x, y, z
        
        # Motion trails
        self.trail_positions = []
        
        # Camera settings
        self.camera_distance = 5.0
        self.camera_elevation = 30.0
        self.camera_azimuth = 45.0
        
        # Update with provided configuration
        if config:
            self.init(config)
    
    def init(self, config):
        """
        Initialize or re-initialize the visualizer with the specified configuration.
        
        Args:
            config (dict): Configuration dictionary
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not isinstance(config, dict):
            self.set_error("Configuration must be a dictionary")
            return False
        
        # Update model type
        if 'model_type' in config:
            model_type = str(config['model_type']).lower()
            if model_type in ['cube', 'aircraft', 'arrow']:
                self.model_type = model_type
            else:
                self.logger.warning(f"Unsupported model type: {model_type}, using 'cube'")
        
        # Update quaternion usage
        if 'use_quaternion' in config:
            self.use_quaternion = bool(config['use_quaternion'])
        
        # Update auto-rotate
        if 'auto_rotate' in config:
            self.auto_rotate = bool(config['auto_rotate'])
        
        # Update show axes
        if 'show_axes' in config:
            self.show_axes = bool(config['show_axes'])
        
        # Update show trails
        if 'show_trails' in config:
            self.show_trails = bool(config['show_trails'])
        
        # Update trail length
        if 'trail_length' in config:
            try:
                trail_length = int(config['trail_length'])
                if trail_length < 1:
                    self.logger.warning("trail_length must be positive, using default")
                else:
                    self.trail_length = trail_length
            except (ValueError, TypeError):
                self.logger.warning("Invalid trail_length value, using default")
        
        # Update model color
        if 'model_color' in config:
            self.model_color = str(config['model_color'])
        
        # Update background color
        if 'background_color' in config:
            self.background_color = str(config['background_color'])
        
        # Update camera settings
        if 'camera_distance' in config:
            try:
                self.camera_distance = float(config['camera_distance'])
            except (ValueError, TypeError):
                self.logger.warning("Invalid camera_distance value, using default")
        
        if 'camera_elevation' in config:
            try:
                self.camera_elevation = float(config['camera_elevation'])
            except (ValueError, TypeError):
                self.logger.warning("Invalid camera_elevation value, using default")
        
        if 'camera_azimuth' in config:
            try:
                self.camera_azimuth = float(config['camera_azimuth'])
            except (ValueError, TypeError):
                self.logger.warning("Invalid camera_azimuth value, using default")
        
        # Reset trails if settings changed
        if self.show_trails:
            self.trail_positions = []
        
        self.initialized = True
        self.clear_error()
        return True
    
    def visualize(self, data):
        """
        Process and prepare 3D orientation data for visualization.
        
        Args:
            data (dict): Processed data with orientation values
            
        Returns:
            dict: 3D visualization data ready for the UI
            
        Raises:
            ValueError: If the data doesn't contain the required fields
        """
        if not self.initialized:
            raise RuntimeError("Visualizer not initialized")
        
        if not isinstance(data, dict):
            self.set_error("Data must be a dictionary")
            return None
        
        # Update orientation from Euler angles or quaternion
        if self.use_quaternion:
            # Use quaternion if available
            if 'quaternion' in data and isinstance(data['quaternion'], (list, tuple)) and len(data['quaternion']) == 4:
                self.quaternion = [float(q) for q in data['quaternion']]
                # Convert quaternion to Euler angles for reference
                self.roll, self.pitch, self.yaw = self._quaternion_to_euler(self.quaternion)
            else:
                # Fall back to Euler angles if quaternion not available
                self._update_euler_angles(data)
                # Convert Euler angles to quaternion
                self.quaternion = self._euler_to_quaternion(self.roll, self.pitch, self.yaw)
        else:
            # Use Euler angles
            self._update_euler_angles(data)
            # Convert Euler angles to quaternion for reference
            self.quaternion = self._euler_to_quaternion(self.roll, self.pitch, self.yaw)
        
        # Update motion trail if enabled
        if self.show_trails:
            # Calculate 3D position (simplified, just for visualization)
            position = [
                np.sin(np.radians(self.yaw)) * np.cos(np.radians(self.pitch)),
                np.cos(np.radians(self.yaw)) * np.cos(np.radians(self.pitch)),
                np.sin(np.radians(self.pitch))
            ]
            
            # Add to trail positions
            self.trail_positions.append(position)
            
            # Limit trail length
            if len(self.trail_positions) > self.trail_length:
                self.trail_positions = self.trail_positions[-self.trail_length:]
        
        # Prepare rotation matrix for 3D visualization
        rotation_matrix = self._get_rotation_matrix()
        
        # Prepare model points based on model type
        model_points = self._get_model_points()
        
        # Prepare visualization data for UI
        viz_data = {
            'type': '3d_orientation',
            'model_type': self.model_type,
            'euler_angles': {
                'roll': self.roll,
                'pitch': self.pitch,
                'yaw': self.yaw
            },
            'quaternion': self.quaternion,
            'rotation_matrix': rotation_matrix.tolist(),
            'model_points': model_points,
            'model_color': self.model_color,
            'background_color': self.background_color,
            'show_axes': self.show_axes,
            'auto_rotate': self.auto_rotate,
            'camera': {
                'distance': self.camera_distance,
                'elevation': self.camera_elevation,
                'azimuth': self.camera_azimuth
            }
        }
        
        # Add trail data if enabled
        if self.show_trails:
            viz_data['show_trails'] = True
            viz_data['trail_positions'] = self.trail_positions
        else:
            viz_data['show_trails'] = False
        
        # Update the data buffer for access by UI
        self.data_buffer = viz_data
        
        # Update visualize count
        super().visualize(data)
        
        return viz_data
    
    def _update_euler_angles(self, data):
        """Update Euler angles from data"""
        # Update roll
        if 'roll' in data:
            try:
                self.roll = float(data['roll'])
            except (ValueError, TypeError):
                self.logger.debug("Invalid roll value")
        
        # Update pitch
        if 'pitch' in data:
            try:
                self.pitch = float(data['pitch'])
            except (ValueError, TypeError):
                self.logger.debug("Invalid pitch value")
        
        # Update yaw
        if 'yaw' in data:
            try:
                self.yaw = float(data['yaw'])
            except (ValueError, TypeError):
                self.logger.debug("Invalid yaw value")
    
    def _euler_to_quaternion(self, roll, pitch, yaw):
        """
        Convert Euler angles to quaternion.
        
        Args:
            roll (float): Roll angle in degrees
            pitch (float): Pitch angle in degrees
            yaw (float): Yaw angle in degrees
            
        Returns:
            list: Quaternion [w, x, y, z]
        """
        # Convert degrees to radians
        roll = np.radians(roll)
        pitch = np.radians(pitch)
        yaw = np.radians(yaw)
        
        # Calculate quaternion components
        cy = np.cos(yaw * 0.5)
        sy = np.sin(yaw * 0.5)
        cp = np.cos(pitch * 0.5)
        sp = np.sin(pitch * 0.5)
        cr = np.cos(roll * 0.5)
        sr = np.sin(roll * 0.5)
        
        w = cr * cp * cy + sr * sp * sy
        x = sr * cp * cy - cr * sp * sy
        y = cr * sp * cy + sr * cp * sy
        z = cr * cp * sy - sr * sp * cy
        
        return [w, x, y, z]
    
    def _quaternion_to_euler(self, q):
        """
        Convert quaternion to Euler angles.
        
        Args:
            q (list): Quaternion [w, x, y, z]
            
        Returns:
            tuple: (roll, pitch, yaw) in degrees
        """
        # Extract quaternion components
        w, x, y, z = q
        
        # Calculate Euler angles
        # Roll (x-axis rotation)
        sinr_cosp = 2 * (w * x + y * z)
        cosr_cosp = 1 - 2 * (x * x + y * y)
        roll = np.arctan2(sinr_cosp, cosr_cosp)
        
        # Pitch (y-axis rotation)
        sinp = 2 * (w * y - z * x)
        if abs(sinp) >= 1:
            # Use 90 degrees if out of range
            pitch = np.copysign(np.pi / 2, sinp)
        else:
            pitch = np.arcsin(sinp)
        
        # Yaw (z-axis rotation)
        siny_cosp = 2 * (w * z + x * y)
        cosy_cosp = 1 - 2 * (y * y + z * z)
        yaw = np.arctan2(siny_cosp, cosy_cosp)
        
        # Convert radians to degrees
        return np.degrees(roll), np.degrees(pitch), np.degrees(yaw)
    
    def _get_rotation_matrix(self):
        """
        Get rotation matrix based on current orientation.
        
        Returns:
            numpy.ndarray: 3x3 rotation matrix
        """
        if self.use_quaternion:
            # From quaternion
            w, x, y, z = self.quaternion
            
            # Calculate rotation matrix from quaternion
            rotation_matrix = np.array([
                [1 - 2*y*y - 2*z*z, 2*x*y - 2*z*w, 2*x*z + 2*y*w],
                [2*x*y + 2*z*w, 1 - 2*x*x - 2*z*z, 2*y*z - 2*x*w],
                [2*x*z - 2*y*w, 2*y*z + 2*x*w, 1 - 2*x*x - 2*y*y]
            ])
        else:
            # From Euler angles
            roll = np.radians(self.roll)
            pitch = np.radians(self.pitch)
            yaw = np.radians(self.yaw)
            
            # Calculate rotation matrices for each axis
            R_x = np.array([
                [1, 0, 0],
                [0, np.cos(roll), -np.sin(roll)],
                [0, np.sin(roll), np.cos(roll)]
            ])
            
            R_y = np.array([
                [np.cos(pitch), 0, np.sin(pitch)],
                [0, 1, 0],
                [-np.sin(pitch), 0, np.cos(pitch)]
            ])
            
            R_z = np.array([
                [np.cos(yaw), -np.sin(yaw), 0],
                [np.sin(yaw), np.cos(yaw), 0],
                [0, 0, 1]
            ])
            
            # Combine rotation matrices
            rotation_matrix = R_z @ R_y @ R_x
        
        return rotation_matrix
    
    def _get_model_points(self):
        """
        Get 3D model points based on model type.
        
        Returns:
            dict: Model vertices and faces
        """
        if self.model_type == 'cube':
            # Define cube vertices (corners)
            vertices = np.array([
                [-1, -1, -1],  # 0: left, bottom, back
                [1, -1, -1],   # 1: right, bottom, back
                [1, 1, -1],    # 2: right, top, back
                [-1, 1, -1],   # 3: left, top, back
                [-1, -1, 1],   # 4: left, bottom, front
                [1, -1, 1],    # 5: right, bottom, front
                [1, 1, 1],     # 6: right, top, front
                [-1, 1, 1]     # 7: left, top, front
            ])
            
            # Define faces (each face is defined by indices of its corners)
            faces = [
                [0, 1, 2, 3],  # back face
                [4, 5, 6, 7],  # front face
                [0, 1, 5, 4],  # bottom face
                [2, 3, 7, 6],  # top face
                [0, 3, 7, 4],  # left face
                [1, 2, 6, 5]   # right face
            ]
            
            return {'vertices': vertices.tolist(), 'faces': faces}
            
        elif self.model_type == 'aircraft':
            # Define aircraft-like model
            vertices = np.array([
                [0, 0, 0],     # 0: center
                [2, 0, 0],     # 1: nose
                [-2, 1, 0],    # 2: left tail
                [-2, -1, 0],   # 3: right tail
                [0, 2, 0],     # 4: left wing tip
                [0, -2, 0],    # 5: right wing tip
                [-1, 0, 1]     # 6: vertical stabilizer
            ])
            
            # Define faces
            faces = [
                [0, 1, 4],     # left wing
                [0, 1, 5],     # right wing
                [0, 2, 3],     # tail
                [0, 2, 6],     # left vertical
                [0, 3, 6],     # right vertical
                [1, 4, 5]      # front
            ]
            
            return {'vertices': vertices.tolist(), 'faces': faces}
            
        elif self.model_type == 'arrow':
            # Define arrow model
            vertices = np.array([
                [0, 0, 0],     # 0: base
                [1, 0, 0],     # 1: tip
                [0.7, 0.2, 0], # 2: right fin
                [0.7, -0.2, 0],# 3: left fin
                [0.7, 0, 0.2], # 4: top fin
                [0.7, 0, -0.2] # 5: bottom fin
            ])
            
            # Define faces
            faces = [
                [0, 1, 2],     # right side
                [0, 1, 3],     # left side
                [0, 1, 4],     # top side
                [0, 1, 5]      # bottom side
            ]
            
            return {'vertices': vertices.tolist(), 'faces': faces}
        
        # Default to cube if model type not recognized
        self.model_type = 'cube'
        return self._get_model_points()
    
    def destroy(self):
        """
        Clean up resources used by the visualizer.
        
        Returns:
            bool: True if successful, False otherwise
        """
        # Reset orientation
        self.roll = 0.0
        self.pitch = 0.0
        self.yaw = 0.0
        self.quaternion = [1.0, 0.0, 0.0, 0.0]
        
        # Clear motion trails
        self.trail_positions = []
        
        self.initialized = False
        self.clear_error()
        return True
    
    def set_camera_position(self, distance=None, elevation=None, azimuth=None):
        """
        Set camera position for 3D view.
        
        Args:
            distance (float, optional): Distance from center
            elevation (float, optional): Elevation angle in degrees
            azimuth (float, optional): Azimuth angle in degrees
            
        Returns:
            bool: True if any parameter was changed
        """
        changed = False
        
        if distance is not None:
            try:
                self.camera_distance = float(distance)
                changed = True
            except (ValueError, TypeError):
                self.logger.warning("Invalid distance value")
        
        if elevation is not None:
            try:
                self.camera_elevation = float(elevation)
                changed = True
            except (ValueError, TypeError):
                self.logger.warning("Invalid elevation value")
        
        if azimuth is not None:
            try:
                self.camera_azimuth = float(azimuth)
                changed = True
            except (ValueError, TypeError):
                self.logger.warning("Invalid azimuth value")
        
        return changed
    
    def get_orientation(self):
        """
        Get current orientation.
        
        Returns:
            dict: Current orientation in Euler angles and quaternion
        """
        return {
            'euler_angles': {
                'roll': self.roll,
                'pitch': self.pitch,
                'yaw': self.yaw
            },
            'quaternion': self.quaternion
        }


# How to extend and modify:
# 1. Add more model types: Add new model definitions in _get_model_points()
# 2. Add textures: Modify visualize() to include texture coordinates and materials
# 3. Add animations: Add methods to support animated transitions between orientations
# 4. Add sensor fusion: Implement sensor fusion algorithms for more accurate orientation tracking
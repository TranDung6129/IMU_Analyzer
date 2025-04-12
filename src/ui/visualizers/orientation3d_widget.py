# File: src/ui/visualizers/orientation3d_widget.py
# Purpose: Widget to display 3D orientation of IMU sensor
# Target Lines: ≤150

"""
Methods to implement:
- __init__(self, parent=None, config=None): Initialize with optional parent and config
- update_data(self, data): Update widget with new orientation data
- set_position(self, position): Set widget position
- set_size(self, size): Set widget size
- _setup_3d_view(self): Setup the 3D visualization
- _update_orientation(self): Update the 3D model with current orientation
- _create_cube_model(self): Create a 3D cube model for visualization
"""

# File: src/ui/visualizers/orientation3d_widget.py
# Purpose: Visualize 3D orientation using OpenGL
# Target Lines: <= 250 (Có thể tăng do OpenGL)

import logging
import numpy as np
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QCheckBox, QHBoxLayout, QComboBox
from PyQt6.QtCore import Qt, QTimer
# --- SỬA ĐỔI: Thêm import cho QOpenGLWidget ---
from PyQt6.QtOpenGLWidgets import QOpenGLWidget
# --- KẾT THÚC SỬA ĐỔI ---
from PyQt6.QtGui import QPainter, QColor, QFont, QMatrix4x4, QVector3D
# Cần import thư viện OpenGL (PyOpenGL)
try:
    from OpenGL import GL as gl
    from OpenGL import GLUT as glut # Có thể cần hoặc không
    OPENGL_AVAILABLE = True
except ImportError:
    logging.getLogger("Orientation3DWidget").error(
        "PyOpenGL or GLUT not found. Please install it: pip install PyOpenGL PyOpenGL_accelerate"
    )
    OPENGL_AVAILABLE = False
    # Định nghĩa lớp giả để tránh lỗi nếu OpenGL không có sẵn
    class QOpenGLWidget: pass # Dummy class

from src.ui.visualizers.base_widget import BaseWidget

class Orientation3DWidget(BaseWidget):
    """
    Widget to display 3D orientation of IMU sensor.
    
    Visualizes roll, pitch, and yaw angles as an interactive 3D model.
    """
    
    def __init__(self, parent=None, config=None):
        """
        Initialize the 3D orientation widget.
        
        Args:
            parent (QWidget, optional): Parent widget
            config (dict, optional): Widget configuration
        """
        # Default configuration
        default_config = {
            "title": "3D Orientation",
            "update_interval": 50,  # ms
            "show_axes": True,
            "show_labels": True,
            "model_type": "cube",  # cube, arrow, custom
            "background_color": [0.2, 0.2, 0.3, 1.0],
            "model_color": [0.8, 0.2, 0.2, 1.0],
            "rotation_order": "XYZ",  # Order to apply rotations
            "auto_rotate": False,  # Automatically rotate view
            "show_trail": False,  # Show motion trail
        }
        
        # Merge with provided config
        if config:
            default_config.update(config)
        
        super().__init__(parent, default_config)
        
        # Current orientation
        self.roll = 0.0  # X-axis rotation in degrees
        self.pitch = 0.0  # Y-axis rotation in degrees
        self.yaw = 0.0  # Z-axis rotation in degrees
        
        # Update timer
        self.update_timer = QTimer()
        self.update_timer.setInterval(self.config["update_interval"])
        self.update_timer.timeout.connect(self._update_orientation)
        
        # Setup 3D view
        self._setup_3d_view()
        
        # Start update timer
        self.update_timer.start()
        
        self.logger.info("Orientation3DWidget initialized")
    
    def _setup_3d_view(self):
        """
        Setup the 3D visualization.
        """
        # Check if OpenGL is available
        if not OPENGL_AVAILABLE:
            # Fallback to simple QLabel
            self.gl_widget = QLabel("OpenGL not available. Please install PyOpenGL for 3D visualization.")
            self.gl_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.gl_widget.setStyleSheet("background-color: #f0f0f0; border: 1px solid #ccc;")
            self.content_layout.addWidget(self.gl_widget)
            self.logger.warning("OpenGL not available, using fallback")
            return
        
        # Create OpenGL widget
        self.gl_widget = OrientationGLWidget(self.config)
        self.content_layout.addWidget(self.gl_widget)
        
        # Add controls
        self._setup_controls()
    
    def _setup_controls(self):
        """
        Setup control panel.
        """
        if not OPENGL_AVAILABLE:
            return
            
        # Create control panel
        control_panel = QHBoxLayout()
        
        # Model type selector
        model_label = QLabel("Model:")
        self.model_selector = QComboBox()
        self.model_selector.addItems(["Cube", "Arrow", "Coordinate Frame"])
        
        # Set current model type
        model_types = {"cube": 0, "arrow": 1, "coordinate": 2}
        self.model_selector.setCurrentIndex(model_types.get(self.config["model_type"].lower(), 0))
        
        # Show axes checkbox
        self.axes_cb = QCheckBox("Show Axes")
        self.axes_cb.setChecked(self.config["show_axes"])
        
        # Auto rotate checkbox
        self.rotate_cb = QCheckBox("Auto Rotate")
        self.rotate_cb.setChecked(self.config["auto_rotate"])
        
        # Add to control panel
        control_panel.addWidget(model_label)
        control_panel.addWidget(self.model_selector)
        control_panel.addStretch(1)
        control_panel.addWidget(self.axes_cb)
        control_panel.addWidget(self.rotate_cb)
        
        # Connect signals
        self.model_selector.currentIndexChanged.connect(self._on_model_changed)
        self.axes_cb.stateChanged.connect(self._on_axes_changed)
        self.rotate_cb.stateChanged.connect(self._on_rotate_changed)
        
        # Add to layout
        self.content_layout.addLayout(control_panel)
    
    def update_data(self, data):
        """
        Update the widget with new orientation data.
        
        Args:
            data (dict): New orientation data containing roll, pitch, yaw
        """
        # Call parent method
        super().update_data(data)
        
        # Extract orientation values
        if 'roll' in data:
            self.roll = data['roll']
        if 'pitch' in data:
            self.pitch = data['pitch']
        if 'yaw' in data:
            self.yaw = data['yaw']
            
        # Update GL widget if available
        if OPENGL_AVAILABLE and hasattr(self, 'gl_widget'):
            self.gl_widget.set_orientation(self.roll, self.pitch, self.yaw)
    
    def _update_orientation(self):
        """
        Update the 3D model with current orientation.
        """
        # For OpenGL widget, the update is handled in paintGL
        if OPENGL_AVAILABLE and hasattr(self, 'gl_widget'):
            self.gl_widget.update()
    
    def set_position(self, position):
        """
        Set the widget position in the grid.
        
        Args:
            position (tuple): Grid position as (row, column)
        """
        super().set_position(position)
    
    def set_size(self, size):
        """
        Set the widget size in the grid.
        
        Args:
            size (tuple): Grid size as (row_span, column_span)
        """
        super().set_size(size)
    
    def _on_model_changed(self, index):
        """
        Handle model type change.
        
        Args:
            index (int): Selected index
        """
        if not OPENGL_AVAILABLE:
            return
            
        # Map index to model type
        models = ["cube", "arrow", "coordinate"]
        self.config["model_type"] = models[index]
        
        # Update GL widget
        self.gl_widget.set_model_type(self.config["model_type"])
    
    def _on_axes_changed(self, state):
        """
        Handle show axes change.
        
        Args:
            state (int): Checkbox state
        """
        if not OPENGL_AVAILABLE:
            return
            
        self.config["show_axes"] = (state == Qt.CheckState.Checked.value)
        self.gl_widget.set_show_axes(self.config["show_axes"])
    
    def _on_rotate_changed(self, state):
        """
        Handle auto rotate change.
        
        Args:
            state (int): Checkbox state
        """
        if not OPENGL_AVAILABLE:
            return
            
        self.config["auto_rotate"] = (state == Qt.CheckState.Checked.value)
        self.gl_widget.set_auto_rotate(self.config["auto_rotate"])


class OrientationGLWidget(QOpenGLWidget):
    """
    OpenGL widget for 3D orientation visualization.
    """
    
    def __init__(self, config, parent=None):
        """
        Initialize the OpenGL widget.
        
        Args:
            config (dict): Widget configuration
            parent (QWidget, optional): Parent widget
        """
        if not OPENGL_AVAILABLE:
            return
            
        super().__init__(parent)
        self.config = config
        self.logger = logging.getLogger("OrientationGLWidget")
        
        # Current orientation
        self.roll = 0.0
        self.pitch = 0.0
        self.yaw = 0.0
        
        # View parameters
        self.xRot = 0
        self.yRot = 0
        self.zRot = 0
        self.zoom = -5.0
        
        # Auto rotation angle
        self.auto_angle = 0.0
        
        # Model attributes
        self.model_type = config["model_type"]
        self.show_axes = config["show_axes"]
        self.auto_rotate = config["auto_rotate"]
        
        self.logger.debug("OrientationGLWidget initialized")
    
    def set_orientation(self, roll, pitch, yaw):
        """
        Set the orientation.
        
        Args:
            roll (float): Roll angle in degrees
            pitch (float): Pitch angle in degrees
            yaw (float): Yaw angle in degrees
        """
        self.roll = roll
        self.pitch = pitch
        self.yaw = yaw
        
        # Request update
        self.update()
    
    def set_model_type(self, model_type):
        """
        Set the model type.
        
        Args:
            model_type (str): Model type (cube, arrow, coordinate)
        """
        self.model_type = model_type
        self.update()
    
    def set_show_axes(self, show_axes):
        """
        Set whether to show axes.
        
        Args:
            show_axes (bool): Whether to show axes
        """
        self.show_axes = show_axes
        self.update()
    
    def set_auto_rotate(self, auto_rotate):
        """
        Set whether to auto rotate.
        
        Args:
            auto_rotate (bool): Whether to auto rotate
        """
        self.auto_rotate = auto_rotate
        self.update()
    
    def initializeGL(self):
        """
        Initialize OpenGL.
        """
        # Basic OpenGL setup
        gl.glClearColor(0.2, 0.2, 0.3, 1.0)
        gl.glEnable(gl.GL_DEPTH_TEST)
        gl.glEnable(gl.GL_BLEND)
        gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)
    
    def paintGL(self):
        """
        Paint the scene.
        """
        # Clear the screen
        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
        
        # Update auto-rotation if enabled
        if self.auto_rotate:
            self.auto_angle += 0.5
            if self.auto_angle >= 360.0:
                self.auto_angle -= 360.0
        
        # Set up the view
        gl.glLoadIdentity()
        gl.glTranslatef(0.0, 0.0, self.zoom)
        
        # Apply auto-rotation if enabled
        if self.auto_rotate:
            gl.glRotatef(self.auto_angle, 0, 1, 0)
        
        # Apply user view rotation
        gl.glRotatef(self.xRot / 16.0, 1.0, 0.0, 0.0)
        gl.glRotatef(self.yRot / 16.0, 0.0, 1.0, 0.0)
        gl.glRotatef(self.zRot / 16.0, 0.0, 0.0, 1.0)
        
        # Draw axes if enabled
        if self.show_axes:
            self._draw_axes()
        
        # Apply sensor orientation
        gl.glRotatef(self.roll, 1.0, 0.0, 0.0)   # Roll around X axis
        gl.glRotatef(self.pitch, 0.0, 1.0, 0.0)  # Pitch around Y axis
        gl.glRotatef(self.yaw, 0.0, 0.0, 1.0)    # Yaw around Z axis
        
        # Draw the model
        if self.model_type == "cube":
            self._draw_cube()
        elif self.model_type == "arrow":
            self._draw_arrow()
        else:
            self._draw_coordinate_frame()
    
    def resizeGL(self, width, height):
        """
        Resize the viewport.
        
        Args:
            width (int): Viewport width
            height (int): Viewport height
        """
        side = min(width, height)
        gl.glViewport((width - side) // 2, (height - side) // 2, side, side)
        
        gl.glMatrixMode(gl.GL_PROJECTION)
        gl.glLoadIdentity()
        gl.glFrustum(-1.0, 1.0, -1.0, 1.0, 5.0, 60.0)
        gl.glMatrixMode(gl.GL_MODELVIEW)
    
    def _draw_axes(self):
        """Draw coordinate axes."""
        # Save current matrix
        gl.glPushMatrix()
        
        # Reset rotation
        gl.glLoadIdentity()
        gl.glTranslatef(0.0, 0.0, self.zoom)
        
        # Draw X axis (red)
        gl.glBegin(gl.GL_LINES)
        gl.glColor3f(1.0, 0.0, 0.0)
        gl.glVertex3f(0.0, 0.0, 0.0)
        gl.glVertex3f(2.0, 0.0, 0.0)
        gl.glEnd()
        
        # Draw Y axis (green)
        gl.glBegin(gl.GL_LINES)
        gl.glColor3f(0.0, 1.0, 0.0)
        gl.glVertex3f(0.0, 0.0, 0.0)
        gl.glVertex3f(0.0, 2.0, 0.0)
        gl.glEnd()
        
        # Draw Z axis (blue)
        gl.glBegin(gl.GL_LINES)
        gl.glColor3f(0.0, 0.0, 1.0)
        gl.glVertex3f(0.0, 0.0, 0.0)
        gl.glVertex3f(0.0, 0.0, 2.0)
        gl.glEnd()
        
        # Restore matrix
        gl.glPopMatrix()
    
    def _draw_cube(self):
        """Draw a cube."""
        # Define cube vertices
        vertices = [
            # Front face
            [-0.5, -0.5, 0.5], [0.5, -0.5, 0.5], [0.5, 0.5, 0.5], [-0.5, 0.5, 0.5],
            # Back face
            [-0.5, -0.5, -0.5], [0.5, -0.5, -0.5], [0.5, 0.5, -0.5], [-0.5, 0.5, -0.5]
        ]
        
        # Define cube faces (indices to vertices)
        faces = [
            [0, 1, 2, 3],  # Front
            [1, 5, 6, 2],  # Right
            [5, 4, 7, 6],  # Back
            [4, 0, 3, 7],  # Left
            [3, 2, 6, 7],  # Top
            [4, 5, 1, 0]   # Bottom
        ]
        
        # Define face colors (RGBA)
        colors = [
            [1.0, 0.0, 0.0, 1.0],  # Front: Red
            [0.0, 1.0, 0.0, 1.0],  # Right: Green
            [0.0, 0.0, 1.0, 1.0],  # Back: Blue
            [1.0, 1.0, 0.0, 1.0],  # Left: Yellow
            [0.0, 1.0, 1.0, 1.0],  # Top: Cyan
            [1.0, 0.0, 1.0, 1.0]   # Bottom: Magenta
        ]
        
        # Draw each face
        for i, face in enumerate(faces):
            gl.glColor4f(*colors[i])
            gl.glBegin(gl.GL_QUADS)
            for j in face:
                gl.glVertex3f(*vertices[j])
            gl.glEnd()
    
    def _draw_arrow(self):
        """Draw an arrow."""
        # Draw shaft
        gl.glColor4f(0.8, 0.8, 0.8, 1.0)
        
        # Draw as a cylinder
        # Simplified implementation - just a line
        gl.glBegin(gl.GL_LINES)
        gl.glVertex3f(0.0, 0.0, 0.0)
        gl.glVertex3f(0.0, 0.0, 1.0)
        gl.glEnd()
        
        # Draw arrowhead
        gl.glColor4f(1.0, 0.0, 0.0, 1.0)
        
        # Cone - simplified as triangle fan
        gl.glBegin(gl.GL_TRIANGLE_FAN)
        gl.glVertex3f(0.0, 0.0, 1.5)  # Tip
        
        # Base vertices
        for i in range(17):
            angle = i * (2.0 * math.pi / 16.0)
            x = 0.3 * math.cos(angle)
            y = 0.3 * math.sin(angle)
            gl.glVertex3f(x, y, 1.0)
        gl.glEnd()
    
    def _draw_coordinate_frame(self):
        """Draw a coordinate frame."""
        # X axis (red)
        gl.glColor3f(1.0, 0.0, 0.0)
        gl.glBegin(gl.GL_LINES)
        gl.glVertex3f(0.0, 0.0, 0.0)
        gl.glVertex3f(1.0, 0.0, 0.0)
        gl.glEnd()
        
        # Y axis (green)
        gl.glColor3f(0.0, 1.0, 0.0)
        gl.glBegin(gl.GL_LINES)
        gl.glVertex3f(0.0, 0.0, 0.0)
        gl.glVertex3f(0.0, 1.0, 0.0)
        gl.glEnd()
        
        # Z axis (blue)
        gl.glColor3f(0.0, 0.0, 1.0)
        gl.glBegin(gl.GL_LINES)
        gl.glVertex3f(0.0, 0.0, 0.0)
        gl.glVertex3f(0.0, 0.0, 1.0)
        gl.glEnd()
        
        # Small cubes at the end of each axis
        # X end
        gl.glPushMatrix()
        gl.glTranslatef(1.0, 0.0, 0.0)
        gl.glScalef(0.1, 0.1, 0.1)
        gl.glColor3f(1.0, 0.0, 0.0)
        self._draw_simple_cube()
        gl.glPopMatrix()
        
        # Y end
        gl.glPushMatrix()
        gl.glTranslatef(0.0, 1.0, 0.0)
        gl.glScalef(0.1, 0.1, 0.1)
        gl.glColor3f(0.0, 1.0, 0.0)
        self._draw_simple_cube()
        gl.glPopMatrix()
        
        # Z end
        gl.glPushMatrix()
        gl.glTranslatef(0.0, 0.0, 1.0)
        gl.glScalef(0.1, 0.1, 0.1)
        gl.glColor3f(0.0, 0.0, 1.0)
        self._draw_simple_cube()
        gl.glPopMatrix()
    
    def _draw_simple_cube(self):
        """Draw a simple single-color cube."""
        # Vertices of a cube
        gl.glBegin(gl.GL_QUADS)
        
        # Front face
        gl.glVertex3f(-1.0, -1.0, 1.0)
        gl.glVertex3f(1.0, -1.0, 1.0)
        gl.glVertex3f(1.0, 1.0, 1.0)
        gl.glVertex3f(-1.0, 1.0, 1.0)
        
        # Back face
        gl.glVertex3f(-1.0, -1.0, -1.0)
        gl.glVertex3f(-1.0, 1.0, -1.0)
        gl.glVertex3f(1.0, 1.0, -1.0)
        gl.glVertex3f(1.0, -1.0, -1.0)
        
        # Top face
        gl.glVertex3f(-1.0, 1.0, -1.0)
        gl.glVertex3f(-1.0, 1.0, 1.0)
        gl.glVertex3f(1.0, 1.0, 1.0)
        gl.glVertex3f(1.0, 1.0, -1.0)
        
        # Bottom face
        gl.glVertex3f(-1.0, -1.0, -1.0)
        gl.glVertex3f(1.0, -1.0, -1.0)
        gl.glVertex3f(1.0, -1.0, 1.0)
        gl.glVertex3f(-1.0, -1.0, 1.0)
        
        # Right face
        gl.glVertex3f(1.0, -1.0, -1.0)
        gl.glVertex3f(1.0, 1.0, -1.0)
        gl.glVertex3f(1.0, 1.0, 1.0)
        gl.glVertex3f(1.0, -1.0, 1.0)
        
        # Left face
        gl.glVertex3f(-1.0, -1.0, -1.0)
        gl.glVertex3f(-1.0, -1.0, 1.0)
        gl.glVertex3f(-1.0, 1.0, 1.0)
        gl.glVertex3f(-1.0, 1.0, -1.0)
        
        gl.glEnd()


# How to modify functionality:
# 1. Add more model types: Implement drawing for different models
# 2. Add camera controls: Add mouse interaction for rotation and zoom
# 3. Add annotations: Add methods to display orientation values
# 4. Add motion recording: Add methods to record and playback motion
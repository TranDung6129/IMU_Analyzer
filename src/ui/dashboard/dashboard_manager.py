# File: src/ui/dashboard/dashboard_manager.py
# Purpose: Manage dashboard layout and widgets
# Target Lines: ≤300

"""
Methods to implement:
- __init__(self, parent=None): Initialize with parent widget
- add_widget(self, widget, position=None, size=None): Add a widget to the dashboard
- enable_drag_and_drop(self): Enable drag and drop functionality for widgets
- save_layout(self, file_path): Save the current layout to a file
- load_layout(self, file_path): Load a layout from a file
- _init_from_config(self, config): Initialize the dashboard from configuration
"""

from PyQt6.QtWidgets import (QWidget, QGridLayout, QVBoxLayout, QHBoxLayout, 
                          QPushButton, QLabel, QFrame, QSplitter, QMessageBox)
from PyQt6.QtCore import Qt, QPoint, QSize, QRect, pyqtSignal, QTimer, QMimeData
from PyQt6.QtGui import QDrag, QCursor
import yaml
import os
import logging


class DashboardManager(QWidget):
    """
    Manages the dashboard layout, widgets, and interactions.
    Supports saving and loading layouts, drag and drop, and widget management.
    """
    
    layout_changed = pyqtSignal()  # Signal emitted when layout changes
    
    def __init__(self, parent=None):
        """
        Initialize the dashboard manager.
        
        Args:
            parent (QWidget, optional): Parent widget
        """
        super().__init__(parent)
        self.logger = logging.getLogger("DashboardManager")

        self.main_layout = QVBoxLayout(self)
        # ... (set margins, spacing) ...
        self._setup_toolbar()

        self.widget_manager = None
        self.dashboard_widget = QWidget()
        self.dashboard_layout = QGridLayout(self.dashboard_widget)
        # ... (set margins, spacing) ...
        self.main_layout.addWidget(self.dashboard_widget)

        self.widgets = {}
        self.next_widget_id = 0

        # --- SỬA ĐỔI: Khởi tạo các biến kéo thả ---
        self.drag_widget = None           # Widget hiện đang được kéo
        self.drag_start_position = None   # Vị trí chuột ban đầu khi bắt đầu kéo (so với widget)
        self.potential_drop_rect = None   # Hình chữ nhật chỉ báo vị trí thả tiềm năng
        self.drop_indicator = None        # Widget chỉ báo vị trí thả
        # Không cần is_dragging, drag_widget khác None là đủ
        # Không cần potential_drag_widget hay drag_start_pos (pos của widget)
        # --- KẾT THÚC SỬA ĐỔI ---

        self.setAcceptDrops(True) # Cho phép nhận drop
        self.dashboard_widget.setAcceptDrops(True) # Cho phép nhận drop

        self.logger.info("DashboardManager initialized")
    
    def _setup_toolbar(self):
        """
        Setup the toolbar with dashboard actions.
        """
        toolbar = QHBoxLayout()
        toolbar.setContentsMargins(5, 5, 5, 5)
        toolbar.setSpacing(10)
        
        # Add toolbar label
        label = QLabel("Dashboard")
        label.setStyleSheet("font-weight: bold;")
        toolbar.addWidget(label)
        
        # Add flexible space
        toolbar.addStretch(1)
        
        # Add save button
        save_button = QPushButton("Save Layout")
        save_button.clicked.connect(self._on_save_button_clicked)
        toolbar.addWidget(save_button)
        
        # Add load button
        load_button = QPushButton("Load Layout")
        load_button.clicked.connect(self._on_load_button_clicked)
        toolbar.addWidget(load_button)
        
        # Add new widget button
        add_widget_button = QPushButton("+ Widget")
        add_widget_button.clicked.connect(self._on_add_widget_button_clicked)
        toolbar.addWidget(add_widget_button)
        
        # Add toolbar to main layout
        self.main_layout.addLayout(toolbar)
    
    def add_widget(self, widget, position=None, size=None):
        """
        Add a widget to the dashboard.
        
        Args:
            widget (QWidget): Widget to add
            position (tuple, optional): Position as (row, column)
            size (tuple, optional): Size as (row_span, column_span)
            
        Returns:
            int: Widget ID
        """
        widget_id = self.next_widget_id
        self.next_widget_id += 1
        
        # If position not specified, find best position
        if position is None:
            position = self._find_best_position()
        
        # If size not specified, use default
        if size is None:
            size = (1, 1)
        
        # Add widget to layout
        row, col = position
        row_span, col_span = size
        
        # Make widget interactive
        widget.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        widget.setMouseTracking(True)
        
        # Add to grid layout
        self.dashboard_layout.addWidget(widget, row, col, row_span, col_span)
        
        # Store widget info
        self.widgets[widget_id] = {
            'widget': widget,
            'position': position,
            'size': size
        }
        
        self.logger.info(f"Added widget {widget_id} at position {position} with size {size}")
        self.layout_changed.emit()
        
        return widget_id
    
    def _find_best_position(self):
        """
        Find the best position for a new widget.
        
        Returns:
            tuple: Best position as (row, column)
        """
        # Default to top-left if no widgets
        if not self.widgets:
            return (0, 0)
        
        # Find the max row and column
        max_row = 0
        max_col = 0
        
        for widget_info in self.widgets.values():
            position = widget_info['position']
            size = widget_info['size']
            
            widget_row = position[0]
            widget_col = position[1]
            
            widget_row_end = widget_row + size[0]
            widget_col_end = widget_col + size[1]
            
            max_row = max(max_row, widget_row_end)
            max_col = max(max_col, widget_col_end)
        
        # Try to add to next column if there's space
        if max_col < 3:  # Limit to 4 columns
            return (0, max_col)
        
        # Otherwise add to next row
        return (max_row, 0)
    
    def enable_drag_and_drop(self):
        """
        Enable drag and drop functionality for widgets.
        """
        # Enable mouse tracking
        self.setMouseTracking(True)
        self.dashboard_widget.setMouseTracking(True)
        
        # Accept drag and drop
        self.setAcceptDrops(True)
        self.dashboard_widget.setAcceptDrops(True)
        
        # Setup grid visualization
        self._setup_grid_visualization()
        
        # Install event filter on all widgets
        for widget_id, widget_info in self.widgets.items():
            widget = widget_info['widget']
            widget.installEventFilter(self)
            
            # Set cursor to indicate draggable
            widget.setCursor(Qt.CursorShape.OpenHandCursor)
        
        self.logger.info("Drag and drop enabled")
        
    def _setup_grid_visualization(self):
        """
        Setup grid visualization for drag and drop.
        """
        # Grid settings
        self.grid_visible = False
        self.grid_color = Qt.GlobalColor.lightGray
        self.grid_cell_width = 240
        self.grid_cell_height = 160
        self.grid_rows = 4
        self.grid_cols = 3
        
        # Create grid overlay widget
        self.grid_overlay = QFrame(self.dashboard_widget)
        self.grid_overlay.setGeometry(0, 0, self.dashboard_widget.width(), self.dashboard_widget.height())
        self.grid_overlay.setStyleSheet("background-color: transparent;")
        self.grid_overlay.lower()  # Put behind other widgets
        self.grid_overlay.hide()
        
        # Grid visualization will be painted in paintEvent of overlay
        self.grid_overlay.paintEvent = self._paint_grid
        
    def _paint_grid(self, event):
        """
        Paint grid lines on overlay.
        
        Args:
            event: Paint event
        """
        if not self.grid_visible:
            return
            
        from PyQt6 import QtGui
        painter = QtGui.QPainter(self.grid_overlay)
        painter.setPen(QtGui.QPen(self.grid_color, 1, Qt.PenStyle.DashLine))
        
        # Draw horizontal grid lines
        for i in range(self.grid_rows + 1):
            y = i * self.grid_cell_height
            painter.drawLine(0, y, self.grid_overlay.width(), y)
        
        # Draw vertical grid lines
        for i in range(self.grid_cols + 1):
            x = i * self.grid_cell_width
            painter.drawLine(x, 0, x, self.grid_overlay.height())
        
    def eventFilter(self, obj, event):
        """
        Filter events for drag and drop.
        
        Args:
            obj: Object that received the event
            event: Event
            
        Returns:
            bool: True if event was handled, False otherwise
        """
        # Only process events for widgets in our dashboard
        widget_id = None
        for wid, widget_info in self.widgets.items():
            if widget_info['widget'] == obj:
                widget_id = wid
                break
                
        if widget_id is None:
            return False
        
        from PyQt6 import QtCore
            
        # Handle mouse press for drag start
        if event.type() == QtCore.QEvent.Type.MouseButtonPress and event.button() == Qt.MouseButton.LeftButton:
            self.drag_widget = obj
            self.drag_position = event.pos()
            self.drag_start_pos = obj.pos()
            
            # Show grid when dragging starts
            self.grid_visible = True
            self.grid_overlay.resize(self.dashboard_widget.size())
            self.grid_overlay.show()
            self.grid_overlay.update()
            
            # Change cursor to indicate dragging
            obj.setCursor(Qt.CursorShape.ClosedHandCursor)
            
            return True
            
        # Handle mouse release for drag end
        elif event.type() == QtCore.QEvent.Type.MouseButtonRelease and event.button() == Qt.MouseButton.LeftButton and self.drag_widget == obj:
            # Reset dragging state
            self.drag_widget = None
            self.drag_position = None
            
            # Hide grid when dragging ends
            self.grid_visible = False
            self.grid_overlay.hide()
            
            # Reset cursor
            obj.setCursor(Qt.CursorShape.OpenHandCursor)
            
            # Emit layout changed signal
            self.layout_changed.emit()
            
            return True
            
        # Handle mouse move for dragging
        elif event.type() == QtCore.QEvent.Type.MouseMove and self.drag_widget == obj:
            if self.drag_position:
                # Calculate new position
                delta = event.pos() - self.drag_position
                new_pos = obj.pos() + delta
                
                # Constrain to grid
                grid_pos = self._snap_to_grid(new_pos)
                obj.move(grid_pos)
                
                # Update widget position in our tracking
                for wid, widget_info in self.widgets.items():
                    if widget_info['widget'] == obj:
                        # Convert pixel position to grid position
                        row = grid_pos.y() // self.grid_cell_height
                        col = grid_pos.x() // self.grid_cell_width
                        
                        # Limit to grid bounds
                        row = max(0, min(row, self.grid_rows - 1))
                        col = max(0, min(col, self.grid_cols - 1))
                        
                        # Update position
                        widget_info['position'] = (row, col)
                        break
                        
                return True
                
        return super().eventFilter(obj, event)
    
    def _snap_to_grid(self, pos):
        """
        Snap a position to the grid.
        
        Args:
            pos (QPoint): Position to snap
            
        Returns:
            QPoint: Snapped position
        """
        from PyQt6.QtCore import QPoint
        
        # Calculate grid cell position
        col = round(pos.x() / self.grid_cell_width)
        row = round(pos.y() / self.grid_cell_height)
        
        # Limit to grid bounds
        col = max(0, min(col, self.grid_cols - 1))
        row = max(0, min(row, self.grid_rows - 1))
        
        # Convert back to pixels
        x = col * self.grid_cell_width
        y = row * self.grid_cell_height
        
        return QPoint(x, y)
    
    def save_layout(self, file_path):
        """
        Save the current layout to a YAML file.

        Args:
            file_path (str): Path to save file (should end in .yaml)

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            layout_data = {'dashboard': {'layout': []}} # Cấu trúc khớp với file yaml mẫu

            for widget_id, widget_info in self.widgets.items():
                widget = widget_info['widget']
                position = widget_info['position']
                size = widget_info['size']
                widget_type = widget.__class__.__name__
                # Lấy config từ widget nếu có phương thức get_config
                widget_config_method = getattr(widget, 'get_config', None)
                widget_config = widget_config_method() if callable(widget_config_method) else {}

                layout_data['dashboard']['layout'].append({
                    # Lưu ý: Không lưu widget_id tự tăng, dựa vào thứ tự trong list khi load?
                    # Hoặc cần cách lấy/gán ID ổn định hơn nếu cần tham chiếu chéo.
                    # Tạm thời lưu cấu trúc như file mẫu, không có ID rõ ràng.
                    # Nếu muốn giữ ID, cần sửa cấu trúc YAML và logic load/save.
                    'type': widget_type,
                    'position': list(position), # Chuyển tuple thành list cho YAML
                    'size': list(size),
                    'config': widget_config,
                    # Thêm sensor_id nếu widget có thông tin này
                    'sensor_id': getattr(widget, 'sensor_id', None) # Ví dụ
                })

            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            # --- SỬA ĐỔI: Lưu file YAML ---
            with open(file_path, 'w') as f:
                yaml.dump(layout_data, f, default_flow_style=False, indent=2)
            # --- KẾT THÚC SỬA ĐỔI ---

            self.logger.info(f"Layout saved to YAML: {file_path}")
            return True

        except Exception as e:
            self.logger.error(f"Error saving YAML layout: {e}", exc_info=True)
            return False
    
    def load_layout(self, file_path, widget_manager=None):
        """ Loads layout from YAML file, using WidgetManager to create widgets. """
        if widget_manager is None:
             self.logger.error("WidgetManager instance is required to load layout.")
             return False
        try:
            if not os.path.exists(file_path):
                self.logger.error(f"Layout file not found: {file_path}")
                # Optionally, create a default empty structure?
                # self._init_from_config({'dashboard': {'layout': []}}, widget_manager)
                return False # Trả về False nếu file không tồn tại

            # --- SỬA ĐỔI: Đọc file YAML ---
            with open(file_path, 'r') as f:
                layout_data = yaml.safe_load(f) # Sử dụng yaml.safe_load
            # --- KẾT THÚC SỬA ĐỔI ---

            if not layout_data or 'dashboard' not in layout_data or 'layout' not in layout_data['dashboard']:
                 self.logger.error(f"Invalid YAML structure in {file_path}. Missing 'dashboard' or 'layout' key.")
                 # Load layout rỗng hoặc báo lỗi
                 self._clear_layout()
                 self._init_from_config({'dashboard': {'layout': []}}, widget_manager) # Load rỗng
                 return False

            self._clear_layout() # Xóa layout hiện tại
            self._init_from_config(layout_data, widget_manager) # Gọi init với cấu trúc YAML
            self.logger.info(f"Layout loaded from YAML: {file_path}")
            return True
        except yaml.YAMLError as ye:
             self.logger.error(f"Error parsing YAML layout file {file_path}: {ye}", exc_info=True)
             QMessageBox.critical(self, "Layout Error", f"Error parsing layout file:\n{file_path}\n\n{ye}")
             return False
        except Exception as e:
            self.logger.error(f"Error loading layout: {e}", exc_info=True)
            QMessageBox.critical(self, "Layout Error", f"Failed to load layout:\n{e}")
            return False
    
    def _init_from_config(self, config, widget_manager):
        """ Initializes the dashboard from YAML config structure, using WidgetManager. """
        # --- SỬA ĐỔI: Phân tích cấu trúc YAML ---
        dashboard_config = config.get('dashboard', {})
        layout_list = dashboard_config.get('layout', [])
        # --- KẾT THÚC SỬA ĐỔI ---

        # Widget ID sẽ được gán tự động bởi self.add_widget
        self.next_widget_id = 0 # Reset ID counter khi load layout

        for widget_info in layout_list: # Duyệt qua list
            try:
                widget_type = widget_info.get('type')
                # Chuyển list từ YAML thành tuple cho position/size
                position = tuple(widget_info.get('position', [0, 0]))
                size = tuple(widget_info.get('size', [1, 1]))
                w_config = widget_info.get('config', {})
                sensor_id = widget_info.get('sensor_id') # Lấy sensor_id

                if not widget_type:
                    self.logger.warning(f"Widget type missing in layout entry: {widget_info}, skipping.")
                    continue

                self.logger.debug(f"Processing widget from layout: type={widget_type}, pos={position}, size={size}")

                # Yêu cầu WidgetManager tạo widget instance
                # WM không cần biết position/size, chỉ cần type và config
                widget_instance = widget_manager.create_widget_instance(widget_type, w_config)

                if widget_instance:
                     # Gán sensor_id cho widget nếu có
                     if sensor_id and hasattr(widget_instance, 'set_sensor_id'):
                          widget_instance.set_sensor_id(sensor_id)
                     elif sensor_id:
                           # Lưu trữ tạm thời nếu widget chưa có set_sensor_id
                           widget_instance.sensor_id = sensor_id

                     # DashboardManager thêm widget vào layout và quản lý ID
                     self.add_widget(widget_instance, position, size)
                else:
                     self.logger.error(f"WidgetManager failed to create instance for type {widget_type} with config {w_config}")

            except Exception as e:
                self.logger.error(f"Error initializing widget from layout config: {widget_info}\nError: {e}", exc_info=True)

        # self.next_widget_id đã được cập nhật bởi self.add_widget
        self.layout_changed.emit()

    def _clear_layout(self):
        # ... (Giữ nguyên logic _clear_layout) ...
        # Remove all widgets from layout
        ids_to_remove = list(self.widgets.keys()) # Tạo bản sao key trước khi xóa
        for widget_id in ids_to_remove:
            widget_info = self.widgets.pop(widget_id, None)
            if widget_info and widget_info.get('widget'):
                widget = widget_info['widget']
                self.dashboard_layout.removeWidget(widget)
                widget.setParent(None)
                widget.deleteLater()

        # Clear widgets dict
        self.widgets.clear()
        self.next_widget_id = 0
        self.logger.debug("Dashboard layout cleared.")
    
    def _on_save_button_clicked(self):
        # --- SỬA ĐỔI: Lưu file YAML ---
        default_save_path = "config/dashboard_layout.yaml" # Đổi thành .yaml
        # Mở dialog lưu file nếu cần
        if self.save_layout(default_save_path):
            QMessageBox.information(self, "Layout Saved", f"Dashboard layout saved to:\n{default_save_path}")
        else:
            QMessageBox.warning(self, "Save Error", "Failed to save dashboard layout.")

    def _on_load_button_clicked(self):
        default_load_path = "config/dashboard.yaml" # Load file cấu hình mặc định
        if hasattr(self.parent(), 'widget_manager'):
            wm = self.parent().widget_manager
            self.load_layout(default_load_path, wm) # Load file YAML mặc định
        else:
            QMessageBox.warning(self, "Error", "Cannot load layout: WidgetManager not found.")

    def _on_add_widget_button_clicked(self):
        """ Handle add widget button click. """
        # --- SỬA ĐỔI: Sử dụng self.widget_manager ---
        if self.widget_manager:
            # Mở dialog chọn loại widget (cần triển khai _show_widget_selection_dialog)
            # widget_type = self._show_widget_selection_dialog()
            widget_type = "TimeSeriesWidget" # Tạm thời dùng mặc định
            if widget_type:
                self.widget_manager.add_widget(widget_type) # Gọi add_widget của WM
            else:
                 self.logger.debug("Widget selection cancelled.")
        else:
             self.logger.error("WidgetManager not found. Cannot add widget.")
             QMessageBox.warning(self, "Error", "Cannot add widget: WidgetManager not found.")
        # --- KẾT THÚC SỬA ĐỔI ---
    
    # Drag and drop implementation
    def mousePressEvent(self, event):
        """ Bắt đầu quá trình kéo thả khi nhấn chuột trái vào widget. """
        if event.button() == Qt.MouseButton.LeftButton:
            # Xác định widget con tại vị trí nhấn chuột
            child_widget = self.childAt(event.position().toPoint())
            # Tìm widget cấp cao nhất (là con trực tiếp của dashboard_widget)
            top_level_widget = None
            temp_widget = child_widget
            while temp_widget is not None and temp_widget != self.dashboard_widget:
                 # Kiểm tra xem temp_widget có nằm trong danh sách widget của chúng ta không
                 is_managed = False
                 for w_info in self.widgets.values():
                      if w_info['widget'] == temp_widget:
                           is_managed = True
                           break
                 if is_managed:
                      top_level_widget = temp_widget
                      break # Tìm thấy widget được quản lý
                 temp_widget = temp_widget.parentWidget() # Đi lên cây widget

            if top_level_widget:
                self.logger.debug(f"Mouse press on widget: {top_level_widget.__class__.__name__}")
                # Lưu widget sẽ kéo và vị trí nhấn chuột tương đối so với widget đó
                self.drag_widget = top_level_widget
                self.drag_start_position = event.position().toPoint() - self.drag_widget.pos()

                # Tạo đối tượng QDrag
                drag = QDrag(self)
                mime_data = QMimeData()
                # Lưu ID của widget vào mimeData để biết widget nào đang được kéo
                widget_id = self._get_widget_id(self.drag_widget)
                if widget_id is not None:
                    mime_data.setText(str(widget_id))
                    drag.setMimeData(mime_data)

                    # Tạo ảnh xem trước khi kéo (tùy chọn)
                    pixmap = self.drag_widget.grab()
                    drag.setPixmap(pixmap)
                    drag.setHotSpot(self.drag_start_position) # Điểm neo của chuột trên ảnh xem trước

                    # Thực hiện kéo thả, chờ kết quả (dropCompleted)
                    self.logger.debug(f"Starting drag for widget ID: {widget_id}")
                    # Ẩn widget gốc trong khi kéo
                    # self.drag_widget.hide()
                    # Thực hiện kéo và xử lý kết quả trong dragEnter/dragMove/dropEvent
                    drop_action = drag.exec(Qt.DropAction.MoveAction)

                    # Xử lý sau khi kéo thả kết thúc (nếu cần, ví dụ nếu drop không thành công)
                    if drop_action == Qt.DropAction.IgnoreAction:
                         self.logger.debug("Drag ignored or cancelled.")
                         # Hiển thị lại widget gốc nếu nó bị ẩn
                         # self.drag_widget.show()
                    self.drag_widget = None # Reset trạng thái kéo
                    self.drag_start_position = None
                    self._remove_drop_indicator() # Xóa chỉ báo thả
                else:
                    self.logger.warning("Could not find ID for the dragged widget.")
                    self.drag_widget = None # Reset nếu không tìm thấy ID
            else:
                 self.logger.debug("Mouse press not on a draggable widget.")
        super().mousePressEvent(event)
    
    def dragEnterEvent(self, event):
        """ Chấp nhận sự kiện kéo vào nếu có dữ liệu hợp lệ. """
        if event.mimeData().hasText():
            # Kiểm tra xem text có phải là ID widget hợp lệ không
            try:
                widget_id = int(event.mimeData().text())
                if widget_id in self.widgets:
                    event.acceptProposedAction()
                    self.logger.debug(f"Drag enter accepted for widget ID: {widget_id}")
                    self._create_drop_indicator() # Tạo chỉ báo thả
                else:
                    event.ignore()
                    self.logger.debug(f"Drag enter ignored, unknown widget ID: {widget_id}")
            except ValueError:
                event.ignore()
                self.logger.debug("Drag enter ignored, invalid mime data.")
        else:
            event.ignore()
            self.logger.debug("Drag enter ignored, no text mime data.")

    def dragMoveEvent(self, event):
        """ Cập nhật vị trí chỉ báo thả khi di chuyển chuột. """
        if event.mimeData().hasText():
            event.acceptProposedAction()
            # Tính toán vị trí ô lưới tiềm năng
            drop_pos = event.position().toPoint()
            row, col = self._pixel_to_grid(drop_pos)

            # Lấy kích thước của widget đang kéo (cần ID từ mimeData)
            row_span, col_span = 1, 1 # Mặc định
            try:
                 widget_id = int(event.mimeData().text())
                 if widget_id in self.widgets:
                      row_span, col_span = self.widgets[widget_id]['size']
            except ValueError:
                 pass # Bỏ qua nếu ID không hợp lệ

            # Cập nhật vị trí và kích thước của chỉ báo thả
            self._update_drop_indicator(row, col, row_span, col_span)
        else:
            event.ignore()

    def dragLeaveEvent(self, event):
        """ Xóa chỉ báo thả khi chuột rời khỏi khu vực dashboard. """
        self.logger.debug("Drag leave")
        self._remove_drop_indicator()
    
    def dropEvent(self, event):
        """ Xử lý khi widget được thả vào dashboard. """
        if event.mimeData().hasText():
            try:
                widget_id = int(event.mimeData().text())
                if widget_id in self.widgets:
                    drop_pos = event.position().toPoint()
                    new_row, new_col = self._pixel_to_grid(drop_pos)

                    widget_info = self.widgets[widget_id]
                    widget_to_move = widget_info['widget']
                    row_span, col_span = widget_info['size']

                    # Kiểm tra xem vị trí mới có hợp lệ không (ví dụ: không chồng lấp quá nhiều)
                    # (Logic kiểm tra chồng lấp phức tạp, tạm bỏ qua)

                    self.logger.info(f"Dropping widget {widget_id} at grid position ({new_row}, {new_col})")

                    # Xóa widget khỏi layout cũ
                    self.dashboard_layout.removeWidget(widget_to_move)

                    # Cập nhật vị trí trong cấu trúc dữ liệu
                    widget_info['position'] = (new_row, new_col)

                    # Thêm widget vào vị trí mới trong layout
                    self.dashboard_layout.addWidget(widget_to_move, new_row, new_col, row_span, col_span)

                    # Hiển thị lại widget nếu đã ẩn
                    widget_to_move.show()

                    event.acceptProposedAction()
                    self.layout_changed.emit() # Thông báo layout thay đổi
                    self._remove_drop_indicator() # Xóa chỉ báo
                    return # Kết thúc xử lý drop thành công
                else:
                     self.logger.warning(f"Dropped widget with unknown ID: {widget_id}")

            except ValueError:
                 self.logger.warning("Drop event with invalid mime data.")
            except Exception as e:
                 self.logger.error(f"Error during drop event: {e}", exc_info=True)

        event.ignore() # Từ chối drop nếu có lỗi hoặc ID không hợp lệ
        self._remove_drop_indicator()
    
    def _get_widget_id(self, widget_instance):
        """ Helper to find the ID of a widget instance. """
        for widget_id, info in self.widgets.items():
            if info['widget'] == widget_instance:
                return widget_id
        return None
    
    def _create_drop_indicator(self):
        """ Creates a visual indicator for the potential drop location. """
        if self.drop_indicator is None:
            self.drop_indicator = QFrame(self.dashboard_widget)
            self.drop_indicator.setObjectName("dropIndicator")
            self.drop_indicator.setStyleSheet("""
                QFrame#dropIndicator {
                    background-color: rgba(66, 135, 245, 0.3);
                    border: 2px dashed #4285F4;
                }
            """)
            self.drop_indicator.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents) # Cho phép sự kiện chuột xuyên qua
            self.drop_indicator.lower() # Đảm bảo nó ở dưới các widget khác
        self.drop_indicator.show()

    def _update_drop_indicator(self, row, col, row_span=1, col_span=1):
        """ Updates the position and size of the drop indicator. """
        if self.drop_indicator:
            # Giới hạn vị trí trong grid (ví dụ: grid 4x3)
            max_rows = self.dashboard_layout.rowCount()
            max_cols = self.dashboard_layout.columnCount()
            # Hoặc dùng giá trị cố định nếu layout chưa có gì
            grid_rows = max(max_rows, 4)
            grid_cols = max(max_cols, 3)

            # Đảm bảo vị trí và kích thước không vượt ra ngoài grid
            valid_row = max(0, min(row, grid_rows - row_span))
            valid_col = max(0, min(col, grid_cols - col_span))
            valid_row_span = max(1, min(row_span, grid_rows - valid_row))
            valid_col_span = max(1, min(col_span, grid_cols - valid_col))


            # Lấy hình học của ô lưới
            # Lưu ý: cellRect trả về tọa độ so với widget chứa layout (self.dashboard_widget)
            target_rect = self.dashboard_layout.cellRect(valid_row, valid_col)

            # Nếu widget chiếm nhiều ô, tính toán hình chữ nhật bao phủ
            if valid_row_span > 1 or valid_col_span > 1:
                 bottom_right_rect = self.dashboard_layout.cellRect(valid_row + valid_row_span - 1, valid_col + valid_col_span - 1)
                 target_rect = target_rect.united(bottom_right_rect)

            # Thêm padding nhỏ
            padding = -self.dashboard_layout.spacing() // 2
            target_rect.adjust(padding, padding, -padding, -padding)

            self.drop_indicator.setGeometry(target_rect)
            self.drop_indicator.raise_() # Đưa lên trên cùng để thấy rõ
            self.drop_indicator.show()

    def _remove_drop_indicator(self):
        """ Removes the drop indicator from the view. """
        if self.drop_indicator:
            self.drop_indicator.hide()
            # Có thể xóa hẳn nếu muốn:
            # self.drop_indicator.setParent(None)
            # self.drop_indicator.deleteLater()
            # self.drop_indicator = None


    def _pixel_to_grid(self, pos):
        """ Converts pixel coordinates (relative to dashboard_widget) to grid row/col. """
        layout = self.dashboard_layout
        container_widget = self.dashboard_widget

        if container_widget.width() <= 0 or container_widget.height() <= 0:
            return (0, 0)

        # --- SỬA ĐỔI: Logic tính toán grid chính xác hơn ---
        best_match = (0, 0)
        min_dist_sq = float('inf')
        found_cell = False

        # Duyệt qua các ô hiện có trong layout để tìm ô gần nhất
        # QGridLayout tự quản lý số hàng/cột, không nên giả định cố định
        for r in range(layout.rowCount()):
            for c in range(layout.columnCount()):
                rect = layout.cellRect(r, c)
                if rect.isValid(): # Chỉ xét ô hợp lệ
                    center = rect.center()
                    dist_sq = (pos.x() - center.x())**2 + (pos.y() - center.y())**2
                    if dist_sq < min_dist_sq:
                        min_dist_sq = dist_sq
                        best_match = (r, c)
                        found_cell = True

        # Nếu không tìm thấy ô nào (layout trống), trả về (0,0)
        if not found_cell:
             return (0, 0)

        # Nếu vị trí chuột nằm ngoài phạm vi các ô hiện có một chút,
        # thử mở rộng grid (tính toán ô mới tiềm năng)
        last_row_rect = layout.cellRect(layout.rowCount() - 1, 0)
        last_col_rect = layout.cellRect(0, layout.columnCount() - 1)

        # Ước lượng kích thước cell từ ô cuối cùng (cần xử lý layout trống)
        cell_height = last_row_rect.height() if last_row_rect.isValid() else 150 # Ước lượng
        cell_width = last_col_rect.width() if last_col_rect.isValid() else 200

        # Tính toán ô dự kiến dựa trên kích thước cell ước lượng
        if cell_width > 0 and cell_height > 0:
             target_col = int(pos.x() / cell_width)
             target_row = int(pos.y() / cell_height)

             # Nếu ô dự kiến nằm ngoài ô gần nhất tìm được, có thể là ô mới
             if target_row > best_match[0] or target_col > best_match[1]:
                  # Giới hạn trong phạm vi hợp lý
                  max_rows_limit = 10
                  max_cols_limit = 5
                  final_row = min(target_row, max_rows_limit)
                  final_col = min(target_col, max_cols_limit)
                  # self.logger.debug(f"Potential new grid cell: ({final_row}, {final_col})")
                  return (final_row, final_col)

        # Trả về ô gần nhất tìm được trong grid hiện tại
        # self.logger.debug(f"Pixel {pos} mapped to closest existing grid cell: {best_match}")
        return best_match
    
    def set_widget_manager(self, widget_manager):
        """ Sets the WidgetManager instance for this DashboardManager. """
        self.widget_manager = widget_manager
        self.logger.info("WidgetManager instance set for DashboardManager.")
    # --- KẾT THÚC THÊM SETTER ---
    
    # def mouseMoveEvent(self, event):
    #     """Handle mouse move events for dragging."""
    #     # Chỉ bắt đầu kéo thả nếu chuột đã di chuyển một khoảng nhất định
    #     if self.potential_drag_widget and self.drag_start_pos:
    #         # Kiểm tra xem chuột đã di chuyển đủ xa chưa để bắt đầu kéo thả
    #         delta = (event.position().toPoint() - self.drag_start_pos)
    #         if delta.manhattanLength() > 5:  # Ngưỡng để xác định đây là kéo thả cố ý
    #             if not self.is_dragging:
    #                 self.is_dragging = True
    #                 self.drag_widget = self.potential_drag_widget
    #                 self.drag_position = event.position().toPoint()
    #                 self.drag_widget.raise_()
                
    #             # Di chuyển widget
    #             delta = event.position().toPoint() - self.drag_position
    #             new_pos = self.drag_widget.pos() + delta
    #             self.drag_widget.move(new_pos)
    #             self.drag_position = event.position().toPoint()
        
    #     super().mouseMoveEvent(event)
    
    # def mouseReleaseEvent(self, event):
    #     """Handle mouse release events for drag end."""
    #     if self.is_dragging and self.drag_widget:
    #         # Calculate grid position based on widget position
    #         grid_pos = self._position_to_grid(self.drag_widget.pos())
            
    #         # Reset widget position to the closest grid position
    #         for widget_id, widget_info in self.widgets.items():
    #             if widget_info['widget'] == self.drag_widget:
    #                 # Update widget info
    #                 widget_info['position'] = grid_pos
                    
    #                 # Remove widget from old position and add to new position
    #                 self.dashboard_layout.removeWidget(self.drag_widget)
    #                 row, col = grid_pos
    #                 row_span, col_span = widget_info['size']
    #                 self.dashboard_layout.addWidget(self.drag_widget, row, col, row_span, col_span)
                    
    #                 self.layout_changed.emit()
    #                 break
            
    #         self.drag_widget = None
    #         self.drag_position = None
    #         self.drag_start_pos = None
    #         self.is_dragging = False
        
    #     super().mouseReleaseEvent(event)
    
   

# How to modify functionality:
# 1. Add widget factory: Implement a widget factory method to create widgets by type
# 2. Add widget configuration: Add methods to configure widgets (e.g., data source)
# 3. Add serialization: Enhance save_layout() to save widget-specific data
# 4. Add grid visualization: Draw grid lines to visualize the grid
# 5. Add resizing: Implement widget resizing functionality
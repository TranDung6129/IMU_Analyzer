# File: src/ui/panels/connection_panel.py
# Purpose: Panel for managing sensor connections
# Target Lines: ≤250 (Có thể tăng do thêm container)

import logging
import os
import serial.tools.list_ports
import sys # Thêm import
import traceback # Thêm import
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QPushButton, QGroupBox, QFormLayout, QScrollArea, QLineEdit,
    QSpinBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QApplication, QStyle, QSizePolicy, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal

class ConnectionPanel(QWidget):
    # ... (Signals và docstring như cũ) ...
    connect_requested = pyqtSignal(str, dict)
    disconnect_requested = pyqtSignal(str)
    configure_requested = pyqtSignal(str, dict)

    def __init__(self, parent=None):
        """
        Initialize the connection panel.
        """
        super().__init__(parent)
        self.logger = logging.getLogger("ConnectionPanel")
        self.connected_devices = {}
        self.engine_adapter = None

        # --- SỬA ĐỔI: Khởi tạo các container và widget liên quan là None ---
        self.connection_type = None
        self.port_combo = None
        self.baud_rate = None
        self.file_path = None
        self.bluetooth_device = None
        self.connect_btn = None
        self.disconnect_btn = None
        self.configure_btn = None
        self.devices_table = None
        self.init_sequence = None

        self.serial_options_container = None
        self.file_options_container = None
        self.bluetooth_options_container = None
        # --- KẾT THÚC SỬA ĐỔI ---

        # --- THÊM TRY-EXCEPT ---
        try:
            self._setup_ui()
            self.logger.debug("ConnectionPanel UI setup completed.")
        except Exception as e:
            self.logger.error(f"!!! Exception during ConnectionPanel._setup_ui: {str(e)}")
            print("--- TRACEBACK IN ConnectionPanel.__init__ ---", file=sys.stderr)
            traceback.print_exc()
            print("--- TRACEBACK END ---", file=sys.stderr)
            # Có thể raise lỗi hoặc hiển thị thông báo


    def set_engine_adapter(self, adapter):
        """Set the engine adapter for this panel."""
        self.engine_adapter = adapter

    def _setup_ui(self):
        """
        Setup UI components.
        """
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5) # Giảm margin

        # --- SỬA ĐỔI: Gọi setup các phần UI ---
        # Phần cài đặt kết nối (chứa các container)
        self._setup_connection_settings_group(main_layout)

        # Phần thiết bị đã kết nối
        self._setup_connected_devices_group(main_layout)

        # Phần nút Connect/Disconnect
        self._setup_action_buttons(main_layout)

        # Phần cấu hình cảm biến
        self._setup_configuration_group(main_layout)
        # --- KẾT THÚC SỬA ĐỔI ---

        main_layout.addStretch() # Đẩy lên trên

        # Gọi update lần đầu SAU KHI mọi thứ đã vào layout
        if self.connection_type:
            self._update_connection_options(self.connection_type.currentText())


    def _setup_connection_settings_group(self, parent_layout):
        """ Setup group box for connection type and settings """
        connection_group = QGroupBox("Connection Settings")
        group_layout = QVBoxLayout(connection_group) # Layout chính cho group box
        group_layout.setSpacing(8)

        # Connection type combo box
        type_layout = QHBoxLayout()
        type_label = QLabel("Connection Type:")
        self.connection_type = QComboBox()
        self.connection_type.addItems(["Serial", "File", "Bluetooth"]) # Thêm loại nếu cần
        self.connection_type.currentTextChanged.connect(self._update_connection_options)
        type_layout.addWidget(type_label)
        type_layout.addWidget(self.connection_type, 1)
        group_layout.addLayout(type_layout) # Thêm layout loại kết nối vào group

        # --- SỬA ĐỔI: Tạo và thêm các container vào group_layout ---
        # Tạo container và layout cho Serial
        self.serial_options_container = QWidget()
        serial_layout = QFormLayout(self.serial_options_container)
        serial_layout.setContentsMargins(0, 5, 0, 5)
        serial_layout.setSpacing(5)
        # Serial Port
        port_sub_layout = QHBoxLayout()
        self.port_combo = QComboBox()
        self.port_combo.setEditable(True)
        port_sub_layout.addWidget(self.port_combo, 1)
        scan_serial_btn = QPushButton("Scan")
        scan_serial_btn.clicked.connect(self.scan_ports)
        port_sub_layout.addWidget(scan_serial_btn)
        serial_layout.addRow("Port:", port_sub_layout)
        # Baud Rate
        self.baud_rate = QComboBox()
        self.baud_rate.addItems(["9600", "19200", "38400", "57600", "115200", "230400", "460800", "921600"])
        self.baud_rate.setCurrentText("115200")
        serial_layout.addRow("Baud Rate:", self.baud_rate)
        group_layout.addWidget(self.serial_options_container) # Thêm container vào group

        # Tạo container và layout cho File
        self.file_options_container = QWidget()
        file_sub_layout = QHBoxLayout(self.file_options_container) # Dùng QHBoxLayout
        file_sub_layout.setContentsMargins(0, 5, 0, 5)
        file_sub_layout.setSpacing(5)
        file_label = QLabel("File:")
        self.file_path = QLineEdit() # Dùng QLineEdit tốt hơn QComboBox cho đường dẫn file
        self.file_path.setPlaceholderText("Enter path or browse")
        browse_btn = QPushButton("Browse")
        browse_btn.clicked.connect(self._browse_file)
        file_sub_layout.addWidget(file_label)
        file_sub_layout.addWidget(self.file_path, 1)
        file_sub_layout.addWidget(browse_btn)
        group_layout.addWidget(self.file_options_container) # Thêm container vào group

        # Tạo container và layout cho Bluetooth
        self.bluetooth_options_container = QWidget()
        bt_sub_layout = QHBoxLayout(self.bluetooth_options_container)
        bt_sub_layout.setContentsMargins(0, 5, 0, 5)
        bt_sub_layout.setSpacing(5)
        bt_label = QLabel("Device:")
        self.bluetooth_device = QComboBox()
        self.bluetooth_device.setEditable(True)
        scan_bluetooth_btn = QPushButton("Scan")
        scan_bluetooth_btn.clicked.connect(self._scan_bluetooth)
        bt_sub_layout.addWidget(bt_label)
        bt_sub_layout.addWidget(self.bluetooth_device, 1)
        bt_sub_layout.addWidget(scan_bluetooth_btn)
        group_layout.addWidget(self.bluetooth_options_container) # Thêm container vào group
        # --- KẾT THÚC SỬA ĐỔI TẠO CONTAINER ---

        parent_layout.addWidget(connection_group) # Thêm group box vào layout cha


    def _setup_connected_devices_group(self, parent_layout):
        """ Setup group box for the connected devices table """
        devices_group = QGroupBox("Connected Devices")
        devices_layout = QVBoxLayout(devices_group)
        self.devices_table = QTableWidget(0, 3)
        self.devices_table.setHorizontalHeaderLabels(["Device Name", "Connection", "Status"])
        self.devices_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.devices_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.devices_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.devices_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.devices_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.devices_table.itemSelectionChanged.connect(self._update_button_states)
        devices_layout.addWidget(self.devices_table)
        parent_layout.addWidget(devices_group)


    def _setup_action_buttons(self, parent_layout):
        """ Setup Connect and Disconnect buttons """
        button_layout = QHBoxLayout()
        self.connect_btn = QPushButton("Connect")
        self.connect_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogApplyButton))
        self.connect_btn.clicked.connect(self.connect_device)
        self.disconnect_btn = QPushButton("Disconnect")
        self.disconnect_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogCancelButton))
        self.disconnect_btn.clicked.connect(self.disconnect_device)
        self.disconnect_btn.setEnabled(False)
        button_layout.addStretch()
        button_layout.addWidget(self.connect_btn)
        button_layout.addWidget(self.disconnect_btn)
        parent_layout.addLayout(button_layout)


    def _setup_configuration_group(self, parent_layout):
         """ Setup group box for sensor configuration """
         config_group = QGroupBox("Sensor Configuration (Optional)")
         config_layout = QFormLayout(config_group) # Dùng QFormLayout
         self.init_sequence = QLineEdit()
         self.init_sequence.setPlaceholderText("Ex: FF AA 69, FF AA 02 01")
         config_layout.addRow("Init Sequence:", self.init_sequence)
         self.configure_btn = QPushButton("Send Configuration")
         self.configure_btn.clicked.connect(self.configure_sensor)
         self.configure_btn.setEnabled(False) # Chỉ bật khi có thiết bị được chọn
         config_layout.addRow(self.configure_btn) # Thêm nút vào form layout
         parent_layout.addWidget(config_group)


    def _update_connection_options(self, connection_type):
        """
        Update connection options based on selected type.
        """
        connection_type = connection_type.lower()
        self.logger.debug(f"Updating visibility for type: {connection_type}")

        # --- SỬA ĐỔI: Gọi setVisible trên các container ---
        # Đảm bảo các container đã được tạo trước khi gọi setVisible
        if hasattr(self, 'serial_options_container') and self.serial_options_container:
            self.serial_options_container.setVisible(connection_type == "serial")
        if hasattr(self, 'file_options_container') and self.file_options_container:
            self.file_options_container.setVisible(connection_type == "file")
        if hasattr(self, 'bluetooth_options_container') and self.bluetooth_options_container:
            self.bluetooth_options_container.setVisible(connection_type == "bluetooth")
        # --- KẾT THÚC SỬA ĐỔI ---

        # Cập nhật các giá trị mặc định hoặc quét nếu cần
        if connection_type == "serial":
            self.scan_ports()
        elif connection_type == "file":
            # Có thể đặt đường dẫn mặc định hoặc không làm gì
            pass
        elif connection_type == "bluetooth":
            self._scan_bluetooth()


    def scan_ports(self):
        """ Scan for available serial ports. """
        if not self.port_combo: return # Kiểm tra widget tồn tại
        current_port = self.port_combo.currentText() # Lưu lại port đang chọn (nếu có)
        self.port_combo.clear()
        ports_found = []
        try:
            ports = serial.tools.list_ports.comports()
            for port in ports:
                ports_found.append(port.device)
                self.port_combo.addItem(f"{port.device} ({port.description})", port.device) # Thêm data là device path
            self.logger.info(f"Found serial ports: {ports_found}")
            if not ports_found:
                self.port_combo.addItem("No ports found")
            else:
                 # Cố gắng chọn lại port cũ nếu còn tồn tại
                 index = self.port_combo.findData(current_port)
                 if index >= 0:
                      self.port_combo.setCurrentIndex(index)
                 elif self.port_combo.count() > 0:
                      self.port_combo.setCurrentIndex(0) # Chọn port đầu tiên nếu không tìm thấy port cũ
        except Exception as e:
            self.logger.error(f"Error scanning serial ports: {e}", exc_info=True)
            self.port_combo.addItem("Error scanning")


    def _browse_file(self):
        """ Browse for a data file. """
        if not self.file_path: return
        from PyQt6.QtWidgets import QFileDialog
        # Lấy thư mục hiện tại của file đang chọn (nếu có) làm thư mục bắt đầu
        start_dir = os.path.dirname(self.file_path.text()) if self.file_path.text() else ""
        file_path_selected, _ = QFileDialog.getOpenFileName(
            self, "Select Sensor Data File", start_dir,
            "CSV files (*.csv);;Text files (*.txt);;All files (*)"
        )
        if file_path_selected:
            self.file_path.setText(file_path_selected)
            self.logger.info(f"Selected file: {file_path_selected}")


    def _scan_bluetooth(self):
        """ Scan for available Bluetooth devices. """
        if not self.bluetooth_device: return
        self.bluetooth_device.clear()
        self.bluetooth_device.addItem("Scanning...")
        self.bluetooth_device.setEnabled(False)
        QApplication.processEvents() # Cập nhật UI

        # Placeholder: Thực hiện scan BT ở đây (có thể cần chạy trong thread riêng)
        # Ví dụ: devices = self.engine_adapter.scan_bluetooth()
        devices = {"00:11:22:AA:BB:CC": "HC-05", "11:22:33:DD:EE:FF": "SensorTag"} # Dữ liệu giả
        self.bluetooth_device.clear()
        if devices:
            for addr, name in devices.items():
                 self.bluetooth_device.addItem(f"{name} ({addr})", addr) # Lưu địa chỉ làm data
            self.logger.info(f"Found Bluetooth devices: {list(devices.values())}")
            self.bluetooth_device.setCurrentIndex(0)
        else:
            self.bluetooth_device.addItem("No devices found")
            self.logger.info("No Bluetooth devices found.")

        self.bluetooth_device.setEnabled(True)


    def connect_device(self):
        """ Connect to the selected device. """
        connection_type = self.connection_type.currentText()
        config = {"type": connection_type}
        device_id = None
        device_name = ""
        connection_info = ""

        try:
            if connection_type == "Serial":
                if not self.port_combo or self.port_combo.currentIndex() < 0:
                    raise ValueError("No serial port selected.")
                # Lấy device path từ data của item đang chọn
                port = self.port_combo.itemData(self.port_combo.currentIndex())
                if not port or "No ports" in port or "Error" in port:
                     raise ValueError("Invalid serial port selected.")
                # Lấy text để hiển thị tên
                port_display_text = self.port_combo.currentText()
                baud_rate_str = self.baud_rate.currentText()
                if not baud_rate_str.isdigit():
                    raise ValueError("Invalid baud rate.")
                baud_rate = int(baud_rate_str)

                config["port"] = port
                config["baudrate"] = baud_rate
                device_id = f"serial_{port.replace('/', '_').replace(':', '_')}"
                device_name = f"Serial: {port_display_text}"
                connection_info = f"{baud_rate} baud"

            elif connection_type == "File":
                file_path_text = self.file_path.text()
                if not file_path_text or not os.path.exists(file_path_text):
                    raise ValueError(f"File not found or invalid path: {file_path_text}")
                config["file_path"] = file_path_text
                # Tạo ID duy nhất từ đường dẫn file
                device_id = f"file_{hash(file_path_text)}"
                device_name = f"File: {os.path.basename(file_path_text)}"
                connection_info = file_path_text

            elif connection_type == "Bluetooth":
                 if not self.bluetooth_device or self.bluetooth_device.currentIndex() < 0:
                      raise ValueError("No Bluetooth device selected.")
                 # Lấy địa chỉ MAC từ data
                 device_addr = self.bluetooth_device.itemData(self.bluetooth_device.currentIndex())
                 if not device_addr or "No devices" in device_addr or "Scanning" in device_addr:
                      raise ValueError("Invalid Bluetooth device selected.")
                 # Lấy text để hiển thị
                 device_display_text = self.bluetooth_device.currentText()

                 config["device_id"] = device_addr # Sửa key thành device_id để khớp EngineAdapter
                 device_id = f"bt_{device_addr.replace(':', '_')}"
                 device_name = f"BT: {device_display_text}"
                 connection_info = device_addr

            else:
                raise ValueError(f"Unsupported connection type: {connection_type}")

            if device_id:
                 self._add_device_to_table(device_id, device_name, connection_info, "Connecting...")
                 self.connect_requested.emit(device_id, config)
                 self.logger.info(f"Connect requested for device {device_id} with config {config}")
                 # Vô hiệu hóa nút connect tạm thời
                 self.connect_btn.setEnabled(False)
            else:
                 # Điều này không nên xảy ra nếu logic ở trên đúng
                 self.logger.error("Could not determine device ID for connection.")

        except ValueError as ve:
            self.logger.error(f"Connection validation error: {ve}")
            QMessageBox.warning(self, "Connection Error", str(ve))
        except Exception as e:
            self.logger.error(f"Unexpected error during connect request: {e}", exc_info=True)
            QMessageBox.critical(self, "Error", f"An unexpected error occurred: {e}")


    def disconnect_device(self):
        """ Disconnect the selected device. """
        selected_rows = self.devices_table.selectedIndexes()
        if not selected_rows: return

        row = selected_rows[0].row()
        device_id_item = self.devices_table.item(row, 0)
        if not device_id_item: return # Kiểm tra item tồn tại

        device_id = device_id_item.data(Qt.ItemDataRole.UserRole)
        if device_id:
            self.logger.info(f"Disconnect requested for device {device_id}")
            self.disconnect_requested.emit(device_id)
            # Cập nhật trạng thái UI (sẽ được cập nhật chính xác bởi update_connection_status)
            self.update_connection_status(device_id, "Disconnecting...")
            # Vô hiệu hóa nút disconnect
            self.disconnect_btn.setEnabled(False)


    def configure_sensor(self):
        """ Send configuration to the selected sensor. """
        selected_rows = self.devices_table.selectedIndexes()
        if not selected_rows:
            QMessageBox.warning(self, "Selection Error", "Please select a device from the table.")
            return

        row = selected_rows[0].row()
        device_id_item = self.devices_table.item(row, 0)
        if not device_id_item: return

        device_id = device_id_item.data(Qt.ItemDataRole.UserRole)
        if not device_id:
             QMessageBox.warning(self, "Error", "Could not identify the selected device.")
             return

        init_sequence_text = self.init_sequence.text().strip()
        # Cho phép chuỗi rỗng nếu người dùng muốn gửi cấu hình mặc định từ file yaml?
        # if not init_sequence_text:
        #     QMessageBox.warning(self, "Input Error", "Init sequence cannot be empty.")
        #     return

        # Tách lệnh bằng dấu phẩy, loại bỏ khoảng trắng thừa
        init_commands = [cmd.strip() for cmd in init_sequence_text.split(',') if cmd.strip()]

        config_to_send = {
            # Có thể thêm các trường config khác lấy từ UI ở đây
            "init_sequence": init_commands
        }

        # Nếu init_sequence rỗng, chỉ gửi một dict rỗng (để engine dùng config mặc định nếu có)
        # if not init_commands:
        #     config_to_send = {}

        self.logger.info(f"Requesting configuration for {device_id} with: {config_to_send}")
        try:
            self.configure_requested.emit(device_id, config_to_send)
            # Tạm thời hiển thị thông báo thành công, engine sẽ xử lý thực tế
            QMessageBox.information(self, "Configuration Sent", f"Configuration request sent for {device_id}.")
            # Cập nhật trạng thái có thể hữu ích:
            # self.update_connection_status(device_id, "Configuring...")
        except Exception as e:
            self.logger.error(f"Error emitting configure signal for {device_id}: {e}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to send configuration request: {e}")


    def _add_device_to_table(self, device_id, device_name, connection_info, status):
        """ Adds or updates a device in the connected devices table. """
        if not self.devices_table: return

        for row in range(self.devices_table.rowCount()):
            item = self.devices_table.item(row, 0)
            if item and item.data(Qt.ItemDataRole.UserRole) == device_id:
                # Update existing row
                self.devices_table.item(row, 0).setText(device_name)
                # Cập nhật item cột 1 và 2 nếu chúng tồn tại
                conn_item = self.devices_table.item(row, 1)
                if conn_item: conn_item.setText(connection_info)
                else: self.devices_table.setItem(row, 1, QTableWidgetItem(connection_info))

                status_item = self.devices_table.item(row, 2)
                if status_item: status_item.setText(status)
                else: self.devices_table.setItem(row, 2, QTableWidgetItem(status))
                self.logger.debug(f"Updated device in table: {device_id}")
                return # Kết thúc sau khi cập nhật

        # Add new row if device not found
        row = self.devices_table.rowCount()
        self.devices_table.insertRow(row)
        name_item = QTableWidgetItem(device_name)
        name_item.setData(Qt.ItemDataRole.UserRole, device_id) # Lưu ID vào item
        self.devices_table.setItem(row, 0, name_item)
        self.devices_table.setItem(row, 1, QTableWidgetItem(connection_info))
        self.devices_table.setItem(row, 2, QTableWidgetItem(status))
        self.logger.debug(f"Added new device to table: {device_id}")

        # Không cần lưu vào self.connected_devices nữa nếu table là nguồn chính


    def update_connection_status(self, device_id, status, is_connected=None):
        """
        Update the status of a connection in the table and button states.
        """
        if not self.devices_table: return
        updated = False
        for row in range(self.devices_table.rowCount()):
            item = self.devices_table.item(row, 0)
            if item and item.data(Qt.ItemDataRole.UserRole) == device_id:
                status_item = self.devices_table.item(row, 2)
                if status_item:
                     status_item.setText(status)
                else:
                     self.devices_table.setItem(row, 2, QTableWidgetItem(status))
                self.logger.debug(f"Updated status for {device_id} to: {status}")
                updated = True
                # Cập nhật trạng thái nút dựa trên is_connected nếu được cung cấp
                if is_connected is not None:
                     # Nếu đây là hàng đang được chọn, cập nhật nút
                     selected_rows = self.devices_table.selectedIndexes()
                     if selected_rows and selected_rows[0].row() == row:
                          self._update_button_states(is_connected)

                break # Kết thúc vòng lặp khi tìm thấy

        if not updated:
             self.logger.warning(f"Could not find device {device_id} in table to update status.")


    def refresh_connections(self):
        """ Refresh the list based on the current connection type. """
        if not self.connection_type: return
        connection_type = self.connection_type.currentText()
        self.logger.debug(f"Refreshing connections for type: {connection_type}")
        if connection_type == "Serial":
            self.scan_ports()
        elif connection_type == "Bluetooth":
            self._scan_bluetooth()
        elif connection_type == "File":
             # Có thể xóa danh sách file cũ hoặc làm mới thư mục gần đây
             pass


    def _update_button_states(self, force_connected_state=None):
        """ Update button enabled states based on table selection and connection status. """
        selected_rows = self.devices_table.selectedIndexes()
        has_selection = bool(selected_rows)
        is_connected = False

        if has_selection:
            row = selected_rows[0].row()
            status_item = self.devices_table.item(row, 2)
            if status_item:
                 current_status = status_item.text().lower()
                 # Xác định trạng thái kết nối dựa trên text (có thể cần chuẩn hóa)
                 is_connected = "connected" in current_status or "running" in current_status

        # Ghi đè trạng thái nếu được cung cấp (hữu ích khi cập nhật từ bên ngoài)
        if force_connected_state is not None:
             is_connected = force_connected_state

        # Nút Connect chỉ bật khi chưa kết nối (bất kể có chọn hay không)
        # Nút Disconnect chỉ bật khi có chọn và đang kết nối
        # Nút Configure chỉ bật khi có chọn (trạng thái kết nối có thể không quan trọng)
        self.connect_btn.setEnabled(not is_connected)
        self.disconnect_btn.setEnabled(has_selection and is_connected)
        self.configure_btn.setEnabled(has_selection)
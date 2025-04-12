# File: src/ui/panels/sensor_panel.py
# Purpose: Panel for sensor management and monitoring
# Target Lines: ≤150

"""
Methods to implement:
- __init__(self, parent=None): Initialize the panel
- _setup_ui(self): Setup UI components
- refresh_sensors(self): Refresh the list of sensors
- add_sensor(self): Add a new sensor
- remove_sensor(self): Remove a selected sensor
- edit_sensor(self): Edit a selected sensor's parameters
- update_sensor_status(self, sensor_id, status): Update the status of a sensor
"""

import logging
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QGroupBox, QFormLayout, QTableWidget,
    QTableWidgetItem, QHeaderView, QComboBox, QDialog,
    QDialogButtonBox, QMessageBox, QCheckBox, QSpinBox
)
from PyQt6.QtCore import Qt, pyqtSignal


class SensorDialog(QDialog):
    """
    Dialog for adding or editing a sensor.
    """
    
    def __init__(self, parent=None, sensor_data=None):
        """
        Initialize the sensor dialog.
        
        Args:
            parent: Parent widget
            sensor_data (dict, optional): Existing sensor data for editing
        """
        super().__init__(parent)
        
        self.sensor_data = sensor_data or {}
        self.setWindowTitle("Sensor Configuration")
        self.resize(400, 300)
        
        self._setup_ui()
    
    def _setup_ui(self):
        """
        Setup UI components.
        """
        layout = QVBoxLayout(self)
        
        # Form layout for sensor parameters
        form_layout = QFormLayout()
        
        # Sensor ID
        self.id_edit = QLineEdit(self.sensor_data.get("id", ""))
        form_layout.addRow("Sensor ID:", self.id_edit)
        
        # Sensor Name
        self.name_edit = QLineEdit(self.sensor_data.get("name", ""))
        form_layout.addRow("Sensor Name:", self.name_edit)
        
        # Sensor Type
        self.type_combo = QComboBox()
        self.type_combo.addItems(["IMU", "GPS", "Temperature", "Pressure", "Other"])
        if "type" in self.sensor_data:
            self.type_combo.setCurrentText(self.sensor_data["type"])
        form_layout.addRow("Sensor Type:", self.type_combo)
        
        # Sampling Rate
        self.rate_spin = QSpinBox()
        self.rate_spin.setMinimum(1)
        self.rate_spin.setMaximum(1000)
        self.rate_spin.setValue(self.sensor_data.get("sampling_rate", 100))
        form_layout.addRow("Sampling Rate (Hz):", self.rate_spin)
        
        # Enabled
        self.enabled_check = QCheckBox()
        self.enabled_check.setChecked(self.sensor_data.get("enabled", True))
        form_layout.addRow("Enabled:", self.enabled_check)
        
        # Description
        self.description_edit = QLineEdit(self.sensor_data.get("description", ""))
        form_layout.addRow("Description:", self.description_edit)
        
        layout.addLayout(form_layout)
        
        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def get_sensor_data(self):
        """
        Get the sensor data from the dialog.
        
        Returns:
            dict: Sensor data
        """
        return {
            "id": self.id_edit.text(),
            "name": self.name_edit.text(),
            "type": self.type_combo.currentText(),
            "sampling_rate": self.rate_spin.value(),
            "enabled": self.enabled_check.isChecked(),
            "description": self.description_edit.text()
        }


class SensorPanel(QWidget):
    """
    Panel for sensor management and monitoring.
    
    Allows adding, removing, and editing sensors,
    as well as monitoring their status.
    """
    
    # Signals
    sensor_added = pyqtSignal(dict)
    sensor_removed = pyqtSignal(str)
    sensor_updated = pyqtSignal(str, dict)
    
    def __init__(self, parent=None):
        """
        Initialize the sensor panel.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        
        self.logger = logging.getLogger("SensorPanel")
        self.sensors = {}
        
        self._setup_ui()
    
    def _setup_ui(self):
        """
        Setup UI components.
        """
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        
        # Sensor list section
        self._setup_sensor_list(main_layout)
        
        # Action buttons
        button_layout = QHBoxLayout()
        
        # Add sensor button
        add_btn = QPushButton("Add Sensor")
        add_btn.clicked.connect(self.add_sensor)
        button_layout.addWidget(add_btn)
        
        # Edit sensor button
        self.edit_btn = QPushButton("Edit Sensor")
        self.edit_btn.clicked.connect(self.edit_sensor)
        self.edit_btn.setEnabled(False)
        button_layout.addWidget(self.edit_btn)
        
        # Remove sensor button
        self.remove_btn = QPushButton("Remove Sensor")
        self.remove_btn.clicked.connect(self.remove_sensor)
        self.remove_btn.setEnabled(False)
        button_layout.addWidget(self.remove_btn)
        
        # Refresh button
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh_sensors)
        button_layout.addWidget(refresh_btn)
        
        main_layout.addLayout(button_layout)
    
    def _setup_sensor_list(self, parent_layout):
        """
        Setup sensor list table.
        
        Args:
            parent_layout: Parent layout to add the table to
        """
        sensors_group = QGroupBox("Sensors")
        sensors_layout = QVBoxLayout(sensors_group)
        
        # Table for sensors
        self.sensors_table = QTableWidget(0, 5)
        self.sensors_table.setHorizontalHeaderLabels(["ID", "Name", "Type", "Rate (Hz)", "Status"])
        self.sensors_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.sensors_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.sensors_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.sensors_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.sensors_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.sensors_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.sensors_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.sensors_table.itemSelectionChanged.connect(self._update_button_states)
        
        sensors_layout.addWidget(self.sensors_table)
        
        parent_layout.addWidget(sensors_group)
    
    def refresh_sensors(self):
        """
        Refresh the list of sensors.
        
        This typically loads sensors from the SensorRegistry.
        """
        # Clear the table
        self.sensors_table.setRowCount(0)
        
        # Add each sensor to the table
        for sensor_id, sensor_data in self.sensors.items():
            self._add_sensor_to_table(sensor_data)
        
        self.logger.info("Sensors refreshed")
    
    def add_sensor(self):
        """
        Add a new sensor.
        
        Opens a dialog to enter sensor details.
        """
        dialog = SensorDialog(self)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            sensor_data = dialog.get_sensor_data()
            
            # Validate sensor data
            if not sensor_data["id"]:
                QMessageBox.warning(self, "Invalid Sensor", "Sensor ID cannot be empty")
                return
                
            if sensor_data["id"] in self.sensors:
                QMessageBox.warning(self, "Invalid Sensor", f"Sensor with ID '{sensor_data['id']}' already exists")
                return
            
            # Add to table and store
            self._add_sensor_to_table(sensor_data)
            self.sensors[sensor_data["id"]] = sensor_data
            
            # Emit signal
            self.sensor_added.emit(sensor_data)
            
            self.logger.info(f"Sensor added: {sensor_data['id']}")
    
    def edit_sensor(self):
        """
        Edit a selected sensor's parameters.
        
        Opens a dialog with existing sensor details.
        """
        selected_rows = self.sensors_table.selectedIndexes()
        if not selected_rows:
            return
            
        row = selected_rows[0].row()
        sensor_id = self.sensors_table.item(row, 0).text()
        
        if sensor_id not in self.sensors:
            return
            
        # Open dialog with existing data
        dialog = SensorDialog(self, self.sensors[sensor_id])
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            sensor_data = dialog.get_sensor_data()
            
            # Validate sensor data
            if not sensor_data["id"]:
                QMessageBox.warning(self, "Invalid Sensor", "Sensor ID cannot be empty")
                return
                
            if sensor_data["id"] != sensor_id and sensor_data["id"] in self.sensors:
                QMessageBox.warning(self, "Invalid Sensor", f"Sensor with ID '{sensor_data['id']}' already exists")
                return
            
            # Update in table and store
            if sensor_data["id"] != sensor_id:
                # ID changed, remove old and add new
                self.sensors.pop(sensor_id)
                self._remove_sensor_from_table(sensor_id)
                self._add_sensor_to_table(sensor_data)
                self.sensors[sensor_data["id"]] = sensor_data
            else:
                # Update existing
                self._update_sensor_in_table(sensor_data)
                self.sensors[sensor_id] = sensor_data
            
            # Emit signal
            self.sensor_updated.emit(sensor_id, sensor_data)
            
            self.logger.info(f"Sensor updated: {sensor_id} -> {sensor_data['id']}")
    
    def remove_sensor(self):
        """
        Remove a selected sensor.
        """
        selected_rows = self.sensors_table.selectedIndexes()
        if not selected_rows:
            return
            
        row = selected_rows[0].row()
        sensor_id = self.sensors_table.item(row, 0).text()
        
        # Confirm removal
        reply = QMessageBox.question(
            self,
            "Remove Sensor",
            f"Are you sure you want to remove sensor '{sensor_id}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Remove from table and store
            self._remove_sensor_from_table(sensor_id)
            self.sensors.pop(sensor_id, None)
            
            # Emit signal
            self.sensor_removed.emit(sensor_id)
            
            self.logger.info(f"Sensor removed: {sensor_id}")
    
    def update_sensor_status(self, sensor_id, status):
        """
        Update the status of a sensor in the table.
        
        Args:
            sensor_id (str): Sensor ID
            status (str): New status
        """
        for row in range(self.sensors_table.rowCount()):
            if self.sensors_table.item(row, 0).text() == sensor_id:
                self.sensors_table.item(row, 4).setText(status)
                break
    
    def _add_sensor_to_table(self, sensor_data):
        """
        Add a sensor to the table.
        
        Args:
            sensor_data (dict): Sensor data
        """
        row = self.sensors_table.rowCount()
        self.sensors_table.insertRow(row)
        
        # ID
        self.sensors_table.setItem(row, 0, QTableWidgetItem(sensor_data["id"]))
        
        # Name
        self.sensors_table.setItem(row, 1, QTableWidgetItem(sensor_data["name"]))
        
        # Type
        self.sensors_table.setItem(row, 2, QTableWidgetItem(sensor_data["type"]))
        
        # Sampling Rate
        self.sensors_table.setItem(row, 3, QTableWidgetItem(str(sensor_data["sampling_rate"])))
        
        # Status
        status = "Enabled" if sensor_data.get("enabled", True) else "Disabled"
        self.sensors_table.setItem(row, 4, QTableWidgetItem(status))
    
    def _update_sensor_in_table(self, sensor_data):
        """
        Update a sensor in the table.
        
        Args:
            sensor_data (dict): Sensor data
        """
        for row in range(self.sensors_table.rowCount()):
            if self.sensors_table.item(row, 0).text() == sensor_data["id"]:
                # Update row
                self.sensors_table.item(row, 1).setText(sensor_data["name"])
                self.sensors_table.item(row, 2).setText(sensor_data["type"])
                self.sensors_table.item(row, 3).setText(str(sensor_data["sampling_rate"]))
                
                status = "Enabled" if sensor_data.get("enabled", True) else "Disabled"
                self.sensors_table.item(row, 4).setText(status)
                
                break
    
    def _remove_sensor_from_table(self, sensor_id):
        """
        Remove a sensor from the table.
        
        Args:
            sensor_id (str): Sensor ID
        """
        for row in range(self.sensors_table.rowCount()):
            if self.sensors_table.item(row, 0).text() == sensor_id:
                self.sensors_table.removeRow(row)
                break
    
    def _update_button_states(self):
        """
        Update button states based on selection.
        """
        selected_rows = self.sensors_table.selectedIndexes()
        has_selection = len(selected_rows) > 0
        
        self.edit_btn.setEnabled(has_selection)
        self.remove_btn.setEnabled(has_selection)
    
    def set_sensors(self, sensors_dict):
        """
        Set the sensors dictionary.
        
        Args:
            sensors_dict (dict): Dictionary of sensors
        """
        self.sensors = sensors_dict
        self.refresh_sensors()

# How to modify functionality:
# 1. Add sensor properties: Update SensorDialog to include additional fields
# 2. Add sensor grouping: Add UI to group sensors by type or location
# 3. Add sensor export/import: Add buttons to export/import sensor configurations
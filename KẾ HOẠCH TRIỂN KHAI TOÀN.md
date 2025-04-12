# KẾ HOẠCH TRIỂN KHAI DỰ ÁN "IMU Analyzer" (Cập nhật cho PyQt6 và SensorConfigurator)

> **Mục tiêu chính**: Xây dựng hệ thống **IMU Analyzer** với kiến trúc phân tầng rõ ràng, plugin-based, hỗ trợ xử lý dữ liệu từ nhiều cảm biến, đồng bộ và bất đồng bộ giữa các pipeline, hiển thị dữ liệu trên dashboard linh hoạt (kéo thả, đổi vị trí, chỉnh kích thước widget), và khả năng mở rộng quy mô. Hệ thống sử dụng **PyQt6** cho giao diện người dùng và tích hợp **SensorConfigurator** để quản lý cấu hình cảm biến đa dạng. Kế hoạch bao gồm hướng dẫn chỉnh sửa chức năng để dễ dàng tùy chỉnh sau này.

---

## I. Tổng Quan Yêu Cầu

### 1. Yêu Cầu Hệ Thống
- **Xử lý dữ liệu cảm biến**:
  - Hỗ trợ nhiều nguồn dữ liệu: Serial, File, Bluetooth, CAN, UDP, WebSocket, v.v.
  - Mỗi cảm biến được xử lý qua một pipeline riêng: DataReader → Decoder → Processor → Analyzer → Visualizer → Writer.
- **Cấu hình cảm biến (mới)**:
  - Hỗ trợ gửi cấu hình khởi tạo tùy biến tới cảm biến (Serial commands, BLE handshake, CAN registry, v.v.).
  - Đồng bộ hóa cấu hình giữa file YAML, UI, và giao tiếp thực tế.
  - Tách biệt logic cấu hình (`SensorConfigurator`) khỏi logic đọc/ghi dữ liệu.
- **Đồng bộ và bất đồng bộ**:
  - Các pipeline chạy song song, không gây xung đột.
  - Sử dụng queue riêng cho mỗi pipeline để tránh contention.
- **Tách biệt Analyzer và Processor**:
  - Processor: Xử lý dữ liệu cơ bản (lọc, chuẩn hóa).
  - Analyzer: Phân tích nâng cao (anomaly detection, ML inference).
- **Dashboard linh hoạt**:
  - Hiển thị dữ liệu từ nhiều cảm biến, phân biệt rõ ràng (tiêu đề, màu sắc).
  - Hỗ trợ kéo thả widget, đổi vị trí, và chỉnh kích thước trực tiếp.
  - Lưu và khôi phục layout dashboard.
- **Mở rộng quy mô**:
  - Hỗ trợ plugin-based architecture (dễ dàng thêm Reader, Decoder, Processor, Analyzer, Visualizer, Writer, Exporter, Configurator).
  - Giám sát hiệu năng (CPU, RAM, throughput) và hiển thị trên UI.
- **Xử lý lỗi**:
  - Xử lý lỗi trong các thành phần (Reader, Writer, Pipeline, Configurator) và ghi log lỗi.
- **Lưu trữ và xuất dữ liệu**:
  - Hỗ trợ ghi dữ liệu thô qua Writer (file, serial, Bluetooth, v.v.).
  - Hỗ trợ xuất dữ liệu đã xử lý qua Exporter (CSV, JSON, v.v.).
- **Giao diện người dùng**:
  - Sử dụng **PyQt6** thay vì PyQt5 để xây dựng giao diện.
  - Hỗ trợ chỉnh sửa cấu hình cảm biến qua UI (sampling rate, enable/disable, v.v.).

### 2. Mục Tiêu của Kế Hoạch
- Cung cấp bộ khung hoàn chỉnh cho hệ thống IMU Analyzer.
- Chia nhỏ công việc thành các giai đoạn và task để triển khai từng bước.
- Đảm bảo tính rõ ràng, tường minh, và dễ thực hiện.
- Tích hợp **SensorConfigurator** để hỗ trợ cấu hình cảm biến đa dạng.
- Bổ sung hướng dẫn chỉnh sửa chức năng để dễ dàng tùy chỉnh sau này.

---

## II. Cấu Trúc Thư Mục Dự Án

```
IMUAnalyzer/
├── main.py
├── config/
│   ├── default.yaml
│   ├── pipelines.yaml
│   ├── sensors.yaml
│   ├── dashboard.yaml
│   └── logs/
│       └── imu_analyzer.log
├── src/
│   ├── core/
│   │   ├── config_loader.py
│   │   ├── engine.py
│   │   ├── pipeline.py
│   │   └── plugin_manager.py
│   ├── io/
│   │   ├── readers/
│   │   │   ├── base_reader.py
│   │   │   ├── file_reader.py
│   │   │   ├── serial_reader.py
│   │   │   ├── bluetooth_reader.py
│   │   │   └── …
│   │   └── writers/
│   │       ├── base_writer.py
│   │       ├── file_writer.py
│   │       ├── serial_writer.py
│   │       ├── bluetooth_writer.py
│   │       └── …
│   ├── plugins/
│   │   ├── decoders/
│   │   │   ├── base_decoder.py
│   │   │   ├── witmotion_decoder.py
│   │   │   ├── custom_decoder.py
│   │   │   └── …
│   │   ├── processors/
│   │   │   ├── base_processor.py
│   │   │   ├── simple_processor.py
│   │   │   └── …
│   │   ├── analyzers/
│   │   │   ├── base_analyzer.py
│   │   │   ├── anomaly_detector.py
│   │   │   ├── ml_inference_analyzer.py
│   │   │   └── …
│   │   ├── visualizers/
│   │   │   ├── base_visualizer.py
│   │   │   ├── time_series_visualizer.py
│   │   │   ├── fft_visualizer.py
│   │   │   ├── orientation3d_visualizer.py
│   │   │   └── …
│   │   ├── exporters/
│   │   │   ├── base_exporter.py
│   │   │   ├── csv_exporter.py
│   │   │   ├── json_exporter.py
│   │   │   └── …
│   │   └── configurators/  # New directory
│   │       ├── base_configurator.py
│   │       ├── witmotion_configurator.py
│   │       ├── mpu6050_configurator.py
│   │       ├── canbus_configurator.py
│   │       └── …
│   ├── ui/
│   │   ├── main_window.py
│   │   ├── panels/
│   │   │   ├── config_panel.py
│   │   │   ├── connection_panel.py
│   │   │   ├── sensor_panel.py
│   │   │   ├── plugin_panel.py
│   │   │   └── monitor_panel.py
│   │   ├── dashboard/
│   │   │   ├── dashboard_manager.py
│   │   │   ├── widget_manager.py
│   │   │   └── layout_config.py
│   │   └── visualizers/
│   │       ├── base_widget.py
│   │       ├── time_series_widget.py
│   │       ├── fft_widget.py
│   │       ├── orientation3d_widget.py
│   │       └── …
│   ├── ui_adapter/
│   │   ├── engine_adapter.py
│   │   └── data_bridge.py
│   ├── system/
│   │   ├── monitor.py
│   │   ├── sensor_registry.py
│   │   └── configurators/  # Moved to plugins/configurators/
│   ├── data/
│   │   └── models.py
│   ├── utils/
│   │   ├── logger.py
│   │   ├── timer.py
│   │   ├── threading_utils.py
│   │   ├── file_utils.py
│   │   ├── config_utils.py
│   │   ├── plugin_utils.py
│   │   ├── sensor_utils.py
│   │   ├── sync_utils.py
│   │   ├── plot_utils.py
│   │   └── error_handler.py
├── tests/
│   ├── test_pipeline.py
│   ├── test_plugin_manager.py
│   ├── test_analyzer.py
│   ├── test_sensor_sync.py
│   ├── test_writer.py
│   ├── test_dashboard.py
│   ├── test_widget.py
│   ├── test_configurator.py  # New test file
│   └── …
├── requirements.txt
├── README.md
└── LICENSE
```

---

## III. Kế Hoạch Triển Khai Chi Tiết Theo Giai Đoạn

### Giai Đoạn 1: Xây Dựng Framework Cơ Bản và Cấu Hình Hệ Thống (Đã Hoàn Thành)

#### Task 1.1: Khởi tạo dự án và file main
- **File**: `main.py`
- **Mục đích**: Điểm vào của ứng dụng.
- **Phương thức**: `main()`
- **Trạng thái**: ✅ Hoàn thành
- **Hướng dẫn chỉnh sửa**:
  - Thay đổi đường dẫn config: Sửa `ConfigLoader("config")`.
  - Thêm logic trước `engine.run()` trong `main()`.

#### Task 1.2: Viết Config Loader
- **File**: `src/core/config_loader.py`
- **Mục đích**: Đọc và validate cấu hình từ YAML.
- **Phương thức**: `__init__`, `load`, `_load_file`, `_merge_configs`, `_validate`
- **Trạng thái**: ✅ Hoàn thành
- **Hướng dẫn chỉnh sửa**:
  - Thêm file config: Sửa `load()` để đọc file mới.
  - Thay đổi validate: Sửa `_validate()` để thêm kiểm tra.
  - Thay đổi hợp nhất: Sửa `_merge_configs()`.

#### Task 1.3: Viết Engine
- **File**: `src/core/engine.py`
- **Mục đích**: Điều phối hệ thống.
- **Phương thức**: `__init__`, `setup`, `_setup_pipelines`, `_setup_monitor`, `_setup_sensor_registry`, `run`, `stop`
- **Trạng thái**: ✅ Hoàn thành
- **Hướng dẫn chỉnh sửa**:
  - Thêm thành phần: Sửa `setup()`.
  - Thay đổi pipeline: Sửa `_setup_pipelines()`.
  - Thay đổi giám sát: Sửa `_setup_monitor()`.

#### Task 1.4: Viết Plugin Manager
- **File**: `src/core/plugin_manager.py`
- **Mục đích**: Quản lý load plugin.
- **Phương thức**: `__init__`, `discover_plugins`, `load_plugin`, `create_plugin_instance`
- **Trạng thái**: ✅ Hoàn thành
- **Hướng dẫn chỉnh sửa**:
  - Thêm thư mục plugin: Sửa `__init__`.
  - Thay đổi load: Sửa `load_plugin()`.
  - Thay đổi instance: Sửa `create_plugin_instance()`.

#### Task 1.5: Viết Interface cơ bản
- **Files**:
  - `src/io/readers/base_reader.py`
  - `src/io/writers/base_writer.py`
  - `src/plugins/decoders/base_decoder.py`
  - `src/plugins/processors/base_processor.py`
  - `src/plugins/analyzers/base_analyzer.py`
  - `src/plugins/visualizers/base_visualizer.py`
  - `src/plugins/exporters/base_exporter.py`
- **Mục đích**: Định nghĩa interface cho các thành phần.
- **Trạng thái**: ✅ Hoàn thành
- **Hướng dẫn chỉnh sửa**:
  - Thêm phương thức: Sửa file interface tương ứng.
  - Thay đổi yêu cầu: Sửa phương thức trừu tượng.

#### Task 1.6: Viết Utilities cơ bản
- **Files**:
  - `src/utils/logger.py`
  - `src/utils/timer.py`
  - `src/utils/threading_utils.py`
  - `src/utils/file_utils.py`
  - `src/utils/config_utils.py`
  - `src/utils/plugin_utils.py`
  - `src/utils/sensor_utils.py`
  - `src/utils/sync_utils.py`
  - `src/utils/plot_utils.py`
  - `src/utils/error_handler.py`
- **Mục đích**: Cung cấp hàm tiện ích.
- **Trạng thái**: ✅ Hoàn thành
- **Hướng dẫn chỉnh sửa**:
  - Thay đổi log: Sửa `get_logger()`.
  - Thêm plot: Sửa `plot_utils.py`.
  - Thay đổi lỗi: Sửa `error_handler.py`.

#### Task 1.7: Viết Data Models
- **File**: `src/data/models.py`
- **Mục đích**: Định nghĩa cấu trúc dữ liệu.
- **Classes**: `SensorData`, `ProcessedData`, `AnalysisResult`
- **Trạng thái**: ✅ Hoàn thành
- **Hướng dẫn chỉnh sửa**:
  - Thêm trường: Sửa class trong `models.py`.
  - Thay đổi cấu trúc: Sửa định nghĩa class.

---

### Giai Đoạn 2: Phát Triển Plugin System & Multi-pipeline (Đã Hoàn Thành)

#### Task 2.1: Viết Pipeline Executor
- **File**: `src/core/pipeline.py`
- **Mục đích**: Quản lý quy trình xử lý dữ liệu.
- **Phương thức**: `__init__`, `setup`, `run`, `_read_loop`, `_decode_loop`, `_process_loop`, `_analyze_loop`, `_visualize_loop`, `_write_loop`, `stop`
- **Trạng thái**: ✅ Hoàn thành
- **Hướng dẫn chỉnh sửa**:
  - Thêm bước: Thêm queue và loop mới.
  - Thay đổi xử lý: Sửa loop tương ứng.
  - Thay đổi dừng: Sửa `stop()`.

#### Task 2.2: Viết cấu hình pipeline
- **Files**: `config/default.yaml`, `config/pipelines.yaml`, `config/sensors.yaml`, `config/dashboard.yaml`
- **Mục đích**: Định nghĩa cấu hình hệ thống.
- **Trạng thái**: ✅ Hoàn thành
- **Hướng dẫn chỉnh sửa**:
  - Thêm pipeline: Sửa `pipelines.yaml`.
  - Thay đổi widget: Sửa `dashboard.yaml`.
  - Thay đổi cảm biến: Sửa `sensors.yaml`.

#### Task 2.3: Viết Data Reader
- **Files**: `src/io/readers/file_reader.py`, `src/io/readers/serial_reader.py`, `src/io/readers/bluetooth_reader.py`
- **Mục đích**: Đọc dữ liệu từ các nguồn.
- **Trạng thái**: ✅ Hoàn thành
- **Hướng dẫn chỉnh sửa**:
  - Thay đổi đọc file: Sửa `read()` trong `file_reader.py`.
  - Thay đổi Bluetooth: Sửa `open()` trong `bluetooth_reader.py`.
  - Thêm trạng thái: Sửa `get_status()`.

#### Task 2.4: Viết Data Writer
- **Files**: `src/io/writers/file_writer.py`, `src/io/writers/serial_writer.py`, `src/io/writers/bluetooth_writer.py`
- **Mục đích**: Ghi dữ liệu ra đích đầu ra.
- **Trạng thái**: ✅ Hoàn thành
- **Hướng dẫn chỉnh sửa**:
  - Thay đổi định dạng: Sửa `write()` trong `file_writer.py`.
  - Thay đổi serial: Sửa `write()` trong `serial_writer.py`.
  - Thêm kiểm tra: Sửa `write()`.

#### Task 2.5: Viết Decoder
- **Files**: `src/plugins/decoders/witmotion_decoder.py`, `src/plugins/decoders/custom_decoder.py`
- **Mục đích**: Giải mã dữ liệu thô.
- **Trạng thái**: ✅ Hoàn thành
- **Hướng dẫn chỉnh sửa**:
  - Thay đổi giải mã: Sửa `decode()`.
  - Thêm cấu hình: Sửa `init()`.

#### Task 2.6: Viết Processor
- **File**: `src/plugins/processors/simple_processor.py`
- **Mục đích**: Xử lý dữ liệu cơ bản.
- **Trạng thái**: ✅ Hoàn thành
- **Hướng dẫn chỉnh sửa**:
  - Thay đổi thuật toán: Sửa `process()`.
  - Thêm cấu hình: Sửa `init()`.

#### Task 2.7: Viết Analyzer
- **Files**: `src/plugins/analyzers/anomaly_detector.py`, `src/plugins/analyzers/ml_inference_analyzer.py`
- **Mục đích**: Phân tích dữ liệu nâng cao.
- **Trạng thái**: ✅ Hoàn thành
- **Hướng dẫn chỉnh sửa**:
  - Thay đổi bất thường: Sửa `analyze()` trong `anomaly_detector.py`.
  - Thay đổi ML: Sửa `init()` trong `ml_inference_analyzer.py`.

#### Task 2.8: Viết Visualizer
- **Files**: `src/plugins/visualizers/time_series_visualizer.py`, `src/plugins/visualizers/fft_visualizer.py`, `src/plugins/visualizers/orientation3d_visualizer.py`
- **Mục đích**: Hiển thị dữ liệu đồ thị.
- **Trạng thái**: ✅ Hoàn thành
- **Hướng dẫn chỉnh sửa**:
  - Thay đổi time series: Sửa `visualize()` trong `time_series_visualizer.py`.
  - Thay đổi FFT: Sửa `visualize()` trong `fft_visualizer.py`.
  - Thay đổi 3D: Sửa `visualize()` trong `orientation3d_visualizer.py`.

---

### Giai Đoạn 2.5: Tích Hợp SensorConfigurator (Mới)

#### Task 2.5.1: Viết Interface cho SensorConfigurator
- **File**: `src/plugins/configurators/base_configurator.py`
- **Mục đích**: Định nghĩa interface cho cấu hình cảm biến.
- **Công việc**:
  - Tạo class trừu tượng `BaseSensorConfigurator`.
- **Phương thức cần có**:
  - `__init__(self, config)`: Khởi tạo với cấu hình.
  - `configure(self)`: Gửi cấu hình đến cảm biến.
- **Bước**:
  1. Tạo thư mục `src/plugins/configurators/`.
  2. Tạo file `base_configurator.py`.
  3. Viết class `BaseSensorConfigurator` (target: ≤150 dòng).
  4. Commit với message: "Add BaseSensorConfigurator interface for sensor configuration".
- **Hướng dẫn chỉnh sửa**:
  - Thêm phương thức: Sửa `BaseSensorConfigurator` (e.g., thêm `reset_config()`).
  - Thay đổi yêu cầu: Sửa `configure()` để thêm tham số.

#### Task 2.5.2: Viết Configurator cho WitMotion
- **File**: `src/plugins/configurators/witmotion_configurator.py`
- **Mục đích**: Gửi cấu hình khởi tạo cho cảm biến WitMotion qua Serial.
- **Công việc**:
  - Tạo class `WitMotionConfigurator` kế thừa `BaseSensorConfigurator`.
- **Phương thức cần có**:
  - `__init__(self, config)`: Khởi tạo với cấu hình.
  - `configure(self)`: Gửi chuỗi lệnh Serial.
- **Bước**:
  1. Tạo file `witmotion_configurator.py`.
  2. Viết class với phương thức trên (target: ≤150 dòng).
  3. Commit với message: "Add WitMotionConfigurator for WitMotion sensor configuration".
- **Hướng dẫn chỉnh sửa**:
  - Thay đổi lệnh Serial: Sửa `configure()` (e.g., thêm lệnh mới).
  - Thêm tham số: Sửa `__init__()` để hỗ trợ config mới.

#### Task 2.5.3: Viết Configurator cho MPU6050
- **File**: `src/plugins/configurators/mpu6050_configurator.py`
- **Mục đích**: Gửi cấu hình khởi tạo cho cảm biến MPU6050 qua I2C/Serial.
- **Công việc**:
  - Tạo class `MPU6050Configurator` kế thừa `BaseSensorConfigurator`.
- **Phương thức cần có**:
  - `__init__(self, config)`: Khởi tạo với cấu hình.
  - `configure(self)`: Gửi lệnh cấu hình.
- **Bước**:
  1. Tạo file `mpu6050_configurator.py`.
  2. Viết class với phương thức trên (target: ≤150 dòng).
  3. Commit với message: "Add MPU6050Configurator for MPU6050 sensor configuration".
- **Hướng dẫn chỉnh sửa**:
  - Thay đổi giao thức: Sửa `configure()` (e.g., từ I2C sang Serial).
  - Thêm cấu hình: Sửa `__init__()`.

#### Task 2.5.4: Cập nhật Pipeline Config để hỗ trợ Configurator
- **File**: `config/pipelines.yaml`
- **Mục đích**: Thêm trường `configurator` vào cấu hình pipeline.
- **Công việc**:
  - Thêm `configurator` với `type` và `config` (e.g., `init_sequence`).
- **Ví dụ**:
  ```yaml
  pipelines:
    - id: "imu_front"
      reader:
        type: "SerialReader"
        config:
          port: "COM3"
          baudrate: 115200
      configurator:
        type: "WitMotionConfigurator"
        config:
          init_sequence:
            - "FF AA 69"
            - "FF AA 02 01"
  ```
- **Bước**:
  1. Mở `config/pipelines.yaml`.
  2. Thêm trường `configurator` như trên.
  3. Commit với message: "Update pipelines.yaml to support SensorConfigurator".
- **Hướng dẫn chỉnh sửa**:
  - Thêm configurator mới: Thêm mục mới vào `pipelines.yaml`.
  - Thay đổi init_sequence: Sửa `config.init_sequence`.

#### Task 2.5.5: Cập nhật Engine để gọi Configurator
- **File**: `src/core/engine.py`
- **Mục đích**: Tích hợp `SensorConfigurator` vào `Engine.setup()`.
- **Công việc**:
  - Cập nhật phương thức `setup()` để kiểm tra và gọi `configure()` nếu có `configurator` trong config.
- **Phương thức cần cập nhật**:
  - `setup(self)`: Thêm logic gọi `PluginManager.load_plugin` cho configurator.
- **Bước**:
  1. Mở `src/core/engine.py`.
  2. Cập nhật `setup()` (target: ≤400 dòng tổng cộng).
  3. Commit với message: "Update Engine to support SensorConfigurator".
- **Hướng dẫn chỉnh sửa**:
  - Thay đổi cách gọi configurator: Sửa logic trong `setup()`.
  - Thêm kiểm tra: Sửa `setup()` để validate config trước khi gọi.

---

### Giai Đoạn 3: Xây Dựng UI Cơ Bản và Tích Hợp Cảm Biến

#### Task 3.1: Viết UI Adapter
- **Files**: `src/ui_adapter/engine_adapter.py`, `src/ui_adapter/data_bridge.py`
- **Mục đích**: Kết nối UI và Engine.
- **Công việc**:
  - Tạo `EngineAdapter`: `set_engine`, `start_pipeline`, `stop_pipeline`.
  - Tạo `DataBridge`: `register_visualizer`, `process_data`.
- **Bước**:
  1. Tạo thư mục `src/ui_adapter/`.
  2. Tạo các file và viết class (target: ≤200 dòng mỗi file).
  3. Commit với message: "Add EngineAdapter and DataBridge for UI integration".
- **Hướng dẫn chỉnh sửa**:
  - Thay đổi truyền dữ liệu: Sửa `process_data()` trong `data_bridge.py`.
  - Thêm lệnh pipeline: Sửa `EngineAdapter` (e.g., thêm `pause_pipeline()`).

#### Task 3.2: Viết Main Window
- **File**: `src/ui/main_window.py`
- **Mục đích**: Tạo cửa sổ chính.
- **Phương thức**: `__init__`, `_setup_ui`, `start_engine`, `stop_engine`, `setup_dashboard`, `update_dashboard`, `update_monitor`
- **Bước**:
  1. Tạo thư mục `src/ui/`.
  2. Tạo file và viết `MainWindow` (target: ≤400 dòng).
  3. Commit với message: "Add MainWindow for application UI with config integration".
- **Hướng dẫn chỉnh sửa**:
  - Thay đổi giao diện: Sửa `_setup_ui()`.
  - Thay đổi Engine: Sửa `start_engine()`.
  - Thay đổi hiệu năng: Sửa `update_monitor()`.

#### Task 3.3: Viết Config Panel
- **File**: `src/ui/panels/config_panel.py`
- **Mục đích**: Chỉnh sửa cấu hình.
- **Phương thức**: `_setup_ui`, `load_config`, `save_config`
- **Bước**:
  1. Tạo thư mục `src/ui/panels/`.
  2. Tạo file và viết class (target: ≤150 dòng).
  3. Commit với message: "Add ConfigPanel for configuration UI".
- **Hướng dẫn chỉnh sửa**:
  - Thay đổi giao diện: Sửa `_setup_ui()`.
  - Thay đổi lưu: Sửa `save_config()`.

#### Task 3.4: Viết Connection Panel
- **File**: `src/ui/panels/connection_panel.py`
- **Mục đích**: Quản lý kết nối cảm biến.
- **Phương thức**: `_setup_ui`, `connect_device`, `disconnect_device`
- **Bước**:
  1. Tạo file và viết class (target: ≤150 dòng).
  2. Commit với message: "Add ConnectionPanel for connection UI".
- **Hướng dẫn chỉnh sửa**:
  - Thay đổi giao diện: Sửa `_setup_ui()`.
  - Thay đổi kết nối: Sửa `connect_device()`.

#### Task 3.5: Viết Sensor Panel
- **File**: `src/ui/panels/sensor_panel.py`
- **Mục đích**: Quản lý cảm biến.
- **Phương thức**: `_setup_ui`, `refresh_sensors`, `add_sensor`, `remove_sensor`
- **Bước**:
  1. Tạo file và viết class (target: ≤150 dòng).
  2. Commit với message: "Add SensorPanel for sensor selection".
- **Hướng dẫn chỉnh sửa**:
  - Thay đổi giao diện: Sửa `_setup_ui()`.
  - Thay đổi làm mới: Sửa `refresh_sensors()`.

#### Task 3.6: Viết Sensor Registry
- **File**: `src/system/sensor_registry.py`
- **Mục đích**: Quản lý cảm biến và trạng thái pipeline.
- **Phương thức**: `register_sensor`, `update_status`, `deregister_sensor`, `get_sensor_status`
- **Bước**:
  1. Tạo thư mục `src/system/`.
  2. Tạo file và viết class (target: ≤200 dòng).
  3. Commit với message: "Add SensorRegistry to manage sensors".
- **Hướng dẫn chỉnh sửa**:
  - Thay đổi trạng thái: Sửa `update_status()`.
  - Thêm thông tin: Sửa `register_sensor()`.

#### Task 3.7: Cập nhật Connection Panel để hỗ trợ Configurator
- **File**: `src/ui/panels/connection_panel.py`
- **Mục đích**: Cho phép gửi cấu hình cảm biến từ UI.
- **Công việc**:
  - Thêm nút “Configure Sensor” để gọi `EngineAdapter.send_configuration`.
- **Phương thức cần thêm**:
  - `configure_sensor(sensor_id, config)`: Gửi cấu hình tới `EngineAdapter`.
- **Bước**:
  1. Mở file `connection_panel.py`.
  2. Cập nhật class (target: ≤150 dòng tổng cộng).
  3. Commit với message: "Update ConnectionPanel to support SensorConfigurator".
- **Hướng dẫn chỉnh sửa**:
  - Thay đổi giao diện: Sửa `_setup_ui()` để thêm trường cấu hình.
  - Thay đổi gửi cấu hình: Sửa `configure_sensor()`.

#### Task 3.8: Cập nhật EngineAdapter để hỗ trợ Configurator
- **File**: `src/ui_adapter/engine_adapter.py`
- **Mục đích**: Thêm khả năng gửi cấu hình cảm biến từ UI.
- **Công việc**:
  - Thêm phương thức `send_configuration` để gọi `SensorConfigurator`.
- **Phương thức cần thêm**:
  - `send_configuration(sensor_id, config)`: Gửi cấu hình tới Engine.
- **Bước**:
  1. Mở file `engine_adapter.py`.
  2. Cập nhật class (target: ≤200 dòng tổng cộng).
  3. Commit với message: "Update EngineAdapter to support SensorConfigurator".
- **Hướng dẫn chỉnh sửa**:
  - Thay đổi gửi cấu hình: Sửa `send_configuration()`.
  - Thêm kiểm tra: Sửa để validate config.

---

### Giai Đoạn 4: Xây Dựng Dashboard Linh Hoạt

#### Task 4.1: Viết Dashboard Manager
- **File**: `src/ui/dashboard/dashboard_manager.py`
- **Mục đích**: Quản lý layout dashboard.
- **Phương thức**: `__init__`, `add_widget`, `enable_drag_and_drop`, `save_layout`, `load_layout`, `_init_from_config`
- **Bước**:
  1. Tạo thư mục `src/ui/dashboard/`.
  2. Tạo file và viết class (target: ≤300 dòng).
  3. Commit với message: "Add DashboardManager to manage widget layout with config".
- **Hướng dẫn chỉnh sửa**:
  - Thay đổi layout: Sửa `_init_from_config()`.
  - Thay đổi lưu: Sửa `save_layout()`.
  - Thay đổi kéo thả: Sửa `enable_drag_and_drop()`.

#### Task 4.2: Viết Widget Manager
- **File**: `src/ui/dashboard/widget_manager.py`
- **Mục đích**: Quản lý widget trên dashboard.
- **Phương thức**: `__init__`, `add_widget`, `update_widget`, `resize_widget`, `remove_widget`
- **Bước**:
  1. Tạo file và viết class (target: ≤200 dòng).
  2. Commit với message: "Add WidgetManager to manage widgets".
- **Hướng dẫn chỉnh sửa**:
  - Thay đổi thêm widget: Sửa `add_widget()`.
  - Thay đổi cập nhật: Sửa `update_widget()`.
  - Thay đổi xóa: Sửa `remove_widget()`.

#### Task 4.3: Viết Layout Config
- **File**: `src/ui/dashboard/layout_config.py`
- **Mục đích**: Lưu và khôi phục layout dashboard.
- **Phương thức**: `__init__`, `save`, `load`
- **Bước**:
  1. Tạo file và viết class (target: ≤150 dòng).
  2. Commit với message: "Add LayoutConfig to save and load dashboard layout".
- **Hướng dẫn chỉnh sửa**:
  - Thay đổi định dạng: Sửa `save()`.
  - Thay đổi đọc: Sửa `load()`.

#### Task 4.4: Viết Interface cho Widget
- **File**: `src/ui/visualizers/base_widget.py`
- **Mục đích**: Interface cho widget trên dashboard.
- **Phương thức**: `__init__`, `update_data`, `set_position`, `set_size`
- **Bước**:
  1. Tạo thư mục `src/ui/visualizers/`.
  2. Tạo file và viết class (target: ≤150 dòng).
  3. Commit với message: "Add BaseWidget interface for dashboard widgets".
- **Hướng dẫn chỉnh sửa**:
  - Thêm phương thức: Sửa `BaseWidget`.
  - Thay đổi cập nhật: Sửa `update_data()`.

#### Task 4.5: Viết Time Series Widget
- **File**: `src/ui/visualizers/time_series_widget.py`
- **Mục đích**: Hiển thị time series.
- **Phương thức**: `__init__`, `update_data`, `set_position`, `set_size`
- **Bước**:
  1. Tạo file và viết class (target: ≤150 dòng).
  2. Commit với message: "Add TimeSeriesWidget for time series display".
- **Hướng dẫn chỉnh sửa**:
  - Thay đổi hiển thị: Sửa `update_data()`.
  - Thay đổi giao diện: Sửa `__init__()`.

#### Task 4.6: Viết FFT Widget
- **File**: `src/ui/visualizers/fft_widget.py`
- **Mục đích**: Hiển thị FFT.
- **Phương thức**: `__init__`, `update_data`, `set_position`, `set_size`
- **Bước**:
  1. Tạo file và viết class (target: ≤150 dòng).
  2. Commit với message: "Add FFTWidget for FFT display".
- **Hướng dẫn chỉnh sửa**:
  - Thay đổi hiển thị: Sửa `update_data()`.
  - Thay đổi giao diện: Sửa `__init__()`.

#### Task 4.7: Viết Orientation 3D Widget
- **File**: `src/ui/visualizers/orientation3d_widget.py`
- **Mục đích**: Hiển thị định hướng 3D.
- **Phương thức**: `__init__`, `update_data`, `set_position`, `set_size`
- **Bước**:
  1. Tạo file và viết class (target: ≤150 dòng).
  2. Commit với message: "Add Orientation3DWidget for 3D orientation display".
- **Hướng dẫn chỉnh sửa**:
  - Thay đổi hiển thị: Sửa `update_data()`.
  - Thay đổi giao diện: Sửa `__init__()`.

#### Task 4.8: Cập nhật Dashboard Manager để hỗ trợ kéo thả
- **File**: `src/ui/dashboard/dashboard_manager.py`
- **Mục đích**: Thêm tính năng kéo thả widget.
- **Phương thức cập nhật**: `enable_drag_and_drop`
- **Bước**:
  1. Mở file và cập nhật (target: ≤300 dòng tổng cộng).
  2. Commit với message: "Update DashboardManager to support drag-and-drop".
- **Hướng dẫn chỉnh sửa**:
  - Thay đổi kéo thả: Sửa `enable_drag_and_drop()`.
  - Thêm giới hạn: Sửa `enable_drag_and_drop()`.

#### Task 4.9: Cập nhật Widget Manager để hỗ trợ chỉnh kích thước
- **File**: `src/ui/dashboard/widget_manager.py`
- **Mục đích**: Thêm tính năng chỉnh kích thước widget.
- **Phương thức cập nhật**: `resize_widget`
- **Bước**:
  1. Mở file và cập nhật (target: ≤200 dòng tổng cộng).
  2. Commit với message: "Update WidgetManager to support widget resizing".
- **Hướng dẫn chỉnh sửa**:
  - Thay đổi kích thước: Sửa `resize_widget()`.
  - Thêm hiệu ứng: Sửa `resize_widget()`.

---

### Giai Đoạn 5: Tích Hợp Plugin Control, Export Tools, và Monitor

#### Task 5.1: Viết Plugin Panel
- **File**: `src/ui/panels/plugin_panel.py`
- **Mục đích**: Quản lý plugin.
- **Phương thức**: `_setup_ui`, `load_plugins`, `enable_plugin`, `disable_plugin`
- **Bước**:
  1. Tạo file và viết class (target: ≤150 dòng).
  2. Commit với message: "Add PluginPanel for plugin control".
- **Hướng dẫn chỉnh sửa**:
  - Thay đổi giao diện: Sửa `_setup_ui()`.
  - Thay đổi bật/tắt: Sửa `enable_plugin()` hoặc `disable_plugin()`.

#### Task 5.2: Viết Exporter
- **Files**: `src/plugins/exporters/csv_exporter.py`, `src/plugins/exporters/json_exporter.py`
- **Mục đích**: Xuất dữ liệu ra file.
- **Phương thức**: `export`, `init`, `destroy`
- **Bước**:
  1. Tạo files và viết classes (target: ≤150 dòng mỗi file).
  2. Commit với message: "Add CSVExporter and JSONExporter for data export".
- **Hướng dẫn chỉnh sửa**:
  - Thay đổi CSV: Sửa `export()` trong `csv_exporter.py`.
  - Thay đổi JSON: Sửa `export()` trong `json_exporter.py`.

#### Task 5.3: Viết System Monitor
- **File**: `src/system/monitor.py`
- **Mục đích**: Giám sát hiệu năng.
- **Phương thức**: `get_cpu_usage`, `get_memory_usage`, `log_system_stats`, `run_monitor`
- **Bước**:
  1. Tạo file và viết class (target: ≤300 dòng).
  2. Commit với message: "Add SystemMonitor for resource monitoring".
- **Hướng dẫn chỉnh sửa**:
  - Thay đổi giám sát: Sửa `get_cpu_usage()` hoặc `get_memory_usage()`.
  - Thay đổi log: Sửa `log_system_stats()`.

#### Task 5.4: Viết Monitor Panel
- **File**: `src/ui/panels/monitor_panel.py`
- **Mục đích**: Hiển thị hiệu năng.
- **Phương thức**: `_setup_ui`, `update_stats`
- **Bước**:
  1. Tạo file và viết class (target: ≤150 dòng).
  2. Commit với message: "Add MonitorPanel for system performance display".
- **Hướng dẫn chỉnh sửa**:
  - Thay đổi giao diện: Sửa `_setup_ui()`.
  - Thay đổi số liệu: Sửa `update_stats()`.

---

### Giai Đoạn 6: Kiểm Thử và Hoàn Thiện

#### Task 6.1: Viết Unit Test
- **Files**:
  - `tests/test_pipeline.py`
  - `tests/test_plugin_manager.py`
  - `tests/test_analyzer.py`
  - `tests/test_sensor_sync.py`
  - `tests/test_writer.py`
  - `tests/test_dashboard.py`
  - `tests/test_widget.py`
  - `tests/test_configurator.py` (mới)
- **Mục đích**: Kiểm thử các thành phần.
- **Bước**:
  1. Tạo thư mục `tests/`.
  2. Tạo files và viết test cases (target: ≤150 dòng mỗi file).
  3. Commit với message: "Add unit tests for pipeline, plugin manager, analyzer, sensor sync, writer, dashboard, widget, and configurator".
- **Hướng dẫn chỉnh sửa**:
  - Thêm test case: Sửa file test tương ứng.
  - Thay đổi kiểm tra: Sửa test case.

#### Task 6.2: Viết requirements.txt
- **File**: `requirements.txt`
- **Mục đích**: Liệt kê thư viện.
- **Nội dung**:
  ```
  PyQt6
  pyyaml
  pyserial
  pybluez
  psutil
  numpy
  matplotlib
  pyqtgraph
  pyopengl
  ```
- **Bước**:
  1. Tạo file và viết nội dung.
  2. Commit với message: "Add requirements.txt for project dependencies".
- **Hướng dẫn chỉnh sửa**:
  - Thêm thư viện: Thêm dòng vào `requirements.txt`.
  - Thay đổi phiên bản: Sửa dòng tương ứng.

#### Task 6.3: Viết README.md
- **File**: `README.md`
- **Mục đích**: Hướng dẫn sử dụng.
- **Nội dung**:
  ```
  # IMU Analyzer

  A system to process, configure, and visualize IMU sensor data using PyQt6.

  ## Installation
  1. Clone the repository.
  2. Install dependencies: `pip install -r requirements.txt`
  3. Run the application: `python main.py`

  ## Features
  - Process data from multiple sensors (Serial, File, Bluetooth, CAN, etc.).
  - Configure sensors with custom initialization (e.g., Serial commands, BLE handshake).
  - Visualize data on a flexible dashboard (drag-and-drop, resize widgets).
  - Support for plugins and extensibility.
  - Monitor system performance (CPU, RAM).
  - Export data to CSV and JSON.
  ```
- **Bước**:
  1. Tạo file và viết nội dung.
  2. Commit với message: "Add README.md for project documentation".
- **Hướng dẫn chỉnh sửa**:
  - Thêm hướng dẫn: Sửa `README.md`.
  - Cập nhật tính năng: Sửa phần "Features".

---

## IV. Hướng Dẫn Đặc Biệt Cho Claude

> **Claude ơi, đây là hướng dẫn chi tiết để bạn triển khai dự án:**
> 1. **Chỉ tập trung viết code theo yêu cầu**: Không thêm tính năng hoặc logic ngoài yêu cầu.
> 2. **Tuân thủ số dòng**: Mỗi file có giới hạn số dòng (≤150 hoặc ≤400 tùy file). Nếu vượt, chia nhỏ logic hoặc báo cáo.
> 3. **Viết header comment**: Mỗi file phải có:
>     ```python
>     # File: <file_path>
>     # Purpose: <mục đích của file>
>     # Target Lines: <giới hạn số dòng>
>     ```
> 4. **Liệt kê phương thức**: Trước khi viết file, liệt kê các phương thức trong comment.
> 5. **Commit rõ ràng**: Sau mỗi task, commit với message được cung cấp.
> 6. **Kiểm tra lỗi**: Sau mỗi giai đoạn, chạy ứng dụng để kiểm tra lỗi (e.g., lỗi import).
> 7. **Không làm phức tạp**: Chỉ làm đúng yêu cầu, không thêm logic phức tạp ngoài hướng dẫn.

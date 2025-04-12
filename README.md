# IMU Analyzer

A comprehensive system to configure, process, analyze, and visualize IMU sensor data in a modern, extensible framework.

## Features

- **Multi-source data handling**: Support for various data sources (Serial, File, Bluetooth, CAN, UDP, WebSocket, etc.)
- **Sensor configuration**: Send custom initialization sequences to sensors (Serial commands, BLE handshake, etc.)
- **Modular pipeline architecture**: Process each sensor through a dedicated pipeline
  - DataReader → Decoder → Processor → Analyzer → Visualizer → Writer
- **Concurrent processing**: Run multiple pipelines in parallel without conflicts
- **Interactive dashboard**: Drag-and-drop widgets, resize, and reposition visualizations
- **Plugin-based system**: Easily extend with custom readers, decoders, processors, analyzers, visualizers, writers, and exporters
- **Performance monitoring**: Track CPU, memory, and pipeline throughput
- **Data export**: Save processed data to various formats (CSV, JSON, etc.)

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/imu-analyzer.git
   cd imu-analyzer
   ```

2. Create a virtual environment (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Run the application:
   ```bash
   python main.py
   ```

## Project Structure

```
IMUAnalyzer/
├── main.py                   # Application entry point
├── config/                   # Configuration files
├── src/                      # Source code
│   ├── core/                 # Core components
│   ├── io/                   # I/O handlers (readers/writers)
│   ├── plugins/              # Plugins (decoders, processors, etc.)
│   ├── ui/                   # User interface components
│   ├── system/               # System utilities
│   ├── data/                 # Data models and structures
│   └── utils/                # Utility functions
├── tests/                    # Unit tests
└── docs/                     # Documentation
```

## Configuration

The application uses YAML files for configuration:

- `config/default.yaml`: Default system settings
- `config/pipelines.yaml`: Pipeline configuration
- `config/sensors.yaml`: Sensor definitions
- `config/dashboard.yaml`: Dashboard layout

Example pipeline configuration:

```yaml
pipelines:
  - id: "imu_front"
    enabled: true
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
    decoder:
      type: "WitMotionDecoder"
      config: {}
    processor:
      type: "SimpleProcessor"
      config: {}
    analyzer:
      type: "AnomalyDetector"
      config: 
        threshold: 0.8
    visualizer:
      type: "TimeSeriesVisualizer"
      config: 
        title: "Front IMU"
    writer:
      type: "FileWriter"
      config:
        file_path: "data/imu_front.csv"
```

## Extending the System

### Adding New Reader/Writer

1. Create a new file in `src/io/readers/` or `src/io/writers/`
2. Extend `BaseReader` or `BaseWriter` class
3. Implement required methods

Example:

```python
from src.io.readers.base_reader import BaseReader

class MyCustomReader(BaseReader):
    def __init__(self, config):
        super().__init__(config)
        # Initialize your reader
    
    def open(self):
        # Open data source
        return True
    
    def read(self):
        # Read data from source
        return {"timestamp": time.time(), "data": "..."}
    
    def close(self):
        # Close data source
        return True
```

### Adding New Processor/Analyzer/Visualizer

1. Create a new file in the appropriate directory under `src/plugins/`
2. Extend the corresponding base class
3. Implement required methods

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/my-feature`)
3. Commit your changes (`git commit -am 'Add new feature'`)
4. Push to the branch (`git push origin feature/my-feature`)
5. Create a new Pull Request
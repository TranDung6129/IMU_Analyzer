# File: debug_plugin_paths.py
import os
import sys
import importlib.util

def check_file_existence(file_path):
    """Kiểm tra xem tệp có tồn tại không và in thông tin chi tiết."""
    if os.path.exists(file_path):
        print(f"✅ Tệp tồn tại: {file_path}")
        try:
            spec = importlib.util.spec_from_file_location("module", file_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Liệt kê các lớp trong module
            import inspect
            classes = [name for name, obj in inspect.getmembers(module, inspect.isclass) 
                      if obj.__module__ == module.__name__]
            print(f"   Các lớp trong module: {classes}")
            
            return True
        except Exception as e:
            print(f"❌ Tệp tồn tại nhưng không thể import: {str(e)}")
            return False
    else:
        print(f"❌ Tệp không tồn tại: {file_path}")
        # In thông tin thư mục cha
        parent_dir = os.path.dirname(file_path)
        if os.path.exists(parent_dir):
            print(f"   Thư mục cha tồn tại: {parent_dir}")
            print(f"   Các tệp trong thư mục cha: {os.listdir(parent_dir)}")
        else:
            print(f"   Thư mục cha không tồn tại: {parent_dir}")
        return False

# Thư mục gốc của dự án
project_root = os.path.abspath(os.path.dirname(__file__))
print(f"Thư mục gốc dự án: {project_root}")

# Danh sách các plugin paths cần kiểm tra
plugin_files = [
    "src/io/readers/serial_reader.py",
    "src/io/readers/file_reader.py",
    "src/io/writers/file_writer.py",
    "src/plugins/configurators/witmotion_configurator.py",
    "src/plugins/decoders/custom_decoder.py"
]

# Kiểm tra từng tệp
for rel_path in plugin_files:
    abs_path = os.path.join(project_root, rel_path)
    check_file_existence(abs_path)

# Kiểm tra PYTHONPATH
print("\nPYTHONPATH:")
for path in sys.path:
    print(f" - {path}")

# In cấu trúc thư mục plugin
def print_dir_structure(directory, prefix=""):
    """In cấu trúc thư mục."""
    if not os.path.exists(directory):
        print(f"{prefix}❌ {os.path.basename(directory)}/ (không tồn tại)")
        return
        
    print(f"{prefix}📁 {os.path.basename(directory)}/")
    prefix += "  "
    
    try:
        items = os.listdir(directory)
        for item in sorted(items):
            item_path = os.path.join(directory, item)
            if os.path.isdir(item_path):
                print_dir_structure(item_path, prefix)
            else:
                print(f"{prefix}📄 {item}")
    except PermissionError:
        print(f"{prefix}❌ Không có quyền truy cập")

print("\nCấu trúc thư mục plugin:")
plugin_dirs = [
    os.path.join(project_root, "src", "io"),
    os.path.join(project_root, "src", "plugins")
]

for plugin_dir in plugin_dirs:
    print_dir_structure(plugin_dir)
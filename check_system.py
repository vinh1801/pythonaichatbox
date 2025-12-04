 # Tập tin kiểm tra nhanh hệ thống trước khi chạy ứng dụng
 # Chạy bằng lệnh: python check_system.py
 # Có thể bổ sung thêm các bước kiểm tra khác nếu cần

import os
import sys
import json
import platform
import psutil
from pathlib import Path

def check_python_version():
    # Kiểm tra phiên bản Python có đáp ứng yêu cầu tối thiểu hay không
    version = sys.version_info
    print(f"Python version: {version.major}.{version.minor}.{version.micro}")
    
    if version.major == 3 and version.minor >= 10:
        print("Python version OK")
        return True
    else:
        print("Python version không phù hợp (cần 3.10+)")
        return False

def check_system_resources():
    # Kiểm tra tài nguyên hệ thống (RAM và CPU)
    print(f"\nHệ điều hành: {platform.system()} {platform.release()}")
    
    # RAM
    ram_gb = psutil.virtual_memory().total / (1024**3)
    print(f"RAM: {ram_gb:.1f} GB")
    
    if ram_gb >= 8:
        print("RAM đủ")
    else:
        print("RAM có thể không đủ (khuyên 8GB+)")
    
    # CPU
    cpu_count = psutil.cpu_count()
    print(f"CPU threads: {cpu_count}")
    
    if cpu_count >= 4:
        print("CPU OK")
    else:
        print("CPU có thể chậm")
    
    return ram_gb >= 8 and cpu_count >= 4

def check_dependencies():
    # Kiểm tra các thư viện Python cần thiết đã được cài đặt chưa
    required_packages = [
        'llama_cpp',
        'colorama',
        'orjson',
        'psutil'
    ]
    
    missing = []
    for package in required_packages:
        try:
            __import__(package)
            print(f"✓ {package}")
        except ImportError:
            print(f"✗ {package} - chưa cài")
            missing.append(package)
    
    return len(missing) == 0

def check_project_structure():
    # Kiểm tra các file và thư mục quan trọng của dự án có đầy đủ không
    required_files = [
        'app.py',
        'config.py',
        'requirements.txt',
        'core/model_llama_cpp.py',
        'core/conversation.py',
        'core/utils.py',
        'ui/gui_tk.py'
    ]
    
    required_dirs = [
        'core',
        'ui',
        'models',
        'logs'
    ]
    
    missing_files = []
    missing_dirs = []
    
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
        else:
            print(f"{file}")
    
    for dir in required_dirs:
        if not os.path.exists(dir):
            missing_dirs.append(dir)
        else:
            print(f"{dir}/")
    
    if missing_files:
        print(f"\nThiếu files: {missing_files}")
    if missing_dirs:
        print(f"\nThiếu directories: {missing_dirs}")
    
    return len(missing_files) == 0 and len(missing_dirs) == 0

def check_config():
    # Kiểm tra file config.json có tồn tại và đúng định dạng không
    if not os.path.exists('config.json'):
        print("✗ Không tìm thấy config.json")
        return False
    
    try:
        with open('config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        required_keys = [
            'model_path', 'n_ctx', 'n_threads', 'n_batch',
            'temperature', 'top_p', 'max_tokens', 'history_max_turns'
        ]
        
        missing_keys = []
        for key in required_keys:
            if key not in config:
                missing_keys.append(key)
            else:
                print(f"✓ {key}: {config[key]}")
        
        if missing_keys:
            print(f"\nThiếu keys trong config: {missing_keys}")
            return False
        
        print("Config OK")
        return True
        
    except json.JSONDecodeError as e:
        print(f"Config không hợp lệ: {e}")
        return False

def check_model():
    # Kiểm tra file model có tồn tại và kích thước phù hợp không
    try:
        import config
        
        model_path = config.MODEL_PATH
        
        if not model_path:
            print("Không có đường dẫn model trong config")
            return False
        
        if not os.path.exists(model_path):
            print(f"Không tìm thấy model: {model_path}")
            print("  Vui lòng đặt file .gguf vào thư mục models/")
            return False
        
        # check file size (in MB)
        size_mb = os.path.getsize(model_path) / (1024 * 1024)
        print(f"Model file: {size_mb:.1f} MB")
        
        if size_mb < 100:
            print("Model có thể quá nhỏ")
        elif size_mb > 10000:
            print("Model có thể quá lớn cho máy yếu")
        
        return True
        
    except Exception as e:
        print(f"✗ Lỗi kiểm tra model: {e}")
        return False

def main():
    # Hàm chính gọi lần lượt các bước kiểm tra hệ thống
    print("=== KIỂM TRA HỆ THỐNG CHAT AI OFFLINE ===\n")
    
    checks = [
        ("Python version", check_python_version),
        ("System resources", check_system_resources),
        ("Dependencies", check_dependencies),
        ("Project structure", check_project_structure),
        ("Config file", check_config),
        ("Model file", check_model)
    ]
    
    results = []
    
    for name, check_func in checks:
        print(f"\n--- {name.upper()} ---")
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"✗ Lỗi kiểm tra {name}: {e}")
            results.append((name, False))
    
    # Tổng kết
    print(f"\n{'='*50}")
    print("TỔNG KẾT:")
    
    passed = 0
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{name}: {status}")
        if result:
            passed += 1
    
    print(f"\nKết quả: {passed}/{len(results)} checks passed")
    
    if passed == len(results):
        print("\nHệ thống sẵn sàng!")
        print("Chạy: python app.py")
    else:
        print("\nCần khắc phục các vấn đề trên")

if __name__ == "__main__":
    main()

 # Các hàm tiện ích dùng chung cho ứng dụng chat
 # Bao gồm cấu hình ghi log và lưu lịch sử hội thoại ra file
import os
import json
from datetime import datetime
from typing import Dict, Any, List
import logging


def setup_logging(log_dir="logs"):
    # Thiết lập cấu hình ghi log cơ bản ra file và ra màn hình
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, f"chat_{datetime.now().strftime('%Y%m%d')}.log")
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )


def save_chat_log(user_message, assistant_message, log_dir="logs"):
    # Lưu một cặp câu hỏi/tra lời vào file log dạng JSON dòng
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, f"chat_{datetime.now().strftime('%Y-%m-%d')}.jsonl")
    
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "user": user_message,
        "assistant": assistant_message
    }
    
    try:
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
    except Exception as e:
        logging.error(f"Lỗi lưu log: {e}")


 # Hàm validate_config cũ đã được chuyển sang xử lý trong config.py


def get_model_info(model_path):
    # Lấy thông tin cơ bản về file model (tồn tại hay không, dung lượng)
    if not os.path.exists(model_path):
        return {"exists": False}
    
    try:
        stat = os.stat(model_path)
        size_mb = stat.st_size / (1024 * 1024)
        return {
            "exists": True,
            "size_mb": round(size_mb, 2)
        }
    except Exception as e:
        return {"exists": True, "error": str(e)}

 # File cấu hình cho ứng dụng chat
 # Tập trung các tham số cần chỉnh sửa ở một nơi

 # Cấu hình liên quan đến model
MODEL_PATH = "models/python.gguf"
N_CTX = 2048          # Kích thước cửa sổ ngữ cảnh
N_THREADS = 4         # Số luồng CPU sử dụng khi suy luận
N_BATCH = 16          # Kích thước batch khi suy luận

# Cấu hình sinh văn bản
TEMPERATURE = 0.8     # Mức độ sáng tạo
TOP_P = 0.95         # Lấy mẫu top-p
MAX_TOKENS = 512      # Độ dài tối đa của văn bản sinh

# Cấu hình số lượt hội thoại lưu lại
HISTORY_MAX_TURNS = 6  # Số lượt hội thoại lưu lại

# Cấu hình thư mục lưu log
LOG_DIR = "logs"      # Thư mục lưu file log

# Trả về toàn bộ cấu hình dưới dạng dict (dùng cho các module khác)
def get_config():
    return {
        "model_path": MODEL_PATH,
        "n_ctx": N_CTX,
        "n_threads": N_THREADS,
        "n_batch": N_BATCH,
        "temperature": TEMPERATURE,
        "top_p": TOP_P,
        "max_tokens": MAX_TOKENS,
        "history_max_turns": HISTORY_MAX_TURNS,
        "log_dir": LOG_DIR
    }

 # Hàm kiểm tra cấu hình có hợp lệ không
def validate_config():
    # Kiểm tra file model có tồn tại không
    import os
    if not os.path.exists(MODEL_PATH):
        return False, f"Model file not found: {MODEL_PATH}"
    
    # Kiểm tra các giá trị cấu hình có nằm trong khoảng cho phép
    if N_CTX < 256 or N_CTX > 8192:
        return False, "N_CTX should be between 256-8192"
    
    if TEMPERATURE < 0 or TEMPERATURE > 2:
        return False, "TEMPERATURE should be between 0-2"
        
    return True, "Config OK"

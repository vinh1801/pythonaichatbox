 # Lớp bao bọc thư viện llama-cpp-python
 # Chịu trách nhiệm tải model và sinh văn bản
import os
from llama_cpp import Llama
import config


class ModelWrapper:
    # Lớp quản lý model Llama và các tham số cấu hình
    
    def __init__(self):
        # Khởi tạo đối tượng, đọc cấu hình và gọi hàm tải model
        self.config = config.get_config()
        self.model = None
        self._initialize_model()
    
    def _validate_config(self):
        # Kiểm tra cấu hình trong file config.py có hợp lệ không
        is_valid, message = config.validate_config()
        if not is_valid:
            raise ValueError(f"Config error: {message}")
    
    def _initialize_model(self):
        # Tải model từ đường dẫn cấu hình
        self._validate_config()  # Kiểm tra cấu hình trước khi tải
        
        model_path = self.config.get('model_path')
        
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Không tìm thấy model: {model_path}")
        
        print(f"Đang tải model từ: {model_path}")
        
        try:
            self.model = Llama(
                model_path=model_path,
                n_ctx=self.config.get('n_ctx', 1024),
                n_threads=self.config.get('n_threads', 4),
                n_batch=self.config.get('n_batch', 16),
                verbose=False
            )
            print("Model đã được tải thành công!")
        except Exception as e:
            raise RuntimeError(f"Lỗi khi tải model: {e}")
    
    def generate(self, prompt, max_tokens=None, temperature=None, top_p=None, stream=None):
        # Gọi model để sinh văn bản từ prompt đầu vào
        if self.model is None:
            raise RuntimeError("Model chưa được khởi tạo")
        
        # Nếu tham số không được truyền vào thì dùng giá trị trong cấu hình
        max_tokens = max_tokens or self.config.get('max_tokens', 256)
        temperature = temperature or self.config.get('temperature', 0.7)
        top_p = top_p or self.config.get('top_p', 0.9)
        stream = stream if stream is not None else self.config.get('stream', False)
        
        try:
            if stream:
                return self._generate_stream(prompt, max_tokens, temperature, top_p)
            else:
                return self._generate_once(prompt, max_tokens, temperature, top_p)
        except Exception as e:
            raise RuntimeError(f"Lỗi khi sinh text: {e}")
    
    def _generate_once(self, prompt, max_tokens, temperature, top_p):
        # Sinh câu trả lời một lần, trả về toàn bộ chuỗi kết quả
        response = self.model(
            prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            stop=["### Human:", "\n### Human:", "Human:", "\nHuman:"],
            echo=False
        )
        
        return response['choices'][0]['text'].strip()
    
    def _generate_stream(self, prompt, max_tokens, temperature, top_p):
        # Sinh câu trả lời dạng từng phần, trả ra luồng văn bản
        stream = self.model(
            prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            stop=["### Human:", "\n### Human:", "Human:", "\nHuman:"],
            echo=False,
            stream=True
        )
        
        for chunk in stream:
            if 'choices' in chunk and len(chunk['choices']) > 0:
                delta = chunk['choices'][0].get('text', '')
                if delta:
                    yield delta
    
    def get_config(self):
        # Trả về bản sao cấu hình hiện tại của model
        return self.config.copy()
    
    def update_config(self, new_config):
        # Cập nhật một số tham số cấu hình trong lúc chương trình đang chạy
        # Lưu ý: không ghi lại vào file config.py
        self.config.update(new_config)
    
    def is_ready(self):
        # Kiểm tra model đã được tải thành công hay chưa
        return self.model is not None

 # Lớp quản lý hội thoại
 # Lưu trữ và xử lý lịch sử các lượt chat
from collections import deque
from typing import List, Dict, Any


class ConversationManager:
    # Lớp lưu và quản lý lịch sử hội thoại
    
    def __init__(self, config):
        self.config = config
        self.history = deque(maxlen=config.get('history_max_turns', 6) * 2)
        
    def add_user_message(self, message):
        # Thêm tin nhắn của người dùng vào lịch sử
        if message.strip():
            self.history.append({"role": "user", "content": message.strip()})
    
    def add_assistant_message(self, message):
        # Thêm câu trả lời của mô hình vào lịch sử
        if message.strip():
            self.history.append({"role": "assistant", "content": message.strip()})
    
    def build_prompt(self, user_input):
        # Xây dựng chuỗi prompt gửi cho mô hình từ lịch sử và câu hỏi mới
        prompt_parts = []
        
        # Thêm lịch sử hội thoại (không bao gồm tin nhắn hiện tại)
        for message in self.history:
            role = message["role"]
            content = message["content"]
            if role == "user":
                prompt_parts.append(f"### Human: {content}")
            else:
                prompt_parts.append(f"### Assistant: {content}")
        
        # Thêm câu hỏi mới
        prompt_parts.append(f"### Human: {user_input}")
        prompt_parts.append("### Assistant:")
        
        return "\n".join(prompt_parts)
    
    def clear_history(self):
        # Xóa toàn bộ lịch sử hội thoại đang lưu
        self.history.clear()
    
    def get_history_count(self):
        # Lấy số lượng tin nhắn đang có trong lịch sử
        return len(self.history)
    
    def is_history_full(self):
        # Kiểm tra lịch sử đã đầy đến giới hạn cấu hình hay chưa
        return len(self.history) >= self.history.maxlen
    
    def trim_history(self, keep_turns=3):
        # Cắt bớt các tin nhắn cũ, chỉ giữ lại một số lượt gần nhất
        if len(self.history) <= keep_turns * 2:
            return
        
        history_list = list(self.history)
        trimmed_history = history_list[-(keep_turns * 2):]
        
        self.history.clear()
        for message in trimmed_history:
            self.history.append(message)

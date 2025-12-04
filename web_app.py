import re
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import config
from core.model_llama_cpp import ModelWrapper
from core.conversation import ConversationManager
from core.database_utils import MongoDBManager
import uuid
import webbrowser
import threading
import time
import os

app = Flask(__name__)
app.secret_key = "bat_ky_chuoi_bi_mat_nao_ban_thich_o_day"  # Bắt buộc phải có để dùng Session

# Khởi tạo các thành phần dùng chung cho web app
conf = config.get_config()
model_wrapper = ModelWrapper()

try:
    mongo_manager = MongoDBManager()
    print("✅ Đã kết nối MongoDB")
except Exception:
    mongo_manager = None

# Lưu ID phiên chat tạm thời cho mỗi người dùng trong bộ nhớ RAM của server
# Dạng: key là username, value là conversation_id hiện tại
user_sessions = {}

# Quản lý ConversationManager riêng cho từng người dùng
# Dạng: key là username, value là đối tượng ConversationManager
user_managers = {}


def get_user_manager(username):
    """Lấy ConversationManager riêng cho từng user, nếu chưa có thì tạo mới."""
    if username not in user_managers:
        user_managers[username] = ConversationManager(conf)
    return user_managers[username]

 # Các route liên quan đến đăng nhập / đăng ký / đăng xuất
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        data = request.json
        username = data.get("username")
        password = data.get("password")
        
        if mongo_manager and mongo_manager.login_user(username, password):
            session['user'] = username # Lưu trạng thái đăng nhập
            
            # Tạo session chat mới nếu chưa có
            if username not in user_sessions:
                user_sessions[username] = str(uuid.uuid4())
                
            return jsonify({"status": "success"})
        return jsonify({"status": "fail", "msg": "Sai tài khoản hoặc mật khẩu!"})
    
    return render_template("login.html")

@app.route("/register", methods=["POST"])
def register():
    data = request.json
    username = data.get("username", "").strip()
    password = data.get("password", "")
    confirm_password = data.get("confirm_password", "")
    
    # Bước 1: Kiểm tra dữ liệu có bị để trống không
    if not username or not password or not confirm_password:
        return jsonify({"status": "fail", "msg": "Vui lòng điền đầy đủ thông tin!"})

    # Bước 2: Kiểm tra độ dài tên đăng nhập (ít nhất 3 ký tự)
    if len(username) < 3:
        return jsonify({"status": "fail", "msg": "Tên đăng nhập phải từ 3 ký tự trở lên!"})

    # Bước 3: Kiểm tra mật khẩu và mật khẩu xác nhận có trùng nhau
    if password != confirm_password:
        return jsonify({"status": "fail", "msg": "Mật khẩu xác nhận không khớp!"})

    # Bước 4: Kiểm tra độ mạnh mật khẩu (>= 6 ký tự, có cả chữ và số)
    # Regex: Ít nhất 6 ký tự, chứa ít nhất 1 chữ cái và 1 chữ số
    if len(password) < 6 or not re.search(r"[a-zA-Z]", password) or not re.search(r"\d", password):
        return jsonify({"status": "fail", "msg": "Mật khẩu yếu! Cần ít nhất 6 ký tự, bao gồm cả chữ và số."})
        
    # Bước 5: Gọi lớp làm việc với MongoDB để tạo tài khoản
    if mongo_manager:
        success, msg = mongo_manager.register_user(username, password)
        return jsonify({"status": "success" if success else "fail", "msg": msg})
    
    return jsonify({"status": "fail", "msg": "Lỗi kết nối Database"})

@app.route("/logout")
def logout():
    """Đăng xuất và xóa dữ liệu phiên đang lưu trong RAM cho user đó."""
    username = session.get('user')
    if username:
        # Xóa thông tin phiên chat và ConversationManager khỏi bộ nhớ
        user_sessions.pop(username, None)
        user_managers.pop(username, None)
    session.pop('user', None)
    return redirect(url_for('login'))

 # Route trang chính, chỉ cho truy cập khi đã đăng nhập
@app.route("/")
def home():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template("index.html", username=session['user'])

 # API chính để nhận câu hỏi và trả về câu trả lời của mô hình (yêu cầu đã đăng nhập)
@app.route("/get_response", methods=["POST"])
def get_bot_response():
    """Xử lý câu hỏi từ giao diện web và trả về câu trả lời của mô hình cho đúng user."""
    if 'user' not in session:
        return jsonify({"response": "Vui lòng đăng nhập lại!"})
    
    username = session['user']
    user_input = request.json.get("msg")
    
    # Lấy ConversationManager riêng của user này
    manager = get_user_manager(username)
    
    # Lấy ID phiên chat hiện tại của người dùng
    current_conv_id = user_sessions.get(username, str(uuid.uuid4()))

    # Xây dựng prompt từ lịch sử của riêng user
    prompt = manager.build_prompt(user_input)
    
    # Gọi model để sinh câu trả lời
    ai_response = model_wrapper.generate(prompt)
    
    # Cập nhật lịch sử hội thoại riêng cho user
    manager.add_user_message(user_input)
    manager.add_assistant_message(ai_response)
    
    if mongo_manager:
        # Lưu nội dung hội thoại kèm theo username để phân biệt người dùng
        mongo_manager.save_message(user_input, ai_response, current_conv_id, username)

    return jsonify({"response": ai_response})

@app.route("/api/history", methods=["GET"])
def get_history_list():
    if 'user' not in session: return jsonify([])
    if mongo_manager:
        return jsonify(mongo_manager.get_conversation_list(session['user']))
    return jsonify([])


@app.route("/api/settings", methods=["GET"])
def get_settings():
    """Trả về các tham số sinh văn bản hiện tại của mô hình cho giao diện web."""
    cfg = model_wrapper.get_config()
    return jsonify({
        "temperature": cfg.get("temperature"),
        "max_tokens": cfg.get("max_tokens"),
        "top_p": cfg.get("top_p")
    })


@app.route("/api/settings", methods=["POST"])
def update_settings():
    """Cập nhật tham số sinh văn bản (temperature, max_tokens, top_p) từ giao diện web."""
    if 'user' not in session:
        return jsonify({"status": "fail", "msg": "Vui lòng đăng nhập lại."}), 401

    data = request.json or {}
    try:
        new_temp = float(data.get("temperature"))
        new_max_tokens = int(data.get("max_tokens"))
        new_top_p = float(data.get("top_p"))
    except (TypeError, ValueError):
        return jsonify({"status": "fail", "msg": "Giá trị tham số không hợp lệ."}), 400

    # Cập nhật cấu hình runtime của model
    model_wrapper.update_config({
        "temperature": new_temp,
        "max_tokens": new_max_tokens,
        "top_p": new_top_p
    })

    return jsonify({"status": "success"})

@app.route("/api/load_chat/<conv_id>", methods=["GET"])
def load_chat_content(conv_id):
    """Tải nội dung một cuộc trò chuyện cũ cho đúng user và nạp lại context vào manager riêng."""
    if 'user' not in session:
        return jsonify([])
    username = session['user']
    
    # Cập nhật ID phiên chat hiện tại khi người dùng chọn cuộc trò chuyện khác
    user_sessions[username] = conv_id
    
    # Lấy ConversationManager riêng và xóa lịch sử cũ trong bộ nhớ
    manager = get_user_manager(username)
    manager.clear_history()
    
    messages = []
    if mongo_manager:
        raw_msgs = mongo_manager.get_messages_by_conversation_id(conv_id, username)
        for m in raw_msgs:
            u_msg = m.get("user_message")
            a_resp = m.get("assistant_response")

            messages.append({"role": "user", "content": u_msg})
            messages.append({"role": "bot", "content": a_resp})
            
            # Nạp lại context vào ConversationManager riêng
            manager.add_user_message(u_msg)
            manager.add_assistant_message(a_resp)
            
    return jsonify(messages)

@app.route("/new_chat", methods=["POST"])
def new_chat():
    if 'user' in session:
        username = session['user']
        user_sessions[username] = str(uuid.uuid4())
        # Xóa lịch sử hội thoại trong ConversationManager riêng nếu đã tồn tại
        if username in user_managers:
            user_managers[username].clear_history()
    return jsonify({"status": "success"})

@app.route("/clear_all", methods=["POST"])
def clear_all_db():
    if 'user' in session and mongo_manager:
        mongo_manager.delete_all_conversations(session['user'])
    return new_chat()

def open_browser():
    time.sleep(1.5)
    webbrowser.open_new("http://localhost:5000")

if __name__ == "__main__":
    threading.Thread(target=open_browser).start()
    app.run(host="0.0.0.0", port=5000, debug=False)
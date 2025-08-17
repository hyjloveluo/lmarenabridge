# id_updater.py
#
# 这是一个经过升级的、一次性的HTTP服务器，用于根据用户选择的模式
# (DirectChat 或 Battle) 接收来自油猴脚本的会话信息，
# 并将其更新到 config.jsonc 文件中。

import http.server
import socketserver
import json
import re
import threading
import os
import requests

# --- 配置 ---
HOST = "127.0.0.1"
PORT = 5103
CONFIG_PATH = 'config.jsonc'

def read_config():
    """读取并解析 config.jsonc 文件，移除注释以便解析。"""
    if not os.path.exists(CONFIG_PATH):
        print(f"❌ 错误：配置文件 '{CONFIG_PATH}' 不存在。")
        return None
    try:
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            # 正则表达式移除行注释和块注释
            content = re.sub(r'//.*', '', f.read())
            content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
            return json.loads(content)
    except Exception as e:
        print(f"❌ 读取或解析 '{CONFIG_PATH}' 时发生错误: {e}")
        return None

def save_config_value(key, value):
    """
    安全地更新 config.jsonc 中的单个键值对，保留原始格式和注释。
    仅适用于值为字符串或数字的情况。
    """
    try:
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            content = f.read()

        # 使用正则表达式安全地替换值
        # 它会查找 "key": "any value" 并替换 "any value"
        pattern = re.compile(rf'("{key}"\s*:\s*")[^"]*(")')
        new_content, count = pattern.subn(rf'\g<1>{value}\g<2>', content, 1)

        if count == 0:
            print(f"🤔 警告: 未能在 '{CONFIG_PATH}' 中找到键 '{key}'。")
            return False

        with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
            f.write(new_content)
        return True
    except Exception as e:
        print(f"❌ 更新 '{CONFIG_PATH}' 时发生错误: {e}")
        return False

def save_session_ids(session_id, message_id):
    """将新的会话ID更新到 config.jsonc 文件。"""
    print(f"\n📝 正在尝试将ID写入 '{CONFIG_PATH}'...")
    res1 = save_config_value("session_id", session_id)
    res2 = save_config_value("message_id", message_id)
    if res1 and res2:
        print(f"✅ 成功更新ID。")
        print(f"   - session_id: {session_id}")
        print(f"   - message_id: {message_id}")
    else:
        print(f"❌ 更新ID失败。请检查上述错误信息。")


class RequestHandler(http.server.SimpleHTTPRequestHandler):
    def _send_cors_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')

    def do_OPTIONS(self):
        self.send_response(204)
        self._send_cors_headers()
        self.end_headers()

    def do_POST(self):
        if self.path == '/update':
            try:
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                data = json.loads(post_data)

                session_id = data.get('sessionId')
                message_id = data.get('messageId')

                if session_id and message_id:
                    print("\n" + "=" * 50)
                    print("🎉 成功从浏览器捕获到ID！")
                    print(f"  - Session ID: {session_id}")
                    print(f"  - Message ID: {message_id}")
                    print("=" * 50)

                    save_session_ids(session_id, message_id)

                    self.send_response(200)
                    self._send_cors_headers()
                    self.end_headers()
                    self.wfile.write(b'{"status": "success"}')

                    print("\n任务完成，服务器将在1秒后自动关闭。")
                    threading.Thread(target=self.server.shutdown).start()

                else:
                    self.send_response(400, "Bad Request")
                    self._send_cors_headers()
                    self.end_headers()
                    self.wfile.write(b'{"error": "Missing sessionId or messageId"}')
            except Exception as e:
                self.send_response(500, "Internal Server Error")
                self._send_cors_headers()
                self.end_headers()
                self.wfile.write(f'{{"error": "Internal server error: {e}"}}'.encode('utf-8'))
        else:
            self.send_response(404, "Not Found")
            self._send_cors_headers()
            self.end_headers()

    def log_message(self, format, *args):
        return

def run_server():
    with socketserver.TCPServer((HOST, PORT), RequestHandler) as httpd:
        print("\n" + "="*50)
        print("  🚀 会话ID更新监听器已启动")
        print(f"  - 监听地址: http://{HOST}:{PORT}")
        print("  - 请在浏览器中操作LMArena页面以触发ID捕获。")
        print("  - 捕获成功后，此脚本将自动关闭。")
        print("="*50)
        httpd.serve_forever()

def notify_api_server():
    """通知主 API 服务器，ID 更新流程已开始。"""
    api_server_url = "http://127.0.0.1:5102/internal/start_id_capture"
    try:
        response = requests.post(api_server_url, timeout=3)
        if response.status_code == 200:
            print("✅ 已成功通知主服务器激活ID捕获模式。")
            return True
        else:
            print(f"⚠️ 通知主服务器失败，状态码: {response.status_code}。")
            print(f"   - 错误信息: {response.text}")
            return False
    except requests.ConnectionError:
        print("❌ 无法连接到主 API 服务器。请确保 api_server.py 正在运行。")
        return False
    except Exception as e:
        print(f"❌ 通知主服务器时发生未知错误: {e}")
        return False

if __name__ == "__main__":
    config = read_config()
    if not config:
        exit(1)

    # --- 获取用户选择 ---
    last_mode = config.get("id_updater_last_mode", "direct_chat")
    mode_map = {"a": "direct_chat", "b": "battle"}
    
    prompt = f"请选择模式 [a: DirectChat, b: Battle] (默认为上次选择的: {last_mode}): "
    choice = input(prompt).lower().strip()

    if not choice:
        mode = last_mode
    else:
        mode = mode_map.get(choice)
        if not mode:
            print(f"无效输入，将使用默认值: {last_mode}")
            mode = last_mode

    save_config_value("id_updater_last_mode", mode)
    print(f"当前模式: {mode.upper()}")
    
    if mode == 'battle':
        last_target = config.get("id_updater_battle_target", "A")
        target_prompt = f"请选择要更新的消息 [A(使用search模型必须选A) 或 B] (默认为上次选择的: {last_target}): "
        target_choice = input(target_prompt).upper().strip()

        if not target_choice:
            target = last_target
        elif target_choice in ["A", "B"]:
            target = target_choice
        else:
            print(f"无效输入，将使用默认值: {last_target}")
            target = last_target
        
        save_config_value("id_updater_battle_target", target)
        print(f"Battle 目标: Assistant {target}")
        print("请注意：无论选择A或B，捕获到的ID都会更新到主 session_id 和 message_id。")

    # 在启动监听之前，先通知主服务器
    if notify_api_server():
        run_server()
        print("服务器已关闭。")
    else:
        print("\n由于无法通知主服务器，ID更新流程中断。")
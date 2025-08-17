# model_updater.py
import requests
import time
import logging

# --- 配置 ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
API_SERVER_URL = "http://127.0.0.1:5102" # 与 api_server.py 中的端口匹配

def trigger_model_update():
    """
    通知主服务器开始模型列表更新流程。
    """
    try:
        logging.info("正在向主服务器发送模型列表更新请求...")
        response = requests.post(f"{API_SERVER_URL}/internal/request_model_update")
        response.raise_for_status()
        
        if response.json().get("status") == "success":
            logging.info("✅ 已成功请求服务器更新模型列表。")
            logging.info("请确保 LMArena 页面已打开，脚本将自动从页面提取最新模型列表。")
            logging.info("服务器将把结果保存在 `available_models.json` 文件中。")
        else:
            logging.error(f"❌ 服务器返回错误: {response.json().get('message')}")

    except requests.exceptions.RequestException as e:
        logging.error(f"❌ 无法连接到主服务器 ({API_SERVER_URL})。")
        logging.error("请确保 `api_server.py` 正在运行中。")
    except Exception as e:
        logging.error(f"发生未知错误: {e}")

if __name__ == "__main__":
    trigger_model_update()
    # 脚本执行完毕后自动退出
    time.sleep(2)

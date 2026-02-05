import os
import json
import requests
from http.server import BaseHTTPRequestHandler
import io


# 新增：通用响应函数（适配 BaseHTTPRequestHandler 输出）
def send_response_handler(handler, status_code, body, headers=None):
    default_headers = {
        "Content-Type": "application/json; charset=utf-8",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type"
    }
    # 合并自定义 headers
    if headers:
        default_headers.update(headers)

    # 发送状态码和响应头
    handler.send_response(status_code)
    for k, v in default_headers.items():
        handler.send_header(k, v)
    handler.end_headers()

    # 发送响应体（需编码为 bytes）
    handler.wfile.write(json.dumps(body, ensure_ascii=False).encode("utf-8"))


# Vercel 原生 Python 函数要求：必须定义 handler 类，继承 BaseHTTPRequestHandler
class handler(BaseHTTPRequestHandler):
    # 处理 OPTIONS 请求（解决跨域预检）
    def do_OPTIONS(self):
        send_response_handler(self, 204, {})

    # 处理 POST 请求（核心业务逻辑）
    def do_POST(self):
        # 1. 读取请求体
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            # 读取并解码请求体
            post_data = self.rfile.read(content_length).decode('utf-8')
            body = json.loads(post_data) if content_length > 0 else {}
        except json.JSONDecodeError as e:
            send_response_handler(self, 400, {"error": "Invalid JSON", "details": str(e)})
            return
        except Exception as e:
            send_response_handler(self, 400, {"error": "Failed to read request body", "details": str(e)})
            return

        # 2. 校验必要参数
        query = body.get("query")
        user_id = body.get("userId", "default_user")
        if not query:
            send_response_handler(self, 400, {"error": "Missing query"})
            return

        # 3. 读取环境变量
        BOT_ID = os.environ.get("COZE_BOT_ID")
        ACCESS_TOKEN = os.environ.get("COZE_ACCESS_TOKEN")
        if not BOT_ID or not ACCESS_TOKEN:
            send_response_handler(self, 500, {"error": "Missing Coze credentials (COZE_BOT_ID/ACCESS_TOKEN)"})
            return

        # 4. 调用 Coze API（核心逻辑）
        try:
            coze_resp = requests.post(
                "https://api.coze.com/v1/bot/chat",
                json={
                    "bot_id": BOT_ID,
                    "user_id": user_id,
                    "query": query
                },
                headers={
                    "Authorization": f"Bearer {ACCESS_TOKEN}",
                    "Content-Type": "application/json"
                },
                timeout=10
            )
            coze_resp.raise_for_status()  # 触发 HTTP 错误异常
            coze_data = coze_resp.json()

            # 解析 Coze 回复
            reply = "无回复"
            for msg in coze_data.get("messages", []):
                if msg.get("role") == "assistant":
                    reply = msg.get("content", "无内容")
                    break

            # 返回成功响应
            send_response_handler(self, 200, {"reply": reply})

        # 细分异常处理
        except requests.exceptions.HTTPError as e:
            send_response_handler(self, 500, {
                "error": "Coze API HTTP Error",
                "status_code": coze_resp.status_code if 'coze_resp' in locals() else None,
                "details": str(e)
            })
        except requests.exceptions.Timeout:
            send_response_handler(self, 500, {"error": "Coze API Request Timeout (10s)"})
        except requests.exceptions.ConnectionError:
            send_response_handler(self, 500, {"error": "Coze API Connection Failed"})
        except Exception as e:
            send_response_handler(self, 500, {"error": "Unknown Error", "details": str(e)})

    # 覆盖 log_message 方法（关闭不必要的日志输出）
    def log_message(self, format, *args):
        return
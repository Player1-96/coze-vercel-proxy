import os
import json
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)


# 这样写可以同时支持 根路径 和 显式的 /api/coze_proxy 路径
@app.route('/', methods=['POST', 'OPTIONS'])
@app.route('/api/coze_proxy', methods=['POST', 'OPTIONS'])
def handle_proxy():
    # 处理浏览器的预检请求 (CORS)
    if request.method == 'OPTIONS':
        return '', 204

    # 1. 获取并解析 JSON Body
    body = request.get_json(silent=True)
    if not body:
        return jsonify({"error": "Invalid JSON or Empty Body"}), 400

    query = body.get("query")
    user_id = body.get("userId", "default_user")

    if not query:
        return jsonify({"error": "Missing 'query' field in JSON"}), 400

    # 2. 从 Vercel 环境变量获取配置
    BOT_ID = os.environ.get("COZE_BOT_ID")
    ACCESS_TOKEN = os.environ.get("COZE_ACCESS_TOKEN")

    if not BOT_ID or not ACCESS_TOKEN:
        return jsonify({
            "error": "Server configuration missing",
            "details": "COZE_BOT_ID or COZE_ACCESS_TOKEN not set in Vercel Environment Variables"
        }), 500

    # 3. 调用 Coze 官方 API
    try:
        # 注意：这里使用的是 Coze 的非流式对话接口
        resp = requests.post(
            "https://api.coze.com/v1/bot/chat",
            json={
                "bot_id": BOT_ID,
                "user_id": user_id,
                "query": query,
                "stream": False  # 确保是非流式返回，方便处理
            },
            headers={
                "Authorization": f"Bearer {ACCESS_TOKEN}",
                "Content-Type": "application/json"
            },
            timeout=30  # 增加超时时间，AI 响应可能较慢
        )

        # 检查 HTTP 状态码
        resp.raise_for_status()
        data = resp.json()

        # 4. 提取回复内容
        # Coze API 的返回结构通常在 messages 列表中寻找 role 为 assistant 的内容
        reply = "未获取到有效回复"
        if "messages" in data:
            for msg in data.get("messages", []):
                if msg.get("role") == "assistant" and msg.get("type") == "answer":
                    reply = msg.get("content", reply)
                    break
        elif "msg" in data:  # 兼容某些 API 版本的报错提示
            reply = data.get("msg", reply)

        return jsonify({
            "success": True,
            "reply": reply,
            "raw_data": data if os.environ.get("DEBUG") == "true" else None
        })

    except requests.exceptions.RequestException as e:
        return jsonify({
            "error": "Failed to connect to Coze API",
            "details": str(e)
        }), 502
    except Exception as e:
        return jsonify({
            "error": "Internal Server Error",
            "details": str(e)
        }), 500

# 注意：Vercel 环境下不需要 app.run()
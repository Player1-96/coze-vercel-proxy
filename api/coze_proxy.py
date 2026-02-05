import os
import json
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)


@app.route('/api/coze_proxy', methods=['POST'])
@app.route('/', methods=['POST']) # 兼容根目录 POST 访问
def handle_proxy():
    # 1. 解析 JSON
    body = request.get_json(silent=True)
    if not body:
        return jsonify({"error": "Invalid JSON"}), 400

    query = body.get("query")
    user_id = body.get("userId", "default_user")

    if not query:
        return jsonify({"error": "Missing query"}), 400

    # 2. 环境变量
    BOT_ID = os.environ.get("COZE_BOT_ID")
    ACCESS_TOKEN = os.environ.get("COZE_ACCESS_TOKEN")

    if not BOT_ID or not ACCESS_TOKEN:
        return jsonify({"error": "Missing Coze credentials"}), 500

    # 3. 调用 Coze
    try:
        resp = requests.post(
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
        resp.raise_for_status()
        data = resp.json()

        reply = "无回复"
        # 注意：根据 Coze API 版本不同，message 结构可能不同，请根据实际情况调整
        for msg in data.get("messages", []):
            if msg.get("role") == "assistant":
                reply = msg.get("content", "无内容")
                break

        return jsonify({"reply": reply})

    except Exception as e:
        return jsonify({"error": str(e)}), 500
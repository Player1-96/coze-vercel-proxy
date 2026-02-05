import os
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)


@app.route('/', defaults={'path': ''}, methods=['GET', 'POST', 'OPTIONS'])
@app.route('/<path:path>', methods=['GET', 'POST', 'OPTIONS'])
def handle_proxy(path):
    if request.method == 'GET':
        return jsonify({"status": "running", "path": path}), 200

    if request.method == 'OPTIONS':
        return '', 204

    body = request.get_json(silent=True)
    if not body or "query" not in body:
        return jsonify({"error": "Missing 'query' in JSON body"}), 400

    BOT_ID = os.environ.get("COZE_BOT_ID")
    ACCESS_TOKEN = os.environ.get("COZE_ACCESS_TOKEN")

    if not BOT_ID or not ACCESS_TOKEN:
        return jsonify({"error": "Missing Environment Variables"}), 500

    try:
        resp = requests.post(
            "https://api.coze.com/v1/bot/chat",
            json={
                "bot_id": BOT_ID,
                "user_id": body.get("userId", "default_user"),
                "query": body.get("query"),
                "stream": False
            },
            headers={
                "Authorization": f"Bearer {ACCESS_TOKEN}",
                "Content-Type": "application/json"
            },
            timeout=30
        )
        resp.raise_for_status()
        return jsonify(resp.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# 关键：必须显式将 app 赋值给 handler，这是解决 issubclass 报错的核心
handler = app
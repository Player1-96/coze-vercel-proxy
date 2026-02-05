import os
import json
import requests


def handler(request):
    # 1. Method 校验
    if request.method != "POST":
        return {
            "statusCode": 405,
            "body": json.dumps({"error": "Method not allowed"}),
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            }
        }

    # 2. 解析 JSON
    try:
        body = request.json()
    except Exception as e:
        return {
            "statusCode": 400,
            "body": json.dumps(
                {"error": "Invalid JSON", "details": str(e)},
                ensure_ascii=False
            ),
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            }
        }

    query = body.get("query")
    user_id = body.get("userId", "default_user")

    if not query:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "Missing query"}, ensure_ascii=False),
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            }
        }

    # 3. 环境变量
    BOT_ID = os.environ.get("COZE_BOT_ID")
    ACCESS_TOKEN = os.environ.get("COZE_ACCESS_TOKEN")

    if not BOT_ID or not ACCESS_TOKEN:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "Missing Coze credentials"}, ensure_ascii=False),
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            }
        }

    # 4. 调用 Coze
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
        for msg in data.get("messages", []):
            if msg.get("role") == "assistant":
                reply = msg.get("content", "无内容")
                break

        return {
            "statusCode": 200,
            "body": json.dumps({"reply": reply}, ensure_ascii=False),
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            }
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)}, ensure_ascii=False),
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            }
        }
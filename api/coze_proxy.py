import os
import json
import requests


# 新增：通用响应函数
def create_response(status_code, body, headers=None):
    default_headers = {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*"
    }
    # 合并自定义 headers（如果有）
    if headers:
        default_headers.update(headers)
    return {
        "statusCode": status_code,
        "body": json.dumps(body, ensure_ascii=False),
        "headers": default_headers
    }


def handler(request):
    # 1. Method 校验
    if request.method != "POST":
        return create_response(405, {"error": "Method not allowed"})

    # 2. 解析 JSON
    try:
        body = request.json()
    except Exception as e:
        return create_response(400, {"error": "Invalid JSON", "details": str(e)})

    query = body.get("query")
    user_id = body.get("userId", "default_user")

    if not query:
        return create_response(400, {"error": "Missing query"})

    # 3. 环境变量
    BOT_ID = os.environ.get("COZE_BOT_ID")
    ACCESS_TOKEN = os.environ.get("COZE_ACCESS_TOKEN")

    if not BOT_ID or not ACCESS_TOKEN:
        return create_response(500, {"error": "Missing Coze credentials"})

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

        return create_response(200, {"reply": reply})

    except requests.exceptions.HTTPError as e:
        # 细分 HTTP 错误（如 401 鉴权失败、404 Bot 不存在）
        return create_response(500, {"error": f"Coze API HTTP 错误: {str(e)}"})
    except requests.exceptions.Timeout:
        return create_response(500, {"error": "Coze API 请求超时"})
    except requests.exceptions.ConnectionError:
        return create_response(500, {"error": "无法连接到 Coze API"})
    except Exception as e:
        return create_response(500, {"error": f"未知错误: {str(e)}"})
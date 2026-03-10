"""
Teams Bot 入口 — aiohttp 服务器
接收 Azure Bot Service 的 webhook 消息，转发给 LabManagerBot 处理

运行方式:
    python bot_app.py

需要配置:
    BOT_APP_ID — Azure Bot 的 App ID
    BOT_APP_PASSWORD — Azure Bot 的 App Password
"""

import os
import sys
from aiohttp import web
from botbuilder.core import (
    BotFrameworkAdapter,
    BotFrameworkAdapterSettings,
    TurnContext,
)
from botbuilder.schema import Activity

from teams_bot import LabManagerBot

# --------------------------------------------------
# 配置
# --------------------------------------------------

BOT_APP_ID = os.getenv("BOT_APP_ID", "")
BOT_APP_PASSWORD = os.getenv("BOT_APP_PASSWORD", "")
BOT_PORT = int(os.getenv("BOT_PORT", "3978"))

SETTINGS = BotFrameworkAdapterSettings(BOT_APP_ID, BOT_APP_PASSWORD)
ADAPTER = BotFrameworkAdapter(SETTINGS)

BOT = LabManagerBot()


# --------------------------------------------------
# 错误处理
# --------------------------------------------------

async def on_error(context: TurnContext, error: Exception):
    print(f"[Bot Error] {error}", file=sys.stderr)
    await context.send_activity("❌ 出了点问题，请稍后再试。")

ADAPTER.on_turn_error = on_error


# --------------------------------------------------
# Webhook 端点
# --------------------------------------------------

async def messages(req: web.Request) -> web.Response:
    """接收来自 Bot Framework / Teams 的消息"""
    if "application/json" not in req.headers.get("Content-Type", ""):
        return web.Response(status=415)

    body = await req.json()
    activity = Activity().deserialize(body)
    auth_header = req.headers.get("Authorization", "")

    response = await ADAPTER.process_activity(activity, auth_header, BOT.on_turn)

    if response:
        return web.json_response(data=response.body, status=response.status)
    return web.Response(status=201)


async def health(req: web.Request) -> web.Response:
    return web.json_response({"status": "ok", "service": "Lab Manager Teams Bot"})


# --------------------------------------------------
# 启动
# --------------------------------------------------

APP = web.Application()
APP.router.add_post("/api/messages", messages)
APP.router.add_get("/api/health", health)

if __name__ == "__main__":
    print("=" * 50)
    print("🤖 Lab Manager Teams Bot")
    print(f"📡 Webhook: http://localhost:{BOT_PORT}/api/messages")
    print(f"🔑 App ID: {BOT_APP_ID or '(not set - local testing mode)'}")
    print("=" * 50)
    try:
        web.run_app(APP, host="0.0.0.0", port=BOT_PORT)
    except Exception as e:
        print(f"Error: {e}")
        raise

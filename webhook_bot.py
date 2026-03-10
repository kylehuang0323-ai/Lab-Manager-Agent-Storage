"""
Teams Outgoing Webhook 服务器
无需 Azure 订阅，直接在 Teams 频道中创建 Outgoing Webhook 即可使用

运行方式:
    python webhook_bot.py

配置:
    .env 中设置 TEAMS_WEBHOOK_SECRET（创建 Outgoing Webhook 时 Teams 会提供）
"""

import base64
import hashlib
import hmac
import html
import json
import os
import re
import sys
import time

from flask import Flask, request, jsonify
from dotenv import load_dotenv

load_dotenv()

# 加载 agent 引擎
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import agent_engine

app = Flask(__name__)

WEBHOOK_SECRET = os.getenv("TEAMS_WEBHOOK_SECRET", "")
WEBHOOK_PORT = int(os.getenv("WEBHOOK_PORT", "3978"))

# 用户对话历史 (per-user)
_histories = {}
MAX_HISTORY = 20


def _strip_mention(text: str) -> str:
    """去除 @mention 标签，只保留用户实际输入"""
    clean = re.sub(r"<at>.*?</at>\s*", "", text or "")
    clean = html.unescape(clean).strip()
    return clean


def _verify_hmac(req_body: bytes, auth_header: str) -> bool:
    """验证 Teams Outgoing Webhook 的 HMAC-SHA256 签名"""
    if not WEBHOOK_SECRET:
        return True  # 未配置密钥时跳过验证（开发模式）

    try:
        # auth_header 格式: "HMAC <base64_signature>"
        provided = auth_header.replace("HMAC ", "").strip()
        secret_bytes = base64.b64decode(WEBHOOK_SECRET)
        computed = base64.b64encode(
            hmac.new(secret_bytes, req_body, hashlib.sha256).digest()
        ).decode()
        return hmac.compare_digest(provided, computed)
    except Exception as e:
        print(f"[HMAC] 验证失败: {e}")
        return False


def _build_adaptive_card(title: str, body_text: str, tool_info: str = "") -> dict:
    """构建 Adaptive Card 响应"""
    card_body = [
        {
            "type": "TextBlock",
            "text": title,
            "weight": "Bolder",
            "size": "Medium",
            "color": "Accent",
        },
        {
            "type": "TextBlock",
            "text": body_text,
            "wrap": True,
            "spacing": "Small",
        },
    ]
    if tool_info:
        card_body.append({
            "type": "TextBlock",
            "text": f"🔧 {tool_info}",
            "wrap": True,
            "size": "Small",
            "isSubtle": True,
            "spacing": "Small",
        })

    card_body.append({
        "type": "TextBlock",
        "text": f"⏱️ {time.strftime('%H:%M:%S')}",
        "size": "Small",
        "isSubtle": True,
        "horizontalAlignment": "Right",
        "spacing": "Medium",
    })

    return {
        "type": "AdaptiveCard",
        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
        "version": "1.4",
        "body": card_body,
    }


@app.route("/api/messages", methods=["POST"])
def webhook():
    """接收 Teams Outgoing Webhook 消息"""
    raw_body = request.get_data()

    # 验证签名
    auth = request.headers.get("Authorization", "")
    if WEBHOOK_SECRET and not _verify_hmac(raw_body, auth):
        return jsonify({"type": "message", "text": "⚠️ 签名验证失败"}), 401

    data = request.get_json(force=True)
    user_text = _strip_mention(data.get("text", ""))
    user_id = data.get("from", {}).get("id", "anonymous")
    user_name = data.get("from", {}).get("name", "用户")

    if not user_text:
        return jsonify({
            "type": "message",
            "text": "👋 你好！我是 Lab Manager，试试发送：查一下库存 或 帮助"
        })

    # 特殊命令
    lower = user_text.lower().strip()
    if lower in ("帮助", "/help", "help"):
        card = _build_adaptive_card(
            "📦 Lab Manager 使用指南",
            "**库存管理:**\n"
            "• 查一下库存 / 还有多少鼠标\n"
            "• 入库 10 个 USB-C 数据线\n"
            "• 出库 2 台 Surface Pro 给 Team A\n"
            "• 查看低库存 / 导出库存报表\n\n"
            "**资产管理:**\n"
            "• 查一下所有 Surface 设备\n"
            "• 资产概览 / 有多少台电脑\n\n"
            "**其他:**\n"
            "• 清除对话 — 重置上下文\n"
            "• 帮助 — 显示此帮助"
        )
        return jsonify({
            "type": "message",
            "attachments": [{
                "contentType": "application/vnd.microsoft.card.adaptive",
                "content": card,
            }]
        })

    if lower in ("清除对话", "/clear", "clear"):
        _histories.pop(user_id, None)
        return jsonify({"type": "message", "text": "🗑️ 对话已清除"})

    # Agent 对话
    history = _histories.get(user_id, [])
    try:
        result = agent_engine.chat(user_text, history)
        reply = result.get("reply", "")
        tool_calls = result.get("tool_calls", [])
    except Exception as e:
        print(f"[Agent Error] {e}")
        return jsonify({"type": "message", "text": f"❌ 处理失败: {e}"})

    # 更新历史
    history.append({"role": "user", "content": user_text})
    history.append({"role": "assistant", "content": reply})
    if len(history) > MAX_HISTORY * 2:
        history = history[-(MAX_HISTORY * 2):]
    _histories[user_id] = history

    # 构建 tool 信息摘要
    tool_info = ""
    if tool_calls:
        tool_names = [tc.get("tool", "") for tc in tool_calls if isinstance(tc, dict)]
        if tool_names:
            tool_info = "调用: " + " → ".join(tool_names)

    # 短回复直接用 text，长回复用 Adaptive Card
    if len(reply) < 200 and not tool_calls:
        return jsonify({"type": "message", "text": reply})

    card = _build_adaptive_card("📦 Lab Manager", reply, tool_info)
    return jsonify({
        "type": "message",
        "attachments": [{
            "contentType": "application/vnd.microsoft.card.adaptive",
            "content": card,
        }]
    })


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "service": "Lab Manager Teams Webhook Bot",
        "secret_configured": bool(WEBHOOK_SECRET),
    })


if __name__ == "__main__":
    print("=" * 55)
    print("🤖 Lab Manager — Teams Outgoing Webhook Bot")
    print(f"📡 Endpoint: http://localhost:{WEBHOOK_PORT}/api/messages")
    print(f"🔑 Secret: {'已配置' if WEBHOOK_SECRET else '未配置 (开发模式)'}")
    print("=" * 55)
    print()
    print("📖 使用步骤:")
    print("  1. 启动 Dev Tunnel: devtunnel host --port-numbers 3978 --allow-anonymous")
    print("  2. 复制 tunnel 的 HTTPS URL")
    print("  3. 在 Teams 频道 → 管理频道 → 应用 → 创建传出 Webhook")
    print("     名称: LabManager, URL: <tunnel_url>/api/messages")
    print("  4. 复制 Teams 给出的安全令牌 → 填入 .env 的 TEAMS_WEBHOOK_SECRET")
    print("  5. 重启本服务, 然后在频道中 @LabManager 发消息即可")
    print()
    app.run(host="0.0.0.0", port=WEBHOOK_PORT, debug=True)

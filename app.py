"""
Lab Manager's Agent for Storage
Flask 主应用 — 提供 Web 管理后台 + Agent 对话 API
"""

from flask import Flask, render_template, jsonify, request, session

import config
import agent_engine

app = Flask(__name__)
app.secret_key = config.SECRET_KEY


# --------------------------------------------------
# 页面路由
# --------------------------------------------------

@app.route("/")
def index():
    return render_template("dashboard.html")


# --------------------------------------------------
# Agent 对话 API
# --------------------------------------------------

@app.route("/api/chat", methods=["POST"])
def api_chat():
    data = request.get_json()
    user_message = data.get("message", "").strip()
    if not user_message:
        return jsonify({"error": "消息不能为空"}), 400

    # 会话历史（存 session）
    if "history" not in session:
        session["history"] = []

    api_key = data.get("api_key") or config.GROQ_API_KEY
    result = agent_engine.chat(
        user_message=user_message,
        conversation_history=session["history"],
        api_key=api_key,
    )

    # 更新历史（保留最近 20 轮）
    session["history"].append({"role": "user", "content": user_message})
    session["history"].append({"role": "assistant", "content": result["reply"]})
    session["history"] = session["history"][-40:]
    session.modified = True

    return jsonify({
        "reply": result["reply"],
        "tool_calls": result["tool_calls"],
        "tool_results": result["tool_results"],
    })


@app.route("/api/chat/clear", methods=["POST"])
def clear_chat():
    session.pop("history", None)
    return jsonify({"status": "ok"})


# --------------------------------------------------
# 健康检查
# --------------------------------------------------

@app.route("/api/health")
def health():
    return jsonify({"status": "ok", "message": "Lab Manager Agent is running"})


# --------------------------------------------------
# 启动
# --------------------------------------------------

if __name__ == "__main__":
    print("=" * 50)
    print("📦 Lab Manager's Agent for Storage")
    print("🌐 http://localhost:5001")
    print("=" * 50)
    app.run(host="0.0.0.0", port=5001, debug=config.DEBUG)

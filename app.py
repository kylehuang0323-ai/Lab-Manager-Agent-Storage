"""
Lab Manager's Agent for Storage
Flask 主应用 — 提供 Web 管理后台 + Agent 对话 API
"""

from flask import Flask, render_template, jsonify

import config

app = Flask(__name__)
app.secret_key = config.SECRET_KEY


# --------------------------------------------------
# 页面路由
# --------------------------------------------------

@app.route("/")
def index():
    return render_template("dashboard.html")


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

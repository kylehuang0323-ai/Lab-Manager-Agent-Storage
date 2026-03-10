"""
Lab Manager's Agent for Storage
Flask 主应用 — 提供 Web 管理后台 + Agent 对话 API
"""

from flask import Flask, render_template, jsonify, request, session, send_file

import config
import agent_engine
import inventory_manager as im
import report_generator as rg
import alert_service

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
# 库存 REST API
# --------------------------------------------------

@app.route("/api/inventory")
def api_inventory():
    """获取全部库存"""
    im.init_data_files()
    items = im.get_all_items()
    return jsonify({"items": items, "total": len(items)})


@app.route("/api/inventory/<item_id>")
def api_item(item_id):
    """获取单个商品"""
    item = im.get_item(item_id)
    if not item:
        return jsonify({"error": "商品不存在"}), 404
    return jsonify(item)


@app.route("/api/inventory/search")
def api_search():
    """搜索商品"""
    keyword = request.args.get("q", "")
    results = im.search_items(keyword) if keyword else im.get_all_items()
    return jsonify({"items": results, "total": len(results)})


@app.route("/api/inventory/categories")
def api_categories():
    """获取分类列表"""
    return jsonify({"categories": im.get_categories()})


@app.route("/api/inventory/low-stock")
def api_low_stock():
    """低库存告警"""
    items = im.get_low_stock_items()
    return jsonify({"items": items, "total": len(items)})


@app.route("/api/transactions")
def api_transactions():
    """出入库记录"""
    item_id = request.args.get("item_id")
    tx_type = request.args.get("type")
    limit = int(request.args.get("limit", 50))
    records = im.get_transactions(item_id=item_id, tx_type=tx_type, limit=limit)
    return jsonify({"records": records, "total": len(records)})


@app.route("/api/report/export", methods=["POST"])
def api_export():
    """导出报表"""
    data = request.get_json() or {}
    report_type = data.get("type", "inventory")
    try:
        if report_type == "transactions":
            path = rg.export_transactions_report()
        else:
            path = rg.export_inventory_report(category=data.get("category"))
        return send_file(path, as_attachment=True)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# --------------------------------------------------
# 低库存告警 API + SSE
# --------------------------------------------------

@app.route("/api/alerts/check")
def api_alert_check():
    """手动触发一次低库存检查"""
    alerts = alert_service.check_low_stock()
    return jsonify({"alerts": alerts, "total": len(alerts)})


@app.route("/api/alerts/stream")
def api_alert_stream():
    """SSE 推送低库存告警到前端"""
    import queue

    q = queue.Queue()

    def on_alert(alerts):
        q.put(alerts)

    alert_service.subscribe_sse(on_alert)

    def generate():
        try:
            while True:
                try:
                    alerts = q.get(timeout=30)
                    yield f"data: {json.dumps(alerts, ensure_ascii=False)}\n\n"
                except queue.Empty:
                    yield ": heartbeat\n\n"
        finally:
            alert_service.unsubscribe_sse(on_alert)

    import json
    from flask import Response
    return Response(generate(), mimetype="text/event-stream",
                    headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


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
    alert_service.start_alert_scheduler(interval_seconds=300)
    print("=" * 50)
    print("📦 Lab Manager's Agent for Storage")
    print("🌐 http://localhost:5001")
    print("⏰ 低库存告警已启动 (每 5 分钟)")
    print("=" * 50)
    app.run(host="0.0.0.0", port=5001, debug=config.DEBUG)

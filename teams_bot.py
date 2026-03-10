"""
Teams Bot 适配器 — 基于 Azure Bot Framework SDK
处理 Teams 消息收发，调用 agent_engine 获取回复，用 Adaptive Cards 展示结果
"""

import json
from botbuilder.core import ActivityHandler, TurnContext, CardFactory
from botbuilder.schema import Activity, ActivityTypes

import agent_engine
import inventory_manager as im


class LabManagerBot(ActivityHandler):
    """Lab Manager Teams Bot"""

    def __init__(self):
        super().__init__()
        # 每个用户独立的对话历史 {user_id: [messages]}
        self._histories = {}

    def _get_history(self, user_id: str) -> list:
        if user_id not in self._histories:
            self._histories[user_id] = []
        return self._histories[user_id]

    # --------------------------------------------------
    # 消息处理
    # --------------------------------------------------

    async def on_message_activity(self, turn_context: TurnContext):
        user_id = turn_context.activity.from_property.id
        text = (turn_context.activity.text or "").strip()

        if not text:
            return

        # 特殊命令
        if text.lower() in ("/help", "帮助"):
            await self._send_help(turn_context)
            return

        if text.lower() in ("/clear", "清除对话"):
            self._histories[user_id] = []
            await turn_context.send_activity("🗑️ 对话已清除")
            return

        if text.lower() in ("/stock", "库存概览"):
            await self._send_inventory_summary(turn_context)
            return

        if text.lower() in ("/low", "低库存"):
            await self._send_low_stock(turn_context)
            return

        # 正常 Agent 对话
        await turn_context.send_activity(Activity(type=ActivityTypes.typing))

        im.init_data_files()
        history = self._get_history(user_id)

        try:
            result = agent_engine.chat(
                user_message=text,
                conversation_history=history,
            )
        except Exception as e:
            await turn_context.send_activity(f"❌ 处理出错: {str(e)}")
            return

        # 更新历史（保留最近 20 轮）
        history.append({"role": "user", "content": text})
        history.append({"role": "assistant", "content": result["reply"]})
        self._histories[user_id] = history[-40:]

        # 发送回复
        if result.get("tool_calls"):
            # 有工具调用 → 用 Adaptive Card 展示
            card = self._build_result_card(result)
            await turn_context.send_activity(
                Activity(
                    type=ActivityTypes.message,
                    attachments=[CardFactory.adaptive_card(card)],
                )
            )
        else:
            await turn_context.send_activity(result["reply"])

    async def on_members_added_activity(self, members_added, turn_context: TurnContext):
        for member in members_added:
            if member.id != turn_context.activity.recipient.id:
                card = self._build_welcome_card()
                await turn_context.send_activity(
                    Activity(
                        type=ActivityTypes.message,
                        attachments=[CardFactory.adaptive_card(card)],
                    )
                )

    # --------------------------------------------------
    # Adaptive Cards
    # --------------------------------------------------

    def _build_welcome_card(self) -> dict:
        return {
            "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
            "type": "AdaptiveCard",
            "version": "1.4",
            "body": [
                {
                    "type": "TextBlock",
                    "text": "📦 Lab Manager Agent",
                    "size": "Large",
                    "weight": "Bolder",
                    "color": "Accent",
                },
                {
                    "type": "TextBlock",
                    "text": "你好！我是 Lab 库存管理助手，可以帮你：",
                    "wrap": True,
                },
                {
                    "type": "FactSet",
                    "facts": [
                        {"title": "📥 入库", "value": "\"入库 50 个 Surface 鼠标\""},
                        {"title": "📤 出库", "value": "\"出库 2 台笔记本给 Team A\""},
                        {"title": "🔍 查询", "value": "\"还有多少鼠标？\""},
                        {"title": "📋 清单", "value": "\"给我完整库存清单\""},
                        {"title": "➕ 新建", "value": "\"新增商品 Type-C 线\""},
                        {"title": "📊 报表", "value": "\"导出本月报表\""},
                    ],
                },
                {
                    "type": "TextBlock",
                    "text": "输入 /help 查看更多命令",
                    "size": "Small",
                    "color": "Light",
                    "isSubtle": True,
                },
            ],
        }

    def _build_result_card(self, result: dict) -> dict:
        """根据 Agent 返回结果构建 Adaptive Card"""
        body = []

        # 工具调用标签
        tools_used = [tc["tool"] for tc in result.get("tool_calls", [])]
        if tools_used:
            tool_names = {
                "stock_in": "📥 入库",
                "stock_out": "📤 出库",
                "create_item": "➕ 新建商品",
                "query_stock": "🔍 查询库存",
                "search_items": "🔎 搜索",
                "list_inventory": "📋 库存清单",
                "get_categories": "🏷️ 分类",
                "get_low_stock": "⚠️ 低库存",
                "get_transactions": "📜 记录",
                "export_report": "📊 导出",
            }
            pills = " ".join([tool_names.get(t, t) for t in tools_used])
            body.append({
                "type": "TextBlock",
                "text": f"🔧 {pills}",
                "size": "Small",
                "color": "Accent",
            })

        # 工具结果表格（如果有库存数据）
        for tr in result.get("tool_results", []):
            res = tr.get("result", {})
            if isinstance(res, dict) and res.get("success") is not None:
                res = res.get("result", res)
            if isinstance(res, list) and len(res) > 0 and isinstance(res[0], dict):
                # 列表数据 → 表格
                table = self._build_data_table(res[:10], tr["tool"])
                if table:
                    body.extend(table)

        # Agent 回复文本
        body.append({
            "type": "TextBlock",
            "text": result["reply"],
            "wrap": True,
        })

        return {
            "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
            "type": "AdaptiveCard",
            "version": "1.4",
            "body": body,
        }

    def _build_data_table(self, items: list, tool_name: str) -> list:
        """将数据列表构建为 FactSet"""
        if not items:
            return []

        elements = []
        if tool_name in ("list_inventory", "query_stock", "search_items", "get_low_stock"):
            for item in items[:8]:
                qty = item.get("quantity", 0)
                min_s = item.get("min_stock", 0)
                status = "🔴" if (min_s and qty == 0) else ("🟡" if (min_s and qty < min_s) else "🟢")
                elements.append({
                    "type": "FactSet",
                    "facts": [
                        {"title": "商品", "value": f"{status} {item.get('name', '')}"},
                        {"title": "数量", "value": f"{qty} {item.get('unit', '')}"},
                        {"title": "分类", "value": str(item.get("category", ""))},
                        {"title": "位置", "value": str(item.get("location", ""))},
                    ],
                })
                elements.append({"type": "TextBlock", "text": " ", "spacing": "Small"})

            if len(items) > 8:
                elements.append({
                    "type": "TextBlock",
                    "text": f"... 还有 {len(items) - 8} 项",
                    "isSubtle": True, "size": "Small",
                })

        elif tool_name == "get_transactions":
            for tx in items[:8]:
                tx_icon = "📥" if tx.get("type") == "in" else "📤"
                elements.append({
                    "type": "FactSet",
                    "facts": [
                        {"title": "操作", "value": f"{tx_icon} {tx.get('item_name', '')}"},
                        {"title": "数量", "value": str(tx.get("quantity", ""))},
                        {"title": "操作人", "value": str(tx.get("operator", ""))},
                        {"title": "时间", "value": str(tx.get("timestamp", ""))},
                    ],
                })
                elements.append({"type": "TextBlock", "text": " ", "spacing": "Small"})

        return elements

    # --------------------------------------------------
    # 快捷命令
    # --------------------------------------------------

    async def _send_help(self, turn_context: TurnContext):
        card = {
            "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
            "type": "AdaptiveCard",
            "version": "1.4",
            "body": [
                {
                    "type": "TextBlock",
                    "text": "📦 Lab Manager — 帮助",
                    "size": "Medium",
                    "weight": "Bolder",
                    "color": "Accent",
                },
                {
                    "type": "TextBlock",
                    "text": "**自然语言指令（直接输入）：**",
                    "wrap": True,
                },
                {
                    "type": "FactSet",
                    "facts": [
                        {"title": "入库", "value": "入库 50 个 Surface 鼠标"},
                        {"title": "出库", "value": "出库 2 台笔记本给 Team A"},
                        {"title": "新建", "value": "新增商品 Type-C 线，类别配件"},
                        {"title": "查询", "value": "还有多少鼠标？"},
                        {"title": "搜索", "value": "有没有 USB 相关的东西？"},
                        {"title": "清单", "value": "给我完整库存清单"},
                        {"title": "低库存", "value": "哪些商品库存不足？"},
                        {"title": "报表", "value": "导出库存报表"},
                    ],
                },
                {
                    "type": "TextBlock",
                    "text": "**快捷命令：**\n- `/stock` — 库存概览\n- `/low` — 低库存告警\n- `/clear` — 清除对话\n- `/help` — 显示帮助",
                    "wrap": True,
                },
            ],
        }
        await turn_context.send_activity(
            Activity(
                type=ActivityTypes.message,
                attachments=[CardFactory.adaptive_card(card)],
            )
        )

    async def _send_inventory_summary(self, turn_context: TurnContext):
        im.init_data_files()
        items = im.get_all_items()
        total_types = len(items)
        total_qty = sum(int(it.get("quantity", 0)) for it in items)
        low = im.get_low_stock_items()
        cats = im.get_categories()

        card = {
            "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
            "type": "AdaptiveCard",
            "version": "1.4",
            "body": [
                {
                    "type": "TextBlock",
                    "text": "📊 库存概览",
                    "size": "Medium",
                    "weight": "Bolder",
                    "color": "Accent",
                },
                {
                    "type": "ColumnSet",
                    "columns": [
                        {"type": "Column", "width": "stretch", "items": [
                            {"type": "TextBlock", "text": str(total_types), "size": "ExtraLarge", "weight": "Bolder", "horizontalAlignment": "Center"},
                            {"type": "TextBlock", "text": "商品种类", "horizontalAlignment": "Center", "isSubtle": True},
                        ]},
                        {"type": "Column", "width": "stretch", "items": [
                            {"type": "TextBlock", "text": str(total_qty), "size": "ExtraLarge", "weight": "Bolder", "horizontalAlignment": "Center"},
                            {"type": "TextBlock", "text": "总库存", "horizontalAlignment": "Center", "isSubtle": True},
                        ]},
                        {"type": "Column", "width": "stretch", "items": [
                            {"type": "TextBlock", "text": str(len(low)), "size": "ExtraLarge", "weight": "Bolder", "horizontalAlignment": "Center", "color": "Attention" if low else "Good"},
                            {"type": "TextBlock", "text": "低库存", "horizontalAlignment": "Center", "isSubtle": True},
                        ]},
                        {"type": "Column", "width": "stretch", "items": [
                            {"type": "TextBlock", "text": str(len(cats)), "size": "ExtraLarge", "weight": "Bolder", "horizontalAlignment": "Center"},
                            {"type": "TextBlock", "text": "分类数", "horizontalAlignment": "Center", "isSubtle": True},
                        ]},
                    ],
                },
            ],
        }

        if low:
            card["body"].append({"type": "TextBlock", "text": "⚠️ 低库存商品:", "weight": "Bolder", "spacing": "Medium"})
            for it in low[:5]:
                card["body"].append({
                    "type": "TextBlock",
                    "text": f"🔴 {it.get('name')} — 剩余 {it.get('quantity')} {it.get('unit')}（最低 {it.get('min_stock')}）",
                    "wrap": True, "color": "Attention",
                })

        await turn_context.send_activity(
            Activity(
                type=ActivityTypes.message,
                attachments=[CardFactory.adaptive_card(card)],
            )
        )

    async def _send_low_stock(self, turn_context: TurnContext):
        im.init_data_files()
        low = im.get_low_stock_items()
        if not low:
            await turn_context.send_activity("✅ 所有商品库存充足，无告警！")
            return

        body = [
            {
                "type": "TextBlock",
                "text": f"⚠️ {len(low)} 项低库存告警",
                "size": "Medium",
                "weight": "Bolder",
                "color": "Attention",
            }
        ]
        for it in low:
            body.append({
                "type": "FactSet",
                "facts": [
                    {"title": "商品", "value": f"🔴 {it.get('name')}"},
                    {"title": "剩余", "value": f"{it.get('quantity')} {it.get('unit')}"},
                    {"title": "最低", "value": str(it.get("min_stock"))},
                    {"title": "位置", "value": str(it.get("location", "-"))},
                ],
            })

        card = {
            "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
            "type": "AdaptiveCard",
            "version": "1.4",
            "body": body,
        }
        await turn_context.send_activity(
            Activity(
                type=ActivityTypes.message,
                attachments=[CardFactory.adaptive_card(card)],
            )
        )

"""
Agent 核心引擎 — 基于 Groq LLM 的意图识别 + Tool-use 执行
通过 system prompt 定义可用工具，解析 LLM 返回的 JSON 调用对应函数
"""

import json
import os
import re
from openai import OpenAI

import config
import inventory_manager as im

# --------------------------------------------------
# LLM 客户端
# --------------------------------------------------

_client = None


def _get_client(api_key: str = None) -> OpenAI:
    global _client
    key = api_key or config.GROQ_API_KEY
    if _client is None or api_key:
        _client = OpenAI(api_key=key, base_url=config.GROQ_BASE_URL)
    return _client


# --------------------------------------------------
# System Prompt
# --------------------------------------------------

SYSTEM_PROMPT = """你是 Lab Manager Agent —— 一个智能库存管理助手，帮助用户管理 Lab 的物料、礼品和资产。

## 你的能力
你可以通过调用工具函数来执行库存操作。当用户的请求需要操作库存时，你必须返回一个 JSON 工具调用。

## 可用工具

1. **stock_in** — 入库
   参数: {"item_id": "ITEM-0001", "quantity": 10, "operator": "操作人", "note": "备注"}

2. **stock_out** — 出库
   参数: {"item_id": "ITEM-0001", "quantity": 5, "operator": "操作人", "recipient": "领用人", "note": "备注"}

3. **create_item** — 新建商品
   参数: {"name": "商品名", "category": "分类", "quantity": 0, "unit": "个", "location": "存放位置", "min_stock": 0}

4. **query_stock** — 查询库存（单个商品或全部）
   参数: {"item_id": "ITEM-0001"} 或 {} 表示查全部

5. **search_items** — 搜索商品
   参数: {"keyword": "搜索关键词"}

6. **list_inventory** — 生成完整库存清单
   参数: {}

7. **get_categories** — 查看所有分类
   参数: {}

8. **get_low_stock** — 查看低库存告警
   参数: {}

9. **get_transactions** — 查看出入库记录
   参数: {"item_id": "可选", "tx_type": "in或out可选", "limit": 20}

10. **export_report** — 导出库存报表
    参数: {"report_type": "inventory 或 transactions"}

## 输出格式

当需要调用工具时，在回复中包含如下 JSON 块：
```tool_call
{"tool": "工具名", "params": {参数}}
```

你可以在一次回复中调用多个工具（多个 ```tool_call 块）。

工具调用后系统会返回结果，你需要基于结果用自然语言回复用户。

## 行为准则
- 如果用户提到商品名但没给 item_id，先用 search_items 搜索，再确认操作
- 出库时如果库存不足，提醒用户
- 对模糊请求友好地追问细节
- 数量和分类要确认清楚再操作
- 回复简洁友好，使用中文
- 如果用户只是闲聊，正常回复，不调用工具
"""


# --------------------------------------------------
# Tool 执行器
# --------------------------------------------------

TOOL_MAP = {
    "stock_in": lambda p: im.stock_in(**p),
    "stock_out": lambda p: im.stock_out(**p),
    "create_item": lambda p: im.create_item(**p),
    "query_stock": lambda p: im.get_item(p["item_id"]) if p.get("item_id") else im.get_all_items(),
    "search_items": lambda p: im.search_items(p["keyword"]),
    "list_inventory": lambda p: im.get_all_items(),
    "get_categories": lambda p: im.get_categories(),
    "get_low_stock": lambda p: im.get_low_stock_items(),
    "get_transactions": lambda p: im.get_transactions(
        item_id=p.get("item_id"), tx_type=p.get("tx_type"), limit=p.get("limit", 20)
    ),
    "export_report": lambda p: _handle_export(p),
}


def _handle_export(params: dict) -> dict:
    """导出报表"""
    import report_generator as rg
    report_type = params.get("report_type", "inventory")
    try:
        if report_type == "transactions":
            path = rg.export_transactions_report(
                item_id=params.get("item_id"),
                tx_type=params.get("tx_type"),
            )
        else:
            path = rg.export_inventory_report(category=params.get("category"))
        filename = os.path.basename(path)
        return {"success": True, "message": f"报表已导出: {filename}", "filename": filename}
    except Exception as e:
        return {"success": False, "error": str(e)}


def _parse_tool_calls(response_text: str) -> list[dict]:
    """从 LLM 回复中解析 tool_call JSON 块"""
    pattern = r"```tool_call\s*\n?(.*?)\n?```"
    matches = re.findall(pattern, response_text, re.DOTALL)
    calls = []
    for match in matches:
        try:
            call = json.loads(match.strip())
            if "tool" in call:
                calls.append(call)
        except json.JSONDecodeError:
            continue
    return calls


def _execute_tool(tool_name: str, params: dict) -> dict:
    """执行单个工具调用"""
    if tool_name not in TOOL_MAP:
        return {"error": f"未知工具: {tool_name}"}
    try:
        result = TOOL_MAP[tool_name](params)
        return {"success": True, "result": result}
    except Exception as e:
        return {"success": False, "error": str(e)}


# --------------------------------------------------
# 对话主函数
# --------------------------------------------------

def chat(user_message: str, conversation_history: list = None,
         api_key: str = None) -> dict:
    """
    处理用户消息，返回 Agent 回复

    Returns:
        {
            "reply": str,           # 最终自然语言回复
            "tool_calls": list,     # 调用的工具列表
            "tool_results": list,   # 工具执行结果
        }
    """
    im.init_data_files()
    client = _get_client(api_key)

    # 构建消息列表
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    if conversation_history:
        messages.extend(conversation_history)
    messages.append({"role": "user", "content": user_message})

    # 第一轮：LLM 分析意图
    response = client.chat.completions.create(
        model=config.AI_MODEL,
        messages=messages,
        temperature=0.3,
        max_tokens=2048,
    )
    assistant_text = response.choices[0].message.content or ""

    # 解析工具调用
    tool_calls = _parse_tool_calls(assistant_text)

    if not tool_calls:
        # 无工具调用，直接返回
        return {
            "reply": assistant_text,
            "tool_calls": [],
            "tool_results": [],
        }

    # 执行工具
    tool_results = []
    for call in tool_calls:
        result = _execute_tool(call["tool"], call.get("params", {}))
        tool_results.append({
            "tool": call["tool"],
            "params": call.get("params", {}),
            "result": result,
        })

    # 第二轮：让 LLM 基于工具结果生成自然语言回复
    # 清理第一轮回复中的 tool_call 块
    clean_text = re.sub(r"```tool_call\s*\n?.*?\n?```", "", assistant_text, flags=re.DOTALL).strip()

    tool_result_text = "\n".join([
        f"工具 `{tr['tool']}` 执行结果:\n{json.dumps(tr['result'], ensure_ascii=False, indent=2)}"
        for tr in tool_results
    ])

    messages.append({"role": "assistant", "content": assistant_text})
    messages.append({
        "role": "user",
        "content": f"[系统] 工具已执行，结果如下：\n{tool_result_text}\n\n请基于上述结果，用简洁友好的中文回复用户。不要再输出 tool_call。"
    })

    response2 = client.chat.completions.create(
        model=config.AI_MODEL,
        messages=messages,
        temperature=0.5,
        max_tokens=1024,
    )
    final_reply = response2.choices[0].message.content or ""

    # 如果第一轮有前缀文本，拼接
    if clean_text:
        final_reply = f"{clean_text}\n\n{final_reply}"

    return {
        "reply": final_reply,
        "tool_calls": tool_calls,
        "tool_results": tool_results,
    }

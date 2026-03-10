"""
低库存告警服务 — 定时扫描 + Teams 主动推送 + Web SSE 推送
"""

import asyncio
import json
import os
import threading
import time
from datetime import datetime
from typing import Callable, Optional

import inventory_manager as im
import config

# --------------------------------------------------
# 告警记录（避免重复告警）
# --------------------------------------------------

_alerted_items: dict[str, str] = {}  # item_id → last_alert_time


def check_low_stock() -> list[dict]:
    """检查低库存并返回需要告警的商品（去重）"""
    im.init_data_files()
    low_items = im.get_low_stock_items()
    alerts = []

    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    for item in low_items:
        item_id = item.get("item_id", "")
        last_alert = _alerted_items.get(item_id)
        # 同一商品每小时最多告警一次
        if last_alert and last_alert[:16] == now[:13]:
            continue
        _alerted_items[item_id] = now
        alerts.append({
            "item_id": item_id,
            "name": item.get("name", ""),
            "category": item.get("category", ""),
            "quantity": int(item.get("quantity", 0)),
            "min_stock": int(item.get("min_stock", 0)),
            "unit": item.get("unit", ""),
            "location": item.get("location", ""),
            "alert_time": now,
        })

    return alerts


# --------------------------------------------------
# Web SSE 推送（给 Web Dashboard 用）
# --------------------------------------------------

_sse_subscribers: list[Callable] = []


def subscribe_sse(callback: Callable):
    _sse_subscribers.append(callback)


def unsubscribe_sse(callback: Callable):
    if callback in _sse_subscribers:
        _sse_subscribers.remove(callback)


def _notify_sse(alerts: list[dict]):
    for cb in _sse_subscribers[:]:
        try:
            cb(alerts)
        except Exception:
            _sse_subscribers.remove(cb)


# --------------------------------------------------
# Teams 主动推送（需要 conversation reference）
# --------------------------------------------------

_conversation_refs: dict[str, dict] = {}  # user_id → conversation_reference


def save_conversation_reference(user_id: str, ref: dict):
    """保存用户的 conversation reference，用于主动推送"""
    _conversation_refs[user_id] = ref


def get_conversation_references() -> dict:
    return _conversation_refs.copy()


# --------------------------------------------------
# 定时扫描线程
# --------------------------------------------------

_scheduler_running = False
_check_interval = 300  # 默认 5 分钟


def start_alert_scheduler(interval_seconds: int = 300,
                           teams_push_callback=None):
    """启动后台定时扫描"""
    global _scheduler_running, _check_interval
    if _scheduler_running:
        return

    _check_interval = interval_seconds
    _scheduler_running = True

    def _run():
        while _scheduler_running:
            try:
                alerts = check_low_stock()
                if alerts:
                    print(f"[Alert] {len(alerts)} 项低库存告警: "
                          + ", ".join(a["name"] for a in alerts))
                    _notify_sse(alerts)
                    if teams_push_callback:
                        teams_push_callback(alerts)
            except Exception as e:
                print(f"[Alert Error] {e}")
            time.sleep(_check_interval)

    t = threading.Thread(target=_run, daemon=True, name="low-stock-alert")
    t.start()
    print(f"[Alert] 低库存告警已启动，每 {interval_seconds} 秒检查一次")


def stop_alert_scheduler():
    global _scheduler_running
    _scheduler_running = False

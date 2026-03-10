# Lab Manager's Agent for Storage

智能 Lab 库存管理 Agent —— 通过自然语言对话实现物料、礼品、资产的出入库管理。

## 功能

- 🤖 自然语言对话管理库存（入库/出库/查询/搜索）
- 📦 商品目录管理（新建/编辑/分类）
- 📊 库存清单与报表导出（Excel）
- 💬 Microsoft Teams Bot 集成
- 🌐 Web 管理后台（仪表盘 + 可视化）

## 技术栈

| 组件 | 选型 |
|------|------|
| AI 模型 | Groq API (Llama 3.3 70B) |
| 后端 | Flask |
| 数据存储 | Excel / CSV (openpyxl) |
| Teams 集成 | Azure Bot Framework SDK |
| 前端 | HTML + CSS + JavaScript |

## 快速开始

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env 填入你的 Groq API Key

# 3. 启动
python app.py
```

## 项目结构

```
├── app.py                  # Flask 主应用
├── config.py               # 配置管理
├── agent_engine.py         # Agent 核心引擎
├── inventory_manager.py    # 库存操作 (Excel CRUD)
├── report_generator.py     # 报表生成
├── teams_bot.py            # Teams Bot 适配器
├── data/                   # 数据文件 (Excel)
├── exports/                # 导出的报表
├── templates/              # HTML 模板
├── static/                 # 静态资源
└── requirements.txt
```

## 分支策略

- `main` — 稳定主线
- `feature/*` — 功能模块分支，完成后合并回 main

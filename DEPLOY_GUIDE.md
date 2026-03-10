# 🤖 Lab Manager — Teams Outgoing Webhook 部署指南

> **无需 Azure 订阅**，仅需一台 Windows 电脑 + Microsoft Teams 即可部署。

---

## 📋 目录

1. [前置条件](#1-前置条件)
2. [安装 Dev Tunnel](#2-安装-dev-tunnel)
3. [登录 Dev Tunnel](#3-登录-dev-tunnel)
4. [启动本地服务](#4-启动本地服务)
5. [获取 HTTPS 公网地址](#5-获取-https-公网地址)
6. [在 Teams 中创建 Outgoing Webhook](#6-在-teams-中创建-outgoing-webhook)
7. [配置安全令牌](#7-配置安全令牌)
8. [验证并使用](#8-验证并使用)
9. [日常使用 & 维护](#9-日常使用--维护)
10. [常见问题](#10-常见问题)

---

## 1. 前置条件

### 你需要准备

| 项目 | 说明 | 获取链接 |
|------|------|----------|
| **Python 3.10+** | 运行后端服务 | https://www.python.org/downloads/ |
| **Groq API Key** | AI Agent 免费推理 | https://console.groq.com/keys |
| **Microsoft Teams** | 桌面版或 Web 版 | https://www.microsoft.com/microsoft-teams/download-app |
| **Dev Tunnel** | 将本地端口暴露到公网 | Step 2 中安装 |

### 安装 Python 依赖

```powershell
cd "C:\Users\v-lexinhuang\MyPythonlearning\Lab manager's agent for storage"
pip install -r requirements.txt
```

### 配置 Groq API Key

编辑项目根目录的 `.env` 文件：

```env
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxxxxxx
```

> 💡 **获取 Groq API Key**: 访问 https://console.groq.com/keys → 点击 "Create API Key" → 复制密钥

---

## 2. 安装 Dev Tunnel

**Dev Tunnel** 是微软官方工具，将本机端口安全转发到一个公网 HTTPS 地址，让 Teams 能够访问你的本地服务。

### 方式一：通过 winget 安装（推荐）

```powershell
winget install Microsoft.devtunnel --accept-source-agreements
```

### 方式二：手动下载

1. 前往官方下载页面：  
   👉 https://learn.microsoft.com/azure/developer/dev-tunnels/get-started#install

2. 下载 Windows (x64) 版本：  
   👉 https://aka.ms/TunnelsCliDownload/win-x64

3. 将下载的 `devtunnel.exe` 放入 PATH 目录（如 `C:\Windows\System32`），或放到项目目录内

### 验证安装

```powershell
devtunnel --version
# 输出类似: Tunnel CLI version: 1.0.1516+7e996fe917
```

> 📖 **官方文档**：https://learn.microsoft.com/azure/developer/dev-tunnels/overview

---

## 3. 登录 Dev Tunnel

首次使用需要用 Microsoft 账号登录：

```powershell
devtunnel user login
```

这会打开浏览器，用你的 **Microsoft / Azure AD 账号**（即公司邮箱）登录。

### 验证登录状态

```powershell
devtunnel user show
```

应显示：

```
Logged in as v-lexinhuang@microsoft.com (Microsoft Entra ID)
```

> 📖 **登录文档**：https://learn.microsoft.com/azure/developer/dev-tunnels/cli-commands#devtunnel-user-login

---

## 4. 启动本地服务

### 方式一：一键启动（推荐）✨

```powershell
cd "C:\Users\v-lexinhuang\MyPythonlearning\Lab manager's agent for storage"
python start_webhook.py
```

这会自动启动 3 个服务：

| 服务 | 端口 | 说明 |
|------|------|------|
| Flask Web Dashboard | `http://localhost:5001` | 网页管理面板 |
| Webhook Bot | `http://localhost:3978` | Teams 消息处理 |
| Dev Tunnel | 自动分配 | HTTPS 公网转发 |

### 方式二：分步手动启动

**终端 1 — Flask Web Dashboard：**
```powershell
python app.py
# 输出: Running on http://0.0.0.0:5001
```

**终端 2 — Webhook Bot：**
```powershell
python webhook_bot.py
# 输出: Endpoint: http://localhost:3978/api/messages
```

**终端 3 — Dev Tunnel：**
```powershell
devtunnel host --port-numbers 3978 --allow-anonymous
```

---

## 5. 获取 HTTPS 公网地址

启动 Dev Tunnel 后，终端会输出类似以下内容：

```
Hosting port: 3978
Connect via browser: https://xxxxxxxx-3978.asse.devtunnels.ms
Inspect network activity: https://xxxxxxxx-3978-inspect.asse.devtunnels.ms

Ready to accept connections for tunnel: xxxxxxxx
```

📋 **复制那个 HTTPS 地址**，例如：
```
https://xxxxxxxx-3978.asse.devtunnels.ms
```

你的 Teams Webhook 回调 URL 将是：
```
https://xxxxxxxx-3978.asse.devtunnels.ms/api/messages
```

### 创建持久化 Tunnel（可选，推荐）

默认 tunnel 每次重启都会变 URL。创建持久化 tunnel 可以固定 URL：

```powershell
# 创建一个持久化 tunnel
devtunnel create lab-manager --allow-anonymous

# 添加端口映射
devtunnel port create lab-manager --port-number 3978

# 启动（以后每次用这个命令）
devtunnel host lab-manager
```

> 📖 **Dev Tunnel 命令参考**：https://learn.microsoft.com/azure/developer/dev-tunnels/cli-commands

---

## 6. 在 Teams 中创建 Outgoing Webhook

### Step 6.1 — 打开 Teams

- **桌面版**：打开 Microsoft Teams 应用
- **Web 版**：访问 https://teams.microsoft.com

### Step 6.2 — 进入目标频道

1. 在左侧栏选择一个 **Team**（团队）
2. 选择或创建一个**频道**（Channel），建议创建一个专用频道，如 "Lab Manager"

> 💡 如果需要创建新频道：右击团队名 → "添加频道" → 输入名称 "Lab Manager"

### Step 6.3 — 打开频道管理

1. 点击频道名称右侧的 **⋯**（更多选项）
2. 选择 **"管理频道"**（Manage channel）

### Step 6.4 — 创建 Outgoing Webhook

1. 在管理页面中，切换到 **"应用"**（Apps）标签页  
2. 找到并点击页面底部的 **"创建传出 Webhook"**（Create an outgoing webhook）按钮
3. 填写以下信息：

| 字段 | 填写内容 |
|------|----------|
| **名称** (Name) | `LabManager` |
| **回调 URL** (Callback URL) | `https://xxxxxxxx-3978.asse.devtunnels.ms/api/messages` |
| **描述** (Description) | `Lab 智能库存与资产管理助手` |
| **头像** (Profile picture) | 可选，上传一个 Bot 头像 |

4. 点击 **"创建"**（Create）

### Step 6.5 — ⚠️ 重要：复制安全令牌！

创建成功后，Teams 会弹出一个对话框，显示一个 **安全令牌**（Security Token）。

```
安全令牌 (Security Token):
xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx=
```

**⚠️ 务必立即复制此令牌！关闭对话框后无法再查看。**

> 📖 **官方文档 — 创建 Outgoing Webhook**：  
> https://learn.microsoft.com/microsoftteams/platform/webhooks-and-connectors/how-to/add-outgoing-webhook

---

## 7. 配置安全令牌

将上一步复制的安全令牌添加到项目的 `.env` 文件中：

### 方式一：手动编辑

用文本编辑器打开 `.env` 文件，添加或修改：

```env
TEAMS_WEBHOOK_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx=
```

### 方式二：使用设置向导

```powershell
python setup_webhook.py
```

向导会引导你完成所有配置步骤，包括粘贴安全令牌。

### 重启 Webhook Bot

配置完令牌后，**需要重启** Webhook Bot 使配置生效：

- 如果使用 `start_webhook.py`：按 `Ctrl+C` 关闭后重新运行
- 如果手动启动：重启 `python webhook_bot.py`

---

## 8. 验证并使用

### 8.1 健康检查

在浏览器中打开：
```
https://xxxxxxxx-3978.asse.devtunnels.ms/api/health
```

应返回：
```json
{
  "status": "ok",
  "service": "Lab Manager Teams Webhook Bot",
  "secret_configured": true
}
```

### 8.2 在 Teams 中测试

在你配置了 Webhook 的频道中，发送以下消息（需要 @提及）：

```
@LabManager 帮助
```

Bot 应回复一张 Adaptive Card，包含所有可用命令。

### 8.3 试试这些命令

| 命令 | 功能 |
|------|------|
| `@LabManager 查一下库存` | 查看当前所有库存 |
| `@LabManager 还有多少鼠标` | 查询特定商品库存 |
| `@LabManager 入库 10 个 USB-C 数据线` | 入库操作 |
| `@LabManager 出库 2 台 Surface Pro 给 Team A` | 出库操作 |
| `@LabManager 查一下所有 Surface 设备` | 资产搜索 |
| `@LabManager 资产概览` | 资产统计汇总 |
| `@LabManager 帮助` | 显示帮助卡片 |
| `@LabManager 清除对话` | 重置对话上下文 |

---

## 9. 日常使用 & 维护

### 每日启动

```powershell
cd "C:\Users\v-lexinhuang\MyPythonlearning\Lab manager's agent for storage"
python start_webhook.py
```

### 查看 Web Dashboard

打开浏览器访问：http://localhost:5001

### 如果 Dev Tunnel URL 变了

1. 复制新的 HTTPS URL
2. 打开 Teams → 频道 → ⋯ → 管理频道 → 应用
3. 找到 LabManager → 编辑 → 更新回调 URL
4. 保存

### 使用持久化 Tunnel 避免 URL 变化

```powershell
# 只需要第一次创建
devtunnel create lab-manager --allow-anonymous
devtunnel port create lab-manager --port-number 3978

# 以后每次启动用
devtunnel host lab-manager
```

### 关闭服务

按 `Ctrl+C` 即可关闭所有服务。

---

## 10. 常见问题

### Q: Teams 中 @LabManager 没有自动补全提示？

**A:** Outgoing Webhook 创建后，需要等待几分钟才会在 @mention 列表中出现。也可以直接手动输入 `@LabManager`。

### Q: Bot 回复 "签名验证失败"？

**A:** 检查 `.env` 文件中的 `TEAMS_WEBHOOK_SECRET` 是否正确。重启 `webhook_bot.py` 使配置生效。

### Q: Dev Tunnel 显示 "not logged in"？

**A:** 运行 `devtunnel user login` 重新登录。

### Q: Bot 回复很慢（>5秒超时）？

**A:** Teams Outgoing Webhook 要求在 **5 秒内响应**。如果 Groq API 延迟较高：
- 检查网络连接
- 在 `.env` 中确认 `GROQ_API_KEY` 正确
- Groq 服务状态查看：https://status.groq.com

### Q: 能在个人聊天（1:1）中使用吗？

**A:** Outgoing Webhook 仅支持**频道**和**群组聊天**中 @mention 使用，不支持 1:1 个人聊天。这是 Teams 平台的限制。  
如果需要 1:1 聊天功能，需要注册 Azure Bot Service（即使免费层也需要 Azure 订阅）：  
https://learn.microsoft.com/azure/bot-service/bot-service-quickstart-registration

### Q: 我需要一直开着电脑吗？

**A:** 是的，因为服务运行在本地。关闭电脑或终端后 Bot 会停止响应。  
如果需要 24/7 运行，可以考虑：
- 部署到一台常开的服务器/工作站
- 未来迁移到云平台（Azure App Service, Railway, Render 等）

### Q: 如何更新代码？

```powershell
cd "C:\Users\v-lexinhuang\MyPythonlearning\Lab manager's agent for storage"
git pull origin main
pip install -r requirements.txt
# 重启服务
python start_webhook.py
```

---

## 📎 参考链接汇总

| 资源 | 链接 |
|------|------|
| **Groq Console (API Key)** | https://console.groq.com/keys |
| **Dev Tunnel 安装** | https://learn.microsoft.com/azure/developer/dev-tunnels/get-started |
| **Dev Tunnel CLI 命令参考** | https://learn.microsoft.com/azure/developer/dev-tunnels/cli-commands |
| **Dev Tunnel 下载 (Windows x64)** | https://aka.ms/TunnelsCliDownload/win-x64 |
| **Teams Outgoing Webhook 官方文档** | https://learn.microsoft.com/microsoftteams/platform/webhooks-and-connectors/how-to/add-outgoing-webhook |
| **Adaptive Cards 设计器** | https://adaptivecards.io/designer/ |
| **Groq 服务状态** | https://status.groq.com |
| **Azure Bot Service (如果以后要升级)** | https://learn.microsoft.com/azure/bot-service/bot-service-quickstart-registration |
| **Microsoft 365 开发者计划 (免费)** | https://developer.microsoft.com/microsoft-365/dev-program |
| **Python 下载** | https://www.python.org/downloads/ |
| **Microsoft Teams 下载** | https://www.microsoft.com/microsoft-teams/download-app |
| **本项目 GitHub** | https://github.com/kylehuang0323-ai/Lab-Manager-Agent-Storage |

---

## 🏗️ 架构概览

```
┌──────────────────────────────────────────────────────────────┐
│                    Microsoft Teams                           │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  频道: Lab Manager                                    │   │
│  │  用户: @LabManager 查一下库存                         │   │
│  └──────────────┬───────────────────────────────────────┘   │
│                 │ HTTPS POST (HMAC-SHA256 签名)              │
└─────────────────┼────────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────┐
│     Dev Tunnel (公网转发)    │
│  https://xxx.devtunnels.ms  │
└──────────────┬──────────────┘
               │ localhost:3978
               ▼
┌──────────────────────────────────────────────────────────────┐
│              你的电脑 (本地运行)                               │
│                                                              │
│  ┌─────────────────┐    ┌──────────────────────────────┐    │
│  │  webhook_bot.py  │───▶│  agent_engine.py (Groq LLM)  │    │
│  │  :3978           │    │  ┌──────────┐ ┌───────────┐  │    │
│  └─────────────────┘    │  │库存管理   │ │资产管理    │  │    │
│                          │  │inventory_ │ │asset_     │  │    │
│  ┌─────────────────┐    │  │manager.py │ │manager.py │  │    │
│  │  Flask Dashboard │    │  └──────────┘ └───────────┘  │    │
│  │  :5001 (Web UI)  │    └──────────────────────────────┘    │
│  └─────────────────┘                                         │
│                          ┌──────────────────┐                │
│                          │  data/ (Excel DB) │                │
│                          └──────────────────┘                │
└──────────────────────────────────────────────────────────────┘
```

---

*最后更新: 2026-03-10*

# Teams App 部署指南

## 前置条件

1. **Azure 账号** — 用于注册 Azure Bot Service
2. **公网 HTTPS 端点** — Bot 需要接收来自 Teams 的 webhook 消息
3. **Microsoft 365 开发者账号** — 用于上传 Teams App

## 步骤一：注册 Azure Bot

1. 登录 [Azure Portal](https://portal.azure.com)
2. 搜索 **Azure Bot** → 创建
3. 填写：
   - Bot handle: `lab-manager-bot`
   - Pricing: F0 (免费)
   - App type: Multi Tenant
   - Creation type: Create new Microsoft App ID
4. 创建完成后，进入 **Configuration**：
   - Messaging endpoint: `https://your-domain.com/api/messages`
5. 进入 **Channels** → 添加 **Microsoft Teams**

## 步骤二：获取 App ID 和 Password

1. 在 Azure Bot 资源 → **Configuration** → 记录 **Microsoft App ID**
2. 点击 **Manage Password** → **New client secret** → 记录 secret value
3. 将两个值填入 `.env`：
   ```
   BOT_APP_ID=your-app-id
   BOT_APP_PASSWORD=your-client-secret
   ```

## 步骤三：本地开发测试

### 使用 Dev Tunnel（推荐）

```bash
# 1. 安装 devtunnel CLI
winget install Microsoft.devtunnel

# 2. 登录
devtunnel user login

# 3. 创建并启动隧道
devtunnel create lab-manager --allow-anonymous
devtunnel port create lab-manager -p 3978
devtunnel host lab-manager

# 4. 获取公网 URL，填入 Azure Bot 的 Messaging endpoint
# 格式: https://xxx.devtunnels.ms/api/messages
```

### 启动 Bot 服务

```bash
# 启动 Teams Bot（端口 3978）
python bot_app.py

# 同时启动 Web 管理后台（端口 5001）
python app.py
```

## 步骤四：打包 Teams App

1. 准备图标文件：
   - `teams_app/color.png` — 192x192 彩色图标
   - `teams_app/outline.png` — 32x32 白色轮廓图标

2. 编辑 `teams_app/manifest.json`：
   - 将 `{{BOT_APP_ID}}` 替换为你的实际 App ID

3. 打包为 zip：
   ```bash
   cd teams_app
   # 将 manifest.json + color.png + outline.png 打成 zip
   Compress-Archive -Path manifest.json, color.png, outline.png -DestinationPath ../lab-manager-teams-app.zip
   ```

## 步骤五：上传到 Teams

1. 打开 **Microsoft Teams**
2. 点击左侧 **Apps** → **Manage your apps** → **Upload an app**
3. 选择 **Upload a custom app** → 上传 zip 包
4. 安装后即可在聊天中 @Lab Manager 使用

## 架构说明

```
Teams 用户 ←→ Azure Bot Service ←→ Bot Webhook (bot_app.py:3978)
                                        ↓
                                  LabManagerBot (teams_bot.py)
                                        ↓
                                  Agent Engine (agent_engine.py)
                                        ↓
                                  Inventory Manager (inventory_manager.py)
                                        ↓
                                  Excel Data (data/*.xlsx)
```

Web 管理后台 (app.py:5001) 与 Bot 共享同一套数据层和 Agent 引擎。

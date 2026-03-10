# 🤖 Copilot Studio + Lab Manager 集成指南

## 架构

```
Teams 用户 → Copilot Studio Agent → REST API Action → ngrok → Flask API (localhost:5001)
```

---

## 第一步：启动本地服务

```powershell
cd "C:\Users\v-lexinhuang\MyPythonlearning\Lab manager's agent for storage"
python start_copilot.py
```

启动后会看到：
```
[ngrok] 🌐 公网 URL: https://xxxx-xxxx.ngrok-free.app
[ngrok] 🤖 Copilot Studio API 端点: https://xxxx-xxxx.ngrok-free.app/api/chat
```

> **⚠️ 注意**: ngrok 免费版每次重启 URL 会变，需要重新配置 Copilot Studio 中的 URL。

---

## 第二步：验证 API 可用

浏览器打开健康检查链接：
```
https://xxxx-xxxx.ngrok-free.app/api/health
```

应返回：
```json
{"status": "ok", "message": "Lab Manager Agent is running"}
```

---

## 第三步：创建 Copilot Studio Agent

### 3.1 打开 Copilot Studio
- 访问 [https://copilotstudio.microsoft.com](https://copilotstudio.microsoft.com)
- 用你的 Microsoft 工作账号登录

### 3.2 创建新 Agent
1. 点击左侧 **"Agents"** → **"+ New agent"**
2. 配置基本信息：
   - **名称**: `Lab Manager`
   - **描述**: `实验室运营管理助手，支持库存查询、出入库、资产管理`
   - **Instructions**: 
     ```
     你是 Lab Manager，一个智能实验室运营管理助手。
     用户可能会用中文或英文与你对话。
     当用户询问库存、资产、出入库相关问题时，调用 chatWithAgent API。
     把 API 返回的 reply 字段内容直接展示给用户。
     如果用户问的不是库存/资产相关的问题，礼貌地引导他们使用相关功能。
     ```
3. 点击 **Create**

### 3.3 添加 REST API Action

#### 方式一：上传 OpenAPI 文件（推荐）
1. 在 Agent 编辑器中，点击 **"+ Add action"**
2. 选择 **"REST API"**（或 "Connector" → "Custom"）
3. 上传项目中的 `openapi.yaml` 文件
4. Copilot Studio 会自动解析出所有 API 端点
5. **关键**：选中 `chatWithAgent` 操作（POST /api/chat）
6. 认证方式选 **"No authentication"**（本地开发阶段）

#### 方式二：手动配置
1. 点击 **"+ Add action"** → **"REST API"**
2. 手动填写：
   - **Base URL**: `https://xxxx-xxxx.ngrok-free.app`
   - **Method**: `POST`
   - **Path**: `/api/chat`
   - **Body**: 
     ```json
     {
       "message": "{user_message}"
     }
     ```
   - **Response**: 映射 `reply` 字段为输出

### 3.4 配置 Topic（对话流）

创建一个 Topic 处理用户的库存/资产查询：

1. 点击 **"Topics"** → **"+ New topic"** → **"From blank"**
2. **Trigger phrases** (触发短语):
   ```
   查库存
   查一下库存
   出库
   入库
   资产管理
   查资产
   帮我查一下
   库存多少
   还有多少
   分配资产
   ```
3. **Add node** → **"Call an action"** → 选择 `chatWithAgent`
4. 把用户的输入（`Activity.Text`）映射到 `message` 参数
5. **Add node** → **"Send a message"** → 用 `reply` 字段回复用户

### 3.5 也可使用"经典"Conversational Agent

如果不想手动配 Topic，可以在 Agent 的 Instructions 中直接引用 REST API Action：
```
当用户提到库存、资产、出入库、鼠标、Surface、设备等关键词时，
使用 chatWithAgent action，将用户的完整消息作为 message 参数传入，
并把返回的 reply 展示给用户。
```
Copilot Studio 的 Generative AI 能力会自动识别何时调用 API。

---

## 第四步：发布到 Teams

1. 在 Agent 编辑器顶部点击 **"Publish"**
2. 点击 **"Channels"** → 启用 **"Microsoft Teams"**
3. 点击 **"Open in Teams"** 测试
4. 在 Teams 中直接对话：
   - `查一下目前所有的库存`
   - `入库 20 个 USB-C 数据线`
   - `把 Surface Pro 分配给 Lexin`
   - `资产概览`
   - `导出库存报表`

---

## 常用 API 端点参考

| 端点 | 说明 | 推荐在 Copilot 中使用 |
|------|------|---------------------|
| `POST /api/chat` | AI 对话（最核心） | ✅ 必须 |
| `GET /api/inventory` | 获取库存列表 | 可选 |
| `GET /api/assets/summary` | 资产统计概览 | 可选 |
| `GET /api/health` | 健康检查 | 调试用 |

> **推荐**: 只配置 `/api/chat` 一个端点即可。Agent 引擎会自动识别用户意图并调用内部工具，无需在 Copilot Studio 端做意图分类。

---

## 故障排查

| 问题 | 解决方案 |
|------|----------|
| ngrok URL 变了 | 重启 `start_copilot.py` 后更新 Copilot Studio 中的 Base URL |
| API 返回 502 | 检查 Flask 是否在运行 (`http://localhost:5001/api/health`) |
| Copilot 不调用 API | 检查 Topic 触发短语是否匹配，或在 Instructions 中加强提示 |
| 中文乱码 | 确保 openapi.yaml 中 charset 正确，Flask 返回 UTF-8 |
| ngrok 免费版限制 | 每分钟 20 次请求限制，个人使用足够 |

---

## 文件说明

| 文件 | 用途 |
|------|------|
| `start_copilot.py` | 一键启动 Flask + ngrok |
| `openapi.yaml` | API 规范文件（上传到 Copilot Studio） |
| `app.py` | Flask 主应用 |
| `agent_engine.py` | Groq LLM Agent 引擎 |
| `webhook_bot.py` | Teams Outgoing Webhook（备用方案） |

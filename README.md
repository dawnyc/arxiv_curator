# Arxiv Curator

Arxiv Curator 是一个基于 FastAPI 和 Vue 3 构建的轻量级 Arxiv 论文浏览与 AI 摘要工具。它可以帮助研究人员快速筛选每日最新的论文，并利用 AI（如 OpenAI 或 DeepSeek）生成精简的中文摘要。

## ✨ 主要功能

*   **📅 每日论文速览**: 按日期和分类（cs.AI, cs.CV, cs.LG, cs.CL）浏览最新的 Arxiv 论文。
*   **🆔 指定论文查询**: 支持直接输入 Arxiv ID（如 `2310.12345`）查询特定论文。
*   **🤖 AI 智能摘要**:
    *   集成 OpenAI 兼容接口（支持 GPT-4o, DeepSeek-V3/R1 等）。
    *   生成结构化的中文摘要（核心问题、方法创新、关键结论）。
    *   支持自定义 API Base URL 和模型名称。
*   **⭐ 收藏与管理**:
    *   收藏感兴趣的论文。
    *   置顶重要论文（📌）。
    *   在收藏列表中直接查看已生成的 AI 摘要。
*   **📱 现代化 UI**:
    *   类似 Tinder 的卡片式浏览体验（左滑 Pass，右滑 Keep）。
    *   响应式设计，支持移动端和桌面端。

## 🛠️ 环境准备

*   **Python**: 3.9 或更高版本
*   **操作系统**: Windows / macOS / Linux

## 🚀 快速开始

### 1. 获取代码

```bash
git clone [<repository-url>](https://github.com/dawnyc/arxiv_curator.git)
cd arxiv_curator
```

### 2. 后端环境配置

进入 `backend` 目录并创建/激活虚拟环境（推荐）：

**macOS / Linux:**
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
```

**Windows:**
```bash
cd backend
python -m venv venv
venv\Scripts\activate
```

### 3. 安装依赖

在激活的虚拟环境中运行：

```bash
pip install -r requirements.txt
```

### 4. 启动服务

使用 `uvicorn` 启动后端服务。后端会自动挂载前端静态页面，因此无需单独启动前端服务。

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

启动成功后，终端会显示类似如下信息：
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

### 5. 访问应用

打开浏览器访问：

**[http://localhost:8000](http://localhost:8000)**

## ⚙️ 配置 AI 服务

首次进入应用时，点击 **"⚙️ Configure API"** 配置 AI 服务：

*   **API Provider**: 默认为 OpenAI / Compatible。
*   **API Key**: 您的 API 密钥（如 OpenAI Key 或 DeepSeek Key）。
*   **Base URL (可选)**:
    *   如果使用 **DeepSeek**，请填写 `https://api.deepseek.com`。
    *   如果使用官方 OpenAI，可留空（默认 `https://api.openai.com/v1`）。
*   **Model Name**:
    *   OpenAI: `gpt-4o`, `gpt-4o-mini`
    *   DeepSeek: `deepseek-chat` (V3), `deepseek-reasoner` (R1)

配置保存在浏览器的 LocalStorage 中，不会上传到服务器。

## 📂 项目结构

```
arxiv_curator/
├── backend/
│   ├── main.py           # FastAPI 入口
│   ├── services.py       # 业务逻辑 (Arxiv API, OpenAI 调用)
│   ├── models.py         # 数据库模型
│   ├── schemas.py        # Pydantic 数据验证
│   ├── database.py       # SQLite 数据库连接
│   ├── arxiv.db          # SQLite 数据库文件 (自动生成)
│   └── requirements.txt  # Python 依赖
├── frontend/
│   └── index.html        # 单页应用入口 (Vue 3 + Tailwind CSS)
└── README.md
```

## 📝 注意事项

*   **Arxiv API 限制**: 频繁请求可能会导致 Arxiv API 暂时限流，请耐心等待。
*   **数据缓存**: 应用会缓存已获取的论文信息以减少 API 调用。可以在设置中点击 "Clear App Cache" 清理缓存。

# fortune-analysis
个人运势分析

## 开发启动

复制环境变量示例并填写 API Key：

```bash
cp .env.example .env
```

默认使用 DeepSeek：

```env
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=你的 DeepSeek API Key
```

如需切换 Kimi：

```env
LLM_PROVIDER=kimi
KIMI_API_KEY=你的 Kimi API Key
```

后端：

```bash
python -m pip install -r requirements.txt
uvicorn backend.app.main:app --reload
```

前端：

```bash
npm install
npm run dev
```

## 部署上线（Render API + Vercel 前端）

架构：**后端**部署在 [Render](https://render.com)（Python Web Service），**前端**部署在 [Vercel](https://vercel.com)（静态构建）。已用 MCP（Firecrawl）对照 [Render FastAPI 文档](https://render.com/docs/deploy-fastapi) 校验常见启动方式（`uvicorn` + `$PORT`）。

### 1. 部署后端（Render）

1. 登录 Render → **New** → **Blueprint**（或 **Web Service**）并连接本 GitHub 仓库。
2. 若使用 Blueprint：选择含 `render.yaml` 的分支，创建后补全 **Environment** 中的密钥变量（`DEEPSEEK_API_KEY` 或 `KIMI_*`，以及 `FRONTEND_ORIGINS`）。
3. **`FRONTEND_ORIGINS`**：填你的 Vercel 站点完整 origin，多个用英文逗号分隔，例如 `https://fortune-xxx.vercel.app,http://127.0.0.1:5173`。勿带路径。
4. 部署完成后记下 **HTTPS 根 URL**（例如 `https://fortune-analysis-api.onrender.com`），供前端使用。

手动创建 Web Service 时：**Build** `pip install -r requirements.txt`，**Start** `uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT`。仓库根目录已提供 `runtime.txt` 指定 Python 3.12。

可选：使用根目录 `Dockerfile` 在支持 Docker 的平台部署，启动命令需读取环境变量 `PORT`。

### 2. 部署前端（Vercel）

1. 登录 Vercel → **Add New Project** → 导入同一 GitHub 仓库。
2. **Framework Preset** 选 Vite；根目录默认仓库根；`vercel.json` 已配置 SPA 回写与构建输出 `dist`。
3. 在 **Settings → Environment Variables** 中为 **Production**（及如需 Preview）添加：
   - **`VITE_API_BASE_URL`** = 上一步 Render 的 API 根 URL（**无**末尾 `/`），例如 `https://fortune-analysis-api.onrender.com`。
4. 保存后重新 **Deploy**。前端请求会直连该地址的 `/optimize`、`/history` 等（与本地 `/api` 代理不同，无需路径前缀）。

### 3. 自检

- 浏览器打开 Vercel 域名，打开开发者工具 **Network**，提交表单应看到对 Render 域名的 `POST .../optimize` 且状态 200。
- 若 CORS 报错：检查 Render 上 `FRONTEND_ORIGINS` 是否与浏览器地址栏 origin **完全一致**（含 `https`）。

## 测试

```bash
python -m unittest discover -s backend/tests
npm test
npm run build
```

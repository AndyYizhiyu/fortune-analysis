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

## 部署上线（腾讯云）

推荐在 **腾讯云轻量应用服务器** 或 **云服务器 CVM**（Linux）上使用 **Docker Compose** 单机部署：同一域名 / 同一端口，**Nginx** 托管前端静态资源，并把 **`/api/*`** 反代到 **FastAPI**（与本地 `vite` 的 `/api` 代理一致，**无需**设置 `VITE_API_BASE_URL`）。

### 1. 准备云主机

1. 在控制台购买 **轻量应用服务器** 或 **CVM**（建议 Ubuntu 22.04），放行安全组 **TCP 80**（及若使用 HTTPS 则 **443**）。
2. SSH 登录主机，安装 [Docker Engine](https://docs.docker.com/engine/install/ubuntu/) 与 [Docker Compose 插件](https://docs.docker.com/compose/install/linux/)。

### 2. 拉代码与配置

```bash
git clone https://github.com/AndyYizhiyu/fortune-analysis.git
cd fortune-analysis
cp .env.example .env
# 编辑 .env：至少填写 DEEPSEEK_API_KEY（或 Kimi 相关变量）
```

**必须**设置 **`FRONTEND_ORIGINS`** 为浏览器实际访问的 origin（与地址栏协议 + 域名 + 端口一致），多个用英文逗号分隔，例如：

```env
FRONTEND_ORIGINS=https://你的备案域名,http://公网IP
```

仅本机试跑 Compose 时可写：`http://127.0.0.1,http://localhost`。

### 3. 启动

```bash
docker compose up -d --build
```

默认 **HTTP 80** 对外（可通过环境变量 `HTTP_PORT` 修改映射，例如 `HTTP_PORT=8080 docker compose up -d`）。

### 4. HTTPS（可选）

- 使用 **腾讯云 SSL 证书** + **负载均衡 CLB** 在 443 终结 TLS，回源到主机 80；或  
- 在主机上自行配置 **Nginx 443 + 证书**（如 Certbot、宝塔等），并将 `FRONTEND_ORIGINS` 增加 `https://你的域名`。

### 5. 与「仅腾讯云」相关的仓库文件

| 路径 | 说明 |
|------|------|
| `docker-compose.yml` | `api`（`Dockerfile`）+ `web`（`deployment/tencent/Dockerfile.web`） |
| `deployment/tencent/nginx.conf` | 静态站点 + `/api/` 反代 |
| `deployment/tencent/Dockerfile.web` | Node 构建 Vue，再拷贝到 Nginx |

### 6. 自检

浏览器打开 `http://你的IP` 或域名，开发者工具 **Network** 中提交表单应出现 **`/api/optimize`** 且状态为 **200**。若 CORS 报错，请核对 **`FRONTEND_ORIGINS`** 是否与地址栏 **完全一致**（含 `http`/`https` 与端口）。

## 测试

```bash
python -m unittest discover -s backend/tests
npm test
npm run build
```

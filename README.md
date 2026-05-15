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

## 部署上线（腾讯云轻量 + Docker）

默认路线：**腾讯云轻量应用服务器（Lighthouse）** + **Docker Compose** 单机部署。架构与本地一致：同一访问地址下，**Nginx** 托管 Vue 静态资源，**`/api/*`** 反代到 **FastAPI**（**无需**设置 `VITE_API_BASE_URL`）。若你使用 **云服务器 CVM**，步骤相同，仅控制台入口不同。

### 1. 购买轻量并开放端口

1. 打开 [轻量应用服务器控制台](https://console.cloud.tencent.com/lighthouse)，新建实例：**地域**就近选择；**镜像**建议 **Ubuntu 22.04**（或自带 Docker 的应用镜像亦可）；**套餐**个人试用可先选较低档；构建镜像时会吃 CPU/内存，若频繁部署建议 **≥ 2GB 内存** 更稳。
2. **防火墙 / 安全组**：在轻量实例面板为服务器放行 **TCP 80**（公网访问 HTTP）。若后续上 HTTPS，再放行 **TCP 443**。注意轻量除「关联安全组」外，常有 **独立防火墙规则**，需在两处或防火墙页签中均放行，否则浏览器无法访问。
3. SSH 登录（控制台「登录」或本地 `ssh ubuntu@服务器IP`），确认系统为 Linux 后再装 Docker。

### 2. 安装 Docker（Ubuntu 示例）

若镜像未预装 Docker，在服务器上执行（官方文档，可按需替换版本）：

- [Install Docker Engine on Ubuntu](https://docs.docker.com/engine/install/ubuntu/)
- [Docker Compose 插件](https://docs.docker.com/compose/install/linux/)

装好后执行 `docker compose version`，有版本号即可。

### 3. 拉代码与配置

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

### 4. 启动

```bash
docker compose up -d --build
```

首次会拉基础镜像并执行前端 `npm run build`，可能需数分钟。默认把容器 **80** 映射到主机 **80**（可通过环境变量 **`HTTP_PORT`** 改成例如 `8080`：`HTTP_PORT=8080 docker compose up -d`）。改端口后，浏览器访问 `http://IP:端口`，且 **`FRONTEND_ORIGINS`** 须带上对应 origin（含端口）。

### 5. HTTPS（可选）

- 使用 **腾讯云 SSL 证书** + **负载均衡 CLB** 在 443 终结 TLS，回源到主机 80；或  
- 在主机上自行配置 **Nginx 443 + 证书**（如 Certbot、宝塔等），并将 `FRONTEND_ORIGINS` 增加 `https://你的域名`。

### 6. 仓库内与部署相关的文件

| 路径 | 说明 |
|------|------|
| `docker-compose.yml` | `api`（`Dockerfile`）+ `web`（`deployment/tencent/Dockerfile.web`） |
| `deployment/tencent/nginx.conf` | 静态站点 + `/api/` 反代 |
| `deployment/tencent/Dockerfile.web` | Node 构建 Vue，再拷贝到 Nginx |

### 7. 自检

浏览器打开 `http://你的IP` 或域名，开发者工具 **Network** 中提交表单应出现 **`/api/optimize`** 且状态为 **200**。若 CORS 报错，请核对 **`FRONTEND_ORIGINS`** 是否与地址栏 **完全一致**（含 `http`/`https` 与端口）。

## 测试

```bash
python -m unittest discover -s backend/tests
npm test
npm run build
```

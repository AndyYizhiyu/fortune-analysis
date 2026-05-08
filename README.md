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

## 测试

```bash
python -m unittest discover -s backend/tests
npm test
npm run build
```

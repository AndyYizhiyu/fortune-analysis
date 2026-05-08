# fortune-analysis
个人运势分析

## 开发启动

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

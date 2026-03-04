# 仪器设备管理系统

一个用于管理测试间仪器设备借用和归还的 Web 应用。

## 功能特性

- 📊 查看仪器设备清单和可用状态
- 📝 借用仪器（支持选择数量）
- 🔄 归还仪器
- 📈 实时统计使用情况
- 📜 查看当前和历史记录

## 本地运行

```bash
python3 server.py
# 或 Flask 版本
python3 app.py
```

访问 http://127.0.0.1:8081

## 部署到 Render（免费）

### 1. 创建 GitHub 仓库

```bash
git init
git add .
git commit -m "Initial commit"
# 在 GitHub 创建仓库后
git remote add origin https://github.com/你的用户名/仪器管理系统.git
git push -u origin main
```

### 2. 部署到 Render

1. 访问 [render.com](https://render.com) 并注册账号
2. 点击 "New +" → "Web Service"
3. 连接你的 GitHub 仓库
4. 配置：
   - **Name**: instrument-management (或你喜欢的名字)
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn --bind 0.0.0.0:$PORT --workers 1 --threads 4 app:app`
5. 点击 "Create Web Service"

### 3. 完成！

等待部署完成后，你会获得一个类似 `https://instrument-management.onrender.com` 的免费域名。

## 数据说明

- 仪器数据存储在 `data/instruments.json`
- 借用记录存储在 `data/records.json`
- 历史记录存储在 `data/history.json`

**注意**: Render 的免费实例磁盘不是持久的，重启后数据可能会丢失。建议定期导出数据。

## 技术栈

- 前端: HTML5 + CSS3 + JavaScript (原生)
- 后端: Flask / Python HTTP Server
- 数据存储: JSON 文件

## 文件说明

- `index.html` - 前端页面
- `server.py` - 原始 Python HTTP 服务器（适合本地使用）
- `app.py` - Flask 版本（适合部署）
- `requirements.txt` - Python 依赖
- `Procfile` - Render 部署配置
- `data/` - 数据存储目录

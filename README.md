# StockBuzzTracker
实时追踪 Reddit热门讨论股票
社交平台过去 24 小时内提及次数最多的美股，计算热度变化以及情感偏好并展示排名。

## ✨ 功能
- 📊 热度排名表：展示股票代码、提及次数、24h变化、点赞数
- 📈 趋势图表：提及次数随时间变化折线图
- 🌐 多平台聚合：Reddit、Twitter（暂无数据）
- ⏰ 实时更新：后端每小时自动抓取，前端每5分钟刷新
- 🎨 深色/浅色主题

## 🚀 快速开始
### 1. 克隆项目
```bash
git clone https://github.com/你的用户名/StockBuzzTracker.git
cd StockBuzzTracker


StockBuzzTracker/
├── backend/
│   ├── main.py               ✅
│   ├── collector/
│   │   └── twitter.py        ✅
│   ├── extractor.py          ✅
│   └── config.py             (可选)
├── data/
│   └── tickers.csv           ✅ (从 NASDAQ 下载并重命名)
├── frontend/
│   └── index.html            ✅
├── requirements.txt          ✅
├──  README.md
├── streamlit_app.py          ✅ 可单独运行查看情感偏好
|── start.bat                 ✅ 一键启动

import streamlit as st
import requests
import pandas as pd
import re
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from datetime import datetime, timedelta
from collections import defaultdict
import time

# ========== 页面设置 ==========
st.set_page_config(page_title="Reddit Stock Sentiment", page_icon="📊", layout="wide")
st.title("📊 Reddit 热门股票情感分析看板")
st.caption("基于 FinBERT 模型 · 数据来源：Reddit (官方 JSON API) · 自动刷新：每10分钟")

# 自动刷新（每10分钟）
from streamlit_autorefresh import st_autorefresh
st_autorefresh(interval=600 * 1000, key="sentiment_refresh")

# ========== 加载 FinBERT ==========
@st.cache_resource
def load_finbert():
    tokenizer = AutoTokenizer.from_pretrained("ProsusAI/finbert")
    model = AutoModelForSequenceClassification.from_pretrained("ProsusAI/finbert")
    model.eval()
    return tokenizer, model

tokenizer, model = load_finbert()

def get_sentiment(text):
    """返回正面、中性、负面概率，以及综合分数 (pos - neg)"""
    inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
    with torch.no_grad():
        outputs = model(**inputs)
        scores = torch.nn.functional.softmax(outputs.logits, dim=-1).squeeze(0)
    neg, neu, pos = scores[0].item(), scores[1].item(), scores[2].item()
    compound = pos - neg
    return neg, neu, pos, compound

# ========== 获取 Reddit 热门股票列表（复用 ApeWisdom）==========
def get_top_tickers(n=10):
    """从 ApeWisdom 获取前 n 个热门股票代码"""
    url = "https://apewisdom.io/api/v1.0/filter/all-stocks/page/1"
    try:
        resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        if resp.status_code != 200:
            return []
        data = resp.json()
        results = data.get("results", [])
        tickers = [r["ticker"] for r in results[:n] if r.get("ticker")]
        return tickers
    except Exception as e:
        st.error(f"获取热门股票列表失败: {e}")
        return []

import feedparser

def fetch_posts_for_ticker(ticker, limit=25):
    """通过 Reddit RSS 搜索包含 $TICKER 的帖子（过去24小时）"""
    query = f"${ticker}"
    url = f"https://www.reddit.com/r/wallstreetbets/search.rss?q={query}&restrict_sr=on&sort=new&t=day&limit={limit}"
    headers = {"User-Agent": "StockBuzzTracker/1.0 (your_reddit_username)"}
    try:
        feed = feedparser.parse(url)
        posts = []
        for entry in feed.entries[:limit]:
            title = entry.get("title", "")
            # Reddit 的 summary 字段通常包含正文或摘要
            summary = entry.get("summary", "")
            full_text = f"{title} {summary}"
            if len(full_text.strip()) >= 20:
                posts.append(full_text)
        return posts
    except Exception as e:
        st.error(f"RSS 抓取 {ticker} 失败: {e}")
        return []

# ========== 主分析流程 ==========
with st.spinner("正在获取 Reddit 热门股票并分析情感，请稍候..."):
    top_tickers = get_top_tickers(10)
    if not top_tickers:
        st.warning("⚠️ 无法获取热门股票列表，请稍后重试。")
        st.stop()

    ticker_sentiments = []
    progress_bar = st.progress(0)

    for i, ticker in enumerate(top_tickers):
        posts = fetch_posts_for_ticker(ticker, limit=25)
        if not posts:
            ticker_sentiments.append({
                "代码": ticker,
                "分析帖子数": 0,
                "平均情感分数": 0,
                "情感标签": "⚪ 数据不足",
                "提及次数": 0
            })
        else:
            total_compound = 0
            for text in posts:
                _, _, _, compound = get_sentiment(text)
                total_compound += compound
            avg_compound = total_compound / len(posts)
            tag = "🟢 正面" if avg_compound > 0.1 else ("🔴 负面" if avg_compound < -0.1 else "⚪ 中性")
            ticker_sentiments.append({
                "代码": ticker,
                "分析帖子数": len(posts),
                "平均情感分数": round(avg_compound, 3),
                "情感标签": tag,
                "提及次数": len(posts)  # 作为提及次数参考
            })
        progress_bar.progress((i + 1) / len(top_tickers))
        time.sleep(1)  # 遵守 Reddit API 速率限制（每分钟60次）

# ========== 展示结果 ==========
df = pd.DataFrame(ticker_sentiments).sort_values("平均情感分数", ascending=False).reset_index(drop=True)
df.index = df.index + 1  # 排名

col1, col2, col3 = st.columns(3)
col1.metric("📋 分析股票数", len(top_tickers))
col2.metric("📄 累计分析帖子", df["分析帖子数"].sum())
col3.metric("🤖 情感模型", "FinBERT")

st.markdown("---")
st.subheader("🏆 情感排行榜")

# 条形图展示平均情感分数
st.bar_chart(df.set_index("代码")["平均情感分数"], use_container_width=True)

# 详细表格
st.dataframe(
    df.style.background_gradient(cmap="RdYlGn", subset=["平均情感分数"]),
    use_container_width=True,
    height=400
)

st.markdown("---")
st.caption("⚠️ 本工具仅供学习研究，不构成任何投资建议。情感分数仅反映 Reddit 讨论的语气，不代表股票未来走势。")
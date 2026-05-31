import os, re, json, time, threading
import requests
import feedparser
from datetime import datetime, timedelta
from collections import defaultdict
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification

# ---------- 加载 FinBERT ----------
tokenizer = AutoTokenizer.from_pretrained("ProsusAI/finbert")
model = AutoModelForSequenceClassification.from_pretrained("ProsusAI/finbert")
model.eval()

def finbert_sentiment(text):
    inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
    with torch.no_grad():
        outputs = model(**inputs)
        scores = torch.nn.functional.softmax(outputs.logits, dim=-1).squeeze(0)
    neg, neu, pos = scores[0].item(), scores[1].item(), scores[2].item()
    return neg, neu, pos, pos - neg

# ---------- ApeWisdom 纯提及次数 ----------
def fetch_apewisdom_mentions(n=25):
    """返回 [{"rank":1, "ticker":"AAPL", "mentions":123}, ...]"""
    url = "https://apewisdom.io/api/v1.0/filter/all-stocks/page/1"
    try:
        resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        if resp.status_code != 200:
            return []
        data = resp.json()
        results = data.get("results", [])
        output = []
        for i, item in enumerate(results[:n]):
            output.append({
                "rank": item.get("rank", i+1),
                "ticker": item.get("ticker", "").upper(),
                "mentions": item.get("mentions", 0)
            })
        return output
    except:
        return []

# ---------- Reddit RSS + FinBERT 情感 ----------
def fetch_reddit_posts_for_ticker(ticker, limit=30):
    url = f"https://www.reddit.com/r/wallstreetbets/search.rss?q=${ticker}&sort=new&restrict_sr=on&t=day&limit={limit}"
    headers = {"User-Agent": "StockBuzzTracker/1.0"}
    try:
        feed = feedparser.parse(url)
        posts = []
        for entry in feed.entries[:limit]:
            text = f"{entry.get('title','')} {entry.get('summary','')}"
            if len(text.strip()) >= 20:
                posts.append(text)
        return posts
    except:
        return []

def compute_sentiment_for_tickers(tickers):
    results = []
    for ticker in tickers:
        posts = fetch_reddit_posts_for_ticker(ticker, limit=30)
        if not posts:
            continue   # 没有帖子就跳过
        scores = [finbert_sentiment(text)[3] for text in posts]
        avg = sum(scores) / len(scores)
        results.append({
            "ticker": ticker,
            "mentions": len(posts),
            "sentiment": round(avg, 3)
        })
    results.sort(key=lambda x: x["mentions"], reverse=True)
    for i, item in enumerate(results):
        item["rank"] = i + 1
    return results

# 缓存情感分析结果
sentiment_cache = {"data": [], "last_updated": None}

def update_sentiment_cache():
    # 获取 ApeWisdom 前20个热门股作为分析种子
    hot_tickers = [item["ticker"] for item in fetch_apewisdom_mentions(20)]
    sentiment_cache["data"] = compute_sentiment_for_tickers(hot_tickers)
    sentiment_cache["last_updated"] = datetime.utcnow().isoformat()

# ---------- FastAPI 应用 ----------
app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

@app.on_event("startup")
def startup():
    # 后台线程初始化情感缓存
    threading.Thread(target=update_sentiment_cache).start()

@app.get("/api/reddit-trending")
def reddit_trending():
    """纯提及次数排名，不包含情感分析"""
    return fetch_apewisdom_mentions(25)

@app.get("/api/reddit-sentiment")
def reddit_sentiment():
    """返回已缓存的情感分析结果（仅包含有帖子的股票）"""
    # 若缓存为空或超过1小时则更新
    if not sentiment_cache["last_updated"] or \
       (datetime.utcnow() - datetime.fromisoformat(sentiment_cache["last_updated"])).seconds > 3600:
        update_sentiment_cache()
    return sentiment_cache["data"]

@app.get("/api/twitter-trending")
def twitter_trending():
    return []  # 预留
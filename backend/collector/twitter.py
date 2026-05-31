import requests
from datetime import datetime, timedelta

STOCKTWITS_API = "https://api.stocktwits.com/api/2/streams/trending.json"

def fetch_twitter_mentions(pages=1):
    """
    使用 StockTwits 免费接口获取当前热门股票讨论。
    返回统一的 mention 列表。
    """
    mentions = []
    try:
        resp = requests.get(STOCKTWITS_API, timeout=10)
        if resp.status_code != 200:
            print(f"StockTwits error {resp.status_code}: {resp.text}")
            return []

        data = resp.json()
        for msg in data.get("messages", []):
            # 提取所有 cashtag
            symbols = []
            for entity in msg.get("entities", {}).get("symbols", []):
                symbols.append(entity.get("symbol", "").upper())
            text = msg.get("body", "")
            score = msg.get("likes", {}).get("total", 0)
            created = msg.get("created_at", datetime.utcnow().isoformat())
            for ticker in symbols:
                mentions.append({
                    "platform": "twitter",  # 保持字段兼容
                    "text": text,
                    "score": score,
                    "created_at": created,
                    "ticker": ticker
                })

    except Exception as e:
        print(f"StockTwits fetch error: {e}")
    return mentions
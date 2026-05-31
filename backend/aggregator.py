from collections import defaultdict
from collector.meiguhuli import fetch_trending as fetch_reddit_trending
from collector.twitter import fetch_twitter_mentions
from extractor import extract_tickers

def get_combined_trending():
    """
    获取 Reddit + Twitter 合并热度榜。
    返回 list[dict]，按总提及次数降序排列。
    """
    # 1. 获取 Reddit 榜单（来自 meiguhuli）
    reddit_data = fetch_reddit_trending()  # list of dict，包含 ticker, mentions, upvotes, change_percent, name, rank

    # 2. 获取 Twitter 提及数据，并统计每个代码的出现次数和点赞数
    twitter_mentions = fetch_twitter_mentions(pages=2)
    twitter_counts = defaultdict(int)
    twitter_scores = defaultdict(int)

    for tweet in twitter_mentions:
        # 从推文文本中提取股票代码
        codes = extract_tickers(tweet.get("text", ""))
        for code in codes:
            twitter_counts[code] += 1
            twitter_scores[code] += tweet.get("score", 0)

    # 3. 合并 Reddit 和 Twitter 数据
    combined = []
    for item in reddit_data:
        ticker = item["ticker"]
        tw_mentions = twitter_counts.get(ticker, 0)
        tw_score = twitter_scores.get(ticker, 0)

        combined.append({
            "rank": item.get("rank"),
            "ticker": ticker,
            "name": item.get("name", ""),
            "reddit_mentions": item.get("mentions", 0),
            "reddit_upvotes": item.get("upvotes", 0),
            "reddit_change": item.get("change_percent", 0),
            "twitter_mentions": tw_mentions,
            "twitter_score": tw_score,
            "total_mentions": item.get("mentions", 0) + tw_mentions
        })

    # 4. 处理可能只在 Twitter 出现但不在 Reddit 榜单的股票（可选）
    #    这里暂时不加，因为 Reddit 榜单已包含了主要热门股

    # 5. 按总提及次数降序排列
    combined.sort(key=lambda x: x["total_mentions"], reverse=True)

    # 重新排名（1、2、3...）
    for i, item in enumerate(combined):
        item["rank"] = i + 1

    return combined
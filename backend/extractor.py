import re
import pandas as pd

# 全局变量存储已加载的股票代码集合
TICKER_SET = set()

def load_tickers(csv_path: str = "data/tickers.csv"):
    global TICKER_SET
    try:
        df = pd.read_csv(csv_path)
        # 自动寻找符号列（不区分大小写）
        symbol_col = None
        for col in df.columns:
            if col.lower() == 'symbol':
                symbol_col = col
                break
        if symbol_col is None:
            raise ValueError("CSV 中缺少 symbol/Symbol 列")
        TICKER_SET = set(df[symbol_col].str.upper().str.strip())
        print(f"Loaded {len(TICKER_SET)} tickers.")
    except FileNotFoundError:
        print(f"Warning: {csv_path} not found.")
        TICKER_SET = set()
    except Exception as e:
        print(f"Error loading tickers: {e}")
        TICKER_SET = set()

def extract_tickers(text: str) -> set:
    """
    从文本中提取类似 $AAPL 的股票代码，并返回在 TICKER_SET 中的有效代码。
    """
    if not text or not isinstance(text, str):
        return set()
    # 匹配 $ 后跟1-5个大写字母
    cashtags = re.findall(r'\$([A-Za-z]{1,5})', text)
    # 转为大写并过滤
    valid = set()
    for code in cashtags:
        code_upper = code.upper().strip()
        if code_upper in TICKER_SET:
            valid.add(code_upper)
    return valid
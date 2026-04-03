"""
A 股行情数据获取 — 共享库模块
数据源：新浪财经（主）+ 腾讯股票（备），自动容错切换。
封装自 https://github.com/mpquant/Ashare

公开 API：
    get_price(code, end_date, count, frequency) -> pd.DataFrame
    get_realtime(code) -> dict
"""

import datetime

import pandas as pd
import requests


def _normalize_code(code: str) -> str:
    xcode = code.replace(".XSHG", "").replace(".XSHE", "")
    if "XSHG" in code:
        return "sh" + xcode
    if "XSHE" in code:
        return "sz" + xcode
    return code


def _get_price_day_tx(code: str, end_date: str = "", count: int = 10, frequency: str = "1d") -> pd.DataFrame:
    unit = "week" if frequency == "1w" else "month" if frequency == "1M" else "day"
    if end_date:
        end_date = end_date.split(" ")[0] if isinstance(end_date, str) else end_date.strftime("%Y-%m-%d")
    if end_date == datetime.datetime.now().strftime("%Y-%m-%d"):
        end_date = ""
    url = f"http://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param={code},{unit},,{end_date},{count},qfq"
    st = requests.get(url, timeout=10).json()
    ms = "qfq" + unit
    stk = st["data"][code]
    buf = stk.get(ms, stk.get(unit))
    df = pd.DataFrame(buf, columns=["time", "open", "close", "high", "low", "volume"], dtype="float")
    df["time"] = pd.to_datetime(df["time"])
    df.set_index("time", inplace=True)
    df.index.name = "date"
    return df


def _get_price_min_tx(code: str, end_date: str | None = None, count: int = 10, frequency: str = "1d") -> pd.DataFrame:
    ts = int(frequency[:-1]) if frequency[:-1].isdigit() else 1
    url = f"http://ifzq.gtimg.cn/appstock/app/kline/mkline?param={code},m{ts},,{count}"
    st = requests.get(url, timeout=10).json()
    buf = st["data"][code][f"m{ts}"]
    df = pd.DataFrame(buf, columns=["time", "open", "close", "high", "low", "volume", "n1", "n2"])
    df = df[["time", "open", "close", "high", "low", "volume"]]
    for col in ["open", "close", "high", "low", "volume"]:
        df[col] = df[col].astype(float)
    df["time"] = pd.to_datetime(df["time"])
    df.set_index("time", inplace=True)
    df.index.name = "date"
    try:
        df["close"].iloc[-1] = float(st["data"][code]["qt"][code][3])
    except (KeyError, IndexError):
        pass
    return df


def _get_price_sina(code: str, end_date: str = "", count: int = 10, frequency: str = "60m") -> pd.DataFrame:
    freq = frequency.replace("1d", "240m").replace("1w", "1200m").replace("1M", "7200m")
    mcount = count
    ts = int(freq[:-1]) if freq[:-1].isdigit() else 1
    if end_date and freq in ("240m", "1200m", "7200m"):
        ed = pd.to_datetime(end_date) if isinstance(end_date, str) else end_date
        unit = {"1200m": 4, "7200m": 29}.get(freq, 1)
        count = count + (datetime.datetime.now() - ed).days // unit
    url = (
        f"http://money.finance.sina.com.cn/quotes_service/api/json_v2.php/"
        f"CN_MarketData.getKLineData?symbol={code}&scale={ts}&ma=5&datalen={count}"
    )
    dstr = requests.get(url, timeout=10).json()
    df = pd.DataFrame(dstr, columns=["day", "open", "high", "low", "close", "volume"])
    for col in ["open", "high", "low", "close", "volume"]:
        df[col] = df[col].astype(float)
    df["day"] = pd.to_datetime(df["day"])
    df.set_index("day", inplace=True)
    df.index.name = "date"
    if end_date and freq in ("240m", "1200m", "7200m"):
        return df[df.index <= end_date][-mcount:]
    return df


def get_price(code: str, end_date: str = "", count: int = 10, frequency: str = "1d") -> pd.DataFrame:
    xcode = _normalize_code(code)
    if frequency in ("1d", "1w", "1M"):
        try:
            return _get_price_sina(xcode, end_date=end_date, count=count, frequency=frequency)
        except Exception:
            return _get_price_day_tx(xcode, end_date=end_date, count=count, frequency=frequency)
    if frequency in ("1m", "5m", "15m", "30m", "60m"):
        if frequency == "1m":
            return _get_price_min_tx(xcode, end_date=end_date, count=count, frequency=frequency)
        try:
            return _get_price_sina(xcode, end_date=end_date, count=count, frequency=frequency)
        except Exception:
            return _get_price_min_tx(xcode, end_date=end_date, count=count, frequency=frequency)
    raise ValueError(f"不支持的频率: {frequency}")


def _get_realtime_sina(code: str) -> dict[str, object]:
    xcode = _normalize_code(code)
    url = f"http://hq.sinajs.cn/list={xcode}"
    headers = {"Referer": "https://finance.sina.com.cn"}
    resp = requests.get(url, timeout=10, headers=headers)
    content = resp.content.decode("gbk")
    parts = content.split('"')
    if len(parts) < 2 or not parts[1].strip():
        raise ValueError(f"新浪接口返回为空（可能被限流）")
    items = parts[1].split(",")
    if len(items) < 32:
        raise ValueError(f"新浪接口数据不完整（仅 {len(items)} 个字段）")
    return {
        "name": items[0],
        "open": float(items[1]),
        "pre_close": float(items[2]),
        "price": float(items[3]),
        "high": float(items[4]),
        "low": float(items[5]),
        "volume": float(items[8]),
        "amount": float(items[9]),
        "date": items[30],
        "time": items[31],
    }


def _get_realtime_tx(code: str) -> dict[str, object]:
    xcode = _normalize_code(code)
    url = f"http://qt.gtimg.cn/q={xcode}"
    resp = requests.get(url, timeout=10)
    content = resp.content.decode("gbk")
    parts = content.split("~")
    if len(parts) < 45:
        raise ValueError(f"腾讯接口数据不完整")
    return {
        "name": parts[1],
        "open": float(parts[5]),
        "pre_close": float(parts[4]),
        "price": float(parts[3]),
        "high": float(parts[33]),
        "low": float(parts[34]),
        "volume": float(parts[6]),
        "amount": float(parts[37]),
        "date": parts[30][:8],
        "time": parts[30][8:],
    }


def get_realtime(code: str) -> dict[str, object]:
    try:
        return _get_realtime_sina(code)
    except Exception:
        return _get_realtime_tx(code)



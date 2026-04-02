"""
技术指标分析 - CLI 工具
基于行情数据计算 MA、MACD、RSI、KDJ、BOLL、成交量等技术指标。
内置行情获取，无需额外数据源。
"""

import argparse
import json
import sys
import os

import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../ashare-price-data/scripts"))
from ashare import get_price


def calc_ma(df: pd.DataFrame) -> dict:
    close = df["close"]
    ma5 = close.rolling(5).mean()
    ma10 = close.rolling(10).mean()
    ma20 = close.rolling(20).mean()
    ma60 = close.rolling(60).mean() if len(close) >= 60 else pd.Series(dtype=float)

    latest = close.iloc[-1]
    result = {
        "name": "移动平均线 (MA)",
        "values": {
            "MA5": round(ma5.iloc[-1], 2) if not ma5.empty and pd.notna(ma5.iloc[-1]) else None,
            "MA10": round(ma10.iloc[-1], 2) if not ma10.empty and pd.notna(ma10.iloc[-1]) else None,
            "MA20": round(ma20.iloc[-1], 2) if not ma20.empty and pd.notna(ma20.iloc[-1]) else None,
            "MA60": round(ma60.iloc[-1], 2) if not ma60.empty and pd.notna(ma60.iloc[-1]) else None,
            "当前价": round(latest, 2),
        },
        "signals": [],
    }

    vals = [v for v in [ma5.iloc[-1] if pd.notna(ma5.iloc[-1]) else None,
                        ma10.iloc[-1] if pd.notna(ma10.iloc[-1]) else None,
                        ma20.iloc[-1] if pd.notna(ma20.iloc[-1]) else None] if v is not None]
    if vals and all(vals[i] >= vals[i + 1] for i in range(len(vals) - 1)):
        result["signals"].append("均线多头排列，短期趋势向上")
    elif vals and all(vals[i] <= vals[i + 1] for i in range(len(vals) - 1)):
        result["signals"].append("均线空头排列，短期趋势向下")

    if pd.notna(ma5.iloc[-1]) and pd.notna(ma10.iloc[-1]):
        if ma5.iloc[-1] > ma10.iloc[-1] and ma5.iloc[-2] <= ma10.iloc[-2]:
            result["signals"].append("MA5 上穿 MA10（短期金叉）")
        elif ma5.iloc[-1] < ma10.iloc[-1] and ma5.iloc[-2] >= ma10.iloc[-2]:
            result["signals"].append("MA5 下穿 MA10（短期死叉）")

    if not result["signals"]:
        result["signals"].append("均线交织，方向不明确")

    return result


def calc_macd(df: pd.DataFrame, short=12, long=26, signal=9) -> dict:
    close = df["close"]
    ema_short = close.ewm(span=short, adjust=False).mean()
    ema_long = close.ewm(span=long, adjust=False).mean()
    dif = ema_short - ema_long
    dea = dif.ewm(span=signal, adjust=False).mean()
    macd_hist = (dif - dea) * 2

    result = {
        "name": "MACD",
        "values": {
            "DIF": round(dif.iloc[-1], 4),
            "DEA": round(dea.iloc[-1], 4),
            "MACD柱": round(macd_hist.iloc[-1], 4),
        },
        "signals": [],
    }

    if dif.iloc[-1] > dea.iloc[-1] and dif.iloc[-2] <= dea.iloc[-2]:
        result["signals"].append("MACD 金叉（DIF 上穿 DEA），看多信号")
    elif dif.iloc[-1] < dea.iloc[-1] and dif.iloc[-2] >= dea.iloc[-2]:
        result["signals"].append("MACD 死叉（DIF 下穿 DEA），看空信号")
    elif dif.iloc[-1] > dea.iloc[-1]:
        result["signals"].append("MACD 多头运行中")
    else:
        result["signals"].append("MACD 空头运行中")

    if macd_hist.iloc[-1] > 0 and macd_hist.iloc[-1] > macd_hist.iloc[-2]:
        result["signals"].append("红柱放大，多头动能增强")
    elif macd_hist.iloc[-1] < 0 and macd_hist.iloc[-1] < macd_hist.iloc[-2]:
        result["signals"].append("绿柱放大，空头动能增强")

    return result


def calc_rsi(df: pd.DataFrame) -> dict:
    close = df["close"]
    result = {"name": "RSI", "values": {}, "signals": []}

    for period in [6, 12, 24]:
        delta = close.diff()
        gain = delta.where(delta > 0, 0).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        val = rsi.iloc[-1]
        if pd.notna(val):
            result["values"][f"RSI{period}"] = round(val, 2)

    rsi6 = result["values"].get("RSI6")
    if rsi6 is not None:
        if rsi6 > 80:
            result["signals"].append(f"RSI6={rsi6}，严重超买区，注意回调风险")
        elif rsi6 > 70:
            result["signals"].append(f"RSI6={rsi6}，进入超买区")
        elif rsi6 < 20:
            result["signals"].append(f"RSI6={rsi6}，严重超卖区，可能存在反弹机会")
        elif rsi6 < 30:
            result["signals"].append(f"RSI6={rsi6}，进入超卖区")
        else:
            result["signals"].append(f"RSI6={rsi6}，处于中性区间")

    return result


def calc_kdj(df: pd.DataFrame, n=9) -> dict:
    low_n = df["low"].rolling(window=n).min()
    high_n = df["high"].rolling(window=n).max()
    rsv = (df["close"] - low_n) / (high_n - low_n) * 100

    k = rsv.ewm(com=2, adjust=False).mean()
    d = k.ewm(com=2, adjust=False).mean()
    j = 3 * k - 2 * d

    result = {
        "name": "KDJ",
        "values": {
            "K": round(k.iloc[-1], 2) if pd.notna(k.iloc[-1]) else None,
            "D": round(d.iloc[-1], 2) if pd.notna(d.iloc[-1]) else None,
            "J": round(j.iloc[-1], 2) if pd.notna(j.iloc[-1]) else None,
        },
        "signals": [],
    }

    if pd.notna(k.iloc[-1]) and pd.notna(d.iloc[-1]):
        if k.iloc[-1] > d.iloc[-1] and k.iloc[-2] <= d.iloc[-2]:
            result["signals"].append("KDJ 金叉")
        elif k.iloc[-1] < d.iloc[-1] and k.iloc[-2] >= d.iloc[-2]:
            result["signals"].append("KDJ 死叉")

        j_val = j.iloc[-1]
        if j_val > 100:
            result["signals"].append(f"J={j_val:.1f}，超买区")
        elif j_val < 0:
            result["signals"].append(f"J={j_val:.1f}，超卖区")

    if not result["signals"]:
        result["signals"].append("KDJ 无明显信号")

    return result


def calc_boll(df: pd.DataFrame, n=20) -> dict:
    close = df["close"]
    mid = close.rolling(n).mean()
    std = close.rolling(n).std()
    upper = mid + 2 * std
    lower = mid - 2 * std

    latest = close.iloc[-1]
    result = {
        "name": "布林带 (BOLL)",
        "values": {
            "上轨": round(upper.iloc[-1], 2) if pd.notna(upper.iloc[-1]) else None,
            "中轨": round(mid.iloc[-1], 2) if pd.notna(mid.iloc[-1]) else None,
            "下轨": round(lower.iloc[-1], 2) if pd.notna(lower.iloc[-1]) else None,
            "当前价": round(latest, 2),
        },
        "signals": [],
    }

    if pd.notna(upper.iloc[-1]):
        if latest >= upper.iloc[-1]:
            result["signals"].append("价格触及或突破上轨，注意超买风险")
        elif latest <= lower.iloc[-1]:
            result["signals"].append("价格触及或突破下轨，可能存在支撑")
        elif latest > mid.iloc[-1]:
            result["signals"].append("价格在中轨上方运行，偏强")
        else:
            result["signals"].append("价格在中轨下方运行，偏弱")

        width = (upper.iloc[-1] - lower.iloc[-1]) / mid.iloc[-1] * 100
        result["values"]["带宽(%)"] = round(width, 2)
        if width < 5:
            result["signals"].append(f"布林带收窄（带宽{width:.1f}%），可能即将变盘")

    return result


def calc_volume(df: pd.DataFrame) -> dict:
    vol = df["volume"]
    ma5_vol = vol.rolling(5).mean()
    ma20_vol = vol.rolling(20).mean()
    latest_vol = vol.iloc[-1]

    result = {
        "name": "成交量分析",
        "values": {
            "最新成交量": int(latest_vol),
            "5日均量": int(ma5_vol.iloc[-1]) if pd.notna(ma5_vol.iloc[-1]) else None,
            "20日均量": int(ma20_vol.iloc[-1]) if pd.notna(ma20_vol.iloc[-1]) else None,
        },
        "signals": [],
    }

    if pd.notna(ma20_vol.iloc[-1]) and ma20_vol.iloc[-1] > 0:
        ratio = latest_vol / ma20_vol.iloc[-1]
        result["values"]["量比(vs20日)"] = round(ratio, 2)
        if ratio > 2:
            result["signals"].append(f"量比 {ratio:.1f}，显著放量")
        elif ratio > 1.5:
            result["signals"].append(f"量比 {ratio:.1f}，温和放量")
        elif ratio < 0.5:
            result["signals"].append(f"量比 {ratio:.1f}，明显缩量")
        else:
            result["signals"].append(f"量比 {ratio:.1f}，成交量正常")

    return result


CALC_MAP = {
    "ma": calc_ma,
    "macd": calc_macd,
    "rsi": calc_rsi,
    "kdj": calc_kdj,
    "boll": calc_boll,
    "vol": calc_volume,
}


def format_report(code: str, results: list[dict]) -> str:
    lines = [f"# {code} 技术指标分析\n"]
    for r in results:
        lines.append(f"## {r['name']}\n")
        lines.append("**数值：**\n")
        for k, v in r["values"].items():
            lines.append(f"- {k}: {v}")
        lines.append("\n**信号：**\n")
        for s in r["signals"]:
            lines.append(f"- {s}")
        lines.append("")
    lines.append("---")
    lines.append("*技术指标仅供参考，不构成投资建议。*")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="技术指标分析")
    parser.add_argument("code", help="证券代码，如 sh600519、sz000001")
    parser.add_argument("--frequency", "-f", default="1d", help="K线周期 (默认 1d)")
    parser.add_argument("--count", "-c", type=int, default=120, help="数据条数 (默认 120)")
    parser.add_argument("--indicators", "-i", default="ma,macd,rsi,kdj,boll,vol",
                        help="指标列表，逗号分隔 (默认全部)")
    args = parser.parse_args()

    try:
        df = get_price(args.code, count=args.count, frequency=args.frequency)
    except Exception as e:
        print(f"获取行情数据失败: {e}", file=sys.stderr)
        sys.exit(1)

    indicators = [i.strip() for i in args.indicators.split(",")]
    results = []
    for ind in indicators:
        if ind in CALC_MAP:
            try:
                results.append(CALC_MAP[ind](df))
            except Exception as e:
                results.append({"name": ind, "values": {}, "signals": [f"计算失败: {e}"]})

    print(format_report(args.code, results))


if __name__ == "__main__":
    main()

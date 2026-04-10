"""
批量获取多只股票实时行情 + 基础技术指标快照。
用于持仓分析时一次性获取所有持仓的最新数据。
"""

import argparse
import json
import sys
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ashare import get_price, get_realtime

import pandas as pd


def calc_basic_indicators(code: str) -> dict[str, object]:
    """获取单只股票的实时行情 + 基础技术指标"""
    result: dict[str, object] = {"code": code}

    try:
        rt = get_realtime(code)
        result["name"] = str(rt["name"])
        price = float(str(rt["price"]))
        pre_close = float(str(rt["pre_close"]))
        result["price"] = price
        result["open"] = float(str(rt["open"]))
        result["pre_close"] = pre_close
        result["high"] = float(str(rt["high"]))
        result["low"] = float(str(rt["low"]))
        if price and pre_close:
            result["change_pct"] = round((price - pre_close) / pre_close * 100, 2)
        else:
            result["change_pct"] = 0
    except Exception as e:
        result["error_realtime"] = str(e)

    if not result.get("price"):
        try:
            df_fallback = get_price(code, count=2, frequency="1d")
            if not df_fallback.empty:
                result["price"] = round(df_fallback["close"].iloc[-1], 2)
                result.setdefault("name", code)
                if len(df_fallback) >= 2:
                    prev = df_fallback["close"].iloc[-2]
                    result["change_pct"] = round((result["price"] - prev) / prev * 100, 2)
        except Exception:
            pass

    if not result.get("price"):
        result["error_realtime"] = result.get("error_realtime", "无法获取价格")
        return result

    try:
        df = get_price(code, count=60, frequency="1d")
        if not df.empty and len(df) >= 20:
            closes = df["close"]
            result["ma5"] = round(closes.iloc[-5:].mean(), 2)
            result["ma10"] = round(closes.iloc[-10:].mean(), 2)
            result["ma20"] = round(closes.iloc[-20:].mean(), 2)
            if len(df) >= 60:
                result["ma60"] = round(closes.iloc[-60:].mean(), 2)

            current = closes.iloc[-1]
            result["vs_ma5"] = "above" if current > result["ma5"] else "below"
            result["vs_ma20"] = "above" if current > result["ma20"] else "below"

            high_60d = df["high"].max()
            low_60d = df["low"].min()
            result["high_60d"] = round(high_60d, 2)
            result["low_60d"] = round(low_60d, 2)
            result["position_60d"] = round((current - low_60d) / (high_60d - low_60d) * 100, 1) if high_60d != low_60d else 50

            pct_changes = closes.pct_change().dropna()
            result["volatility_60d"] = round(pct_changes.std() * (252 ** 0.5) * 100, 1)

            change_20d = (closes.iloc[-1] - closes.iloc[-20]) / closes.iloc[-20] * 100
            result["change_20d"] = round(change_20d, 2)

            ema12 = closes.ewm(span=12, adjust=False).mean()
            ema26 = closes.ewm(span=26, adjust=False).mean()
            dif = ema12 - ema26
            dea = dif.ewm(span=9, adjust=False).mean()
            result["macd_dif"] = round(dif.iloc[-1], 3)
            result["macd_dea"] = round(dea.iloc[-1], 3)
            result["macd_signal"] = "golden_cross" if dif.iloc[-1] > dea.iloc[-1] and dif.iloc[-2] <= dea.iloc[-2] else \
                                    "death_cross" if dif.iloc[-1] < dea.iloc[-1] and dif.iloc[-2] >= dea.iloc[-2] else \
                                    "bullish" if dif.iloc[-1] > dea.iloc[-1] else "bearish"

            n = 14
            delta = closes.diff()
            gain = delta.where(delta > 0, 0).rolling(window=n).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=n).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            result["rsi_14"] = round(rsi.iloc[-1], 1)
            result["rsi_signal"] = "overbought" if rsi.iloc[-1] > 70 else "oversold" if rsi.iloc[-1] < 30 else "neutral"

    except Exception as e:
        result["error_indicator"] = str(e)

    return result


def main():
    parser = argparse.ArgumentParser(description="批量获取股票行情和基础指标")
    parser.add_argument("codes", nargs="+", help="股票代码列表，如 sh600519 sz000001")
    parser.add_argument("--format", choices=["json", "table"], default="table", help="输出格式")
    args = parser.parse_args()

    results = []
    with ThreadPoolExecutor(max_workers=6) as executor:
        futures = {executor.submit(calc_basic_indicators, code): code for code in args.codes}
        for future in as_completed(futures):
            try:
                results.append(future.result())
            except Exception as e:
                results.append({"code": futures[future], "error": str(e)})

    code_order = {code: i for i, code in enumerate(args.codes)}
    results.sort(key=lambda x: code_order.get(x["code"], 999))

    if args.format == "json":
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        print("# 批量行情快照\n")
        print("| 代码 | 名称 | 现价 | 涨跌% | 60日位置 | MA趋势 | MACD | RSI | 信号 |")
        print("|------|------|------|-------|---------|--------|------|-----|------|")
        for r in results:
            if "error_realtime" in r:
                print(f"| {r['code']} | - | 获取失败 | - | - | - | - | - | {r['error_realtime'][:30]} |")
                continue

            ma_trend = ""
            if "vs_ma5" in r and "vs_ma20" in r:
                if r["vs_ma5"] == "above" and r["vs_ma20"] == "above":
                    ma_trend = "多头"
                elif r["vs_ma5"] == "below" and r["vs_ma20"] == "below":
                    ma_trend = "空头"
                else:
                    ma_trend = "震荡"

            macd_label = {"golden_cross": "金叉", "death_cross": "死叉", "bullish": "多", "bearish": "空"}.get(r.get("macd_signal", ""), "-")
            rsi_label = {"overbought": "超买", "oversold": "超卖", "neutral": "中性"}.get(r.get("rsi_signal", ""), "-")

            pos = r.get("position_60d", "-")
            pos_str = f"{pos}%" if isinstance(pos, (int, float)) else pos

            rsi_val = r.get("rsi_14", "-")
            chg = r.get("change_pct", 0)
            chg_str = f"{chg:+.2f}%" if isinstance(chg, (int, float)) else "-"

            signals = []
            if r.get("rsi_signal") == "overbought":
                signals.append("RSI超买")
            if r.get("rsi_signal") == "oversold":
                signals.append("RSI超卖")
            if r.get("macd_signal") == "golden_cross":
                signals.append("MACD金叉")
            if r.get("macd_signal") == "death_cross":
                signals.append("MACD死叉")

            print(f"| {r['code']} | {r.get('name', '-')} | {r.get('price', '-')} | {chg_str} | {pos_str} | {ma_trend} | {macd_label} | {rsi_val} | {'、'.join(signals) if signals else '-'} |")

        print()
        for r in results:
            if "error_realtime" in r:
                continue
            print(f"### {r.get('name', r['code'])} ({r['code']})")
            print(f"- 现价 {r.get('price', '-')}，今日 {r.get('change_pct', 0):+.2f}%")
            if "ma5" in r:
                print(f"- 均线：MA5={r['ma5']} MA10={r['ma10']} MA20={r['ma20']}" + (f" MA60={r['ma60']}" if "ma60" in r else ""))
            if "position_60d" in r:
                print(f"- 60日区间 [{r.get('low_60d', '-')}, {r.get('high_60d', '-')}]，当前位于 {r['position_60d']}% 位置")
            if "change_20d" in r:
                print(f"- 近20日涨跌：{r['change_20d']:+.2f}%，年化波动率：{r.get('volatility_60d', '-')}%")
            if "rsi_14" in r:
                print(f"- RSI(14)={r['rsi_14']}，MACD {'多头' if r.get('macd_signal') in ('bullish', 'golden_cross') else '空头'}")
            print()


if __name__ == "__main__":
    main()

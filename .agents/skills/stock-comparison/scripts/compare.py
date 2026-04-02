"""
股票对比分析 - CLI 工具
对比多只股票的行情走势和财务指标。
"""

import argparse
import sys
import os

import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../ashare-price-data/scripts"))
from ashare import get_price


def compare_price(codes: list[str], days: int = 60) -> str:
    """对比多只股票行情走势"""
    lines = ["## 行情走势对比\n"]
    data = {}
    for code in codes:
        try:
            df = get_price(code, count=days, frequency="1d")
            if df.empty:
                continue
            first_close = df["close"].iloc[0]
            last_close = df["close"].iloc[-1]
            high = df["high"].max()
            low = df["low"].min()
            vol_avg = df["volume"].mean()
            change_pct = (last_close - first_close) / first_close * 100
            volatility = df["close"].pct_change().std() * (252 ** 0.5) * 100
            data[code] = {
                "最新价": round(last_close, 2),
                "区间涨跌幅": f"{change_pct:+.2f}%",
                "最高价": round(high, 2),
                "最低价": round(low, 2),
                "年化波动率": f"{volatility:.1f}%",
                "日均成交量": f"{vol_avg/10000:.0f}万",
            }
        except Exception as e:
            data[code] = {"错误": str(e)}

    if not data:
        return "未能获取任何股票数据"

    header = "| 指标 | " + " | ".join(data.keys()) + " |"
    sep = "|------" + "|------" * len(data) + "|"
    lines.extend([header, sep])

    all_keys = list(next(iter(data.values())).keys())
    for key in all_keys:
        row = f"| {key} |"
        for code in data:
            row += f" {data[code].get(key, 'N/A')} |"
        lines.append(row)

    return "\n".join(lines)


def compare_financial(codes: list[str]) -> str:
    """对比多只股票财务指标"""
    lines = ["## 财务指标对比\n"]

    try:
        import akshare as ak
    except ImportError:
        return "需要安装 akshare: pip install akshare"

    data = {}
    for code in codes:
        pure_code = code.replace("sh", "").replace("sz", "")
        try:
            indicator = ak.stock_financial_analysis_indicator(symbol=pure_code)
            if indicator.empty:
                continue
            latest = indicator.iloc[0]
            data[code] = {
                "报告期": str(latest.get("日期", "N/A")),
                "ROE(%)": latest.get("摊薄净资产收益率(%)", "N/A"),
                "毛利率(%)": latest.get("销售毛利率(%)", "N/A"),
                "净利率(%)": latest.get("销售净利率(%)", "N/A"),
                "负债率(%)": latest.get("资产负债率(%)", "N/A"),
                "每股收益": latest.get("摊薄每股收益(元)", "N/A"),
                "每股净资产": latest.get("每股净资产_调整后(元)", "N/A"),
            }
        except Exception as e:
            data[code] = {"错误": str(e)}

    if not data:
        return "未能获取任何财务数据"

    header = "| 指标 | " + " | ".join(data.keys()) + " |"
    sep = "|------" + "|------" * len(data) + "|"
    lines.extend([header, sep])

    all_keys = list(next(iter(data.values())).keys())
    for key in all_keys:
        row = f"| {key} |"
        for code in data:
            val = data[code].get(key, "N/A")
            if val is not None:
                try:
                    val = f"{float(val):.2f}"
                except (ValueError, TypeError):
                    pass
            row += f" {val} |"
        lines.append(row)

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="股票对比分析")
    parser.add_argument("codes", nargs="+", help="股票代码列表（2-10个）")
    parser.add_argument("--mode", "-m", default="all", choices=["price", "financial", "all"],
                        help="对比模式 (默认 all)")
    parser.add_argument("--days", "-d", type=int, default=60, help="行情对比天数 (默认 60)")
    args = parser.parse_args()

    if len(args.codes) < 2:
        print("至少需要 2 只股票进行对比", file=sys.stderr)
        sys.exit(1)
    if len(args.codes) > 10:
        print("最多支持 10 只股票对比", file=sys.stderr)
        sys.exit(1)

    title = "# 股票对比分析: " + " vs ".join(args.codes) + "\n"
    print(title)

    if args.mode in ("price", "all"):
        print(compare_price(args.codes, args.days))
        print()

    if args.mode in ("financial", "all"):
        print(compare_financial(args.codes))


if __name__ == "__main__":
    main()

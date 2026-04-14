"""
A 股行情数据获取 - CLI 入口
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir, os.pardir, os.pardir, "shared"))
from ashare import get_price, get_realtime


def main():
    parser = argparse.ArgumentParser(description="A 股行情数据获取")
    parser.add_argument("code", help="证券代码，如 sh600519、sz000001、000001.XSHG")
    parser.add_argument("--frequency", "-f", default="1d",
                        help="数据频率: 1d/1w/1M/1m/5m/15m/30m/60m (默认 1d)")
    parser.add_argument("--count", "-c", type=int, default=30, help="数据条数 (默认 30)")
    parser.add_argument("--end-date", "-e", default="", help="截止日期 YYYY-MM-DD")
    parser.add_argument("--realtime", "-r", action="store_true", help="获取实时行情")
    args = parser.parse_args()

    try:
        if args.realtime:
            data = get_realtime(args.code)
            print(json.dumps(data, ensure_ascii=False, indent=2))
        else:
            df = get_price(args.code, end_date=args.end_date, count=args.count, frequency=args.frequency)
            print(df.to_csv())
    except Exception as e:
        print(f"错误: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

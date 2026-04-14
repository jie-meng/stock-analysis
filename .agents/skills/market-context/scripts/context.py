"""
市场环境上下文 - CLI 工具
获取行业板块走势/资金流、大宗商品价格、个股新闻、宏观经济指标。
"""

import argparse
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta

os.environ["TQDM_DISABLE"] = "1"

try:
    import akshare as ak
    import pandas as pd
except ImportError:
    print("需要安装依赖: pip install akshare pandas", file=sys.stderr)
    sys.exit(1)

COMMODITY_MAP = {
    "AL0": "沪铝",
    "CU0": "沪铜",
    "SC0": "原油",
    "AU0": "沪金",
    "I0": "铁矿石",
    "RB0": "螺纹钢",
    "AG0": "沪银",
    "C0": "玉米",
    "P0": "棕榈油",
    "CF0": "棉花",
}

DEFAULT_COMMODITIES = ["AL0", "CU0", "SC0", "AU0", "I0"]


# ── sector: 板块排名 + 资金流 ───────────────────────────────────

def cmd_sector(args):
    keyword = args.keyword
    top = args.top
    sector_type = args.type

    sections = []

    if sector_type in ("industry", "both"):
        sections.append(_sector_with_fund_flow(
            "行业", keyword, top,
            ak.stock_board_industry_name_em,
            "行业资金流",
        ))

    if sector_type in ("concept", "both"):
        sections.append(_sector_with_fund_flow(
            "概念", keyword, top,
            ak.stock_board_concept_name_em,
            "概念资金流",
        ))

    print("\n".join(sections))


def _sector_with_fund_flow(label, keyword, top, name_func, flow_type):
    lines = []

    with ThreadPoolExecutor(max_workers=2) as pool:
        f_names = pool.submit(_fetch_sector_names, label, name_func)
        f_flow = pool.submit(_fetch_fund_flow, flow_type)
        names_df = f_names.result()
        flow_df = f_flow.result()

    if names_df is None:
        return f"## {label}板块排名\n\n获取{label}板块数据失败\n"

    if keyword:
        names_df = names_df[names_df["板块名称"].str.contains(keyword, na=False)]
        if names_df.empty:
            return f"## {label}板块（关键词：{keyword}）\n\n未找到包含「{keyword}」的{label}板块\n"
        lines.append(f"## {label}板块（关键词：{keyword}）\n")
    else:
        names_df = names_df.head(top)
        lines.append(f"## {label}板块 Top {top} 涨幅排名\n")

    header = "| 排名 | 板块名称 | 涨跌幅 | 换手率 | 上涨/下跌 | 领涨股 |"
    sep = "|------|---------|--------|--------|----------|--------|"
    lines.extend([header, sep])

    for _, row in names_df.iterrows():
        rise = row.get("上涨家数", "-")
        fall = row.get("下跌家数", "-")
        lines.append(
            f"| {row.get('排名', '-')} "
            f"| {row['板块名称']} "
            f"| {row.get('涨跌幅', 'N/A')}% "
            f"| {row.get('换手率', 'N/A')}% "
            f"| {rise}/{fall} "
            f"| {row.get('领涨股票', '-')} |"
        )

    if flow_df is not None:
        lines.append("")
        if keyword:
            flow_df = flow_df[flow_df["名称"].str.contains(keyword, na=False)]

        flow_subset = flow_df.head(top) if not keyword else flow_df
        if not flow_subset.empty:
            lines.append(f"### {label}板块资金流向\n")
            fh = "| 板块 | 涨跌幅 | 主力净流入 | 主力净占比 | 超大单净流入 | 主力最大股 |"
            fs = "|------|--------|----------|----------|------------|----------|"
            lines.extend([fh, fs])
            for _, row in flow_subset.iterrows():
                net_in = row.get("今日主力净流入-净额", 0)
                net_in_str = _format_amount(net_in)
                big_in = row.get("今日超大单净流入-净额", 0)
                big_in_str = _format_amount(big_in)
                lines.append(
                    f"| {row['名称']} "
                    f"| {row.get('今日涨跌幅', 'N/A')}% "
                    f"| {net_in_str} "
                    f"| {row.get('今日主力净流入-净占比', 'N/A')}% "
                    f"| {big_in_str} "
                    f"| {row.get('今日主力净流入最大股', '-')} |"
                )

    lines.append("")
    return "\n".join(lines)


def _fetch_sector_names(label, func):
    try:
        return func()
    except Exception as e:
        print(f"获取{label}板块列表失败: {e}", file=sys.stderr)
        return None


def _fetch_fund_flow(flow_type):
    try:
        return ak.stock_sector_fund_flow_rank(
            indicator="今日", sector_type=flow_type
        )
    except Exception as e:
        print(f"获取资金流向失败: {e}", file=sys.stderr)
        return None


def _format_amount(val):
    try:
        v = float(val)
        if abs(v) >= 1e8:
            return f"{v / 1e8:.2f}亿"
        elif abs(v) >= 1e4:
            return f"{v / 1e4:.0f}万"
        return f"{v:.0f}"
    except (ValueError, TypeError):
        return str(val)


# ── commodity: 大宗商品价格 ──────────────────────────────────────

def cmd_commodity(args):
    symbols = args.symbols.split(",")
    days = args.days

    lines = ["# 大宗商品价格走势\n"]

    results = {}
    with ThreadPoolExecutor(max_workers=5) as pool:
        futures = {
            pool.submit(_fetch_commodity, sym.strip(), days): sym.strip()
            for sym in symbols
        }
        for future in as_completed(futures):
            sym = futures[future]
            results[sym] = future.result()

    for sym in symbols:
        sym = sym.strip()
        name = COMMODITY_MAP.get(sym, sym)
        data = results.get(sym)

        if data is None:
            lines.append(f"## {name}（{sym}）\n\n获取数据失败\n")
            continue

        df = data
        latest = df.iloc[-1]
        first = df.iloc[0]

        latest_price = float(latest["收盘价"])
        first_price = float(first["收盘价"])
        change_pct = (latest_price - first_price) / first_price * 100
        high = float(df["最高价"].max())
        low = float(df["最低价"].min())

        direction = "↑" if change_pct > 0 else "↓" if change_pct < 0 else "→"

        lines.append(f"## {name}（{sym}）\n")
        lines.append(f"- **最新价**: {latest_price:.1f}（{latest['日期']}）")
        lines.append(f"- **{len(df)}日涨跌**: {direction} {change_pct:+.2f}%")
        lines.append(f"- **区间最高**: {high:.1f}")
        lines.append(f"- **区间最低**: {low:.1f}")
        lines.append(f"- **波动幅度**: {(high - low) / low * 100:.2f}%")
        lines.append("")

        lines.append("近期走势：")
        lines.append("| 日期 | 收盘价 | 涨跌 |")
        lines.append("|------|--------|------|")
        show_rows = df.tail(min(10, len(df)))
        prev_close = None
        for _, row in show_rows.iterrows():
            close = float(row["收盘价"])
            if prev_close is not None:
                chg = (close - prev_close) / prev_close * 100
                chg_str = f"{chg:+.2f}%"
            else:
                chg_str = "-"
            lines.append(f"| {row['日期']} | {close:.1f} | {chg_str} |")
            prev_close = close
        lines.append("")

    print("\n".join(lines))


def _fetch_commodity(symbol, days):
    try:
        df = ak.futures_main_sina(symbol=symbol)
        if df is None or df.empty:
            return None
        return df.tail(days)
    except Exception as e:
        print(f"获取期货 {symbol} 失败: {e}", file=sys.stderr)
        return None


# ── news: 个股新闻 ──────────────────────────────────────────────

def cmd_news(args):
    code = args.code.zfill(6)
    count = args.count

    lines = [f"# {code} 最新新闻\n"]

    try:
        df = ak.stock_news_em(symbol=code)
        if df is None or df.empty:
            lines.append("未获取到相关新闻")
            print("\n".join(lines))
            return

        df = df.head(count)
        for i, (_, row) in enumerate(df.iterrows(), 1):
            title = row.get("新闻标题", "无标题")
            pub_time = row.get("发布时间", "未知时间")
            source = row.get("文章来源", "未知来源")
            content = row.get("新闻内容", "")

            if len(content) > 200:
                content = content[:200] + "..."

            lines.append(f"### {i}. {title}")
            lines.append(f"**{pub_time}** | {source}\n")
            if content:
                lines.append(f"> {content}\n")

    except Exception as e:
        lines.append(f"获取新闻失败: {e}")

    print("\n".join(lines))


# ── macro: 宏观经济指标 ──────────────────────────────────────────

def cmd_macro(args):
    lines = ["# 宏观经济指标\n"]

    with ThreadPoolExecutor(max_workers=2) as pool:
        f_pmi = pool.submit(_fetch_pmi)
        f_cpi = pool.submit(_fetch_cpi)
        pmi_text = f_pmi.result()
        cpi_text = f_cpi.result()

    lines.append(pmi_text)
    lines.append(cpi_text)

    print("\n".join(lines))


def _fetch_pmi():
    try:
        df = ak.macro_china_pmi()
        if df is None or df.empty:
            return "## PMI\n\n获取失败\n"

        latest = df.iloc[0]
        lines = ["## PMI（制造业采购经理指数）\n"]
        lines.append(f"- **月份**: {latest.get('月份', 'N/A')}")
        lines.append(f"- **制造业 PMI**: {latest.get('制造业-指数', 'N/A')}")
        lines.append(f"- **非制造业 PMI**: {latest.get('非制造业-指数', 'N/A')}")

        mfg = latest.get("制造业-指数")
        if mfg is not None:
            try:
                v = float(mfg)
                if v > 50:
                    lines.append(f"- **景气判断**: 扩张区间（>{50}）")
                elif v == 50:
                    lines.append("- **景气判断**: 荣枯线")
                else:
                    lines.append(f"- **景气判断**: 收缩区间（<{50}）")
            except (ValueError, TypeError):
                pass

        recent = df.head(6)
        lines.append("\n近期趋势：")
        lines.append("| 月份 | 制造业 | 非制造业 |")
        lines.append("|------|--------|---------|")
        for _, row in recent.iterrows():
            lines.append(
                f"| {row.get('月份', 'N/A')} "
                f"| {row.get('制造业-指数', 'N/A')} "
                f"| {row.get('非制造业-指数', 'N/A')} |"
            )
        lines.append("")
        return "\n".join(lines)
    except Exception as e:
        return f"## PMI\n\n获取失败: {e}\n"


def _fetch_cpi():
    try:
        df = ak.macro_china_cpi_monthly()
        if df is None or df.empty:
            return "## CPI\n\n获取失败\n"

        df = df.dropna(subset=["今值"])
        if df.empty:
            return "## CPI\n\n无有效数据\n"

        latest = df.iloc[-1]
        lines = ["## CPI（消费者价格指数月率）\n"]
        lines.append(f"- **日期**: {latest.get('日期', 'N/A')}")
        lines.append(f"- **今值**: {latest.get('今值', 'N/A')}%")
        lines.append(f"- **前值**: {latest.get('前值', 'N/A')}%")

        recent = df.tail(6)
        lines.append("\n近期趋势：")
        lines.append("| 日期 | CPI 月率 | 前值 |")
        lines.append("|------|---------|------|")
        for _, row in recent.iterrows():
            lines.append(
                f"| {row.get('日期', 'N/A')} "
                f"| {row.get('今值', 'N/A')}% "
                f"| {row.get('前值', 'N/A')}% |"
            )
        lines.append("")
        return "\n".join(lines)
    except Exception as e:
        return f"## CPI\n\n获取失败: {e}\n"


# ── overview: 全景概览 ──────────────────────────────────────────

def cmd_overview(args):
    keyword = args.keyword

    print("# 市场环境全景概览\n")
    print(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
    print("---\n")

    sector_args = argparse.Namespace(
        type="industry", keyword=keyword, top=10 if not keyword else 30
    )
    cmd_sector(sector_args)

    print("\n---\n")

    commodity_args = argparse.Namespace(
        symbols=",".join(DEFAULT_COMMODITIES), days=10
    )
    cmd_commodity(commodity_args)

    print("\n---\n")

    macro_args = argparse.Namespace()
    cmd_macro(macro_args)


# ── CLI 入口 ─────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="市场环境上下文")
    subparsers = parser.add_subparsers(dest="command", help="子命令")

    p_sector = subparsers.add_parser("sector", help="行业/概念板块排名与资金流")
    p_sector.add_argument("--type", default="industry",
                          choices=["industry", "concept", "both"])
    p_sector.add_argument("--keyword", default=None, help="板块名称关键词")
    p_sector.add_argument("--top", type=int, default=15, help="显示前N个")

    p_commodity = subparsers.add_parser("commodity", help="大宗商品期货价格")
    p_commodity.add_argument("--symbols", default=",".join(DEFAULT_COMMODITIES),
                             help="逗号分隔的期货代码")
    p_commodity.add_argument("--days", type=int, default=20, help="历史天数")

    p_news = subparsers.add_parser("news", help="个股新闻")
    p_news.add_argument("--code", required=True, help="6位股票代码")
    p_news.add_argument("--count", type=int, default=5, help="新闻条数")

    p_macro = subparsers.add_parser("macro", help="宏观经济指标")

    p_overview = subparsers.add_parser("overview", help="全景概览")
    p_overview.add_argument("--keyword", default=None, help="聚焦关键词")

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(1)

    commands = {
        "sector": cmd_sector,
        "commodity": cmd_commodity,
        "news": cmd_news,
        "macro": cmd_macro,
        "overview": cmd_overview,
    }
    commands[args.command](args)


if __name__ == "__main__":
    main()

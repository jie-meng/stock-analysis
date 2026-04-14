"""
公司画像 - CLI 工具
获取 A 股上市公司基本信息、主营构成、十大股东、业绩快报/预告。
"""

import argparse
import os
import sys

os.environ["TQDM_DISABLE"] = "1"

try:
    import akshare as ak
    import pandas as pd
except ImportError:
    print("需要安装依赖: pip install akshare pandas", file=sys.stderr)
    sys.exit(1)


def _market_prefix(stock_code: str) -> str:
    c = stock_code.lstrip("0").zfill(6) if len(stock_code) <= 6 else stock_code
    if c.startswith(("6", "9")):
        return f"SH{c}"
    return f"SZ{c}"


def get_company_info(stock_code: str) -> str:
    """通过巨潮接口获取公司基本信息"""
    lines = ["## 公司基本信息\n"]
    try:
        df = ak.stock_profile_cninfo(symbol=stock_code)
        if df is None or df.empty:
            lines.append("未获取到公司基本信息")
            return "\n".join(lines)

        row = df.iloc[0]
        fields = {
            "公司名称": "公司名称",
            "A股简称": "股票简称",
            "A股代码": "股票代码",
            "所属行业": "所属行业",
            "所属市场": "所属市场",
            "成立日期": "成立日期",
            "上市日期": "上市日期",
            "注册资金": "注册资金（万元）",
            "法人代表": "法人代表",
            "官方网站": "官方网站",
            "注册地址": "注册地址",
        }
        for col, label in fields.items():
            val = row.get(col, "N/A")
            if val is not None and str(val) != "None":
                lines.append(f"- **{label}**: {val}")

        main_biz = row.get("主营业务")
        if main_biz and str(main_biz) != "None":
            lines.append(f"\n### 主营业务\n\n{main_biz}")

        intro = row.get("机构简介")
        if intro and str(intro) != "None":
            short = intro[:500] + "..." if len(str(intro)) > 500 else intro
            lines.append(f"\n### 公司简介\n\n{short}")

    except Exception as e:
        lines.append(f"获取公司信息失败: {e}")

    return "\n".join(lines)


def get_revenue_breakdown(stock_code: str) -> str:
    """获取主营构成（按产品 + 按地区）"""
    symbol = _market_prefix(stock_code)
    lines = ["## 主营构成\n"]

    try:
        df = ak.stock_zygc_em(symbol=symbol)
        if df is None or df.empty:
            lines.append("未获取到主营构成数据")
            return "\n".join(lines)

        latest_date = df["报告日期"].max()
        latest = df[df["报告日期"] == latest_date]

        lines.append(f"报告期: {latest_date}\n")

        for classify_type in ["按产品分类", "按行业分类"]:
            subset = latest[latest["分类类型"] == classify_type]
            if subset.empty:
                continue
            lines.append(f"### {classify_type}\n")
            lines.append("| 项目 | 营收（亿元） | 占比 | 毛利率 |")
            lines.append("|------|------------|------|--------|")
            for _, row in subset.iterrows():
                name = row.get("主营构成", "N/A")
                revenue = row.get("主营收入", 0)
                ratio = row.get("收入比例", 0)
                margin = row.get("毛利率", None)
                rev_str = f"{float(revenue) / 1e8:.2f}" if revenue else "N/A"
                ratio_str = f"{float(ratio) * 100:.1f}%" if ratio else "N/A"
                margin_str = f"{float(margin) * 100:.1f}%" if margin and str(margin) != "nan" else "N/A"
                lines.append(f"| {name} | {rev_str} | {ratio_str} | {margin_str} |")
            lines.append("")

        by_region = latest[latest["分类类型"] == "按地区分类"]
        if not by_region.empty:
            lines.append("### 按地区分类\n")
            lines.append("| 地区 | 营收（亿元） | 占比 | 毛利率 |")
            lines.append("|------|------------|------|--------|")
            for _, row in by_region.iterrows():
                name = row.get("主营构成", "N/A")
                revenue = row.get("主营收入", 0)
                ratio = row.get("收入比例", 0)
                margin = row.get("毛利率", None)
                rev_str = f"{float(revenue) / 1e8:.2f}" if revenue else "N/A"
                ratio_str = f"{float(ratio) * 100:.1f}%" if ratio else "N/A"
                margin_str = f"{float(margin) * 100:.1f}%" if margin and str(margin) != "nan" else "N/A"
                lines.append(f"| {name} | {rev_str} | {ratio_str} | {margin_str} |")
            lines.append("")

    except Exception as e:
        lines.append(f"获取主营构成失败: {e}")

    return "\n".join(lines)


def get_top_holders(stock_code: str) -> str:
    """获取十大股东"""
    lines = ["## 十大股东\n"]

    try:
        df = ak.stock_main_stock_holder(stock=stock_code)
        if df is None or df.empty:
            lines.append("未获取到股东信息")
            return "\n".join(lines)

        latest_date = df["截至日期"].max()
        latest = df[df["截至日期"] == latest_date]

        lines.append(f"截至: {latest_date}\n")

        holder_count = latest.iloc[0].get("股东总数", "N/A")
        avg_shares = latest.iloc[0].get("平均持股数", "N/A")
        lines.append(f"- **股东总数**: {holder_count}")
        lines.append(f"- **平均持股数**: {avg_shares}\n")

        lines.append("| 排名 | 股东名称 | 持股比例(%) | 股本性质 |")
        lines.append("|------|---------|-----------|---------|")
        for _, row in latest.iterrows():
            rank = row.get("编号", "")
            name = row.get("股东名称", "N/A")
            ratio = row.get("持股比例", "N/A")
            ratio = "N/A" if ratio is None or str(ratio) == "nan" else ratio
            nature = row.get("股本性质", "N/A")
            lines.append(f"| {rank} | {name} | {ratio} | {nature} |")

    except Exception as e:
        lines.append(f"获取股东信息失败: {e}")

    return "\n".join(lines)


def get_latest_earnings(stock_code: str) -> str:
    """获取最新业绩快报和业绩预告"""
    lines = ["## 最新业绩动态\n"]

    for date_str in ["20251231", "20250930", "20250630", "20250331"]:
        try:
            df = ak.stock_yjkb_em(date=date_str)
            if df is None or df.empty:
                continue
            row = df[df["股票代码"] == stock_code]
            if row.empty:
                continue

            r = row.iloc[0]
            period = date_str[:4] + "-" + date_str[4:6] + "-" + date_str[6:]
            lines.append(f"### 业绩快报（{period}）\n")

            rev = r.get("营业收入-营业收入", 0)
            rev_prev = r.get("营业收入-去年同期", 0)
            rev_growth = r.get("营业收入-同比增长", None)
            profit = r.get("净利润-净利润", 0)
            profit_prev = r.get("净利润-去年同期", 0)
            profit_growth = r.get("净利润-同比增长", None)
            eps = r.get("每股收益", "N/A")
            bps = r.get("每股净资产", "N/A")
            roe = r.get("净资产收益率", "N/A")

            lines.append("| 指标 | 本期 | 去年同期 | 同比增长 |")
            lines.append("|------|------|---------|---------|")
            rev_str = f"{float(rev) / 1e8:.2f}亿" if rev else "N/A"
            rev_prev_str = f"{float(rev_prev) / 1e8:.2f}亿" if rev_prev else "N/A"
            rev_g_str = f"{float(rev_growth):.2f}%" if rev_growth is not None else "N/A"
            lines.append(f"| 营业收入 | {rev_str} | {rev_prev_str} | {rev_g_str} |")

            profit_str = f"{float(profit) / 1e8:.2f}亿" if profit else "N/A"
            profit_prev_str = f"{float(profit_prev) / 1e8:.2f}亿" if profit_prev else "N/A"
            profit_g_str = f"{float(profit_growth):.2f}%" if profit_growth is not None else "N/A"
            lines.append(f"| 净利润 | {profit_str} | {profit_prev_str} | {profit_g_str} |")

            lines.append(f"\n- **每股收益**: {eps} 元")
            lines.append(f"- **每股净资产**: {bps} 元")
            lines.append(f"- **净资产收益率**: {roe}%")
            lines.append(f"- **公告日期**: {r.get('公告日期', 'N/A')}")
            break
        except Exception:
            continue

    if len(lines) == 1:
        lines.append("暂无业绩快报数据")

    lines.append("")

    for date_str in ["20260331", "20251231", "20250930", "20250630"]:
        try:
            df = ak.stock_yjyg_em(date=date_str)
            if df is None or df.empty:
                continue
            row = df[df["股票代码"] == stock_code]
            if row.empty:
                continue

            r = row.iloc[0]
            period = date_str[:4] + "-" + date_str[4:6] + "-" + date_str[6:]
            lines.append(f"### 业绩预告（{period}）\n")
            lines.append(f"- **预告类型**: {r.get('预告类型', 'N/A')}")
            lines.append(f"- **预测指标**: {r.get('预测指标', 'N/A')}")
            lines.append(f"- **预测数值**: {r.get('预测数值', 'N/A')}")
            lines.append(f"- **业绩变动幅度**: {r.get('业绩变动幅度', 'N/A')}")
            lines.append(f"- **上年同期值**: {r.get('上年同期值', 'N/A')}")

            reason = r.get("业绩变动原因", "")
            if reason and str(reason) != "nan":
                lines.append(f"- **变动原因**: {reason}")
            break
        except Exception:
            continue

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="A 股公司画像")
    parser.add_argument("code", help="股票代码（6位数字），如 688267")
    parser.add_argument("--module", "-m", default="all",
                        choices=["info", "revenue", "holders", "earnings", "all"],
                        help="查询模块 (默认 all)")
    args = parser.parse_args()

    code = args.code.lstrip("0") if len(args.code) > 6 else args.code
    code = code.zfill(6)

    print(f"# {code} 公司画像\n")

    modules = {
        "info": get_company_info,
        "revenue": get_revenue_breakdown,
        "holders": get_top_holders,
        "earnings": get_latest_earnings,
    }

    if args.module == "all":
        for name, func in modules.items():
            print(func(code))
            print("\n---\n")
    else:
        print(modules[args.module](code))


if __name__ == "__main__":
    main()

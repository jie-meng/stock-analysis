"""
财务数据分析 - CLI 工具
使用 akshare 获取 A 股上市公司财务报表，计算核心财务指标。
支持同花顺 + 东方财富双数据源自动容错。
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
    """根据股票代码推断市场前缀（SH/SZ），用于东方财富 em 接口"""
    c = stock_code.lstrip("0").zfill(6) if len(stock_code) <= 6 else stock_code
    if c.startswith(("6", "9")):
        return f"SH{c}"
    return f"SZ{c}"


def _try_get_summary_ths(stock_code: str, years: int) -> str | None:
    """通过同花顺接口获取财务摘要（覆盖面广，含科创板）"""
    try:
        df = ak.stock_financial_abstract_ths(symbol=stock_code, indicator="按年度")
        if df is None or df.empty:
            return None

        recent = df.tail(years) if len(df) > years else df
        lines = [f"## 核心指标趋势（最近 {len(recent)} 年）\n"]

        header = "| 报告期 | 营业收入 | 营收增速 | 净利润 | 净利增速 | EPS | 毛利率 | 净利率 | ROE | 负债率 |"
        sep = "|--------|----------|----------|--------|----------|-----|--------|--------|-----|--------|"
        lines.append(header)
        lines.append(sep)
        for _, row in recent.iterrows():
            lines.append(
                f"| {row.get('报告期', 'N/A')} "
                f"| {row.get('营业总收入', 'N/A')} "
                f"| {row.get('营业总收入同比增长率', 'N/A')} "
                f"| {row.get('净利润', 'N/A')} "
                f"| {row.get('净利润同比增长率', 'N/A')} "
                f"| {row.get('基本每股收益', 'N/A')} "
                f"| {row.get('销售毛利率', 'N/A')} "
                f"| {row.get('销售净利率', 'N/A')} "
                f"| {row.get('净资产收益率', 'N/A')} "
                f"| {row.get('资产负债率', 'N/A')} |"
            )

        latest = df.iloc[-1]
        lines.append(f"\n## 最新年度详细指标（{latest.get('报告期', 'N/A')}）\n")
        detail_items = {
            "每股净资产": "每股净资产",
            "每股经营现金流": "每股经营现金流",
            "流动比率": "流动比率",
            "速动比率": "速动比率",
            "存货周转天数": "存货周转天数",
            "应收账款周转天数": "应收账款周转天数",
            "营业周期": "营业周期（天）",
        }
        for col, label in detail_items.items():
            val = latest.get(col, "N/A")
            if val is not None and val != "N/A":
                lines.append(f"- **{label}**: {val}")

        return "\n".join(lines)
    except Exception:
        return None


def _try_get_summary_em(stock_code: str, years: int) -> str | None:
    """通过东方财富 em 接口获取核心财务指标（需 SH/SZ 前缀）"""
    try:
        symbol = _market_prefix(stock_code)
        df = ak.stock_financial_analysis_indicator_em(symbol=symbol)
        if df is None or df.empty:
            return None

        recent = df.head(years * 4)
        lines = ["## 核心指标（最近报告期）\n"]
        latest = recent.iloc[0]

        for col in recent.columns[:15]:
            val = latest.get(col, "N/A")
            if val is not None and str(val) != "nan":
                lines.append(f"- **{col}**: {val}")

        return "\n".join(lines)
    except Exception:
        return None


def get_financial_summary(stock_code: str, years: int = 3) -> str:
    lines = [f"# {stock_code} 财务分析报告\n"]

    result = _try_get_summary_ths(stock_code, years)
    if result:
        lines.append(result)
    else:
        result = _try_get_summary_em(stock_code, years)
        if result:
            lines.append(result)
        else:
            lines.append(f"未找到 {stock_code} 的财务指标数据（同花顺和东方财富均无返回）")

    return "\n".join(lines)


def get_report(stock_code: str, report_type: str) -> str:
    symbol_em = _market_prefix(stock_code)
    lines = []

    if report_type in ("balance", "all"):
        lines.append("## 资产负债表（最近一期）\n")
        try:
            df = ak.stock_balance_sheet_by_report_em(symbol=symbol_em)
            if df is not None and not df.empty:
                latest = df.iloc[0]
                key_items = {
                    "TOTAL_ASSETS": "总资产",
                    "TOTAL_LIABILITIES": "总负债",
                    "TOTAL_EQUITY": "股东权益",
                    "MONETARYFUNDS": "货币资金",
                    "ACCOUNTS_RECE": "应收账款",
                    "INVENTORY": "存货",
                }
                report_date = latest.get("REPORT_DATE", "N/A")
                lines.append(f"报告期: {report_date}\n")
                for item, label in key_items.items():
                    val = latest.get(item)
                    if val is not None and str(val) != "nan":
                        try:
                            lines.append(f"- **{label}**: {float(val)/1e8:.2f} 亿")
                        except (ValueError, TypeError):
                            lines.append(f"- **{label}**: {val}")
                    else:
                        lines.append(f"- **{label}**: N/A")
            else:
                lines.append("未获取到资产负债表数据")
        except Exception as e:
            lines.append(f"获取资产负债表失败: {e}")

    if report_type in ("income", "all"):
        lines.append("\n## 利润表（最近一期）\n")
        try:
            df = ak.stock_profit_sheet_by_report_em(symbol=symbol_em)
            if df is not None and not df.empty:
                latest = df.iloc[0]
                key_items = {
                    "TOTAL_OPERATE_INCOME": "营业总收入",
                    "OPERATE_COST": "营业成本",
                    "OPERATE_PROFIT": "营业利润",
                    "TOTAL_PROFIT": "利润总额",
                    "NETPROFIT": "净利润",
                }
                report_date = latest.get("REPORT_DATE", "N/A")
                lines.append(f"报告期: {report_date}\n")
                for item, label in key_items.items():
                    val = latest.get(item)
                    if val is not None and str(val) != "nan":
                        try:
                            lines.append(f"- **{label}**: {float(val)/1e8:.2f} 亿")
                        except (ValueError, TypeError):
                            lines.append(f"- **{label}**: {val}")
                    else:
                        lines.append(f"- **{label}**: N/A")
            else:
                lines.append("未获取到利润表数据")
        except Exception as e:
            lines.append(f"获取利润表失败: {e}")

    if report_type in ("cashflow", "all"):
        lines.append("\n## 现金流量表（最近一期）\n")
        try:
            df = ak.stock_cash_flow_sheet_by_report_em(symbol=symbol_em)
            if df is not None and not df.empty:
                latest = df.iloc[0]
                key_items = {
                    "NETCASH_OPERATE": "经营活动现金流净额",
                    "NETCASH_INVEST": "投资活动现金流净额",
                    "NETCASH_FINANCE": "筹资活动现金流净额",
                    "CCE_ADD": "现金及等价物净增加额",
                }
                report_date = latest.get("REPORT_DATE", "N/A")
                lines.append(f"报告期: {report_date}\n")
                for item, label in key_items.items():
                    val = latest.get(item)
                    if val is not None and str(val) != "nan":
                        try:
                            lines.append(f"- **{label}**: {float(val)/1e8:.2f} 亿")
                        except (ValueError, TypeError):
                            lines.append(f"- **{label}**: {val}")
                    else:
                        lines.append(f"- **{label}**: N/A")
            else:
                lines.append("未获取到现金流量表数据")
        except Exception as e:
            lines.append(f"获取现金流量表失败: {e}")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="A 股财务数据分析")
    parser.add_argument("code", help="股票代码（6位数字），如 600519、000001")
    parser.add_argument("--years", "-y", type=int, default=3, help="分析年数 (默认 3)")
    parser.add_argument("--report", "-r", default="all",
                        choices=["balance", "income", "cashflow", "all"],
                        help="报表类型 (默认 all)")
    args = parser.parse_args()

    code = args.code.lstrip("0") if len(args.code) > 6 else args.code
    code = code.zfill(6)

    print(get_financial_summary(code, args.years))
    print("\n---\n")
    print(get_report(code, args.report))


if __name__ == "__main__":
    main()

"""
财务数据分析 - CLI 工具
使用 akshare 获取 A 股上市公司财务报表，计算核心财务指标。
"""

import argparse
import sys

try:
    import akshare as ak
    import pandas as pd
except ImportError:
    print("需要安装依赖: pip install akshare pandas", file=sys.stderr)
    sys.exit(1)


def get_financial_summary(stock_code: str, years: int = 3) -> str:
    """获取并分析财务数据，返回 Markdown 格式报告"""
    lines = [f"# {stock_code} 财务分析报告\n"]

    try:
        indicator = ak.stock_financial_analysis_indicator(symbol=stock_code)
        if indicator.empty:
            return f"未找到 {stock_code} 的财务数据"
        recent = indicator.head(years * 4)

        lines.append("## 核心指标（最近报告期）\n")
        latest = indicator.iloc[0]
        lines.append(f"- **报告期**: {latest.get('日期', 'N/A')}")

        key_metrics = {
            "摊薄净资产收益率(%)": "ROE",
            "加权净资产收益率(%)": "加权 ROE",
            "摊薄每股收益(元)": "每股收益(EPS)",
            "每股净资产_调整后(元)": "每股净资产(BPS)",
            "每股经营性现金流(元)": "每股经营现金流",
            "销售毛利率(%)": "毛利率",
            "销售净利率(%)": "净利率",
            "资产负债率(%)": "资产负债率",
            "流动比率": "流动比率",
            "速动比率": "速动比率",
        }
        for col, label in key_metrics.items():
            val = latest.get(col, "N/A")
            if val != "N/A" and val is not None:
                try:
                    val = f"{float(val):.2f}"
                except (ValueError, TypeError):
                    pass
            lines.append(f"- **{label}**: {val}")

        lines.append(f"\n## 指标趋势（最近 {years} 年）\n")
        trend_cols = ["日期", "摊薄净资产收益率(%)", "销售毛利率(%)", "销售净利率(%)", "资产负债率(%)"]
        available = [c for c in trend_cols if c in recent.columns]
        if available:
            annual = recent[recent["日期"].astype(str).str.endswith("1231")] if "日期" in recent.columns else recent.head(years)
            if annual.empty:
                annual = recent.head(years)
            lines.append("| 报告期 | ROE(%) | 毛利率(%) | 净利率(%) | 负债率(%) |")
            lines.append("|--------|--------|-----------|-----------|-----------|")
            for _, row in annual.iterrows():
                date = row.get("日期", "N/A")
                roe = row.get("摊薄净资产收益率(%)", "N/A")
                gm = row.get("销售毛利率(%)", "N/A")
                nm = row.get("销售净利率(%)", "N/A")
                debt = row.get("资产负债率(%)", "N/A")
                lines.append(f"| {date} | {roe} | {gm} | {nm} | {debt} |")

    except Exception as e:
        lines.append(f"\n获取财务指标失败: {e}")

    return "\n".join(lines)


def get_report(stock_code: str, report_type: str) -> str:
    """获取特定报表数据"""
    lines = []
    try:
        if report_type in ("balance", "all"):
            lines.append("## 资产负债表（最近一期）\n")
            df = ak.stock_balance_sheet_by_report_em(symbol=stock_code)
            if not df.empty:
                latest = df.iloc[0]
                key_items = ["TOTAL_ASSETS", "TOTAL_LIABILITIES", "TOTAL_EQUITY",
                             "MONETARYFUNDS", "ACCOUNTS_RECE", "INVENTORY"]
                labels = {"TOTAL_ASSETS": "总资产", "TOTAL_LIABILITIES": "总负债",
                          "TOTAL_EQUITY": "股东权益", "MONETARYFUNDS": "货币资金",
                          "ACCOUNTS_RECE": "应收账款", "INVENTORY": "存货"}
                for item in key_items:
                    val = latest.get(item, "N/A")
                    label = labels.get(item, item)
                    if val != "N/A" and val is not None:
                        try:
                            val = f"{float(val)/1e8:.2f} 亿"
                        except (ValueError, TypeError):
                            pass
                    lines.append(f"- **{label}**: {val}")

        if report_type in ("income", "all"):
            lines.append("\n## 利润表（最近一期）\n")
            df = ak.stock_profit_sheet_by_report_em(symbol=stock_code)
            if not df.empty:
                latest = df.iloc[0]
                key_items = ["TOTAL_OPERATE_INCOME", "OPERATE_COST", "OPERATE_PROFIT",
                             "TOTAL_PROFIT", "NETPROFIT"]
                labels = {"TOTAL_OPERATE_INCOME": "营业总收入", "OPERATE_COST": "营业成本",
                          "OPERATE_PROFIT": "营业利润", "TOTAL_PROFIT": "利润总额",
                          "NETPROFIT": "净利润"}
                for item in key_items:
                    val = latest.get(item, "N/A")
                    label = labels.get(item, item)
                    if val != "N/A" and val is not None:
                        try:
                            val = f"{float(val)/1e8:.2f} 亿"
                        except (ValueError, TypeError):
                            pass
                    lines.append(f"- **{label}**: {val}")

        if report_type in ("cashflow", "all"):
            lines.append("\n## 现金流量表（最近一期）\n")
            df = ak.stock_cash_flow_sheet_by_report_em(symbol=stock_code)
            if not df.empty:
                latest = df.iloc[0]
                key_items = ["NETCASH_OPERATE", "NETCASH_INVEST", "NETCASH_FINANCE",
                             "CCE_ADD"]
                labels = {"NETCASH_OPERATE": "经营活动现金流净额",
                          "NETCASH_INVEST": "投资活动现金流净额",
                          "NETCASH_FINANCE": "筹资活动现金流净额",
                          "CCE_ADD": "现金及等价物净增加额"}
                for item in key_items:
                    val = latest.get(item, "N/A")
                    label = labels.get(item, item)
                    if val != "N/A" and val is not None:
                        try:
                            val = f"{float(val)/1e8:.2f} 亿"
                        except (ValueError, TypeError):
                            pass
                    lines.append(f"- **{label}**: {val}")

    except Exception as e:
        lines.append(f"\n获取报表数据失败: {e}")

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
    if args.report != "all" or True:
        print("\n---\n")
        print(get_report(code, args.report))


if __name__ == "__main__":
    main()

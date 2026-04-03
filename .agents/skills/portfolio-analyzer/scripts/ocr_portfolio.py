"""
从券商持仓截图中 OCR 提取持仓数据。
用于不支持图片理解的模型，作为视觉读图的降级方案。

依赖：pip install rapidocr-onnxruntime Pillow
"""

import argparse
import json
import re
import sys
from pathlib import Path

try:
    from rapidocr_onnxruntime import RapidOCR
except ImportError:
    print("需要安装 OCR 依赖：pip install rapidocr-onnxruntime Pillow", file=sys.stderr)
    sys.exit(1)


def ocr_image(engine: RapidOCR, image_path: str) -> list[str]:
    """OCR 一张图片，返回所有识别出的文本行"""
    result, _ = engine(image_path)
    if not result:
        return []
    return [item[1] for item in result]


KNOWN_ETF_KEYWORDS = [
    "ETF", "LOF", "50", "300", "500", "1000",
    "恒生", "纳指", "标普", "中概", "科创", "创业板",
]


def classify_asset(name: str) -> str:
    """判断资产类型"""
    if any(kw in name for kw in KNOWN_ETF_KEYWORDS):
        return "ETF/基金"
    if "港元" in name or "-W" in name or "-S" in name:
        return "港股"
    return "A股"


def parse_portfolio_lines(lines: list[str]) -> dict:
    """
    从 OCR 文本行中提取持仓信息。
    券商 APP 持仓截图的典型布局：
      - 顶部：总资产、可用资金
      - 列表：证券名称、数量、现价/成本、盈亏
    """
    portfolio = {
        "total_assets": None,
        "available_cash": None,
        "stock_value": None,
        "total_pnl": None,
        "holdings": [],
        "raw_lines": lines,
    }

    for i, line in enumerate(lines):
        if "总资产" in line or "人民币总资产" in line:
            nums = re.findall(r"[\d,]+\.\d{2}", " ".join(lines[max(0, i):i+3]))
            if nums:
                portfolio["total_assets"] = nums[0].replace(",", "")

        if "可用" in line:
            nums = re.findall(r"[\d,]+\.\d{2}", " ".join(lines[max(0, i):i+3]))
            if nums:
                portfolio["available_cash"] = nums[-1].replace(",", "")

        if re.match(r"^股票[>＞\s]*$", line.strip()):
            nearby_text = " ".join(lines[i:min(len(lines), i+6)])
            nums = re.findall(r"[\d,]+\.\d{2}", nearby_text)
            if nums and not portfolio.get("stock_value"):
                portfolio["stock_value"] = nums[0].replace(",", "")

        if ("持仓盈亏" in line or "持仓收益" in line) and "今日" not in line and "列表" not in line:
            nearby_text = " ".join(lines[i:min(len(lines), i+3)])
            nums = re.findall(r"[+-][\d,]+\.\d{2}", nearby_text)
            if nums and not portfolio.get("total_pnl"):
                portfolio["total_pnl"] = nums[0].replace(",", "")

    holdings = _extract_holdings(lines)
    portfolio["holdings"] = holdings
    return portfolio


def _extract_holdings(lines: list[str]) -> list[dict]:
    """
    从文本行中提取个股持仓明细。
    策略：找到看起来像股票名的行，然后在附近行中收集数值。
    """
    holdings = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()

        if _looks_like_stock_name(line):
            holding = {"name": line, "type": classify_asset(line)}
            nearby = " ".join(lines[max(0, i):min(len(lines), i+4)])
            numbers = re.findall(r"[-+]?[\d,]+\.?\d*", nearby)
            numbers = [n.replace(",", "") for n in numbers if not re.match(r"^\d{6}$", n.replace(",", ""))]

            float_nums = []
            for n in numbers:
                try:
                    float_nums.append(float(n))
                except ValueError:
                    pass

            if float_nums:
                _assign_numbers_to_holding(holding, float_nums, nearby)

            pct_matches = re.findall(r"[-+]?\d+\.?\d*%", nearby)
            if pct_matches:
                holding["pnl_pct"] = pct_matches[0]

            holdings.append(holding)

        i += 1
    return holdings


def _looks_like_stock_name(text: str) -> bool:
    """判断一行文本是否像股票/ETF 名称"""
    text = text.strip()
    if not text or len(text) < 2 or len(text) > 20:
        return False
    if re.match(r"^[\d.,+\-%\s]+$", text):
        return False
    if re.match(r"^[\d.,]+港元", text):
        return False
    skip = [
        "买入", "卖出", "撤单", "持仓", "查询", "证券", "数量", "现价",
        "成本", "盈亏", "市值", "今日", "总资产", "可用", "股票", "理财",
        "活钱", "资金", "仓位", "批量", "条件单", "大事", "国债", "清仓",
        "人民币", "部分", "暂不可用", "普通交易", "定价", "定时", "涨跌",
        "策略",
    ]
    if any(kw in text for kw in skip):
        return False
    if re.search(r"[\u4e00-\u9fff]", text) and len(text) <= 12:
        return True
    if any(kw in text for kw in KNOWN_ETF_KEYWORDS) and len(text) <= 15:
        return True
    return False


def _assign_numbers_to_holding(holding: dict, nums: list[float], context: str) -> None:
    """
    尝试将识别出的数字分配给持仓字段。
    券商截图典型顺序：数量、现价、成本、盈亏金额。
    """
    int_like = [n for n in nums if n == int(n) and n >= 100]
    if int_like:
        holding["quantity"] = int(int_like[0])

    prices = [n for n in nums if 0.1 < n < 10000 and n != int(n)]
    if len(prices) >= 2:
        holding["current_price"] = prices[0]
        holding["cost_price"] = prices[1]
    elif len(prices) == 1:
        holding["current_price"] = prices[0]

    large = [n for n in nums if abs(n) >= 100 and n != holding.get("quantity", 0)]
    if large:
        for n in large:
            if n > 10000:
                if "market_value" not in holding:
                    holding["market_value"] = n
            elif "pnl" not in holding and any(c in context for c in "+-盈亏"):
                holding["pnl"] = n


def _deduplicate_holdings(holdings: list[dict]) -> list[dict]:
    """按名称去重（多张截图可能有重叠区域）。保留信息更完整的那条。"""
    seen: dict[str, dict] = {}
    for h in holdings:
        name = h.get("name", "")
        if name in seen:
            existing = seen[name]
            filled_existing = sum(1 for v in existing.values() if v and v != "-")
            filled_new = sum(1 for v in h.values() if v and v != "-")
            if filled_new > filled_existing:
                seen[name] = h
        else:
            seen[name] = h
    return list(seen.values())


def format_markdown(portfolio: dict) -> str:
    """输出 Markdown 格式的持仓数据"""
    lines = ["# OCR 持仓数据提取结果\n"]
    lines.append("> **注意**：以下数据通过 OCR 自动识别，可能存在误差，请核对后使用。\n")

    lines.append("## 账户概览\n")
    lines.append(f"- 总资产：{portfolio.get('total_assets', '未识别')}")
    lines.append(f"- 可用资金：{portfolio.get('available_cash', '未识别')}")
    lines.append(f"- 股票市值：{portfolio.get('stock_value', '未识别')}")
    lines.append(f"- 持仓盈亏：{portfolio.get('total_pnl', '未识别')}")
    lines.append("")

    holdings = _deduplicate_holdings(portfolio["holdings"])
    if holdings:
        lines.append("## 持仓明细\n")
        lines.append("| 名称 | 类型 | 数量 | 现价 | 成本 | 盈亏 | 盈亏% |")
        lines.append("|------|------|------|------|------|------|-------|")
        for h in holdings:
            name = h.get("name", "?")
            atype = h.get("type", "?")
            qty = h.get("quantity", "-")
            price = h.get("current_price", "-")
            cost = h.get("cost_price", "-")
            pnl = h.get("pnl", "-")
            pnl_pct = h.get("pnl_pct", "-")
            lines.append(f"| {name} | {atype} | {qty} | {price} | {cost} | {pnl} | {pnl_pct} |")
        lines.append(f"\n共识别到 **{len(holdings)}** 只持仓。")
    else:
        lines.append("**未能识别到持仓明细。**请检查截图是否清晰完整。")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="从券商持仓截图中 OCR 提取持仓数据",
        epilog="示例：python ocr_portfolio.py 1.jpg 2.jpg 3.jpg"
    )
    parser.add_argument("images", nargs="+", help="持仓截图路径（支持多张）")
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown",
                        help="输出格式（默认 markdown）")
    parser.add_argument("--raw", action="store_true", help="同时输出原始 OCR 文本")
    args = parser.parse_args()

    for img in args.images:
        if not Path(img).exists():
            print(f"文件不存在：{img}", file=sys.stderr)
            sys.exit(1)

    engine = RapidOCR()

    all_lines: list[str] = []
    for img in args.images:
        img_lines = ocr_image(engine, img)
        all_lines.extend(img_lines)

    portfolio = parse_portfolio_lines(all_lines)

    if args.format == "json":
        output = {k: v for k, v in portfolio.items() if k != "raw_lines"}
        if args.raw:
            output["raw_lines"] = portfolio["raw_lines"]
        print(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        print(format_markdown(portfolio))
        if args.raw:
            print("\n---\n## OCR 原始文本\n")
            for line in portfolio["raw_lines"]:
                print(f"- {line}")


if __name__ == "__main__":
    main()

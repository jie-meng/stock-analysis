"""
A 股选股筛选器 - CLI 工具
内置预设策略 + 自定义条件，两阶段筛选（粗筛→精筛）。
"""

import argparse
import json
import os
import sys
import time

os.environ["TQDM_DISABLE"] = "1"

try:
    import akshare as ak
    import pandas as pd
except ImportError:
    print("需要安装依赖: pip install akshare pandas", file=sys.stderr)
    sys.exit(1)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SECTORS_FILE = os.path.join(SCRIPT_DIR, "sectors.json")

# ---------------------------------------------------------------------------
# 预设策略定义
# ---------------------------------------------------------------------------

STRATEGIES = {
    "high-dividend": {
        "label": "高分红策略",
        "description": "股息率高、连续分红、经营稳健",
        "coarse": {
            "pe_min": 0,
            "pe_max": 30,
            "min_market_cap": 50,
            "exclude_st": True,
        },
        "fine": {
            "div_yield_min": 3.0,
            "consecutive_dividend_years": 3,
        },
        "default_sort": "div_yield",
        "default_sort_asc": False,
    },
    "value-quality": {
        "label": "价值优选策略",
        "description": "低估值 + 高 ROE + 盈利增长 + 财务安全",
        "coarse": {
            "pe_min": 0,
            "pe_max": 25,
            "pb_max": 5,
            "min_market_cap": 80,
            "exclude_st": True,
        },
        "fine": {
            "roe_min": 12.0,
            "profit_growth_min": 0.0,
            "debt_ratio_max": 60.0,
        },
        "default_sort": "roe",
        "default_sort_asc": False,
    },
    "policy-theme": {
        "label": "政策主题策略",
        "description": "政策重点方向 + 基本面过滤",
        "coarse": {
            "pe_min": 0,
            "pe_max": 80,
            "exclude_st": True,
        },
        "fine": {},
        "default_sort": "pe",
        "default_sort_asc": True,
    },
}


# ---------------------------------------------------------------------------
# 数据获取层
# ---------------------------------------------------------------------------

def get_all_stocks() -> pd.DataFrame:
    """获取全市场 A 股实时数据（东方财富）"""
    print("正在获取全市场数据...", file=sys.stderr)
    t0 = time.time()
    df = ak.stock_zh_a_spot_em()
    elapsed = time.time() - t0
    print(f"全市场数据获取完成，共 {len(df)} 只，耗时 {elapsed:.0f}s", file=sys.stderr)
    return df


def get_concept_stocks(concept_name: str) -> set[str]:
    """获取某个概念板块的成分股代码集合"""
    try:
        df = ak.stock_board_concept_cons_em(symbol=concept_name)
        return set(df["代码"].astype(str).str.zfill(6))
    except Exception:
        print(f"  警告: 概念板块 '{concept_name}' 获取失败，跳过", file=sys.stderr)
        return set()


def get_concept_stocks_with_data(concept_name: str) -> pd.DataFrame:
    """获取板块成分股及其行情数据（含 PE/PB/市值等），返回 DataFrame"""
    try:
        df = ak.stock_board_concept_cons_em(symbol=concept_name)
        df["代码"] = df["代码"].astype(str).str.zfill(6)
        return df
    except Exception:
        print(f"  警告: 概念板块 '{concept_name}' 获取失败，跳过", file=sys.stderr)
        return pd.DataFrame()


def get_sector_stocks(theme: str | None = None) -> set[str]:
    """根据 sectors.json 获取政策主题相关股票代码集合"""
    if not os.path.exists(SECTORS_FILE):
        print(f"警告: {SECTORS_FILE} 不存在，政策主题筛选不可用", file=sys.stderr)
        return set()

    with open(SECTORS_FILE, "r", encoding="utf-8") as f:
        sectors = json.load(f)

    all_codes: set[str] = set()

    for theme_key, theme_data in sectors.items():
        if theme and theme != theme_key:
            continue
        sub_themes = theme_data.get("sub_themes", {})
        for sub_name, sub_data in sub_themes.items():
            boards = sub_data.get("concept_boards", [])
            print(f"  获取 [{theme_key}/{sub_name}] 板块成分股...", file=sys.stderr)
            for board in boards:
                codes = get_concept_stocks(board)
                all_codes |= codes
                print(f"    {board}: {len(codes)} 只", file=sys.stderr)

    print(f"  政策主题股票池合计: {len(all_codes)} 只（去重后）", file=sys.stderr)
    return all_codes


def get_sector_stocks_with_data(theme: str | None = None) -> pd.DataFrame:
    """获取政策主题相关股票及行情数据，直接从板块接口聚合（无需全市场接口）"""
    if not os.path.exists(SECTORS_FILE):
        print(f"警告: {SECTORS_FILE} 不存在，政策主题筛选不可用", file=sys.stderr)
        return pd.DataFrame()

    with open(SECTORS_FILE, "r", encoding="utf-8") as f:
        sectors = json.load(f)

    frames: list[pd.DataFrame] = []

    for theme_key, theme_data in sectors.items():
        if theme and theme != theme_key:
            continue
        sub_themes = theme_data.get("sub_themes", {})
        for sub_name, sub_data in sub_themes.items():
            boards = sub_data.get("concept_boards", [])
            print(f"  获取 [{theme_key}/{sub_name}] 板块成分股...", file=sys.stderr)
            for board in boards:
                df = get_concept_stocks_with_data(board)
                if not df.empty:
                    frames.append(df)
                    print(f"    {board}: {len(df)} 只", file=sys.stderr)

    if not frames:
        return pd.DataFrame()

    combined = pd.concat(frames, ignore_index=True).drop_duplicates(subset=["代码"])
    print(f"  政策主题股票池合计: {len(combined)} 只（去重后）", file=sys.stderr)
    return combined


def get_dividend_info(stock_code: str) -> dict:
    """获取个股分红信息"""
    info = {"div_yield": None, "consecutive_years": 0}
    try:
        df = ak.stock_history_dividend_detail(
            symbol=stock_code, indicator="分红"
        )
        if df is None or df.empty:
            return info

        implemented = df[df["进度"] == "实施"]
        if implemented.empty:
            return info

        info["consecutive_years"] = len(implemented)

        latest_payout = implemented.iloc[0].get("派息", 0)
        try:
            info["latest_payout_per_10"] = float(latest_payout)
        except (ValueError, TypeError):
            info["latest_payout_per_10"] = 0
    except Exception:
        pass
    return info


def get_financial_indicators(stock_code: str) -> dict:
    """获取个股关键财务指标"""
    result = {
        "roe": None,
        "gross_margin": None,
        "net_margin": None,
        "debt_ratio": None,
        "revenue_growth": None,
        "profit_growth": None,
    }
    try:
        df = ak.stock_financial_analysis_indicator(symbol=stock_code)
        if df is None or df.empty:
            return result

        latest = df.iloc[0]
        result["roe"] = _safe_float(latest.get("摊薄净资产收益率(%)"))
        result["gross_margin"] = _safe_float(latest.get("销售毛利率(%)"))
        result["net_margin"] = _safe_float(latest.get("销售净利率(%)"))
        result["debt_ratio"] = _safe_float(latest.get("资产负债率(%)"))
    except Exception:
        pass

    return result


def _safe_float(val) -> float | None:
    if val is None:
        return None
    try:
        v = float(val)
        return v if not pd.isna(v) else None
    except (ValueError, TypeError):
        return None


# ---------------------------------------------------------------------------
# 粗筛阶段
# ---------------------------------------------------------------------------

def coarse_filter(df: pd.DataFrame, params: dict,
                  sector_codes: set[str] | None = None) -> pd.DataFrame:
    """粗筛：使用向量化操作快速过滤"""
    mask = pd.Series(True, index=df.index)

    if params.get("exclude_st", True):
        if "名称" in df.columns:
            mask &= ~df["名称"].str.contains("ST|退", na=False, regex=True)

    if "市盈率-动态" in df.columns:
        pe = pd.to_numeric(df["市盈率-动态"], errors="coerce")
        pe_min = params.get("pe_min")
        pe_max = params.get("pe_max")
        if pe_min is not None:
            mask &= pe > pe_min
        if pe_max is not None:
            mask &= pe <= pe_max

    if "市净率" in df.columns and "pb_max" in params:
        pb = pd.to_numeric(df["市净率"], errors="coerce")
        mask &= (pb > 0) & (pb <= params["pb_max"])

    if "总市值" in df.columns and "min_market_cap" in params:
        cap = pd.to_numeric(df["总市值"], errors="coerce")
        mask &= cap >= params["min_market_cap"] * 1e8

    result = df[mask].copy()

    if sector_codes and "代码" in result.columns:
        result = result[
            result["代码"].astype(str).str.zfill(6).isin(sector_codes)
        ]

    return result


# ---------------------------------------------------------------------------
# 精筛阶段
# ---------------------------------------------------------------------------

def fine_filter_high_dividend(stocks: pd.DataFrame,
                              params: dict, top: int) -> list[dict]:
    """高分红策略精筛：获取分红数据"""
    results = []
    div_yield_min = params.get("div_yield_min", 3.0)
    min_years = params.get("consecutive_dividend_years", 3)

    indexed = stocks.copy()
    indexed["_code"] = indexed["代码"].astype(str).str.zfill(6)
    indexed = indexed.set_index("_code")
    codes = indexed.index.tolist()
    total = len(codes)

    for i, code in enumerate(codes):
        if i % 20 == 0:
            print(f"  精筛进度: {i}/{total}...", file=sys.stderr)

        try:
            row = indexed.loc[code]
            price = _safe_float(row.get("最新价"))
            if not price or price <= 0:
                continue

            div_info = get_dividend_info(code)
            if div_info["consecutive_years"] < min_years:
                continue

            payout = div_info.get("latest_payout_per_10", 0)
            if payout <= 0:
                continue

            actual_yield = (payout / 10) / price * 100
            if actual_yield < div_yield_min:
                continue

            results.append({
                "代码": code,
                "名称": str(row.get("名称", "")),
                "最新价": price,
                "div_yield": round(actual_yield, 2),
                "pe": _safe_float(row.get("市盈率-动态")),
                "pb": _safe_float(row.get("市净率")),
                "market_cap": _cap_yi(_safe_float(row.get("总市值"))),
                "连续分红年数": div_info["consecutive_years"],
            })
        except Exception:
            continue

    return results


def fine_filter_value_quality(stocks: pd.DataFrame,
                              params: dict, top: int) -> list[dict]:
    """价值优选策略精筛：获取财务指标"""
    results = []
    roe_min = params.get("roe_min", 12.0)
    profit_growth_min = params.get("profit_growth_min")
    debt_ratio_max = params.get("debt_ratio_max")
    revenue_growth_min = params.get("revenue_growth_min")

    indexed = stocks.copy()
    indexed["_code"] = indexed["代码"].astype(str).str.zfill(6)
    indexed = indexed.set_index("_code")
    codes = indexed.index.tolist()
    total = len(codes)

    for i, code in enumerate(codes):
        if i % 20 == 0:
            print(f"  精筛进度: {i}/{total}...", file=sys.stderr)

        try:
            fin = get_financial_indicators(code)

            roe = fin.get("roe")
            if roe is None or roe < roe_min:
                continue

            debt = fin.get("debt_ratio")
            if debt_ratio_max is not None and debt is not None and debt > debt_ratio_max:
                continue

            profit_g = fin.get("profit_growth")
            if profit_growth_min is not None and profit_g is not None and profit_g < profit_growth_min:
                continue

            rev_g = fin.get("revenue_growth")
            if revenue_growth_min is not None and rev_g is not None and rev_g < revenue_growth_min:
                continue

            row = indexed.loc[code]
            results.append({
                "代码": code,
                "名称": str(row.get("名称", "")),
                "最新价": _safe_float(row.get("最新价")),
                "pe": _safe_float(row.get("市盈率-动态")),
                "pb": _safe_float(row.get("市净率")),
                "roe": round(roe, 2),
                "gross_margin": _round_or_na(fin.get("gross_margin")),
                "debt_ratio": _round_or_na(fin.get("debt_ratio")),
                "market_cap": _cap_yi(_safe_float(row.get("总市值"))),
            })
        except Exception:
            continue

    return results


def fine_filter_policy_theme(stocks: pd.DataFrame,
                             params: dict, top: int) -> list[dict]:
    """政策主题策略精筛：板块已在粗筛过滤，此处只做整理排序"""
    results = []
    indexed = stocks.copy()
    indexed["_code"] = indexed["代码"].astype(str).str.zfill(6)
    indexed = indexed.set_index("_code")
    has_cap = "总市值" in indexed.columns

    for code in indexed.index:
        try:
            row = indexed.loc[code]
            entry = {
                "代码": code,
                "名称": str(row.get("名称", "")),
                "最新价": _safe_float(row.get("最新价")),
                "pe": _safe_float(row.get("市盈率-动态")),
                "pb": _safe_float(row.get("市净率")),
                "涨跌幅": _safe_float(row.get("涨跌幅")),
                "换手率": _safe_float(row.get("换手率")),
            }
            if has_cap:
                entry["market_cap"] = _cap_yi(_safe_float(row.get("总市值")))
            results.append(entry)
        except Exception:
            continue

    return results


def fine_filter_custom(stocks: pd.DataFrame,
                       params: dict, top: int) -> list[dict]:
    """自定义策略精筛"""
    results = []
    roe_min = params.get("roe_min")
    div_yield_min = params.get("div_yield_min")
    debt_ratio_max = params.get("debt_ratio_max")
    revenue_growth_min = params.get("revenue_growth_min")
    profit_growth_min = params.get("profit_growth_min")

    need_financial = any(v is not None for v in [roe_min, debt_ratio_max,
                                                  revenue_growth_min,
                                                  profit_growth_min])
    need_dividend = div_yield_min is not None

    indexed = stocks.copy()
    indexed["_code"] = indexed["代码"].astype(str).str.zfill(6)
    indexed = indexed.set_index("_code")
    codes = indexed.index.tolist()
    total = len(codes)

    for i, code in enumerate(codes):
        if i % 20 == 0:
            print(f"  精筛进度: {i}/{total}...", file=sys.stderr)

        try:
            row = indexed.loc[code]
            entry = {
                "代码": code,
                "名称": str(row.get("名称", "")),
                "最新价": _safe_float(row.get("最新价")),
                "pe": _safe_float(row.get("市盈率-动态")),
                "pb": _safe_float(row.get("市净率")),
                "market_cap": _cap_yi(_safe_float(row.get("总市值"))),
            }

            if need_financial:
                fin = get_financial_indicators(code)
                roe = fin.get("roe")
                if roe_min is not None and (roe is None or roe < roe_min):
                    continue
                debt = fin.get("debt_ratio")
                if debt_ratio_max is not None and debt is not None and debt > debt_ratio_max:
                    continue
                entry["roe"] = _round_or_na(roe)
                entry["debt_ratio"] = _round_or_na(fin.get("debt_ratio"))

            if need_dividend:
                price = entry["最新价"]
                if not price or price <= 0:
                    continue
                div_info = get_dividend_info(code)
                payout = div_info.get("latest_payout_per_10", 0)
                if payout <= 0:
                    continue
                actual_yield = (payout / 10) / price * 100
                if actual_yield < div_yield_min:
                    continue
                entry["div_yield"] = round(actual_yield, 2)

            results.append(entry)
        except Exception:
            continue

    return results


# ---------------------------------------------------------------------------
# 输出格式化
# ---------------------------------------------------------------------------

def _cap_yi(val: float | None) -> float | None:
    if val is None:
        return None
    return round(val / 1e8, 1)


def _round_or_na(val: float | None, n: int = 2) -> str:
    if val is None:
        return "N/A"
    return str(round(val, n))


def format_results(results: list[dict], strategy_label: str,
                   total_market: int, coarse_count: int,
                   sort_key: str, sort_asc: bool, top: int) -> str:
    """格式化输出结果为 Markdown"""
    valid = [r for r in results if r.get(sort_key) is not None]
    na_items = [r for r in results if r.get(sort_key) is None]
    valid.sort(key=lambda x: x[sort_key], reverse=not sort_asc)
    sorted_results = (valid + na_items)[:top]

    lines = [f"# 选股结果：{strategy_label}\n"]
    lines.append(
        f"全市场 {total_market} 只 → 粗筛 {coarse_count} 只 "
        f"→ 精筛 {len(results)} 只 → 展示 Top {min(top, len(sorted_results))}\n"
    )

    if not sorted_results:
        lines.append("未找到符合条件的股票。\n")
        lines.append("建议：放宽筛选条件重试。")
        return "\n".join(lines)

    cols = list(sorted_results[0].keys())
    col_labels = {
        "代码": "代码", "名称": "名称", "最新价": "最新价",
        "pe": "PE(动)", "pb": "PB", "roe": "ROE(%)",
        "div_yield": "股息率(%)", "gross_margin": "毛利率(%)",
        "debt_ratio": "负债率(%)", "market_cap": "市值(亿)",
        "连续分红年数": "连续分红年数",
        "涨跌幅": "涨跌幅(%)", "换手率": "换手率(%)",
    }
    header = "| 排名 | " + " | ".join(col_labels.get(c, c) for c in cols) + " |"
    sep = "|---" + "|---" * len(cols) + "|"
    lines.extend([header, sep])

    for rank, item in enumerate(sorted_results, 1):
        vals = []
        for c in cols:
            v = item.get(c)
            if v is None:
                vals.append("N/A")
            elif isinstance(v, float):
                vals.append(f"{v:.2f}" if abs(v) < 10000 else f"{v:.0f}")
            else:
                vals.append(str(v))
        lines.append(f"| {rank} | " + " | ".join(vals) + " |")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------

def run_strategy(strategy_name: str, theme: str | None,
                 sort_key: str | None, top: int) -> str:
    strategy = STRATEGIES[strategy_name]
    coarse_params = strategy["coarse"]
    fine_params = strategy["fine"]
    sort_k = sort_key or strategy["default_sort"]
    sort_asc = strategy["default_sort_asc"]

    if strategy_name == "policy-theme":
        return _run_policy_theme(strategy, theme, sort_k, sort_asc, top)

    sector_codes = None
    if coarse_params.get("use_sector_filter"):
        sector_codes = get_sector_stocks(theme)
        if not sector_codes:
            return "政策主题股票池为空。请检查 sectors.json 配置或指定有效的 --theme。"

    df = get_all_stocks()
    total_market = len(df)

    coarse = coarse_filter(df, coarse_params, sector_codes)
    coarse_count = len(coarse)
    print(f"粗筛完成: {total_market} → {coarse_count}", file=sys.stderr)

    if coarse_count == 0:
        return f"# 选股结果：{strategy['label']}\n\n粗筛后无符合条件的股票。请放宽条件重试。"

    if coarse_count > 200:
        print(f"  粗筛结果 {coarse_count} 只偏多，收紧市值门槛缩小范围...",
              file=sys.stderr)
        cap_col = "总市值"
        if cap_col in coarse.columns:
            sorted_caps = coarse[cap_col].dropna().sort_values(ascending=False)
            if len(sorted_caps) > 200:
                cap_cutoff = sorted_caps.iloc[199]
                coarse = coarse[coarse[cap_col] >= cap_cutoff]
                coarse_count = len(coarse)
                print(f"  收紧后: {coarse_count}", file=sys.stderr)

    print(f"开始精筛（{strategy['label']}）...", file=sys.stderr)

    if strategy_name == "high-dividend":
        results = fine_filter_high_dividend(coarse, fine_params, top)
    elif strategy_name == "value-quality":
        results = fine_filter_value_quality(coarse, fine_params, top)
    else:
        results = []

    print(f"精筛完成: {len(results)} 只符合条件", file=sys.stderr)
    return format_results(results, strategy["label"], total_market,
                          coarse_count, sort_k, sort_asc, top)


def _run_policy_theme(strategy: dict, theme: str | None,
                      sort_key: str, sort_asc: bool, top: int) -> str:
    """政策主题策略快速路径：直接从板块接口获取数据，跳过全市场接口"""
    coarse_params = strategy["coarse"]

    sector_df = get_sector_stocks_with_data(theme)
    if sector_df.empty:
        return "政策主题股票池为空。请检查 sectors.json 配置或指定有效的 --theme。"

    total_pool = len(sector_df)
    coarse = coarse_filter(sector_df, coarse_params)
    coarse_count = len(coarse)
    print(f"粗筛完成: 板块池 {total_pool} 只 → {coarse_count} 只", file=sys.stderr)

    if coarse_count == 0:
        return f"# 选股结果：{strategy['label']}\n\n粗筛后无符合条件的股票。请放宽条件重试。"

    results = fine_filter_policy_theme(coarse, strategy["fine"], top)
    print(f"整理完成: {len(results)} 只", file=sys.stderr)

    return format_results(results, strategy["label"], total_pool,
                          coarse_count, sort_key, sort_asc, top)


def run_custom(args) -> str:
    coarse_params = {
        "exclude_st": not args.include_st,
        "min_market_cap": args.min_market_cap,
    }
    if args.pe_max is not None:
        coarse_params["pe_max"] = args.pe_max
    if args.pe_min is not None:
        coarse_params["pe_min"] = args.pe_min
    if args.pb_max is not None:
        coarse_params["pb_max"] = args.pb_max

    sector_codes = None
    if args.sector:
        sector_codes = get_concept_stocks(args.sector)
        if not sector_codes:
            return f"概念板块 '{args.sector}' 获取失败或无成分股。"

    df = get_all_stocks()
    total_market = len(df)

    coarse = coarse_filter(df, coarse_params, sector_codes)
    coarse_count = len(coarse)
    print(f"粗筛完成: {total_market} → {coarse_count}", file=sys.stderr)

    if coarse_count == 0:
        return "# 自定义选股结果\n\n粗筛后无符合条件的股票。请放宽条件重试。"

    if coarse_count > 200:
        print(f"  粗筛结果 {coarse_count} 只偏多，收紧市值门槛...", file=sys.stderr)
        cap_col = "总市值"
        if cap_col in coarse.columns:
            sorted_caps = coarse[cap_col].dropna().sort_values(ascending=False)
            if len(sorted_caps) > 200:
                cap_cutoff = sorted_caps.iloc[199]
                coarse = coarse[coarse[cap_col] >= cap_cutoff]
                coarse_count = len(coarse)
                print(f"  收紧后: {coarse_count}", file=sys.stderr)

    fine_params = {}
    if args.roe_min is not None:
        fine_params["roe_min"] = args.roe_min
    if args.div_yield_min is not None:
        fine_params["div_yield_min"] = args.div_yield_min
    if args.debt_ratio_max is not None:
        fine_params["debt_ratio_max"] = args.debt_ratio_max
    if args.revenue_growth_min is not None:
        fine_params["revenue_growth_min"] = args.revenue_growth_min
    if args.profit_growth_min is not None:
        fine_params["profit_growth_min"] = args.profit_growth_min

    print("开始精筛（自定义条件）...", file=sys.stderr)
    results = fine_filter_custom(coarse, fine_params, args.top)
    print(f"精筛完成: {len(results)} 只符合条件", file=sys.stderr)

    sort_k = args.sort or "pe"
    return format_results(results, "自定义筛选", total_market,
                          coarse_count, sort_k, True, args.top)


def main():
    parser = argparse.ArgumentParser(
        description="A 股选股筛选器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "预设策略:\n"
            "  high-dividend   高分红策略（股息率>=3%, 连续分红>=3年）\n"
            "  value-quality   价值优选策略（PE<=25, ROE>=12%, 低负债）\n"
            "  policy-theme    政策主题策略（十五五规划相关板块）\n"
            "\n"
            "示例:\n"
            "  screener.py --strategy high-dividend\n"
            "  screener.py --strategy policy-theme --theme 新能源\n"
            "  screener.py --custom --pe-max 20 --roe-min 15 --debt-ratio-max 50\n"
        ),
    )

    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--strategy", "-s",
                      choices=list(STRATEGIES.keys()),
                      help="预设策略")
    mode.add_argument("--custom", action="store_true",
                      help="自定义筛选模式")

    parser.add_argument("--theme", help="政策主题子方向 (仅 policy-theme)")
    parser.add_argument("--top", type=int, default=30, help="输出前 N 只 (默认 30)")
    parser.add_argument("--sort", help="排序字段: roe/pe/div_yield/market_cap")

    parser.add_argument("--pe-max", type=float, help="PE 上限")
    parser.add_argument("--pe-min", type=float, default=0, help="PE 下限 (默认 0)")
    parser.add_argument("--pb-max", type=float, help="PB 上限")
    parser.add_argument("--roe-min", type=float, help="ROE 下限(%%)")
    parser.add_argument("--div-yield-min", type=float, help="股息率下限(%%)")
    parser.add_argument("--debt-ratio-max", type=float, help="负债率上限(%%)")
    parser.add_argument("--revenue-growth-min", type=float, help="营收增速下限(%%)")
    parser.add_argument("--profit-growth-min", type=float, help="净利增速下限(%%)")
    parser.add_argument("--sector", help="限定概念板块名称")
    parser.add_argument("--min-market-cap", type=float, default=50,
                        help="最低市值(亿, 默认 50)")
    parser.add_argument("--include-st", action="store_true",
                        help="包含 ST 股票")

    args = parser.parse_args()

    if args.strategy:
        result = run_strategy(args.strategy, args.theme, args.sort, args.top)
    else:
        result = run_custom(args)

    print(result)


if __name__ == "__main__":
    main()

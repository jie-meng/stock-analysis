"""
A 股选股筛选器 - CLI 工具

架构：并发批量获取 → merge → 向量化筛选。

数据源（均为批量接口）：
  1. 东财 clist API（直调，绕过 akshare 的页间 sleep）— 板块成分股 + PE/PB
  2. stock_yjbb_em        — 全市场 ROE/EPS/利润增速/营收增速/毛利率（~80s）
  3. stock_fhps_em         — 全市场股息率/EPS/BPS（~28s）
  4. stock_zcfz_em         — 全市场资产负债率（~40s）
  5. stock_history_dividend — 全市场分红次数（~3s）
  6. stock_zh_a_spot_em     — 全市场 PE/PB/市值（备选，~7min）

2-5 并发执行，板块获取同步并发。
"""

import argparse
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

os.environ["TQDM_DISABLE"] = "1"

try:
    import akshare as ak
    import pandas as pd
    import requests
except ImportError:
    print("需要安装依赖: pip install akshare pandas requests", file=sys.stderr)
    sys.exit(1)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SECTORS_FILE = os.path.join(SCRIPT_DIR, "sectors.json")

STRATEGIES = {
    "high-dividend": {
        "label": "高分红策略",
        "description": "股息率高、连续分红、经营稳健",
        "defaults": {
            "pe_min": 0, "pe_max": 30, "min_market_cap": 50,
            "div_yield_min": 3.0, "consecutive_dividend_years": 3,
        },
        "default_sort": "div_yield",
        "default_sort_asc": False,
    },
    "value-quality": {
        "label": "价值优选策略",
        "description": "低估值 + 高 ROE + 盈利增长 + 财务安全",
        "defaults": {
            "pe_min": 0, "pe_max": 25, "pb_max": 5, "min_market_cap": 80,
            "roe_min": 12.0, "profit_growth_min": 0.0, "debt_ratio_max": 60.0,
        },
        "default_sort": "roe",
        "default_sort_asc": False,
    },
    "policy-theme": {
        "label": "政策主题策略",
        "description": "政策重点方向 + 基本面过滤",
        "defaults": {
            "pe_min": 0, "pe_max": 80,
        },
        "default_sort": "pe",
        "default_sort_asc": True,
    },
}


# ---------------------------------------------------------------------------
# 日志
# ---------------------------------------------------------------------------

def _log(msg: str):
    print(msg, file=sys.stderr, flush=True)


# ---------------------------------------------------------------------------
# 板块数据 — 直调东财 API，并发获取，无页间 sleep
# ---------------------------------------------------------------------------

def _resolve_board_codes(board_names: list[str]) -> dict[str, str]:
    """板块名称 → BK 代码映射"""
    try:
        name_df = ak.stock_board_concept_name_em()
        return {
            row["板块名称"]: row["板块代码"]
            for _, row in name_df.iterrows()
            if row["板块名称"] in board_names
        }
    except Exception:
        return {}


def _fetch_board_direct(bk_code: str) -> list[dict]:
    """直调东财 clist API 获取板块成分股，无 sleep"""
    url = "https://29.push2.eastmoney.com/api/qt/clist/get"
    all_rows: list[dict] = []
    page = 1
    while True:
        params = {
            "pn": str(page), "pz": "100",
            "po": "1", "np": "1",
            "ut": "bd1d9ddb04089700cf9c27f6f7426281",
            "fltt": "2", "invt": "2",
            "fid": "f12",
            "fs": f"b:{bk_code} f:!50",
            "fields": "f2,f3,f9,f12,f14,f20,f21,f23",
        }
        try:
            r = requests.get(url, params=params, timeout=15)
            data = r.json()
        except Exception:
            break
        if not data.get("data") or not data["data"].get("diff"):
            break
        all_rows.extend(data["data"]["diff"])
        if len(all_rows) >= data["data"]["total"]:
            break
        page += 1
    return all_rows


def _parse_board_rows(rows: list[dict]) -> pd.DataFrame:
    """解析东财 clist 原始返回为标准 DataFrame"""
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    result = pd.DataFrame()
    result["代码"] = df.get("f12", "").astype(str).str.zfill(6)
    result["名称"] = df.get("f14", "")
    result["最新价"] = pd.to_numeric(df.get("f2"), errors="coerce")
    result["涨跌幅"] = pd.to_numeric(df.get("f3"), errors="coerce")
    result["市盈率-动态"] = pd.to_numeric(df.get("f9"), errors="coerce")
    result["市净率"] = pd.to_numeric(df.get("f23"), errors="coerce")
    result["总市值"] = pd.to_numeric(df.get("f20"), errors="coerce")
    result["流通市值"] = pd.to_numeric(df.get("f21"), errors="coerce")
    return result


def fetch_sector_pool_concurrent(theme: str | None) -> pd.DataFrame:
    """并发获取全部相关板块成分股"""
    if not os.path.exists(SECTORS_FILE):
        _log(f"警告: {SECTORS_FILE} 不存在")
        return pd.DataFrame()

    with open(SECTORS_FILE, "r", encoding="utf-8") as f:
        sectors = json.load(f)

    board_names = []
    board_meta: dict[str, str] = {}
    for theme_key, theme_data in sectors.items():
        if theme and theme != theme_key:
            continue
        for sub_name, sub_data in theme_data.get("sub_themes", {}).items():
            for board in sub_data.get("concept_boards", []):
                if board not in board_meta:
                    board_names.append(board)
                    board_meta[board] = f"{theme_key}/{sub_name}"

    if not board_names:
        return pd.DataFrame()

    _log(f"解析 {len(board_names)} 个概念板块代码...")
    bk_map = _resolve_board_codes(board_names)
    resolved = [(name, bk_map[name]) for name in board_names if name in bk_map]
    missing = [name for name in board_names if name not in bk_map]
    if missing:
        _log(f"  未找到板块: {', '.join(missing)}")

    _log(f"并发获取 {len(resolved)} 个板块成分股...")
    t0 = time.time()
    frames: list[pd.DataFrame] = []

    def _fetch_one(name_code: tuple) -> tuple[str, pd.DataFrame]:
        name, code = name_code
        rows = _fetch_board_direct(code)
        df = _parse_board_rows(rows)
        return name, df

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(_fetch_one, nc): nc[0] for nc in resolved}
        for f in as_completed(futures):
            name, df = f.result()
            if not df.empty:
                frames.append(df)
                _log(f"  {name}: {len(df)} 只")
            else:
                _log(f"  {name}: 获取失败")

    if not frames:
        return pd.DataFrame()

    combined = pd.concat(frames, ignore_index=True).drop_duplicates(subset=["代码"])
    _log(f"  板块池合计: {len(combined)} 只（去重后）, 耗时 {time.time()-t0:.0f}s")
    return combined


# ---------------------------------------------------------------------------
# 批量财务数据获取（全市场）
# ---------------------------------------------------------------------------

def fetch_yjbb() -> pd.DataFrame:
    """全市场业绩报表：ROE、EPS、利润增速、营收增速、毛利率 ~80s"""
    _log("获取业绩报表（ROE/增速）...")
    t0 = time.time()
    for date in ["20241231", "20231231"]:
        try:
            df = ak.stock_yjbb_em(date=date)
            if df is not None and len(df) > 100:
                break
        except Exception:
            continue
    else:
        _log("  警告: 业绩报表获取失败")
        return pd.DataFrame()

    df["代码"] = df["股票代码"].astype(str).str.zfill(6)
    result = pd.DataFrame({
        "代码": df["代码"],
        "roe": pd.to_numeric(df["净资产收益率"], errors="coerce"),
        "eps": pd.to_numeric(df["每股收益"], errors="coerce"),
        "profit_growth": pd.to_numeric(df["净利润-同比增长"], errors="coerce"),
        "revenue_growth": pd.to_numeric(df["营业总收入-同比增长"], errors="coerce"),
        "gross_margin": pd.to_numeric(df["销售毛利率"], errors="coerce"),
    })
    _log(f"  业绩报表: {len(result)} 只, 耗时 {time.time()-t0:.0f}s")
    return result.drop_duplicates(subset=["代码"])


def fetch_fhps() -> pd.DataFrame:
    """全市场分红送配：股息率 ~28s"""
    _log("获取分红数据（股息率）...")
    t0 = time.time()
    for date in ["20241231", "20231231"]:
        try:
            df = ak.stock_fhps_em(date=date)
            if df is not None and len(df) > 100:
                break
        except Exception:
            continue
    else:
        _log("  警告: 分红数据获取失败")
        return pd.DataFrame()

    df["代码"] = df["代码"].astype(str).str.zfill(6)
    result = pd.DataFrame({
        "代码": df["代码"],
        "div_yield": pd.to_numeric(df["现金分红-股息率"], errors="coerce") * 100,
    })
    _log(f"  分红数据: {len(result)} 只, 耗时 {time.time()-t0:.0f}s")
    return result.drop_duplicates(subset=["代码"])


def fetch_zcfz() -> pd.DataFrame:
    """全市场资产负债表：资产负债率 ~40s"""
    _log("获取资产负债表（负债率）...")
    t0 = time.time()
    for date in ["20241231", "20231231"]:
        try:
            df = ak.stock_zcfz_em(date=date)
            if df is not None and len(df) > 100:
                break
        except Exception:
            continue
    else:
        _log("  警告: 资产负债表获取失败")
        return pd.DataFrame()

    df["代码"] = df["股票代码"].astype(str).str.zfill(6)
    result = pd.DataFrame({
        "代码": df["代码"],
        "debt_ratio": pd.to_numeric(df["资产负债率"], errors="coerce"),
    })
    _log(f"  资产负债表: {len(result)} 只, 耗时 {time.time()-t0:.0f}s")
    return result.drop_duplicates(subset=["代码"])


def fetch_dividend_history() -> pd.DataFrame:
    """全市场分红历史：分红次数 ~3s"""
    _log("获取分红历史...")
    t0 = time.time()
    try:
        df = ak.stock_history_dividend()
    except Exception:
        _log("  警告: 分红历史获取失败")
        return pd.DataFrame()

    df["代码"] = df["代码"].astype(str).str.zfill(6)
    result = df[["代码", "分红次数"]].copy()
    result["分红次数"] = pd.to_numeric(result["分红次数"], errors="coerce").fillna(0).astype(int)
    _log(f"  分红历史: {len(result)} 只, 耗时 {time.time()-t0:.0f}s")
    return result


def fetch_all_stocks() -> pd.DataFrame:
    """全市场 A 股实时数据（备选，最慢）"""
    _log("获取全市场数据（约需 5-7 分钟）...")
    t0 = time.time()
    df = ak.stock_zh_a_spot_em()
    df["代码"] = df["代码"].astype(str).str.zfill(6)
    _log(f"  全市场: {len(df)} 只, 耗时 {time.time()-t0:.0f}s")
    return df


# ---------------------------------------------------------------------------
# 并发数据获取调度
# ---------------------------------------------------------------------------

def _fetch_financial_data_concurrent(params: dict) -> dict[str, pd.DataFrame]:
    """根据筛选条件，并发获取所需的财务数据"""
    need_roe = params.get("roe_min") is not None
    need_growth = params.get("profit_growth_min") is not None
    need_rev_growth = params.get("revenue_growth_min") is not None
    need_div = params.get("div_yield_min") is not None
    need_div_hist = params.get("consecutive_dividend_years") is not None
    need_debt = params.get("debt_ratio_max") is not None
    need_yjbb = need_roe or need_growth or need_rev_growth

    tasks: dict[str, callable] = {}
    if need_yjbb:
        tasks["yjbb"] = fetch_yjbb
    if need_div:
        tasks["fhps"] = fetch_fhps
    if need_debt:
        tasks["zcfz"] = fetch_zcfz
    if need_div_hist:
        tasks["divhist"] = fetch_dividend_history

    if not tasks:
        return {}

    results: dict[str, pd.DataFrame] = {}
    with ThreadPoolExecutor(max_workers=len(tasks)) as executor:
        future_map = {executor.submit(fn): name for name, fn in tasks.items()}
        for f in as_completed(future_map):
            name = future_map[f]
            try:
                results[name] = f.result()
            except Exception as e:
                _log(f"  {name} 获取失败: {e}")
                results[name] = pd.DataFrame()

    return results


# ---------------------------------------------------------------------------
# 筛选引擎
# ---------------------------------------------------------------------------

def run_screen(args) -> str:
    t_start = time.time()
    params, label, sort_key, sort_asc = _build_params(args)

    use_theme = args.theme or (args.strategy == "policy-theme")

    # --- 阶段 1: 并发获取行情 + 财务数据 ---
    with ThreadPoolExecutor(max_workers=2) as executor:
        if use_theme:
            pool_future = executor.submit(fetch_sector_pool_concurrent, args.theme)
        elif args.sector:
            pool_future = executor.submit(
                lambda: ak.stock_board_concept_cons_em(symbol=args.sector)
            )
        else:
            pool_future = executor.submit(fetch_all_stocks)

        fin_future = executor.submit(_fetch_financial_data_concurrent, params)

        base_df = pool_future.result()
        fin_data = fin_future.result()

    if base_df is None or base_df.empty:
        if use_theme:
            themes = _list_available_themes()
            return f"板块池为空。可用 --theme: {', '.join(themes)}"
        return "数据获取失败。"

    if args.sector and "代码" in base_df.columns:
        base_df["代码"] = base_df["代码"].astype(str).str.zfill(6)

    total_pool = len(base_df)
    source_label = f"{'板块池' if use_theme else ('板块 ' + args.sector if args.sector else '全市场')} {total_pool} 只"

    # --- 标准化行情列 ---
    base = pd.DataFrame({"代码": base_df["代码"]})
    base["名称"] = base_df.get("名称", "")
    base["最新价"] = pd.to_numeric(base_df.get("最新价"), errors="coerce")
    base["pe"] = pd.to_numeric(base_df.get("市盈率-动态"), errors="coerce")
    base["pb"] = pd.to_numeric(base_df.get("市净率"), errors="coerce")
    if "总市值" in base_df.columns:
        base["market_cap"] = pd.to_numeric(base_df["总市值"], errors="coerce") / 1e8
    if "涨跌幅" in base_df.columns:
        base["涨跌幅"] = pd.to_numeric(base_df["涨跌幅"], errors="coerce")

    # --- 阶段 2: 粗筛 PE/PB/ST/市值 ---
    mask = pd.Series(True, index=base.index)
    if not args.include_st:
        mask &= ~base["名称"].str.contains("ST|退", na=False, regex=True)

    pe_min = params.get("pe_min", 0)
    pe_max = params.get("pe_max")
    if pe_min is not None:
        mask &= base["pe"] > pe_min
    if pe_max is not None:
        mask &= base["pe"] <= pe_max
    if "pb_max" in params and "pb" in base.columns:
        mask &= (base["pb"] > 0) & (base["pb"] <= params["pb_max"])
    if "min_market_cap" in params and "market_cap" in base.columns:
        mask &= base["market_cap"] >= params["min_market_cap"]

    base = base[mask].copy()
    coarse_count = len(base)
    _log(f"粗筛: {source_label} → {coarse_count} 只")

    if coarse_count == 0:
        return f"# 选股结果：{label}\n\n粗筛后无符合条件的股票。请放宽条件。"

    # --- 阶段 3: merge 财务数据 ---
    if "yjbb" in fin_data and not fin_data["yjbb"].empty:
        base = base.merge(fin_data["yjbb"], on="代码", how="left")
    if "fhps" in fin_data and not fin_data["fhps"].empty:
        base = base.merge(fin_data["fhps"], on="代码", how="left")
    if "zcfz" in fin_data and not fin_data["zcfz"].empty:
        base = base.merge(fin_data["zcfz"], on="代码", how="left")
    if "divhist" in fin_data and not fin_data["divhist"].empty:
        base = base.merge(fin_data["divhist"], on="代码", how="left")

    # --- 阶段 4: 向量化精筛 ---
    mask2 = pd.Series(True, index=base.index)

    if params.get("div_yield_min") is not None:
        mask2 &= base.get("div_yield", pd.Series(dtype=float)).fillna(0) >= params["div_yield_min"]
    if params.get("consecutive_dividend_years") is not None:
        mask2 &= base.get("分红次数", pd.Series(dtype=float)).fillna(0) >= params["consecutive_dividend_years"]
    if params.get("roe_min") is not None:
        mask2 &= base.get("roe", pd.Series(dtype=float)).fillna(0) >= params["roe_min"]
    if params.get("profit_growth_min") is not None:
        mask2 &= base.get("profit_growth", pd.Series(dtype=float)).fillna(-999) >= params["profit_growth_min"]
    if params.get("revenue_growth_min") is not None:
        mask2 &= base.get("revenue_growth", pd.Series(dtype=float)).fillna(-999) >= params["revenue_growth_min"]
    if params.get("debt_ratio_max") is not None:
        mask2 &= base.get("debt_ratio", pd.Series(dtype=float)).fillna(999) <= params["debt_ratio_max"]

    base = base[mask2].copy()
    fine_count = len(base)
    _log(f"精筛: {coarse_count} → {fine_count} 只")

    # --- 排序 + 输出 ---
    if sort_key in base.columns:
        base = base.sort_values(sort_key, ascending=sort_asc, na_position="last")

    top_n = min(args.top, len(base))
    base = base.head(top_n)

    elapsed = time.time() - t_start
    _log(f"总耗时: {elapsed:.0f}s")

    return _format_output(base, label, total_pool, coarse_count, fine_count, top_n, params, elapsed)


# ---------------------------------------------------------------------------
# 参数构建
# ---------------------------------------------------------------------------

def _build_params(args) -> tuple[dict, str, str, bool]:
    if args.strategy:
        strategy = STRATEGIES[args.strategy]
        params = dict(strategy["defaults"])
        label = strategy["label"]
        default_sort = strategy["default_sort"]
        sort_asc = strategy["default_sort_asc"]
    else:
        params = {"pe_min": 0}
        label = "自定义筛选"
        default_sort = "pe"
        sort_asc = True

    if args.pe_max is not None:
        params["pe_max"] = args.pe_max
    if args.pe_min is not None:
        params["pe_min"] = args.pe_min
    if args.pb_max is not None:
        params["pb_max"] = args.pb_max
    if args.min_market_cap != 50 or "min_market_cap" not in params:
        params["min_market_cap"] = args.min_market_cap
    if args.roe_min is not None:
        params["roe_min"] = args.roe_min
    if args.div_yield_min is not None:
        params["div_yield_min"] = args.div_yield_min
    if args.debt_ratio_max is not None:
        params["debt_ratio_max"] = args.debt_ratio_max
    if args.revenue_growth_min is not None:
        params["revenue_growth_min"] = args.revenue_growth_min
    if args.profit_growth_min is not None:
        params["profit_growth_min"] = args.profit_growth_min
    if args.consecutive_div_years is not None:
        params["consecutive_dividend_years"] = args.consecutive_div_years

    if args.theme and "pe_max" not in params:
        params["pe_max"] = 80

    sort_k = args.sort or default_sort
    if args.div_yield_min is not None and args.sort is None:
        sort_k = "div_yield"
        sort_asc = False
    elif args.roe_min is not None and args.sort is None and args.div_yield_min is None:
        sort_k = "roe"
        sort_asc = False

    return params, label, sort_k, sort_asc


# ---------------------------------------------------------------------------
# 输出格式化
# ---------------------------------------------------------------------------

def _format_output(df: pd.DataFrame, label: str,
                   total: int, coarse: int, fine: int,
                   top_n: int, params: dict, elapsed: float = 0) -> str:
    lines = [f"# 选股结果：{label}\n"]
    lines.append(f"股票池 {total} 只 → 粗筛 {coarse} 只 → 精筛 {fine} 只 → 展示 Top {top_n}")
    if elapsed:
        lines.append(f"（耗时 {elapsed:.0f} 秒）")
    lines.append("")

    cond_parts = []
    if "pe_max" in params:
        cond_parts.append(f"PE≤{params['pe_max']}")
    if "roe_min" in params:
        cond_parts.append(f"ROE≥{params['roe_min']}%")
    if "div_yield_min" in params:
        cond_parts.append(f"股息率≥{params['div_yield_min']}%")
    if "consecutive_dividend_years" in params:
        cond_parts.append(f"分红≥{params['consecutive_dividend_years']}次")
    if "profit_growth_min" in params:
        cond_parts.append(f"利润增速≥{params['profit_growth_min']}%")
    if "revenue_growth_min" in params:
        cond_parts.append(f"营收增速≥{params['revenue_growth_min']}%")
    if "debt_ratio_max" in params:
        cond_parts.append(f"负债率≤{params['debt_ratio_max']}%")
    if cond_parts:
        lines.append(f"筛选条件：{' | '.join(cond_parts)}\n")

    if len(df) == 0:
        lines.append("未找到符合条件的股票。建议放宽条件重试。")
        return "\n".join(lines)

    display_cols = [
        ("代码", "代码"), ("名称", "名称"), ("最新价", "最新价"),
        ("pe", "PE(动)"), ("pb", "PB"),
    ]
    if "market_cap" in df.columns and df["market_cap"].notna().any():
        display_cols.append(("market_cap", "市值(亿)"))
    if "roe" in df.columns and df["roe"].notna().any():
        display_cols.append(("roe", "ROE(%)"))
    if "div_yield" in df.columns and df["div_yield"].notna().any():
        display_cols.append(("div_yield", "股息率(%)"))
    if "分红次数" in df.columns and df["分红次数"].notna().any():
        display_cols.append(("分红次数", "分红次数"))
    if "profit_growth" in df.columns and df["profit_growth"].notna().any():
        display_cols.append(("profit_growth", "利润增速(%)"))
    if "revenue_growth" in df.columns and df["revenue_growth"].notna().any():
        display_cols.append(("revenue_growth", "营收增速(%)"))
    if "debt_ratio" in df.columns and df["debt_ratio"].notna().any():
        display_cols.append(("debt_ratio", "负债率(%)"))

    col_keys = [c[0] for c in display_cols]
    col_labels = [c[1] for c in display_cols]

    header = "| 排名 | " + " | ".join(col_labels) + " |"
    sep = "|---" + "|---" * len(col_labels) + "|"
    lines.extend([header, sep])

    for rank, (_, row) in enumerate(df.iterrows(), 1):
        vals = []
        for key in col_keys:
            v = row.get(key)
            if v is None or (isinstance(v, float) and pd.isna(v)):
                vals.append("-")
            elif isinstance(v, float):
                if abs(v) >= 10000:
                    vals.append(f"{v:.0f}")
                else:
                    vals.append(f"{v:.2f}")
            else:
                vals.append(str(v))
        lines.append(f"| {rank} | " + " | ".join(vals) + " |")

    return "\n".join(lines)


def _list_available_themes() -> list[str]:
    if not os.path.exists(SECTORS_FILE):
        return []
    with open(SECTORS_FILE, "r", encoding="utf-8") as f:
        return list(json.load(f).keys())


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="A 股选股筛选器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "预设策略 (可选，提供默认条件基线):\n"
            "  high-dividend   高分红策略（股息率>=3%%, 连续分红>=3次）\n"
            "  value-quality   价值优选策略（PE<=25, ROE>=12%%, 低负债）\n"
            "  policy-theme    政策主题策略（十五五规划相关板块）\n"
            "\n"
            "策略和自定义参数可组合，用户参数覆盖策略默认值。\n"
            "\n"
            "示例:\n"
            "  screener.py --strategy high-dividend\n"
            "  screener.py --theme 半导体 --pe-max 20 --roe-min 10\n"
            "  screener.py --theme 新能源 --div-yield-min 2 --roe-min 10\n"
            "  screener.py --pe-max 20 --roe-min 15 --debt-ratio-max 50\n"
        ),
    )

    parser.add_argument("--strategy", "-s", choices=list(STRATEGIES.keys()),
                        help="预设策略 (可选)")
    parser.add_argument("--theme",
                        help="政策主题方向 (sectors.json 中的键名)")
    parser.add_argument("--sector", help="限定概念板块名称")
    parser.add_argument("--top", type=int, default=30, help="输出前 N 只 (默认 30)")
    parser.add_argument("--sort", help="排序字段: roe/pe/div_yield/market_cap")

    parser.add_argument("--pe-max", type=float, help="PE 上限")
    parser.add_argument("--pe-min", type=float, default=0, help="PE 下限 (默认 0)")
    parser.add_argument("--pb-max", type=float, help="PB 上限")
    parser.add_argument("--roe-min", type=float, help="ROE 下限")
    parser.add_argument("--div-yield-min", type=float, help="股息率下限")
    parser.add_argument("--debt-ratio-max", type=float, help="负债率上限")
    parser.add_argument("--revenue-growth-min", type=float, help="营收增速下限")
    parser.add_argument("--profit-growth-min", type=float, help="净利增速下限")
    parser.add_argument("--consecutive-div-years", type=int,
                        help="最少连续分红次数")
    parser.add_argument("--min-market-cap", type=float, default=50,
                        help="最低市值(亿, 默认 50)")
    parser.add_argument("--include-st", action="store_true",
                        help="包含 ST 股票")

    args = parser.parse_args()

    if not args.strategy and not args.theme and not args.sector:
        has_any = any([
            args.pe_max, args.pb_max, args.roe_min, args.div_yield_min,
            args.debt_ratio_max, args.revenue_growth_min,
            args.profit_growth_min,
        ])
        if not has_any:
            parser.error("请指定 --strategy, --theme, --sector, 或至少一个筛选条件")

    print(run_screen(args))


if __name__ == "__main__":
    main()

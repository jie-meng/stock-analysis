---
name: stock-screener
description: >
  A 股选股筛选器。内置三种预设策略：高分红股（high-dividend）、价值优选（value-quality）、
  政策主题（policy-theme），也支持自定义条件组合筛选。通过 akshare 批量接口获取数据，
  采用"批量获取 → merge → 向量化筛选"架构，无逐个 API 调用。
  当用户提到选股、筛选股票、股票筛选、screener、找股票、符合条件的股票时触发。
  触发短语："帮我选股"、"筛选股票"、"选股"、"高分红股票"、"高股息"、
  "价值选股"、"低估值"、"好公司"、"十五五规划"、"政策主题"、
  "stock screener"、"find stocks"、"screen stocks"、"筛一下"、"选几只股票"。
---

# A 股选股筛选器

内置多种预设策略 + 自定义条件，从全市场筛选符合条件的股票。

## 架构

**并发批量获取 → merge → 向量化筛选**，无逐个股票 API 调用。

板块获取和财务数据并发执行，板块内部也并发。

数据源（均为批量接口）：

| 接口 | 耗时 | 返回内容 |
|------|------|---------|
| 东财 clist API（直调，绕过 akshare 的页间 sleep） | ~60s（27 板块并发） | 板块成分股 + PE/PB/市值 |
| `stock_yjbb_em` | ~80s | 全市场 ROE/EPS/利润增速/营收增速/毛利率 |
| `stock_fhps_em` | ~28s | 全市场股息率 |
| `stock_zcfz_em` | ~40s | 全市场资产负债率 |
| `stock_history_dividend` | ~3s | 全市场分红次数 |
| `stock_zh_a_spot_em` | ~7min | 全市场 PE/PB/市值（备选，仅无板块时使用） |

流程：
1. 并发：获取行情池（板块并发或全市场）+ 获取财务数据（yjbb/fhps/zcfz/divhist 并发）
2. PE/PB/ST/市值粗筛（向量化）
3. merge 财务数据（ROE、股息率、负债率、利润增速）
4. 向量化精筛 → 排序 → 输出

## 前置条件

```bash
pip install akshare pandas
```

## 使用方式

### 预设策略 + 自定义参数（可组合，用户参数覆盖策略默认值）

```bash
# 高分红策略
python .agents/skills/stock-screener/scripts/screener.py --strategy high-dividend

# 价值优选策略
python .agents/skills/stock-screener/scripts/screener.py --strategy value-quality

# 政策主题策略（全部十五五方向）
python .agents/skills/stock-screener/scripts/screener.py --strategy policy-theme

# 政策主题 + 自定义条件覆盖
python .agents/skills/stock-screener/scripts/screener.py --strategy policy-theme \
  --pe-max 20 --div-yield-min 2 --roe-min 10

# 单一主题方向（更快，~3 分钟）
python .agents/skills/stock-screener/scripts/screener.py --theme 新能源 --pe-max 20 --roe-min 10
```

### 自定义筛选

```bash
python .agents/skills/stock-screener/scripts/screener.py \
  --pe-max 20 --pb-max 3 --roe-min 15 --div-yield-min 2 \
  --sector 光伏概念
```

### 参数一览

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--strategy` | 预设策略：`high-dividend` / `value-quality` / `policy-theme` | 无 |
| `--theme` | 政策主题方向（sectors.json 的键名），可与 --strategy 组合 | 全部主题 |
| `--sector` | 限定单个概念板块 | 无 |
| `--top` | 输出前 N 只 | `30` |
| `--sort` | 排序字段：`roe` / `pe` / `div_yield` / `market_cap` | 策略默认 |
| `--pe-max` | 市盈率上限 | - |
| `--pe-min` | 市盈率下限 | `0` |
| `--pb-max` | 市净率上限 | - |
| `--roe-min` | ROE 下限（%） | - |
| `--div-yield-min` | 股息率下限（%） | - |
| `--profit-growth-min` | 净利增速下限（%） | - |
| `--consecutive-div-years` | 最少分红次数 | - |
| `--min-market-cap` | 最低市值（亿） | `50` |
| `--include-st` | 包含 ST 股票 | 默认排除 |

## 预设策略说明

### high-dividend（高分红策略）

| 条件 | 阈值 | 原因 |
|------|------|------|
| 股息率 | ≥ 3% | 高于多数理财产品收益 |
| 连续分红 | ≥ 3 次 | 分红持续性 |
| PE | 0 < PE ≤ 30 | 排除亏损和泡沫 |
| 市值 | ≥ 50 亿 | 流动性保障 |

### value-quality（价值优选策略）

| 条件 | 阈值 | 原因 |
|------|------|------|
| PE | 0 < PE ≤ 25 | 估值合理 |
| PB | ≤ 5 | 资产未严重高估 |
| ROE | ≥ 12% | 资本回报能力 |
| 净利润增速 | ≥ 0% | 盈利未恶化 |
| 负债率 | ≤ 60% | 财务安全 |

### policy-theme（政策主题策略）

可用 `--theme` 值：新能源、半导体、人工智能、生物医药、高端制造、数字经济、绿色经济

## 耗时参考

| 场景 | 预计耗时 |
|------|---------|
| 单板块 `--sector 光伏概念` | ~30 秒 |
| 单主题 `--theme 新能源` + 财务条件 | ~1.5 分钟 |
| 全主题 `--strategy policy-theme` + 全部条件 | ~1.5 分钟 |
| 全市场（无 theme/sector） | ~8-10 分钟 |

## 筛选结果审查：配合 market-context 技能（必做）

筛选器输出的是**候选名单**，不是推荐名单。拿到筛选结果后，必须用 `market-context` 技能对候选标的做行业环境审查：

### 审查步骤

1. **行业板块表现**：`context.py sector --keyword <行业关键词>`
   - 候选股所属行业板块近期涨跌幅如何？资金是在流入还是流出？
   - 行业板块走弱 + 个股低估值 = 可能是低估值陷阱

2. **上游商品价格**（资源/周期股必查）：`context.py commodity --symbols <品种>`
   - 原材料价格趋势直接影响周期股盈利预期
   - 铝业股看铝价（AL0）、铜业看铜价（CU0）、钢铁看铁矿石（I0）和螺纹钢（RB0）

3. **重大事件搜索**：用 **WebSearch** 搜索候选行业的最新动态
   - 地缘冲突、供给冲击、政策转向等"变量因素"可能让低 PE 的股票变成翻倍股，也可能让看似安全的股票暴跌

### 审查输出

在向用户展示筛选结果时，每个候选标的应附带：
- 所属行业当前景气度评估（基于板块走势和资金流数据）
- 关键变量因素提示（如有）
- 风险标注（如行业走弱、政策风险等）

## 注意事项

- 策略和自定义参数可组合，用户参数覆盖策略默认值
- ROE 使用东财业绩报表的加权净资产收益率（stock_yjbb_em），准确
- 筛选结果是进一步分析的起点，建议用 financial-data-analysis 和 technical-indicator 深入
- 政策主题板块映射在 `sectors.json`，可按需更新

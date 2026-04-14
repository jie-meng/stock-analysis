---
name: financial-data-analysis
description: >
  分析股票财务数据，计算关键财务指标（PE、PB、ROE、毛利率、负债率等），
  生成财务健康评估报告。通过 akshare 获取 A 股上市公司财务报表数据。
  当用户提到基本面分析、财务分析、财报、财务指标、估值分析、PE/PB/ROE、
  利润表、资产负债表、现金流量表、年报、季报，或要求判断一家公司财务状况时触发。
  触发短语："分析财务"、"看看基本面"、"财务数据"、"估值如何"、"值不值得买"、
  "financial analysis"、"fundamental analysis"、"valuation"、"financial health"。
---

# 财务数据分析

获取 A 股上市公司财务报表，计算核心财务指标，生成可读的财务分析摘要。

## 前置条件

```bash
pip install akshare pandas
```

## 使用方式

```bash
# 分析单只股票的财务数据
python .agents/skills/financial-data-analysis/scripts/finance.py <股票代码> [--years 3]

# 获取特定报表
python .agents/skills/financial-data-analysis/scripts/finance.py <股票代码> --report balance
python .agents/skills/financial-data-analysis/scripts/finance.py <股票代码> --report income
python .agents/skills/financial-data-analysis/scripts/finance.py <股票代码> --report cashflow

# 包含最新业绩快报/预告
python .agents/skills/financial-data-analysis/scripts/finance.py <股票代码> --earnings

# 包含估值上下文（PE/PB 历史分位）
python .agents/skills/financial-data-analysis/scripts/finance.py <股票代码> --valuation

# 全部输出（财务 + 报表 + 业绩快报 + 估值分位）
python .agents/skills/financial-data-analysis/scripts/finance.py <股票代码> --full
```

### 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| 股票代码 | 6 位纯数字，如 `600519`、`000001` | 必填 |
| `--years` | 分析最近几年的数据 | `3` |
| `--report` | 指定报表：`balance` / `income` / `cashflow` / `all` | `all` |
| `--earnings` | 输出最新业绩快报和业绩预告 | 不输出 |
| `--valuation` | 输出 PE/PB 近一年历史分位数 | 不输出 |
| `--full` | 输出全部信息（等价于 --earnings --valuation） | 不输出 |

### 输出内容

脚本输出结构化的 Markdown 格式分析报告，包含：

1. **估值指标**：市盈率（PE）、市净率（PB）、市销率（PS）
2. **盈利能力**：净资产收益率（ROE）、毛利率、净利率
3. **成长性**：营收增长率、净利润增长率
4. **财务安全**：资产负债率、流动比率、速动比率
5. **现金流**：经营现金流/净利润比率
6. **最新业绩**（--earnings）：业绩快报（自动搜索最近已披露的报告期）和业绩预告
7. **估值上下文**（--valuation）：PE(TTM)/PB 近一年分位数、最高/最低/中位数

## 分析框架参考

在向用户呈现分析结果时，可参考以下判断标准：

| 指标 | 优秀 | 良好 | 关注 |
|------|------|------|------|
| ROE | > 15% | 10-15% | < 10% |
| 毛利率 | > 40% | 20-40% | < 20% |
| 资产负债率 | < 40% | 40-60% | > 60% |
| 营收增长率 | > 20% | 10-20% | < 0% |
| 经营现金流/净利润 | > 1.0 | 0.7-1.0 | < 0.7 |

不同行业的标准有差异，金融、地产行业的负债率天然较高，需结合行业特性判断。

## 配合市场环境上下文使用（推荐）

财务数据反映的是过去的经营结果。为避免脱离市场环境的孤立分析，
**建议在财务分析前或分析后**，配合 `market-context` 技能补充以下信息：

| 补充数据 | 命令 | 分析价值 |
|---------|------|---------|
| 所属行业板块走势 | `context.py sector --keyword <行业>` | 行业整体是在走强还是走弱，个股表现是跑赢还是跑输行业 |
| 板块资金流向 | 同上（输出含资金流） | 主力资金是在流入还是流出该行业 |
| 上游原材料价格 | `context.py commodity --symbols <品种>` | 对资源/制造业公司，原材料价格直接影响毛利率和盈利预期 |
| 个股最新新闻 | `context.py news --code <代码>` | 是否有重大事件可能改变财务预期（并购、政策、事故等） |
| 最新行业事件 | **WebSearch** 搜索 | 地缘政治、政策变化等财报无法反映的变量因素 |

**典型场景**：用户问"银泰铝业基本面怎么样"→ 除了看财报，还应该看铝价走势（`commodity --symbols AL0`）、
有色金属板块资金流（`sector --keyword 铝`）、最新新闻和地缘事件。
这些"变量因素"可能比历史财报数字更能决定未来走势。

## 注意事项

- 股票代码使用纯 6 位数字（不带 sh/sz 前缀）
- akshare 获取的是公开披露的财报数据，可能有数据延迟
- 首次运行可能需要较长时间下载数据
